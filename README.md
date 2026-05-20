# TicTacToe

A terminal TicTacToe game with a text-based UI built in Python using [Textual](https://textual.textualize.io/).

![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![Textual](https://img.shields.io/badge/textual-8.x-green)

## Features

- **Two game modes** — play against a friend or challenge the AI
- **Unbeatable AI** — uses the minimax algorithm; best you can do is draw
- **Keyboard-driven** — navigate the board with arrow keys, place pieces with Enter
- **Win celebration** — the winning cells flash when the game ends
- **Pause / resume** — step away mid-game without losing your position
- **Instant reset** — start a new game at any time with a single key

## Requirements

- Python 3.9 or later
- pip

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-username/TicTacToe.git
cd TicTacToe

# 2. Create and activate a virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux
.venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt
```

## Starting the game

```bash
python main.py
```

You will be presented with a mode selection screen. Use the mouse or Tab + Enter to choose a mode:

| Mode | Description |
|---|---|
| **2 Players** | Two humans take turns on the same terminal |
| **vs AI** | You play as X against the computer (O) |

## Controls

| Key | Action |
|---|---|
| Arrow keys | Move the cursor around the board |
| Enter / Space | Place your piece on the highlighted cell |
| `R` | Reset the game and start over |
| `P` | Pause / unpause |
| `Q` | Quit the game |

## Stopping the game

Press `Q` at any time to exit cleanly, or use `Ctrl+C` in the terminal.

To deactivate the virtual environment when you are done:

```bash
deactivate
```

## How to play

1. The board is a 3×3 grid. Player X always goes first.
2. Use the arrow keys to move the yellow-highlighted cursor to an empty cell.
3. Press Enter or Space to place your piece.
4. The first player to get three of their pieces in a row (horizontal, vertical, or diagonal) wins.
5. If all nine cells are filled with no winner, the game is a draw.
6. When the game ends the winning cells flash. Press `R` to play again or `Q` to quit.

## Project structure

```
TicTacToe/
├── main.py          # Textual TUI — screens, widgets, key bindings
├── game.py          # Pure game logic — board, win detection, minimax AI
└── requirements.txt # Python dependencies
```

## License

MIT
