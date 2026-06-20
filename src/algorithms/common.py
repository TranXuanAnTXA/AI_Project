"""Các hàm hỗ trợ dùng chung và kiểu dữ liệu kết quả cho các thuật toán tìm kiếm.
Đóng vai trò là "tài nguyên dùng chung" (Shared Toolkit), cung cấp các cấu trúc dữ liệu chuẩn hóa và các hàm hỗ trợ cơ bản cho mọi thuật toán tìm kiếm.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, Sequence

Coordinate = tuple[int, int]
Grid = Sequence[Sequence[int]]


@dataclass(frozen=True)
class PathSearchResult:
    """Đầu ra tiêu chuẩn cho các thuật toán tìm đường.

    Thuộc tính:
        path: Đường đi từ điểm bắt đầu đến điểm đích (bao gồm cả 2 điểm). Trống nếu không tìm thấy đường.
        visited_order: Các ô đã được mở rộng (duyệt) theo thứ tự xử lý.
        expanded_nodes: Số lượng ô đã lấy ra khỏi hàng đợi (số ô thực sự đã được mở rộng để xét).
        frontier_max_size: Kích thước lớn nhất của hàng đợi (frontier) trong suốt quá trình chạy.
        found: True nếu tìm thấy đường đi tới đích.
    """

    path: list[Coordinate]
    visited_order: list[Coordinate]
    expanded_nodes: int
    frontier_max_size: int
    found: bool


def validate_grid(grid: Grid) -> None:
    if not grid or not grid[0]:
        raise ValueError("ma trận (grid) phải chứa ít nhất một hàng và một cột")


def in_bounds(grid: Grid, node: Coordinate) -> bool:
    row, col = node
    return 0 <= row < len(grid) and 0 <= col < len(grid[0])


def is_walkable(grid: Grid, node: Coordinate) -> bool:
    return in_bounds(grid, node) and grid[node[0]][node[1]] != 1


def iter_neighbors(grid: Grid, node: Coordinate, allow_diagonal: bool = False) -> Iterator[Coordinate]:
    row, col = node
    offsets = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    if allow_diagonal:
        offsets.extend([(-1, -1), (-1, 1), (1, -1), (1, 1)])

    for row_offset, col_offset in offsets:
        neighbor = (row + row_offset, col + col_offset)
        if is_walkable(grid, neighbor):
            yield neighbor


def reconstruct_path(came_from: dict[Coordinate, Coordinate | None], goal: Coordinate) -> list[Coordinate]:
    if goal not in came_from:
        return []

    path: list[Coordinate] = []
    current: Coordinate | None = goal
    while current is not None:
        path.append(current)
        current = came_from[current]
    path.reverse()
    return path
