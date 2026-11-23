"""Sessão UDP LAN; o anfitrião encaminha as posições dos jogadores."""

import ipaddress
import json
import socket
import time

PORT = 27830
TIMEOUT = 4
MAX_CLIENTS = 7


class LanSession:
    def __init__(self, address=None, port=PORT):
        self.host = address is None
        self.server = None if self.host else (str(ipaddress.IPv4Address(address)), port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self.socket.bind(("", port if self.host else 0))
            self.socket.setblocking(False)
        except OSError:
            self.socket.close()
            raise
        self.peers = {}
        self.players = []
        self.last_reply = time.monotonic()
        self.next_send = 0.0
        self.connected = self.host

    def close(self):
        if self.host:
            for address in self.peers:
                self.send(["ctrl-revolt-server-closed-v1", None], address)
        else:
            self.send(["ctrl-revolt-leave-v1", None], self.server)
        self.socket.close()

    def send(self, packet, target):
        try:
            self.socket.sendto(json.dumps(packet).encode("ascii"), target)
        except OSError:
            pass

    @staticmethod
    def valid_position(value):
        return (
            isinstance(value, list) and len(value) == 3
            and all(type(part) is int for part in value)
            and -128 <= value[0] <= 4096 and -1024 <= value[1] <= 2048
            and value[2] in (-1, 1)
        )

    def tick(self, position):
        now = time.monotonic()
        for _ in range(32):
            try:
                raw, sender = self.socket.recvfrom(512)
            except OSError:
                break
            if not self.host and sender != self.server:
                continue
            try:
                packet = json.loads(raw)
            except (ValueError, RecursionError):
                continue
            if not isinstance(packet, list) or len(packet) != 2:
                continue
            kind, data = packet
            if self.host and kind == "ctrl-revolt-position-v1" and self.valid_position(data):
                if sender in self.peers or len(self.peers) < MAX_CLIENTS:
                    self.peers[sender] = (now, data)
            elif self.host and kind == "ctrl-revolt-leave-v1":
                self.peers.pop(sender, None)
            elif not self.host and kind == "ctrl-revolt-server-closed-v1":
                self.connected = False
                self.players = []
                return False
            elif not self.host and kind == "ctrl-revolt-players-v1":
                if isinstance(data, list) and len(data) <= MAX_CLIENTS and all(map(self.valid_position, data)):
                    self.players = data
                    self.last_reply = now
                    self.connected = True

        if self.host:
            self.peers = {address: entry for address, entry in self.peers.items() if now - entry[0] < TIMEOUT}
            self.players = [entry[1] for entry in self.peers.values()]

        if now >= self.next_send:
            self.next_send = now + 0.05
            if self.host:
                for address in self.peers:
                    others = [entry[1] for peer, entry in self.peers.items() if peer != address]
                    self.send(["ctrl-revolt-players-v1", [position, *others]], address)
            else:
                self.send(["ctrl-revolt-position-v1", position], self.server)
        return self.host or now - self.last_reply < TIMEOUT
