"""Level progression management."""


class LevelManager:
    def __init__(self) -> None:
        self.phase = 1

    def advance(self) -> None:
        self.phase += 1
