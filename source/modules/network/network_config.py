"""
Configurações centralizadas para a infraestrutura de rede do TAC3 (LAN Multiplayer).
"""

# Configurações de Conexão e Portas
DEFAULT_HOST: str = "127.0.0.1"
DEFAULT_TCP_PORT: int = 7777
DEFAULT_UDP_PORT: int = 7778

# Limites de Participantes e Sessão
MAX_PLAYERS: int = 2
PROTOCOL_VERSION: int = 1
MAX_NAME_LENGTH: int = 16

# Limites de Pacotes e Segurança
MAX_PACKET_SIZE: int = 1024          # 1 KB por datagrama/mensagem
MAX_PAYLOAD_SIZE: int = 800

# Temporizadores e Frequências
CONNECTION_TIMEOUT: float = 5.0     # Segundos sem resposta antes de timeout
PING_INTERVAL: float = 1.0          # Intervalo entre pings de medição de latência
SIMULATION_TICK_RATE: int = 60      # 60 Hz no servidor (física e lógica autoritativa)
NETWORK_SYNC_RATE: int = 25         # 25 Hz de envio de snapshots de estado (broadcast UDP)

# Interpolação e Suavização de Movimento no Cliente
INTERPOLATION_DELAY: float = 0.100  # 100 ms de atraso para absorver jitter da rede LAN
SNAPSHOT_BUFFER_MAX_SIZE: int = 60  # Capacidade máxima do buffer histórico (~2.4 segundos)
SNAP_DISTANCE_THRESHOLD: float = 200.0  # Limiar para snap direto (teleporte/respawn)
