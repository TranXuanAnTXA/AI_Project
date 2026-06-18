"""Game state management."""


class GameState:
    def __init__(self) -> None:
        self.turn = 0
        self.ram = 0
        self.cpu = 0
        self.anomaly_meter = 0
