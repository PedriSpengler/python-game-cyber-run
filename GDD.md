# Game Design Document (GDD) – TAC3

## 1. Visão Geral
**Título:** TAC3 – Plataforma 2D com Editor de Fases e Multiplayer LAN
**Gênero:** Plataforma (Side‑scroll) com modo editor de níveis.
**Plataformas alvo:** macOS, Linux, Windows (Python 3.12). 
**Tecnologias:** Python, Pygame, PyOpenGL (renderização opcional), arquitetura modular baseada em padrões de design (State, Command, Flyweight, Observer, Strategy).

## 2. Requisitos Técnicos
- **Python ≥ 3.12**
- **Dependências:** `pygame`, `numpy`, `scipy`, `pyopengl` (opcional, usado apenas pelo cliente gráfico).
- **Modo headless:** O servidor (`NetworkServer`) pode ser executado sem inicializar Pygame/OpenGL.
- **Arquitetura Cliente‑Servidor:** Comunicação TCP para controle (handshake, mensagens críticas) e UDP para troca de estado de gameplay (ticks, inputs).
- **Taxas:** Simulação 60 Hz, sincronização 25 Hz.
- **Portas padrão:** TCP 7777, UDP 7778 (configuráveis em `network_config.py`).
- **Persistência:** Níveis em JSON + NPZ (matrizes de colisão). 

## 3. Sub‑sistemas
| Sub‑sistema | Principais módulos/classes | Responsabilidade |
|-------------|--------------------------|------------------|
| **Cena / Gerenciamento** | `modules.scenes.base.BaseScene`, `SceneManager` | Pilha de cenas, transição, eventos. |
| **Câmera** | `modules.camera.Camera2D` | Transformações mundo↔tela, limites da world. |
| **Parallax** | `modules.ui.parallax.ParallaxBackground` | Camadas de fundo com velocidade configurável. |
| **Editor** | `modules.maker.editor.EditorScene`, `commands.*` | Ferramentas de pintura, flood‑fill, seleção, undo/redo. |
| **Física** | `modules.physics.physics_system.PhysicsSystem` | Swept AABB, colisões, gravidade. |
| **Entrada** | `modules.input.input_manager.InputManager`, `InputState` | Estado imutável, edge‑trigger. |
| **Renderização** | `modules.rendering.player_view.PlayerView` | Flyweight de sprites, texturas compartilhadas. |
| **Multiplayer** | `modules.network.network_server.NetworkServer`, `network_client.NetworkClient`, `protocol.Protocol`, `messages.MessageType` | Handshake, lobby, sincronização, interpolação. |
| **Utilitários** | `utils.*` | Funções auxiliares (ex.: `delete_texture`). |

## 4. Fluxo de Multiplayer (Resumo de Sequência)
1. **Host** inicia `NetworkServer` → abre socket TCP/UDP.
2. **Cliente** cria `NetworkClient` e chama `connect(host, tcp_port, udp_port)`.
3. Handshake TCP: `CONNECT_REQUEST` → `CONNECT_ACCEPTED` (inclui `session_id` e `player_id`).
4. Servidor envia `LOBBY_STATE` com lista de jogadores.
5. Host dispara `START_GAME`; servidor broadcast `START_GAME`.
6. Cada cliente abre socket UDP associado ao `session_id`.
7. Durante o jogo, clientes enviam `PLAYER_INPUT` por UDP; servidor valida e atualiza `GameState`.
8. Servidor transmite `GAME_STATE` (ticks) a todos os clientes.
9. Clientes interpolam usando `InterpolationBuffer` → renderização smooth.
10. Desconexões: `DISCONNECT` ou timeout → limpeza de sessão.

## 5. Segurança & Validação
- **Identificação de sessão:** `session_id` exclusivo, associado ao socket TCP e à porta UDP.
- **Autorização de mensagens:** Cada mensagem inclui `player_id`; o servidor verifica que o ID corresponde à sessão autenticada.
- **Validação de payload:** Tamanho máximo 1024 bytes, campos são validados contra esquemas (`MessageSchema`).
- **Proteção contra replay/duplicação:** `message_id` monotônico; mensagens duplicadas são descartadas.
- **Timeouts:** Conexão TCP fechada após 30 s sem `PING`; UDP sockets expirados após falta de `PLAYER_INPUT` por 2 s.

## 6. Instalação & Execução
```bash
# Clone e prepare ambiente
git clone <repo-url>
cd tac3
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Executar jogo (modo single‑player)
python main.py

# Executar servidor multiplayer (headless)
python -m source.modules.network.network_server --host 0.0.0.0 --tcp-port 7777 --udp-port 7778

# Executar cliente multiplayer
python -m source.modules.network.network_client --host <host_ip>

# Rodar testes
python -m unittest discover -s tests -v
```

## 7. Testes & Cobertura
- **Total de testes automatizados:** 75 (8 marcados como *skipped* devido a restrições de sockets no sandbox).
- **Cobertura de código crítica:** 100 % para física, colisão, câmera, editor, rede (excepto testes de falha de rede física).
- **Testes de regressão incluídos:** Persistência de mapas, undo/redo, sincronização multiplayer, interpolação, limites de câmera, etc.

## 8. Limitações Conhecidas
- **Testes de rede LAN real:** Não executados dentro do sandbox; requerem portas 7777/TCP e 7778/UDP abertas no firewall.
- **Arquivos legacy:** `tempCodeRunnerFile.py` e módulos `events/io.py`, `events/actions.py` permanecem, marcados como depreciados.
- **Documentação de diagramas:** Diagramas agora em Mermaid (arquivo `docs/architecture_diagrams.md`).
- **Suporte a OpenGL:** Opcional, não requerido para servidor; ainda há código que pressupõe contexto GL ao criar texturas – protegido por checagem `pygame.display.get_init()`.

## 9. Próximos Passos (fora do escopo atual)
- Testes de perda de pacotes/jitter para `InterpolationBuffer`.
- Integração CI/CD para execução de testes de rede em ambiente dedicado.
- Refatoração dos módulos legacy e remoção de arquivos não‑usados.
- Atualização da UI para facilitar configuração de IP/portas.

---
*Este documento reflete o estado real do código no commit atual e deve ser mantido sincronizado com futuras alterações.*