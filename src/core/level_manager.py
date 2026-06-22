"""
📄 Tên File: level_manager.py (Nằm trong src/core/)
* Vai trò: Tự động quét các thư mục src/levels/level_xx/ và nạp cấu hình từ file JSON.
"""
import os
import json

class LevelManager:
    def __init__(self):
        self.current_level = 1
        self.max_levels = 7
        self.levels_config = {}
        self.levels_dir = os.path.join("src", "levels")

        self._load_all_levels()

    def _load_all_levels(self):
        """Quét qua các thư mục level_01 -> level_07 và nạp file config.json"""
        for i in range(1, self.max_levels + 1):
            folder_name = f"level_{i:02d}" # Tạo chuỗi "level_01", "level_02"...
            config_path = os.path.join(self.levels_dir, folder_name, "config.json")

            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    try:
                        self.levels_config[i] = json.load(f)
                    except json.JSONDecodeError:
                        print(f"❌ Lỗi: File {config_path} bị sai định dạng JSON!")
            else:
                # Nếu chưa tạo file json cho level đó thì dùng config mặc định an toàn
                self.levels_config[i] = self._get_fallback_config(i)

    def _get_fallback_config(self, level_id):
        """Cấu hình an toàn phòng trường hợp bạn chưa kịp tạo thư mục cho Level đó"""
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

    def get_current_config(self):
        return self.levels_config.get(self.current_level, self._get_fallback_config(self.current_level))

    def get_unlocked_algorithms(self):
        return self.get_current_config()["algorithms"]

    def set_level(self, level_num):
        if 1 <= level_num <= self.max_levels:
            self.current_level = level_num
            print(f"🌍 Đã nạp dữ liệu Level {level_num}: {self.get_current_config()['name']}")

    def get_current_maps(self):
        """Trả về danh sách bản đồ có sẵn của level hiện tại"""
        return self.get_current_config().get("maps", [])

    def get_unlocked_traps(self):
        """Trả về danh sách các loại bẫy được phép dùng của level hiện tại"""
        return self.get_current_config().get("unlocked_traps", [])