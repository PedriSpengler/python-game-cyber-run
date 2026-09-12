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
| Reiniciar após fim | `Enter` |
| Menu/voltar | `Esc` |

## Testes e ativos

```powershell
python -m unittest discover -s tests
python scripts/generate_sounds.py
```

Os sprites são pixel art gerada em memória por matrizes no módulo `game.systems.assets`. Os cinco efeitos `.wav` foram sintetizados pelo script incluído, sem material protegido de terceiros.

O relatório está em `docs/GDD_CTRL_REVOLT.pdf`. Antes da entrega, substitua os campos amarelos com nomes, contribuições e URL real do GitHub; depois rode `python scripts/build_report.py` para atualizar o PDF.

## Estrutura

```text
game/
├── components/ # vida reutilizável
├── core/       # loop principal
├── entities/   # jogador, inimigos, itens e projéteis
├── scenes/     # menu, gameplay e resultado
├── systems/    # física, dinâmica, combate, áudio e sprites
├── ui/         # HUD
└── world/      # dados da fase, cenário e plataformas
```
