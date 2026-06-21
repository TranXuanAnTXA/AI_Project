"""Các hàm hỗ trợ dùng chung và kiểu dữ liệu kết quả cho các thuật toán tìm kiếm.
Đóng vai trò là "tài nguyên dùng chung" (Shared Toolkit), cung cấp các cấu trúc dữ liệu chuẩn hóa và các hàm hỗ trợ cơ bản cho mọi thuật toán tìm kiếm. Việc tách file này ra giúp mã nguồn của các thuật toán chính (BFS, A*,...) trở nên cực kỳ ngắn gọn và dễ bảo trì.

Cách hoạt động (How it works):
File này không chứa logic của bất kỳ thuật toán nào. Thay vào đó, nó định nghĩa "khuôn mẫu" (PathSearchResult) mà mọi thuật toán bắt buộc phải tuân theo khi trả về kết quả. Đồng thời, nó xử lý sẵn các tác vụ lặp đi lặp lại mang tính hình học trên ma trận như: kiểm tra ranh giới, kiểm tra vật cản, và mò mẫm truy vết lại đường đi sau khi đã tìm thấy đích.

Các Hàm/Class chính (Core Functions):
- PathSearchResult (Data Class): Đóng gói toàn bộ đầu ra của một thuật toán vào một đối tượng duy nhất, chứa thông tin về đường đi, thứ tự duyệt, và các chỉ số tài nguyên (RAM/CPU) để gửi ra cho UI hiển thị.
- validate_grid(grid): Kiểm tra an toàn, ném lỗi ngay nếu nhận vào một ma trận rỗng.
- in_bounds(grid, node): Kiểm tra xem tọa độ node (dòng, cột) có bị lọt ra ngoài ranh giới của bản đồ hay không.
- is_walkable(grid, node): Kiểm tra kép: ô đó phải nằm trong bản đồ (in_bounds) VÀ không phải là tường (giá trị khác 1).
- iter_neighbors(...): Generator cực kỳ quan trọng. Trả về danh sách tọa độ các ô láng giềng xung quanh ô hiện tại (hỗ trợ cả việc cho phép đi chéo hay không).
- reconstruct_path(came_from, goal): Hàm "Truy vết". Khi thuật toán chạm đích, hàm này dùng từ điển came_from (lưu vết node cha) để dò ngược từ Đích về Bắt đầu, từ đó tạo ra danh sách đường đi màu tím cuối cùng.

Mối liên hệ (Dependencies):
File này là file "cấp thấp nhất" trong logic AI, không phụ thuộc vào file nào khác trong dự án (chỉ dùng thư viện chuẩn Python). Nó được import bởi tất cả các file chứa thuật toán tìm đường (như pathfinding.py).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Iterator, Sequence

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