from dataclasses import dataclass


@dataclass(frozen=True)
class InputState:
    """
    Estrutura imutável de comandos do jogador para determinado tick de simulação.
    Isolada de qualquer dependência gráfica ou de rede.
    """
    move_x: int = 0          # -1 (Esquerda), 0 (Parado), +1 (Direita)
    jump: bool = False       # True apenas no frame em que o pulo é pressionado (Edge Trigger)
    jump_held: bool = False  # True enquanto o botão de pulo estiver sendo mantido pressionado
    action: bool = False     # Botão de ação/interação futura
    tick: int = 0            # Número sequencial do tick (preparação para rede)
