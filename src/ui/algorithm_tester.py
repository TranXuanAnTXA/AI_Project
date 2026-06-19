"""Interactive Pygame UI for testing path-finding algorithms on a fixed map.

Lớp Giao diện (View) và Lớp Điều khiển (Controller). Đây là ứng dụng độc lập dùng để chạy thử, trực quan hóa và so sánh hiệu suất của các thuật toán tìm đường trên một bản đồ cố định.
Lắng nghe tương tác của người dùng (chọn thuật toán, bấm nút chạy).
Trích xuất mảng visited_order từ kết quả và dùng một bộ đếm (animation_index) để vẽ dần dần từng ô lên màn hình theo từng khung hình (frame), tạo ra hiệu ứng hoạt ảnh (animation)
Các Hàm/Class chính (Core Functions):

AlgorithmChoice & Button: Các Data Class nhỏ để lưu trữ cấu hình nút bấm trên giao diện.

AlgorithmTesterApp: Class chính bọc toàn bộ ứng dụng Pygame.

_run_selected_algorithm(): Kích hoạt thuật toán tính toán ngầm và reset bộ đếm hoạt ảnh về 0.

_step_animation(): Tăng dần bộ đếm khung hình để tạo hiệu ứng thuật toán đang "loang" ra.

_draw_grid() & _draw_panel(): Đọc trạng thái hiện tại và vẽ lưới, đường đi, cũng như bảng thống kê (Số ô duyệt, Độ dài đường đi) lên màn hình.

run(): Vòng lặp trò chơi chính (Main Game Loop) duy trì cửa sổ Pygame.
Mối liên hệ (Dependencies): Gọi logic từ src.algorithms. Lấy dữ liệu bản đồ mẫu từ src.core.fixed_maps. Dùng các hằng số màu sắc/kích thước từ src.utils.constants. Gọi các hàm vẽ hình cơ bản từ module lân cận .grid_renderer.


"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pygame

from src.algorithms import a_star, bfs, dfs, greedy
from src.algorithms.common import PathSearchResult
from src.core.fixed_maps import FIXED_GRID, GOAL_NODE, START_NODE
from src.utils.constants import FPS, SCREEN_HEIGHT, SCREEN_WIDTH

from .grid_renderer import draw_cell_grid, draw_nodes, draw_start_goal, draw_text


@dataclass(frozen=True)
class AlgorithmChoice:
    key: str
    label: str
    runner: Callable[[list[list[int]], tuple[int, int], tuple[int, int]], PathSearchResult]


@dataclass
class Button:
    rect: pygame.Rect
    label: str
    key: str


class AlgorithmTesterApp:
    """Trình trực quan hóa đơn giản cho bản đồ kiểm thử cố định.

    Đầu vào (Input):
        - Lưới cố định (fixed grid) từ `src/core/fixed_maps.py`
        - Điểm bắt đầu (start node)
        - Điểm đích (goal node)
        - Thuật toán được chọn

    Đầu ra (Output):
        - Lưới được vẽ lên màn hình
        - Hoạt ảnh thứ tự các ô được duyệt (visited order)
        - Đường đi cuối cùng và bảng thống kê

    Các biến được quản lý (Managed variables):
        - `selected_algorithm`: Thuật toán đang chọn
        - `result`: Kết quả trả về từ thuật toán
        - `animation_index`: Chỉ số khung hình hiện tại của hoạt ảnh
        - `animation_running`: Trạng thái hoạt ảnh đang chạy hay không
        - `clock`: Bộ đếm thời gian của Pygame
        - `buttons`: Danh sách các nút bấm UI
    """

    WINDOW_TITLE = "Self-Defeating Dungeon - Algorithm Tester"
    GRID_ORIGIN = (40, 40)
    CELL_SIZE = 48
    GRID_WIDTH = len(FIXED_GRID[0])
    GRID_HEIGHT = len(FIXED_GRID)
    GRID_PIXEL_WIDTH = GRID_WIDTH * CELL_SIZE
    GRID_PIXEL_HEIGHT = GRID_HEIGHT * CELL_SIZE
    PANEL_X = GRID_ORIGIN[0] + GRID_PIXEL_WIDTH + 40
    PANEL_Y = 40

    COLORS = {
        "background": (18, 20, 28),
        "panel": (28, 32, 44),
        "panel_border": (66, 76, 106),
        "floor": (245, 247, 250),
        "wall": (31, 36, 48),
        "grid_border": (190, 198, 214),
        "visited": (173, 216, 230),
        "frontier": (241, 196, 15),
        "path": (155, 89, 182),
        "current": (255, 165, 0),
        "start": (46, 204, 113),
        "goal": (231, 76, 60),
        "text": (245, 247, 250),
        "muted": (185, 193, 214),
        "button": (43, 50, 68),
        "button_hover": (72, 84, 116),
        "button_active": (91, 125, 212),
    }

    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(self.WINDOW_TITLE)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 22)
        self.small_font = pygame.font.SysFont("consolas", 18)
        self.title_font = pygame.font.SysFont("consolas", 28, bold=True)

        self.algorithms = [
            AlgorithmChoice("bfs", "BFS", bfs),
            AlgorithmChoice("dfs", "DFS", dfs),
            AlgorithmChoice("a_star", "A*", a_star),
            AlgorithmChoice("greedy", "Greedy", greedy),
        ]
        self.buttons = self._build_buttons()
        self.selected_algorithm = self.algorithms[0]
        self.result: PathSearchResult | None = None
        self.animation_index = 0
        self.animation_running = False
        self.animation_speed = 1
        self.running = True

    def _build_buttons(self) -> list[Button]:
        buttons: list[Button] = []
        start_y = 130
        for index, choice in enumerate(self.algorithms):
            rect = pygame.Rect(self.PANEL_X, start_y + index * 58, 220, 44)
            buttons.append(Button(rect=rect, label=choice.label, key=choice.key))
        buttons.append(Button(rect=pygame.Rect(self.PANEL_X, 370, 220, 44), label="Run selected", key="run"))
        buttons.append(Button(rect=pygame.Rect(self.PANEL_X, 428, 220, 44), label="Reset animation", key="reset"))
        buttons.append(Button(rect=pygame.Rect(self.PANEL_X, 486, 220, 44), label="Quit", key="quit"))
        return buttons

    def _run_selected_algorithm(self) -> None:
        self.result = self.selected_algorithm.runner(FIXED_GRID, START_NODE, GOAL_NODE)
        self.animation_index = 0
        self.animation_running = True

    def _reset_animation(self) -> None:
        self.result = None
        self.animation_index = 0
        self.animation_running = False

    def _handle_click(self, position: tuple[int, int]) -> None:
        for button in self.buttons:
            if button.rect.collidepoint(position):
                if button.key == "run":
                    self._run_selected_algorithm()
                    return
                if button.key == "reset":
                    self._reset_animation()
                    return
                if button.key == "quit":
                    self.running = False
                    return

                self.selected_algorithm = next(choice for choice in self.algorithms if choice.key == button.key)
                self._run_selected_algorithm()
                return

    def _step_animation(self) -> None:
        if not self.animation_running or not self.result:
            return

        if self.animation_index < len(self.result.visited_order):
            self.animation_index += self.animation_speed
        else:
            self.animation_index = len(self.result.visited_order)
            self.animation_running = False

    def _draw_panel(self) -> None:
        panel_rect = pygame.Rect(self.PANEL_X - 20, 20, 360, SCREEN_HEIGHT - 40)
        pygame.draw.rect(self.screen, self.COLORS["panel"], panel_rect, border_radius=16)
        pygame.draw.rect(self.screen, self.COLORS["panel_border"], panel_rect, 2, border_radius=16)

        draw_text(self.screen, self.title_font, "Algorithm Tester", (self.PANEL_X, self.PANEL_Y), self.COLORS["text"])
        draw_text(self.screen, self.small_font, "Fixed 10x10 map", (self.PANEL_X, self.PANEL_Y + 34), self.COLORS["muted"])
        draw_text(self.screen, self.small_font, f"Start: {START_NODE}  Goal: {GOAL_NODE}", (self.PANEL_X, self.PANEL_Y + 56), self.COLORS["muted"])

        for button in self.buttons:
            is_selected = button.key == self.selected_algorithm.key
            is_hovered = button.rect.collidepoint(pygame.mouse.get_pos())
            color = self.COLORS["button_active"] if is_selected else self.COLORS["button_hover"] if is_hovered else self.COLORS["button"]
            pygame.draw.rect(self.screen, color, button.rect, border_radius=10)
            pygame.draw.rect(self.screen, self.COLORS["panel_border"], button.rect, 1, border_radius=10)
            draw_text(self.screen, self.font, button.label, (button.rect.x + 16, button.rect.y + 10), self.COLORS["text"])

        if not self.result:
            draw_text(self.screen, self.font, "Status: idle", (self.PANEL_X, 560), self.COLORS["text"])
            draw_text(self.screen, self.small_font, "Click an algorithm to run it.", (self.PANEL_X, 592), self.COLORS["muted"])
            return

        path_length = len(self.result.path)
        visited_count = len(self.result.visited_order)
        draw_text(self.screen, self.font, f"Status: {'found' if self.result.found else 'not found'}", (self.PANEL_X, 560), self.COLORS["text"])
        draw_text(self.screen, self.small_font, f"Path length: {path_length}", (self.PANEL_X, 592), self.COLORS["muted"])
        draw_text(self.screen, self.small_font, f"Visited nodes: {visited_count}", (self.PANEL_X, 616), self.COLORS["muted"])
        draw_text(self.screen, self.small_font, f"Expanded nodes: {self.result.expanded_nodes}", (self.PANEL_X, 640), self.COLORS["muted"])
        draw_text(self.screen, self.small_font, f"Frontier peak: {self.result.frontier_max_size}", (self.PANEL_X, 664), self.COLORS["muted"])

    def _draw_grid(self) -> None:
        draw_cell_grid(
            pygame,
            self.screen,
            FIXED_GRID,
            self.GRID_ORIGIN,
            self.CELL_SIZE,
            self.COLORS["wall"],
            self.COLORS["floor"],
            self.COLORS["grid_border"],
        )

        if self.result:
            visited_slice = self.result.visited_order[: self.animation_index]
            draw_nodes(pygame, self.screen, visited_slice, self.GRID_ORIGIN, self.CELL_SIZE, self.COLORS["visited"])

            frontier_node = None
            if self.animation_index > 0 and self.animation_index <= len(self.result.visited_order):
                frontier_node = self.result.visited_order[min(self.animation_index - 1, len(self.result.visited_order) - 1)]

            if frontier_node is not None:
                draw_nodes(pygame, self.screen, [frontier_node], self.GRID_ORIGIN, self.CELL_SIZE, self.COLORS["current"])

            # Đã vá lỗi: Chỉ vẽ đường đi khi hoạt ảnh quét bản đồ đã chạy xong
            if self.result.found and not self.animation_running:
                draw_nodes(pygame, self.screen, self.result.path, self.GRID_ORIGIN, self.CELL_SIZE, self.COLORS["path"])

        draw_start_goal(
            pygame,
            self.screen,
            START_NODE,
            GOAL_NODE,
            self.GRID_ORIGIN,
            self.CELL_SIZE,
            self.COLORS["start"],
            self.COLORS["goal"],
        )

    def run(self) -> None:
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self._handle_click(event.pos)

            self._step_animation()
            self.screen.fill(self.COLORS["background"])
            self._draw_grid()
            self._draw_panel()
            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()