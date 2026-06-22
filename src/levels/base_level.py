"""
📄 Tên File: base_level.py (Nằm trong src/levels/)
* Vai trò: Khuôn mẫu (Interface) chuẩn cho mọi màn chơi.
"""

class BaseLevel:
    def __init__(self, config: dict):
        self.config = config
        self.id = config.get("id", 1)
        self.name = config.get("name", "Unknown Level")
        self.map_file = config.get("map_file", "")

    def get_allowed_algorithms(self):
        return self.config.get("algorithms", [])

    def get_allowed_traps(self):
        return self.config.get("unlocked_traps", [])

    def check_custom_win_condition(self, game_state):
        """Cho phép các Level sau này tự định nghĩa điều kiện thắng/thua dị biệt"""
        pass