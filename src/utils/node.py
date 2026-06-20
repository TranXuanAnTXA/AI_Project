"""Node representation for pathfinding."""


class Node:
    """A node in a search tree/graph representing grid coordinates."""
    def __init__(self, x: int, y: int, parent=None) -> None:
        self.x = x
        self.y = y
        self.parent = parent
        self.g_score = 0.0
        self.h_score = 0.0
        self.f_score = 0.0

    def __lt__(self, other: "Node") -> bool:
        return self.f_score < other.f_score

    def __repr__(self) -> str:
        return f"Node(x={self.x}, y={self.y}, f={self.f_score})"
