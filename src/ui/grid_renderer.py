"""Các hàm hỗ trợ vẽ lưới đồ họa (rendering).
Cung cấp các hàm công cụ chuyên biệt để vẽ các thành phần đồ họa (lưới, ô vuông, văn bản) lên màn hình bằng thư viện Pygame. Việc bóc tách này giúp file điều khiển chính (algorithm_tester.py) gọn gàng và dễ đọc hơn.

Cách hoạt động (How it works): Các hàm trong file này hoạt động như những "người thợ sơn". Chúng nhận nguyên liệu đầu vào là tọa độ (dòng, cột) từ ma trận, kích thước ô (pixel), màu sắc và bề mặt màn hình (surface). Sau đó, chúng làm toán để quy đổi tọa độ ma trận thành tọa độ pixel thực tế trên màn hình và dùng Pygame để tô màu lên đó.

Các Hàm chính (Core Functions):

draw_cell_grid(): Quét toàn bộ ma trận 2D để vẽ bản đồ gốc (vẽ sàn nhà, tường chắn và viền kẻ cho từng ô).

draw_nodes(): Nhận một danh sách tọa độ (ví dụ: mảng các ô đã duyệt, mảng đường đi) và tô màu hàng loạt cho các tọa độ đó.

draw_start_goal(): Hàm chuyên dụng để vẽ đè điểm Bắt đầu và điểm Đích với màu sắc nổi bật.

draw_text(): Hàm tiện ích giúp in chữ (render font) lên bề mặt UI.

Mối liên hệ (Dependencies): Nhận tham chiếu trực tiếp từ thư viện pygame. Phục vụ như một công cụ đắc lực cho các file giao diện ở tầng View (như algorithm_tester.py)."""

from __future__ import annotations

from typing import Iterable, Sequence


def draw_cell_grid(pygame, surface, grid: Sequence[Sequence[int]], origin: tuple[int, int], cell_size: int, wall_color, floor_color, border_color) -> None:
    """Vẽ toàn bộ bản đồ lưới (tường và sàn) kèm theo đường viền."""
    origin_x, origin_y = origin
    for row_index, row in enumerate(grid):
        for col_index, tile in enumerate(row):
            color = wall_color if tile == 1 else floor_color
            rect = (origin_x + col_index * cell_size, origin_y + row_index * cell_size, cell_size, cell_size)
            pygame.draw.rect(surface, color, rect)
            pygame.draw.rect(surface, border_color, rect, 1)


def draw_nodes(pygame, surface, nodes: Iterable[tuple[int, int]], origin: tuple[int, int], cell_size: int, color) -> None:
    """Tô màu cho một tập hợp các ô cụ thể (ví dụ: các ô đã duyệt, đường đi)."""
    origin_x, origin_y = origin
    for row, col in nodes:
        rect = (origin_x + col * cell_size, origin_y + row * cell_size, cell_size, cell_size)
        pygame.draw.rect(surface, color, rect)


def draw_start_goal(pygame, surface, start: tuple[int, int], goal: tuple[int, int], origin: tuple[int, int], cell_size: int, start_color, goal_color) -> None:
    """Vẽ điểm xuất phát và điểm đích lên lưới."""
    origin_x, origin_y = origin
    start_rect = (origin_x + start[1] * cell_size, origin_y + start[0] * cell_size, cell_size, cell_size)
    goal_rect = (origin_x + goal[1] * cell_size, origin_y + goal[0] * cell_size, cell_size, cell_size)
    pygame.draw.rect(surface, start_color, start_rect)
    pygame.draw.rect(surface, goal_color, goal_rect)


def draw_text(surface, font, text: str, position: tuple[int, int], color) -> None:
    """Hiển thị văn bản (text) lên bề mặt màn hình."""
    text_surface = font.render(text, True, color)
    surface.blit(text_surface, position)