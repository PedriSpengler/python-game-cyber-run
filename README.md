# CTRL//REVOLT: Industrial Cyber-Run

Protótipo acadêmico de plataforma 2D no estilo *run and gun*, desenvolvido em Python com Pygame. Alex Byte, um engenheiro renegado, invade a infraestrutura da OmniCore para derrubar a inteligência artificial autoritária CENTINELA.

## Executar no Windows

1. Instale Python 3.11 ou superior e marque **Add Python to PATH**.
2. Abra o PowerShell nesta pasta.
3. Crie e ative o ambiente virtual:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

4. Execute:

```powershell
python main.py
```

## Controles

| Ação | Teclas |
|---|---|
| Mover | `A`/`D` |
| Pular/pulo duplo | `W` ou `Espaço` |
| Mirar em oito direções | Setas |
| Atirar | `J` (segure) |
| Dash | `K` |
| Overclock | `L` |
| Escudo antivírus | `I` |
| Alternar tela cheia/janela | `F11` |
| Reiniciar após fim | `Enter` |
| Voltar ao menu na tela de resultado | `M` |
| Voltar ou sair, conforme a tela | `Esc` |

## Editor e multiplayer LAN

- **Editor de fases** permite posicionar plataformas, início, saída, inimigos e itens. Use `Ctrl+Z` para desfazer, `Ctrl+S` para salvar e `Enter` para testar.
- **Hospedar partida LAN** abre uma sessão na porta UDP 27830. Em outro dispositivo na mesma rede, escolha **Entrar em partida LAN** e informe o IPv4 do anfitrião. A sessão comporta até oito jogadores e compartilha a posição e a direção dos avatares.
- **Configurações** ajusta e salva o volume dos efeitos.

## Testes e ativos

```powershell
python -m unittest discover -s tests
python scripts/generate_sounds.py
```

Os sprites são pixel art gerada em memória por matrizes no módulo `game.systems.assets`. Os cinco efeitos `.wav` foram sintetizados pelo script incluído, sem material protegido de terceiros.

O GDD está disponível em [PDF](docs/GDD_CTRL_REVOLT.pdf) e [HTML](docs/GDD_CTRL_REVOLT.html). Após editar o HTML, execute `python scripts/build_report.py` para regenerar o PDF. A [apresentação do projeto](docs/CTRL-REVOLT-Apresentacao.pptx) também está na pasta de documentação.

## Estrutura

```text
game/
├── components/ # vida reutilizável
├── core/       # loop principal
├── entities/   # jogador, inimigos, itens e projéteis
├── scenes/     # menu, editor, partida e resultado
├── systems/    # física, combate, áudio, sprites, persistência e LAN
├── ui/         # HUD
└── world/      # dados da fase, cenário e plataformas
```
