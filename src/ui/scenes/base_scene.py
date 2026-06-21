"""
📄 Tên File: base_scene.py (Nằm trong src/ui/scenes/)
* Vai trò: Khuôn mẫu gốc. Bất kỳ Scene nào cũng phải kế thừa class này và có đủ 3 hàm cơ bản.
"""

class BaseScene:
    def __init__(self, manager):
        self.manager = manager  # Lưu lại SceneManager để gọi lệnh chuyển cảnh khi cần

    def process_event(self, event):
        """Xử lý sự kiện bàn phím, chuột riêng cho Scene này."""
        pass

    def update(self, time_delta):
        """Cập nhật logic, tọa độ, trạng thái mỗi frame."""
        pass

    def render(self, surface):
        """Vẽ đồ họa lên màn hình."""
        pass