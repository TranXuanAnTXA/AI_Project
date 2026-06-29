"""
📄 Tên File: level_manager.py (Nằm trong src/core/)
* Cập nhật: Hỗ trợ cấu trúc algo_groups để phân loại thuật toán.
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

    def _load_save_data(self) -> int:
        if os.path.exists(self.save_file):
            with open(self.save_file, "r") as f:
                try:
                    data = json.load(f)
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
            print(f"🌍 Đã chuyển sang Level {self.current_level}: {self.get_current_config().get('name', '')}")
            return True
        return False

    def get_level_config(self, level_id: int):
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

        fallback_data = self._get_fallback_config(level_id)
        self.levels_config[level_id] = fallback_data
        return fallback_data

    def _get_fallback_config(self, level_id):
        return {
            "id": level_id,
            "name": f"LEVEL {level_id}: COMING SOON",
            "desc": "Đang xây dựng...",
            "algo_groups": [
                {
                    "group_name": "Uninformed Search",
                    "algos": ["BFS"]
                }
            ],
            "unlocked_traps": ["WALL"],
            "max_rounds": 3,
            "retries": 1,
            "ram_max": 200, "cpu_max": 500,
            "map_file": "assets/maps/dungeon_map_1.tmx"
        }

    def get_current_config(self):
        return self.get_level_config(self.current_level)

    def get_unlocked_algorithms(self):
        """Gom toàn bộ thuật toán trong các nhóm lại thành 1 list phẳng (Phòng ngừa lỗi tương thích ngược)"""
        cfg = self.get_current_config()
        if "algo_groups" in cfg:
            algos = []
            for group in cfg["algo_groups"]:
                algos.extend(group.get("algos", []))
            return algos
        return cfg.get("algorithms", [])

    def set_level(self, level_num):
        if 1 <= level_num <= self.max_levels:
            self.current_level = level_num
            print(f"🌍 Đã nạp dữ liệu Level {level_num}: {self.get_current_config().get('name', '')}")

    def get_current_maps(self):
        return self.get_current_config().get("maps", [])

    def get_unlocked_traps(self):
        return self.get_current_config().get("unlocked_traps", [])