from __future__ import annotations

from enum import Enum, auto

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.screen import ModalScreen, Screen
from textual.timer import Timer
from textual.widget import Widget
from textual.widgets import Button, Label, Static

from game import EMPTY, PLAYER_O, PLAYER_X, GameState, get_ai_move


class GameMode(Enum):
    TWO_PLAYER = auto()
    VS_AI = auto()


class CellWidget(Static):
    DEFAULT_CSS = """
    CellWidget {
        width: 7;
        height: 3;
        border: solid $primary;
        background: $surface;
        content-align: center middle;
        text-style: bold;
    }
    CellWidget.cursor {
        border: solid yellow;
        background: $boost;
    }
    CellWidget.winner {
        background: $success;
        color: $text;
    }
    CellWidget.winner-off {
        background: $surface;
        color: $text;
    }
    """

    class Selected(Message):
        def __init__(self, cell_index: int) -> None:
            super().__init__()
            self.cell_index = cell_index

    def __init__(self, cell_index: int, **kwargs) -> None:
        super().__init__(" ", **kwargs)
        self.cell_index = cell_index

    def on_click(self) -> None:
        self.post_message(self.Selected(self.cell_index))


class BoardWidget(Widget, can_focus=True):
    cursor_row: reactive[int] = reactive(0)
    cursor_col: reactive[int] = reactive(0)

    DEFAULT_CSS = """
    BoardWidget {
        layout: grid;
        grid-size: 3 3;
        grid-columns: 7 7 7;
        grid-rows: 3 3 3;
        width: 21;
        height: 9;
    }
    """

    BINDINGS = [
        Binding("up",    "cursor_up",    "", show=False),
        Binding("down",  "cursor_down",  "", show=False),
        Binding("left",  "cursor_left",  "", show=False),
        Binding("right", "cursor_right", "", show=False),
        Binding("enter", "confirm",      "", show=False),
        Binding("space", "confirm",      "", show=False),
    ]

    class MoveMade(Message):
        def __init__(self, cell: int) -> None:
            super().__init__()
            self.cell = cell

    def compose(self) -> ComposeResult:
        for i in range(9):
            yield CellWidget(cell_index=i, id=f"cell-{i}")

    def on_mount(self) -> None:
        self._refresh_cursor()

    def _cell(self, row: int, col: int) -> CellWidget:
        return self.query_one(f"#cell-{row * 3 + col}", CellWidget)

    def _refresh_cursor(self) -> None:
        for cell in self.query(CellWidget):
            cell.remove_class("cursor")
        self._cell(self.cursor_row, self.cursor_col).add_class("cursor")

    def watch_cursor_row(self) -> None:
        self._refresh_cursor()

    def watch_cursor_col(self) -> None:
        self._refresh_cursor()

    def update_cell(self, cell_index: int, symbol: str) -> None:
        self.query_one(f"#cell-{cell_index}", CellWidget).update(symbol)

    def action_cursor_up(self)    -> None: self.cursor_row = max(0, self.cursor_row - 1)
    def action_cursor_down(self)  -> None: self.cursor_row = min(2, self.cursor_row + 1)
    def action_cursor_left(self)  -> None: self.cursor_col = max(0, self.cursor_col - 1)
    def action_cursor_right(self) -> None: self.cursor_col = min(2, self.cursor_col + 1)

    def action_confirm(self) -> None:
        self.post_message(self.MoveMade(self.cursor_row * 3 + self.cursor_col))

    def on_cell_widget_selected(self, event: CellWidget.Selected) -> None:
        self.cursor_row = event.cell_index // 3
        self.cursor_col = event.cell_index % 3
        self.post_message(self.MoveMade(event.cell_index))


class PauseModal(ModalScreen[None]):
    DEFAULT_CSS = """
    PauseModal {
        align: center middle;
    }
    PauseModal > Vertical {
        width: 28;
        height: auto;
        border: double $warning;
        background: $surface;
        padding: 1 2;
        align: center middle;
    }
    PauseModal #pause-title {
        text-style: bold;
        content-align: center middle;
        width: 100%;
        height: 1;
        margin-bottom: 1;
    }
    PauseModal Button {
        width: 100%;
        margin-top: 1;
    }
    """

    BINDINGS = [
        Binding("p", "resume",   "Resume", priority=True),
        Binding("q", "quit_app", "Quit",   priority=True),
    ]

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("PAUSED", id="pause-title")
            yield Button("Resume  (P)", id="resume-btn", variant="primary")
            yield Button("Quit Game  (Q)", id="quit-btn", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "resume-btn":
            self.dismiss()
        else:
            self.app.exit()

    def action_resume(self) -> None:
        self.dismiss()

    def action_quit_app(self) -> None:
        self.app.exit()


class GameScreen(Screen):
    CSS = """
    GameScreen {
        align: center middle;
    }
    #game-container {
        width: 40;
        height: auto;
        align: center middle;
        layout: vertical;
    }
    #title {
        text-style: bold;
        content-align: center middle;
        width: 100%;
        height: 1;
        margin-bottom: 1;
    }
    #status {
        content-align: center middle;
        width: 100%;
        height: 1;
        margin-top: 1;
    }
    #controls {
        content-align: center middle;
        width: 100%;
        height: 1;
        margin-top: 1;
        color: $text-muted;
    }
    """

    BINDINGS = [
        Binding("r", "reset_game",   "Reset", priority=True),
        Binding("p", "toggle_pause", "Pause", priority=True),
        Binding("q", "quit_game",    "Quit",  priority=True),
    ]

    def __init__(self, mode: GameMode) -> None:
        super().__init__()
        self.mode = mode
        self.state = GameState()
        self._input_locked = False
        self._blink_timer: Timer | None = None
        self._blink_state = False
        self._was_blinking = False

    def compose(self) -> ComposeResult:
        mode_str = "2 Players" if self.mode == GameMode.TWO_PLAYER else "vs AI  (you are X)"
        with Vertical(id="game-container"):
            yield Label(f"TicTacToe — {mode_str}", id="title")
            yield BoardWidget(id="board")
            yield Static("", id="status")
            yield Static("[R] Reset   [P] Pause/Menu   [Q] Quit", id="controls")

    def on_mount(self) -> None:
        self.state.reset()
        self._sync_board()
        self._update_status()
        self.query_one("#board", BoardWidget).focus()

    # ------------------------------------------------------------------ board

    def _sync_board(self) -> None:
        symbols = {PLAYER_X: "[bold cyan]X[/]", PLAYER_O: "[bold red]O[/]", EMPTY: " "}
        board = self.query_one("#board", BoardWidget)
        for i, val in enumerate(self.state.board):
            board.update_cell(i, symbols[val])

    def _update_status(self) -> None:
        s = self.query_one("#status", Static)
        w = self.state.winner
        if w is None:
            if self.mode == GameMode.VS_AI and self.state.current_player == PLAYER_O:
                s.update("AI (O) is thinking...")
            else:
                player = "X" if self.state.current_player == PLAYER_X else "O"
                s.update(f"Player {player}'s turn")
        elif w == 0:
            s.update("It's a DRAW!")
        else:
            winner = "X" if w == PLAYER_X else "O"
            if self.mode == GameMode.VS_AI:
                if w == PLAYER_X:
                    s.update("Congratulations! You WIN!")
                else:
                    s.update("AI wins! Better luck next time.")
            else:
                s.update(f"Congratulations! Player {winner} WINS!")

    # ------------------------------------------------------------------ moves

    def on_board_widget_move_made(self, event: BoardWidget.MoveMade) -> None:
        if self._input_locked or self.state.winner is not None:
            return
        if not self.state.is_valid_move(event.cell):
            return
        self.state.apply_move(event.cell)
        self._sync_board()
        self._update_status()
        if self.state.winner is not None:
            self._start_celebration()
            return
        if self.mode == GameMode.VS_AI and self.state.current_player == PLAYER_O:
            self._input_locked = True
            self.set_timer(0.6, self._make_ai_move)

    def _make_ai_move(self) -> None:
        move = get_ai_move(self.state)
        if move != -1:
            self.state.apply_move(move)
            self._sync_board()
            self._update_status()
        self._input_locked = False
        if self.state.winner is not None:
            self._start_celebration()

    # ------------------------------------------------------------------ celebration

    def _start_celebration(self) -> None:
        if self.state.winner == 0 or self.state.winning_line is None:
            return
        for idx in self.state.winning_line:
            self.query_one(f"#cell-{idx}", CellWidget).add_class("winner")
        self._blink_state = True
        self._blink_timer = self.set_interval(0.35, self._tick_blink)

    def _tick_blink(self) -> None:
        self._blink_state = not self._blink_state
        if self.state.winning_line is None:
            return
        for idx in self.state.winning_line:
            cell = self.query_one(f"#cell-{idx}", CellWidget)
            if self._blink_state:
                cell.remove_class("winner-off")
                cell.add_class("winner")
            else:
                cell.remove_class("winner")
                cell.add_class("winner-off")

    def _stop_celebration(self) -> None:
        if self._blink_timer is not None:
            self._blink_timer.stop()
            self._blink_timer = None
        for cell in self.query(CellWidget):
            cell.remove_class("winner")
            cell.remove_class("winner-off")

    # ------------------------------------------------------------------ actions

    def action_reset_game(self) -> None:
        self._stop_celebration()
        self._input_locked = False
        self.state.reset()
        self._sync_board()
        self._update_status()
        board = self.query_one("#board", BoardWidget)
        board.cursor_row = 0
        board.cursor_col = 0
        board.focus()

    def action_toggle_pause(self) -> None:
        self._was_blinking = self._blink_timer is not None
        if self._blink_timer is not None:
            self._blink_timer.pause()
        self.app.push_screen(PauseModal(), self._on_pause_dismissed)

    def _on_pause_dismissed(self, _: None) -> None:
        if self._was_blinking and self._blink_timer is not None:
            self._blink_timer.resume()

    def action_quit_game(self) -> None:
        self.app.exit()


class ModeScreen(Screen[GameMode]):
    DEFAULT_CSS = """
    ModeScreen {
        align: center middle;
        layout: vertical;
    }
    ModeScreen #title {
        text-style: bold;
        content-align: center middle;
        width: 100%;
        margin-bottom: 2;
        height: 1;
    }
    ModeScreen #subtitle {
        content-align: center middle;
        width: 100%;
        margin-bottom: 1;
        height: 1;
    }
    ModeScreen Button {
        width: 22;
        margin: 1 0;
    }
    """

    def compose(self) -> ComposeResult:
        yield Label("T I C T A C T O E", id="title")
        yield Label("Choose a game mode:", id="subtitle")
        yield Button("  2 Players", id="two_player", variant="primary")
        yield Button("  vs AI",     id="vs_ai",      variant="success")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "two_player":
            self.dismiss(GameMode.TWO_PLAYER)
        else:
            self.dismiss(GameMode.VS_AI)


class TicTacToeApp(App[None]):
    TITLE = "TicTacToe"

    def on_mount(self) -> None:
        self.push_screen(ModeScreen(), self._on_mode_selected)

    def _on_mode_selected(self, mode: GameMode) -> None:
        self.push_screen(GameScreen(mode))


if __name__ == "__main__":
    TicTacToeApp().run()
