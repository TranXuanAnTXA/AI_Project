import pygame

class Camera:
    def __init__(self, viewport_width: int, viewport_height: int, map_pixel_width: int, map_pixel_height: int):
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.map_pixel_width = map_pixel_width
        self.map_pixel_height = map_pixel_height

        self.current_center = pygame.math.Vector2(0, 0)
        self.target_center = pygame.math.Vector2(0, 0)

        self.current_zoom = 1.0
        self.target_zoom = 1.0

        self.is_dragging = False
        self.drag_last_pos = (0, 0)

    def get_min_zoom(self) -> float:
        min_zoom_x = self.viewport_width / self.map_pixel_width
        min_zoom_y = self.viewport_height / self.map_pixel_height
        return min(min_zoom_x, min_zoom_y)

    def zoom_to_fit(self):
        self.target_zoom = self.get_min_zoom()
        self.target_center.x = self.map_pixel_width / 2
        self.target_center.y = self.map_pixel_height / 2

    def handle_input(self, event, offset_x=0, offset_y=0):
        if event.type == pygame.MOUSEWHEEL:
            min_zoom = self.get_min_zoom()
            self.target_zoom = max(min_zoom, min(2.0, self.target_zoom + event.y * 0.1))

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if offset_x <= event.pos[0] <= offset_x + self.viewport_width and \
                    offset_y <= event.pos[1] <= offset_y + self.viewport_height:
                self.is_dragging = True
                self.drag_last_pos = event.pos

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.is_dragging = False

        elif event.type == pygame.MOUSEMOTION and self.is_dragging:
            dx = event.pos[0] - self.drag_last_pos[0]
            dy = event.pos[1] - self.drag_last_pos[1]

            self.target_center.x -= dx / self.current_zoom
            self.target_center.y -= dy / self.current_zoom
            self.drag_last_pos = event.pos

    def set_target(self, target_x: float, target_y: float, target_zoom: float = 1.0):
        self.target_center.x = target_x
        self.target_center.y = target_y
        self.target_zoom = target_zoom

    def focus_on_area(self, visited_points: list[tuple[int, int]], tile_size: int):
        if not visited_points:
            return

        min_x = min(x for x, y in visited_points)
        max_x = max(x for x, y in visited_points)
        min_y = min(y for x, y in visited_points)
        max_y = max(y for x, y in visited_points)

        center_x = ((min_x + max_x) / 2) * tile_size + tile_size / 2
        center_y = ((min_y + max_y) / 2) * tile_size + tile_size / 2
        self.target_center = pygame.math.Vector2(center_x, center_y)

        scan_w = (max_x - min_x + 4) * tile_size
        scan_h = (max_y - min_y + 4) * tile_size

        zoom_x = self.viewport_width / scan_w if scan_w > 0 else 1.0
        zoom_y = self.viewport_height / scan_h if scan_h > 0 else 1.0

        self.target_zoom = max(min(zoom_x, zoom_y, 1.0), 0.45)

    def update(self, time_delta: float):
        # [ĐÃ SỬA]: Giảm tốc độ Lerp từ 5.0 xuống 2.0 để camera di chuyển "chậm dần" mượt hơn.
        lerp_speed = 2.0
        self.current_center.x += (self.target_center.x - self.current_center.x) * lerp_speed * time_delta
        self.current_center.y += (self.target_center.y - self.current_center.y) * lerp_speed * time_delta

        # [ĐÃ SỬA]: Giảm độ Snap xuống 0.05 để tránh giật cục khi camera sắp dừng hẳn
        if abs(self.target_center.x - self.current_center.x) < 0.05:
            self.current_center.x = self.target_center.x
        if abs(self.target_center.y - self.current_center.y) < 0.05:
            self.current_center.y = self.target_center.y

        self.current_zoom += (self.target_zoom - self.current_zoom) * 3 * time_delta

    def get_offset(self) -> pygame.math.Vector2:
        scaled_w = int(self.map_pixel_width * self.current_zoom)
        scaled_h = int(self.map_pixel_height * self.current_zoom)

        scaled_cam_x = self.current_center.x * self.current_zoom
        scaled_cam_y = self.current_center.y * self.current_zoom

        offset_x = self.viewport_width / 2 - scaled_cam_x
        offset_y = self.viewport_height / 2 - scaled_cam_y

        if scaled_w > self.viewport_width:
            offset_x = min(0, max(self.viewport_width - scaled_w, offset_x))
        else:
            offset_x = (self.viewport_width - scaled_w) / 2

        if scaled_h > self.viewport_height:
            offset_y = min(0, max(self.viewport_height - scaled_h, offset_y))
        else:
            offset_y = (self.viewport_height - scaled_h) / 2

        # [ĐÃ SỬA]: Dùng round() để bo tròn chính xác, làm camera chạy êm như bôi mỡ
        return pygame.math.Vector2(round(offset_x), round(offset_y))

    @property
    def zoom(self) -> float:
        return self.current_zoom