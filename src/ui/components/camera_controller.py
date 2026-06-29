"""
📄 Tên File: camera_controller.py (Nằm trong src/ui/components/)
* Vai trò: Đạo diễn hình ảnh. Xử lý logic bám theo Hero hoặc Focus toàn bản đồ.
"""
import pygame

class CameraController:
    def __init__(self, camera):
        self.camera = camera
        self.timer = 1.0 # Đồng hồ đếm trễ 1 giây (chuyển từ main.py sang)
        self.local_search_algos = ["HILL_CLIMBING", "SIMULATED_ANNEALING", "LOCAL_BEAM"]

    def reset_to_hero(self, hero, view_h, tile_size):
        """Đặt camera focus vào Hero ở nửa dưới màn hình ngay khi bắt đầu."""
        init_x = hero.pixel_pos[0] + tile_size // 2
        init_y = hero.pixel_pos[1] + tile_size // 2
        offset_y = (view_h * 0.15)

        if hasattr(self.camera, 'current_center'):
            self.camera.current_center = pygame.math.Vector2(init_x, init_y - offset_y)
            self.camera.set_target(init_x, init_y - offset_y, target_zoom=1.0)
        else:
            self.camera.update(init_x, init_y - offset_y)

    def update_cinematic(self, time_delta, current_speed, phase, state, selected_algo, visited_nodes, hero, view_h, tile_size, boss=None):
        """Xử lý logic theo dõi Hero & Boss (Cinematic) hoặc nhìn toàn cảnh (Phase Boss)."""

        # [MỚI]: Nếu là Phase Boss -> Zoom toàn bản đồ
        if phase == "BOSS":
            if hasattr(self.camera, 'zoom_to_fit'):
                self.camera.zoom_to_fit()

        # Nếu là Phase Hero
        elif phase == "HERO" and state not in ["PREPARING", "ANNOUNCING", "LEVEL_COMPLETE"]:

            # 1. Nếu là BFS/A* đang chạy tìm đường -> Focus lấy toàn bộ Area quét
            if state == "EXECUTING" and selected_algo not in self.local_search_algos and hasattr(self.camera, 'focus_on_area'):
                self.camera.focus_on_area(list(visited_nodes), tile_size)

            # 2. Hero đang di chuyển
            else:
                self.timer += time_delta * current_speed
                if self.timer >= 1.0:
                    self.timer = 0.0 # Reset đồng hồ

                    # [MỚI]: Nếu có Boss -> Bao quát cả Hero và Boss
                    if boss and hasattr(self.camera, 'focus_on_entities'):
                        self.camera.focus_on_entities(hero, boss, padding=250)
                    # Nếu KHÔNG có Boss -> Bám theo Hero như cũ
                    else:
                        hero_x = hero.pixel_pos[0] + tile_size // 2
                        hero_y = hero.pixel_pos[1] + tile_size // 2
                        zoom = getattr(self.camera, 'zoom', 1.0)
                        if zoom <= 0.01: zoom = 1.0
                        offset_y = (view_h * 0.15) / zoom

                        if hasattr(self.camera, 'set_target'):
                            self.camera.set_target(hero_x, hero_y - offset_y, target_zoom=1.0)

        # 3. Cập nhật vị trí vật lý thực tế của Camera
        if hasattr(self.camera, 'update'):
            try:
                self.camera.update(time_delta)
            except TypeError:
                self.camera.update()