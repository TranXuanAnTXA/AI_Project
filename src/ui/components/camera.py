import pygame

class Camera:
    def __init__(self, viewport_width: int, viewport_height: int, map_pixel_width: int, map_pixel_height: int):
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.map_pixel_width = map_pixel_width
        self.map_pixel_height = map_pixel_height

        # Vị trí tâm camera hiện tại và mục tiêu (Sử dụng Vector2 để tính toán Lerp mượt mà)
        self.current_center = pygame.math.Vector2(0, 0)
        self.target_center = pygame.math.Vector2(0, 0)

        # Tỷ lệ thu phóng hiện tại và mục tiêu
        self.current_zoom = 1.0
        self.target_zoom = 1.0

        self.is_dragging = False
        self.drag_last_pos = (0, 0)

    def get_min_zoom(self) -> float:
        """
        Tính độ zoom nhỏ nhất sao cho map vừa khít viewport,
        Nhìn thấy toàn bộ map 30x30 mà không bị cắt xén.
        """
        min_zoom_x = self.viewport_width / self.map_pixel_width
        min_zoom_y = self.viewport_height / self.map_pixel_height

        # ĐỔI THÀNH min() ĐỂ THU NHỎ THẤY ĐƯỢC TOÀN BỘ MAP
        return min(min_zoom_x, min_zoom_y)

    def zoom_to_fit(self):
        """Lệnh tự động thu nhỏ hết cỡ và đưa camera ra giữa tâm bản đồ."""
        self.target_zoom = self.get_min_zoom()
        self.target_center.x = self.map_pixel_width / 2
        self.target_center.y = self.map_pixel_height / 2

    def handle_input(self, event, offset_x=0, offset_y=0):
        """
        Camera tự xử lý các sự kiện chuột. Không hề có chữ "BOSS" nào ở đây.
        offset_x, offset_y: Tọa độ góc trên bên trái của Viewport (để tính vùng click cho chuẩn).
        """
        # 1. Lăn chuột để Zoom (Giới hạn từ min_zoom đến 2.0)
        if event.type == pygame.MOUSEWHEEL:
            min_zoom = self.get_min_zoom()
            self.target_zoom = max(min_zoom, min(2.0, self.target_zoom + event.y * 0.1))

        # 2. Bấm chuột trái để kéo
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Chỉ cho phép kéo nếu click vào bên trong Viewport
            if offset_x <= event.pos[0] <= offset_x + self.viewport_width and \
                    offset_y <= event.pos[1] <= offset_y + self.viewport_height:
                self.is_dragging = True
                self.drag_last_pos = event.pos

        # 3. Nhả chuột
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.is_dragging = False

        # 4. Kéo rê chuột
        elif event.type == pygame.MOUSEMOTION and self.is_dragging:
            dx = event.pos[0] - self.drag_last_pos[0]
            dy = event.pos[1] - self.drag_last_pos[1]

            # Di chuyển ngược chiều chuột và scale theo zoom
            self.target_center.x -= dx / self.current_zoom
            self.target_center.y -= dy / self.current_zoom
            self.drag_last_pos = event.pos

    def set_target(self, target_x: float, target_y: float, target_zoom: float = 1.0):
        """Đặt mục tiêu di chuyển và độ zoom cho camera (Ví dụ: bám theo Hero)."""
        self.target_center.x = target_x
        self.target_center.y = target_y
        self.target_zoom = target_zoom

    def focus_on_area(self, visited_points: list[tuple[int, int]], tile_size: int):
        """
        Tự động tính toán tâm và độ zoom để bao trọn vùng thuật toán đang quét.
        visited_points: Danh sách các tọa độ lưới (x, y) đã duyệt.
        """
        if not visited_points:
            return

        min_x = min(x for x, y in visited_points)
        max_x = max(x for x, y in visited_points)
        min_y = min(y for x, y in visited_points)
        max_y = max(y for x, y in visited_points)

        # Tính toán tâm của vùng quét (đổi từ tọa độ lưới sang pixel)
        center_x = ((min_x + max_x) / 2) * tile_size + tile_size / 2
        center_y = ((min_y + max_y) / 2) * tile_size + tile_size / 2
        self.target_center = pygame.math.Vector2(center_x, center_y)

        # Tính toán độ zoom phù hợp dựa trên kích thước vùng quét (+4 ô đệm để nhìn thoáng hơn)
        scan_w = (max_x - min_x + 4) * tile_size
        scan_h = (max_y - min_y + 4) * tile_size

        zoom_x = self.viewport_width / scan_w if scan_w > 0 else 1.0
        zoom_y = self.viewport_height / scan_h if scan_h > 0 else 1.0

        # Giới hạn tỷ lệ zoom trong khoảng từ 0.45 đến 1.0
        self.target_zoom = max(min(zoom_x, zoom_y, 1.0), 0.45)

    def update(self, time_delta: float):
        """Cập nhật vị trí và độ zoom mượt mà sử dụng Lerp theo thời gian thực."""
        # Nội suy tuyến tính (Lerp) vị trí tâm (Tốc độ = 5)
        self.current_center.x += (self.target_center.x - self.current_center.x) * 5 * time_delta
        self.current_center.y += (self.target_center.y - self.current_center.y) * 5 * time_delta

        # Nội suy tuyến tính (Lerp) độ zoom (Tốc độ = 3)
        self.current_zoom += (self.target_zoom - self.current_zoom) * 3 * time_delta

    def get_offset(self) -> pygame.math.Vector2:
        """
        Tính toán và trả về Vector độ lệch (Offset) để vẽ bản đồ lên viewport.
        Đã bao gồm logic khóa viền không cho trượt ra ngoài rìa bản đồ.
        """
        # Kích thước bản đồ sau khi nhân với tỷ lệ zoom
        scaled_w = int(self.map_pixel_width * self.current_zoom)
        scaled_h = int(self.map_pixel_height * self.current_zoom)

        # Tọa độ tâm camera sau khi nhân tỷ lệ zoom
        scaled_cam_x = self.current_center.x * self.current_zoom
        scaled_cam_y = self.current_center.y * self.current_zoom

        # Tính toán tọa độ Top-Left lý thuyết để đưa tâm camera vào giữa viewport
        offset_x = self.viewport_width / 2 - scaled_cam_x
        offset_y = self.viewport_height / 2 - scaled_cam_y

        # Giới hạn trục X (Khóa viền trái/phải hoặc căn giữa nếu bản đồ nhỏ hơn viewport)
        if scaled_w > self.viewport_width:
            offset_x = min(0, max(self.viewport_width - scaled_w, offset_x))
        else:
            offset_x = (self.viewport_width - scaled_w) / 2

        # Giới hạn trục Y (Khóa viền trên/dưới hoặc căn giữa nếu bản đồ nhỏ hơn viewport)
        if scaled_h > self.viewport_height:
            offset_y = min(0, max(self.viewport_height - scaled_h, offset_y))
        else:
            offset_y = (self.viewport_height - scaled_h) / 2

        return pygame.math.Vector2(offset_x, offset_y)

    @property
    def zoom(self) -> float:
        """Trả về độ zoom hiện tại của camera."""
        return self.current_zoom