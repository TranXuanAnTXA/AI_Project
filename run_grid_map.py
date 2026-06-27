import sys
import os
import pygame

# 1. Thêm thư mục src vào hệ thống đường dẫn để import code thật
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

try:
    from core.grid_map import GridMap
    print("✅ Kết nối hệ thống GridMap thật thành công!")
except ImportError as e:
    print(f"❌ Không tìm thấy mã nguồn tại src/core/grid_map/. Lỗi: {e}")
    sys.exit(1)

# 2. Khởi tạo Pygame & Font
pygame.init()
pygame.display.set_caption("GridMap Real Visual Test")
FONT = pygame.font.SysFont("Arial", 16)

# Cấu hình đường dẫn tài nguyên thật của bạn
TMX_PATH = "assets/maps/dungeon_map_1.tmx"
IMG_PATH = "assets/images/walls_floor.png"

# Kiểm tra file trước khi chạy để tránh crash bất ngờ
if not os.path.exists(TMX_PATH) or not os.path.exists(IMG_PATH):
    print(f"❌ Thiếu file! Hãy đảm bảo tồn tại:\n- {TMX_PATH}\n- {IMG_PATH}")
    sys.exit(1)

# 3. Khởi tạo hệ thống GridMap thật từ Giai đoạn 4
map_system = GridMap(TMX_PATH, IMG_PATH)

# Lấy thông tin kích thước từ loader
TILE_W = map_system.loader.tile_width
TILE_H = map_system.loader.tile_height

# Ma trận ảo có thêm 2 hàng/cột do thuật toán "Ảo hóa viền" ở Giai đoạn 2
BORDERED_ROWS = len(map_system.bordered_matrix)
BORDERED_COLS = len(map_system.bordered_matrix[0])

# Thiết lập kích thước màn hình linh hoạt theo kích thước map
SCREEN_WIDTH = BORDERED_COLS * TILE_W + 250  # Dành 250px bên phải làm HUD info
SCREEN_HEIGHT = max(BORDERED_ROWS * TILE_H, 480)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()

# Tọa độ test tương tác (Vị trí ô lưới gốc chưa bọc viền)
test_logic_x, test_logic_y = 2, 2

running = True
status_text = "Sẵn sàng test va chạm."

while running:
    # --- XỬ LÝ SỰ KIỆN ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = pygame.mouse.get_pos()
            # Kiểm tra nếu click vào khu vực nút bấm trên HUD
            btn_rect = pygame.Rect(BORDERED_COLS * TILE_W + 20, 150, 210, 40)
            if btn_rect.collidepoint(mx, my):
                # Thử đặt tường Boss thông qua Facade API (Kiểm tra BFS luôn)
                if (test_logic_x, test_logic_y) not in map_system.controller.boss_walls:
                    success = map_system.spawn_boss_wall(test_logic_x, test_logic_y)
                    status_text = "Boss đặt tường THÀNH CÔNG!" if success else "BFS CHẶN: Làm kẹt map!"
                else:
                    map_system.destroy_boss_wall(test_logic_x, test_logic_y)
                    status_text = "Đã phá hủy tường Boss."

    # --- RENDER ĐỒ HỌA TRỰC QUAN ---
    screen.fill((30, 30, 30)) # Nền tối gạch nét bản đồ

    # Duyệt qua ma trận "Ảo hóa viền" để vẽ các Tile thật lên màn hình
    for b_y in range(BORDERED_ROWS):
        for b_x in range(BORDERED_COLS):
            gid = map_system.bordered_matrix[b_y][b_x]

            if gid > 0:
                # Lấy trực tiếp Surface đã được subsurface từ TileEngine thật
                tile_surface = map_system.get_tile_image(gid)
                screen.blit(tile_surface, (b_x * TILE_W, b_y * TILE_H))

            # Vẽ lưới mờ để dễ phân biệt các ô
            pygame.draw.rect(screen, (50, 50, 50), (b_x * TILE_W, b_y * TILE_H, TILE_W, TILE_H), 1)

    # Vẽ vị trí Start (S) và Goal (G) thật từ Tiled Object lên màn hình
    # Cần cộng 1 vào tọa độ vì ma trận hiển thị là ma trận đã bọc viền
    orig_start = map_system.controller.start_grid
    orig_goal = map_system.controller.goal_grid

    # Vẽ Start (Xanh lá)
    pygame.draw.rect(screen, (0, 255, 0), ((orig_start[0] + 1) * TILE_W, (orig_start[1] + 1) * TILE_H, TILE_W, TILE_H), 2)
    screen.blit(FONT.render("S", True, (0, 255, 0)), ((orig_start[0] + 1) * TILE_W + TILE_W//3, (orig_start[1] + 1) * TILE_H + TILE_H//4))

    # Vẽ Goal (Đỏ)
    pygame.draw.rect(screen, (255, 0, 0), ((orig_goal[0] + 1) * TILE_W, (orig_goal[1] + 1) * TILE_H, TILE_W, TILE_H), 2)
    screen.blit(FONT.render("G", True, (255, 0, 0)), ((orig_goal[0] + 1) * TILE_W + TILE_W//3, (orig_goal[1] + 1) * TILE_H + TILE_H//4))

    # Vẽ các tường Boss động đang có trong Controller
    for (bx, by) in map_system.controller.boss_walls.keys():
        # Vẽ một ô màu cam đại diện cho tường Boss trên lưới hiển thị (+1 viền)
        pygame.draw.rect(screen, (255, 140, 0), ((bx + 1) * TILE_W + 4, (by + 1) * TILE_H + 4, TILE_W - 8, TILE_H - 8))

    # --- VẼ BẢNG ĐIỀU KHIỂN HUD (BÊN PHẢI) ---
    hud_x = BORDERED_COLS * TILE_W + 20

    screen.blit(FONT.render("THÔNG SỐ MAP THẬT", True, (255, 255, 255)), (hud_x, 20))
    screen.blit(FONT.render(f"Size gốc: {map_system.loader.width}x{map_system.loader.height}", True, (200, 200, 200)), (hud_x, 50))
    screen.blit(FONT.render(f"Size + Viền ảo: {BORDERED_COLS}x{BORDERED_ROWS}", True, (200, 200, 200)), (hud_x, 75))
    screen.blit(FONT.render(f"Start Grid: {orig_start}", True, (0, 255, 0)), (hud_x, 100))

    # Nút bấm tương tác đặt tường
    btn_rect = pygame.Rect(hud_x, 150, 210, 40)
    pygame.draw.rect(screen, (0, 100, 200), btn_rect)
    screen.blit(FONT.render("Đặt/Phá Tường Boss (2,2)", True, (255, 255, 255)), (hud_x + 15, 160))

    # Trạng thái logic va chạm thực tế từ controller
    is_walk = map_system.is_walkable(test_logic_x, test_logic_y)
    screen.blit(FONT.render(f"Logic Walkable(2,2): {is_walk}", True, (255, 255, 0)), (hud_x, 210))
    screen.blit(FONT.render(f"Log: {status_text}", True, (255, 100, 100)), (hud_x, 240))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()