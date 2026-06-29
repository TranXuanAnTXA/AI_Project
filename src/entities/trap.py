import pygame

class Trap:
    def __init__(self, x: int, y: int, width: int, height: int, tile_size: int):
        self.grid_x = x
        self.grid_y = y
        self.pixel_x = x * tile_size
        self.pixel_y = y * tile_size
        self.width_pixels = width * tile_size
        self.height_pixels = height * tile_size
        self.tile_size = tile_size

        # Load 5 frame của ảnh (5 hàng ngang)
        self.frames = self._load_frames("assets/sprites/trap_animation.png")
        self.current_frame = 0.0
        self.state = "idle"
        self.animation_speed = 0.4
        self.image = self.frames[0]
        self.is_triggered_fully = False # Kiểm tra chông đã đâm hết cỡ chưa

    def _load_frames(self, path):
        try:
            sheet = pygame.image.load(path).convert_alpha()
        except Exception as e:
            print(f"Lỗi tải ảnh bẫy: {e}")
            surf = pygame.Surface((self.width_pixels, self.height_pixels))
            surf.fill((100, 100, 100)) # Màu mặc định nếu mất ảnh
            return [surf] * 5

        # Ảnh bạn gửi có 5 khung hình theo chiều dọc
        frame_w = sheet.get_width()
        frame_h = sheet.get_height() // 5
        frames = []

        for i in range(5):
            # Cắt từng hàng 
            frame_surf = pygame.Surface((frame_w, frame_h), pygame.SRCALPHA)
            frame_surf.blit(sheet, (0, 0), (0, i * frame_h, frame_w, frame_h))

            # Scale cho vừa với kích thước thật của bẫy trên lưới Tiled
            scaled_surf = pygame.transform.scale(frame_surf, (self.width_pixels, self.height_pixels))
            frames.append(scaled_surf)

        return frames

    def trigger(self):
        """ Kích hoạt chông đâm lên """
        if self.state == "idle":
            self.state = "triggered"
            self.current_frame = 0.0

    def update(self, time_delta: float, speed_multiplier: float = 1.0):
        # Nếu đang kích hoạt thì chạy frame từ 0 đến 4
        if self.state == "triggered" and not self.is_triggered_fully:
            self.current_frame += self.animation_speed * speed_multiplier

            if self.current_frame >= len(self.frames) - 1:
                self.current_frame = len(self.frames) - 1
                self.is_triggered_fully = True # Khóa luôn ở trạng thái gai nhọn

            self.image = self.frames[int(self.current_frame)]

    def draw(self, surface, offset_x=0, offset_y=0):
        surface.blit(self.image, (self.pixel_x + offset_x, self.pixel_y + offset_y))