"""Uninformed search algorithms."""
from collections import deque

from .common import Grid, Coordinate, validate_grid, reconstruct_path, iter_neighbors
from .pathfinding import bfs, dfs

def bfs_generator(grid: Grid, start: Coordinate, goal: Coordinate):
    """Generator mô phỏng BFS cho hiệu ứng robot dò đường."""
    validate_grid(grid)
    queue = deque([start])
    came_from: dict[Coordinate, Coordinate | None] = {start: None}
    visited: set[Coordinate] = {start}

    while queue:
        current = queue.popleft()

        if current == goal:
            # Tìm thấy đích, trả về trạng thái cuối cùng kèm đường đi
            yield current, list(queue), visited, reconstruct_path(came_from, goal)
            return

        for neighbor in iter_neighbors(grid, current):
            if neighbor not in visited:
                visited.add(neighbor)
                came_from[neighbor] = current
                queue.append(neighbor)

        # Tạm dừng và ném trạng thái hiện tại ra cho giao diện vẽ Robot
        yield current, list(queue), visited, []

