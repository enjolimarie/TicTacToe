EMPTY = 0
PLAYER_X = 1
PLAYER_O = -1

WIN_LINES: list[tuple[int, int, int]] = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),  # rows
    (0, 3, 6), (1, 4, 7), (2, 5, 8),  # cols
    (0, 4, 8), (2, 4, 6),              # diagonals
]


class GameState:
    """
    Board layout (flat index):
        0 | 1 | 2
        ---------
        3 | 4 | 5
        ---------
        6 | 7 | 8
    """

    def __init__(self) -> None:
        self.board: list[int] = [EMPTY] * 9
        self.current_player: int = PLAYER_X
        self.winner: int | None = None          # None=ongoing, 0=draw, 1=X, -1=O
        self.winning_line: tuple[int, int, int] | None = None

    def reset(self) -> None:
        self.board = [EMPTY] * 9
        self.current_player = PLAYER_X
        self.winner = None
        self.winning_line = None

    def is_valid_move(self, cell: int) -> bool:
        return 0 <= cell <= 8 and self.board[cell] == EMPTY

    def apply_move(self, cell: int) -> None:
        if not self.is_valid_move(cell):
            raise ValueError(f"Invalid move: cell {cell}")
        self.board[cell] = self.current_player
        self._check_terminal()
        if self.winner is None:
            self.current_player = -self.current_player

    def _check_terminal(self) -> None:
        for line in WIN_LINES:
            a, b, c = line
            if self.board[a] != EMPTY and self.board[a] == self.board[b] == self.board[c]:
                self.winner = self.board[a]
                self.winning_line = line
                return
        if all(v != EMPTY for v in self.board):
            self.winner = 0

    def available_moves(self) -> list[int]:
        return [i for i, v in enumerate(self.board) if v == EMPTY]

    def clone(self) -> "GameState":
        s = GameState()
        s.board = self.board[:]
        s.current_player = self.current_player
        s.winner = self.winner
        s.winning_line = self.winning_line
        return s


def minimax(state: GameState, depth: int, is_maximizing: bool) -> int:
    if state.winner == PLAYER_X:
        return 10 - depth
    if state.winner == PLAYER_O:
        return depth - 10
    if state.winner == 0 or not state.available_moves():
        return 0

    if is_maximizing:
        best = -100
        for move in state.available_moves():
            child = state.clone()
            child.apply_move(move)
            best = max(best, minimax(child, depth + 1, False))
        return best
    else:
        best = 100
        for move in state.available_moves():
            child = state.clone()
            child.apply_move(move)
            best = min(best, minimax(child, depth + 1, True))
        return best


def get_ai_move(state: GameState) -> int:
    """Return the best cell index for PLAYER_O (minimizer) using minimax."""
    best_score = 101
    best_move = -1
    for move in state.available_moves():
        child = state.clone()
        child.apply_move(move)
        score = minimax(child, 0, True)
        if score < best_score:
            best_score = score
            best_move = move
    return best_move
