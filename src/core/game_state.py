"""
📄 Tên File: game_state.py (Nằm trong src/core/)
* Vai trò: Quản lý toàn bộ trạng thái, tài nguyên và luật chơi của Game (Không dính dáng tới UI/Pygame).
"""

from enum import Enum, auto

class GamePhase(Enum):
    """Định nghĩa các Pha (Phase) luân phiên trong game."""
    HERO_PLANNING = auto()   # Pha 1: Hero đang dùng phòng Giả lập để chọn thuật toán
    BOSS_TRAPPING = auto()   # Pha 2: Boss đang đặt bẫy, bóp méo địa hình
    GHOST_RUNNING = auto()   # Pha 2.5: Bóng ma của Hero bắt đầu chạy thuật toán đã chốt
    SURVIVAL_MODE = auto()   # Pha 3: Boss xuất hiện, chuyển sang game sinh tồn


class GameState:
    """Lớp đối tượng lưu trữ và quản lý luật chơi."""

    def __init__(self, max_anomaly: int = 100):
        # 1. QUẢN LÝ PHA VÀ LƯỢT CHƠI
        self.current_phase = GamePhase.HERO_PLANNING
        self.round_number = 1

        # 2. QUẢN LÝ TÀI NGUYÊN (METRICS)
        self.anomaly_meter = 0              # Điểm dị thường (0 -> max_anomaly)
        self.max_anomaly = max_anomaly
        self.hero_energy_cores = 2          # Dùng để Hero bật tính năng "Phòng Giả Lập"
        self.boss_malice_points = 50        # Dùng để Boss mua bẫy (đổi địa hình, đổi Heuristic)

        # 3. TRẠNG THÁI AI & BẢN ĐỒ
        self.selected_algorithm: str | None = None  # Tên thuật toán Hero đã chốt (vd: "a_star")
        self.is_boss_spawned = False                # Cờ đánh dấu Boss (The Purger) đã thức tỉnh chưa
        # self.current_map = None                   # (Sẽ chứa đối tượng GridMap của màn hiện tại)

    def switch_phase(self, new_phase: GamePhase) -> None:
        """Chuyển đổi giữa các Pha trong game."""
        self.current_phase = new_phase
        # Nếu chuyển lại về Hero Planning, nghĩa là bắt đầu một vòng chơi (Round) mới
        if new_phase == GamePhase.HERO_PLANNING:
            self.round_number += 1

    def commit_hero_algorithm(self, algorithm_name: str) -> bool:
        """Hero chốt thuật toán ở Pha 1. Trả về True nếu thành công."""
        if self.current_phase != GamePhase.HERO_PLANNING:
            return False

        self.selected_algorithm = algorithm_name
        self.switch_phase(GamePhase.BOSS_TRAPPING) # Chốt xong thì đổi phiên cho Boss
        return True

    def use_hero_simulation(self) -> bool:
        """Hero kích hoạt phòng giả lập (Tốn 1 Lõi năng lượng)."""
        if self.hero_energy_cores > 0:
            self.hero_energy_cores -= 1
            return True
        return False

    def add_anomaly_points(self, points: int) -> bool:
        """
        Cộng điểm sai lầm vào hệ thống.
        Được gọi bởi thư mục `algorithms` khi thuật toán duyệt ô thừa.
        Trả về True nếu thanh Anomaly đầy (Boss thức tỉnh).
        """
        self.anomaly_meter += points
        if self.anomaly_meter >= self.max_anomaly:
            self.anomaly_meter = self.max_anomaly
            self.trigger_boss_event()
            return True
        return False

    def trigger_boss_event(self) -> None:
        """Kích hoạt sự kiện Boss khi hệ thống quá tải."""
        self.is_boss_spawned = True
        self.switch_phase(GamePhase.SURVIVAL_MODE)
        # Tại đây UI sẽ nhận thấy cờ is_boss_spawned = True và bắt đầu nháy đèn đỏ, vẽ hình Boss ra.

    def reset_state_for_new_level(self, new_max_anomaly: int = 100) -> None:
        """Reset các chỉ số khi chuyển sang màn chơi mới (Level mới)."""
        self.current_phase = GamePhase.HERO_PLANNING
        self.round_number = 1
        self.anomaly_meter = 0
        self.max_anomaly = new_max_anomaly
        self.selected_algorithm = None
        self.is_boss_spawned = False