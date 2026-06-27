"""
📄 Tên File: level_manager.py (Nằm trong src/core/)
* Cập nhật: Cơ chế Lazy Loading (Chỉ tải config của Level khi được yêu cầu).
"""
import os
import json

class LevelManager:
    def __init__(self):
        self.current_level = 1
        self.max_levels = 7
        self.levels_config = {}
        self.levels_dir = os.path.join("src", "levels")

        self.save_file = "save_data.json"
        self.unlocked_level = self._load_save_data()

        # ĐÃ XÓA hàm _load_all_levels() ở đây!

    def _load_save_data(self) -> int:
        """Đọc file save, ép buộc mở khóa luôn đến Level 3 để TEST"""
        if os.path.exists(self.save_file):
            with open(self.save_file, "r") as f:
                try:
                    data = json.load(f)
                    # Ép hệ thống luôn lấy mức lớn nhất giữa file save và 3
                    return max(data.get("unlocked_level", 1), 3)
                except:
                    return 3
        return 3

    def unlock_next_level(self):
        if self.current_level >= self.unlocked_level and self.current_level < self.max_levels:
            self.unlocked_level = self.current_level + 1
            with open(self.save_file, "w") as f:
                json.dump({"unlocked_level": self.unlocked_level}, f)

    def get_unlocked_level(self) -> int:
        return self.unlocked_level

    def advance_level(self) -> bool:
        if self.current_level < self.max_levels:
            self.current_level += 1
            print(f"🌍 Đã chuyển sang Level {self.current_level}: {self.get_current_config()['name']}")
            return True
        return False

    # [MỚI] Hàm chỉ nạp đúng 1 file config khi được gọi
    def get_level_config(self, level_id: int):
        # Nếu đã nạp rồi thì lấy ra dùng luôn (Cache)
        if level_id in self.levels_config:
            return self.levels_config[level_id]

        folder_name = f"level_{level_id:02d}"
        config_path = os.path.join(self.levels_dir, folder_name, "config.json")

        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                try:
                    config_data = json.load(f)
                    self.levels_config[level_id] = config_data
                    return config_data
                except json.JSONDecodeError:
                    print(f"❌ Lỗi: File {config_path} bị sai định dạng JSON!")

        # Nếu file chưa tồn tại hoặc bị lỗi, trả về cấu hình an toàn
        fallback_data = self._get_fallback_config(level_id)
        self.levels_config[level_id] = fallback_data
        return fallback_data

    def _get_fallback_config(self, level_id):
        return {
            "id": level_id,
            "name": f"LEVEL {level_id}: COMING SOON",
            "desc": "Đang xây dựng...",
            "algorithms": ["BFS"],
            "unlocked_traps": ["WALL"],
            "max_rounds": 3,
            "retries": 1,
            "ram_max": 200, "cpu_max": 500,
            "map_file": "assets/maps/dungeon_map_1.tmx"
        }

    # Đã sửa lại để gọi hàm lấy theo ID ở trên
    def get_current_config(self):
        return self.get_level_config(self.current_level)

    def get_unlocked_algorithms(self):
        return self.get_current_config()["algorithms"]

    def set_level(self, level_num):
        if 1 <= level_num <= self.max_levels:
            self.current_level = level_num
            print(f"🌍 Đã nạp dữ liệu Level {level_num}: {self.get_current_config()['name']}")

    def get_current_maps(self):
        return self.get_current_config().get("maps", [])

    def get_unlocked_traps(self):
        return self.get_current_config().get("unlocked_traps", [])