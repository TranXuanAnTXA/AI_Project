"""
📄 File: run_test.py (Nằm ở gốc dự án)
* Cập nhật: Cọ vẽ, BFS ngăn chặn Soft-lock và Kỹ thuật 3 Lớp Vẽ (Sandwich) bảo toàn 2.5D.
"""
import pygame
import sys
import os

# Thêm thư mục 'src' vào tầm vực tìm kiếm để import
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))
from src.core.grid_map import GridMap

def main():
    pygame.init()
    pygame.display.set_mode((1, 1), pygame.HIDDEN)

    tmx_path = os.path.join("assets", "maps", "dungeon_map_1.tmx")
    game_map = GridMap(tmx_path, scale=2)

    window_size = game_map.width * game_map.tile_size
    screen = pygame.display.set_mode((window_size, window_size))
    pygame.display.set_caption("🎮 Phòng Giả Lập - Xây Tường Tự Do & Chống Chặn Đường")

    clock = pygame.time.Clock()
    running = True

    mock_hero_pos = game_map.start_points[0] if game_map.start_points else (2, 2)
    mock_goal_pos = game_map.goal_point if game_map.goal_point else (game_map.width - 3, game_map.height - 3)

    blocked_effects = {}  # {(grid_x, grid_y): frames_to_live}

    def handle_place_wall(grid_x, grid_y):
        if (grid_x, grid_y) == mock_hero_pos or (grid_x, grid_y) == mock_goal_pos:
            return

        status = game_map.place_boss_wall(grid_x, grid_y, mock_hero_pos, mock_goal_pos)

        if status == "BLOCKED":
            blocked_effects[(grid_x, grid_y)] = 20 # Sáng lên trong 20 frame rồi vụt tắt

    def handle_remove_wall(grid_x, grid_y):
        game_map.remove_boss_wall(grid_x, grid_y)

    print("\n" + "="*60)
    print("🕹️ HƯỚNG DẪN KIỂM THỬ TRONG PHÒNG THÍ NGHIỆM:")
    print("👉 🟦 Xanh Dương (Hero) | 🟩 Xanh Lá (Goal)")
    print("👉 GIỮ CHUỘT TRÁI + KÉO : Xây tường.")
    print("👉 GIỮ CHUỘT PHẢI + KÉO : Xóa tường.")
    print("="*60 + "\n")

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                grid_x, grid_y = mouse_x // game_map.tile_size, mouse_y // game_map.tile_size

                if event.button == 1:
                    handle_place_wall(grid_x, grid_y)
                elif event.button == 3:
                    handle_remove_wall(grid_x, grid_y)

            elif event.type == pygame.MOUSEMOTION:
                buttons = pygame.mouse.get_pressed()
                mouse_x, mouse_y = pygame.mouse.get_pos()
                grid_x, grid_y = mouse_x // game_map.tile_size, mouse_y // game_map.tile_size

                if buttons[0]:
                    handle_place_wall(grid_x, grid_y)
                elif buttons[2]:
                    handle_remove_wall(grid_x, grid_y)

        screen.fill((20, 20, 20))

        # ---------------------------------------------------------
        # KỸ THUẬT VẼ BÁNH MÌ KẸP (SANDWICH RENDERING)
        # ---------------------------------------------------------
        # LỚP 1: Nền nhà và chân tường
        game_map.render_bottom(screen)

        # LỚP 2: Vẽ Hero và Goal đè lên sàn nhưng chui dưới mái nhà
        hx, hy = mock_hero_pos
        hero_rect = (hx * game_map.tile_size, hy * game_map.tile_size, game_map.tile_size, game_map.tile_size)
        pygame.draw.rect(screen, (50, 150, 255), hero_rect)
        pygame.draw.rect(screen, (255, 255, 255), hero_rect, 2)

        gx, gy = mock_goal_pos
        goal_rect = (gx * game_map.tile_size, gy * game_map.tile_size, game_map.tile_size, game_map.tile_size)
        pygame.draw.rect(screen, (50, 255, 50), goal_rect)
        pygame.draw.rect(screen, (255, 255, 255), goal_rect, 2)

        # LỚP 3: Mái nhà và các đồ vật lơ lửng che khuất Hero
        game_map.render_top(screen)

        # ---------------------------------------------------------

        # Hiệu ứng Tường Vỡ (Màu Đỏ nhấp nháy)
        effect_surface = pygame.Surface((game_map.tile_size, game_map.tile_size), pygame.SRCALPHA)
        to_remove = []

        for (bx, by), frames in blocked_effects.items():
            if frames > 0:
                alpha = min(255, frames * 12)
                effect_surface.fill((255, 50, 50, alpha))
                screen.blit(effect_surface, (bx * game_map.tile_size, by * game_map.tile_size))
                blocked_effects[(bx, by)] -= 1
            else:
                to_remove.append((bx, by))

        for key in to_remove:
            del blocked_effects[key]

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()