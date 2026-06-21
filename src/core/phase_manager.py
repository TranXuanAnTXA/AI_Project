"""
📄 Tên File: phase_manager.py (Nằm trong src/core/)
"""
class PhaseManager:
    def __init__(self, dashboard):
        self.dashboard = dashboard
        self.state = "IDLE" # Các trạng thái: IDLE, SIMULATING, MOVING, REWINDING, PAUSED

    def set_state(self, new_state):
        self.state = new_state
        if new_state == "IDLE":
            self.dashboard.algo_state = "IDLE"

    def sync_with_dashboard(self, on_start_callback):
        """Đọc tín hiệu từ UI Dashboard để đổi State nội bộ."""
        dash_state = self.dashboard.algo_state

        # UI Bấm Play từ lúc đang rảnh
        if dash_state == "RUNNING" and self.state == "IDLE":
            self.set_state("SIMULATING")
            on_start_callback() # Trigger khởi tạo Simulator
        elif dash_state == "PAUSED" and self.state == "SIMULATING":
            self.set_state("PAUSED")
        # UI Bấm Resume từ lúc Paused
        elif dash_state == "RUNNING" and self.state == "PAUSED":
            self.set_state("SIMULATING")

        # UI Bấm Stop
        elif dash_state == "IDLE" and self.state in ["SIMULATING", "MOVING", "PAUSED"]:
            self.set_state("IDLE")

    def check_goal_collision(self, hero, goal_pos):
        """Kích hoạt Rewind nếu chạm đích."""
        if self.state == "MOVING" and not hero.is_moving and not hero.path:
            current_grid = (hero.grid_pos[0], hero.grid_pos[1])
            if current_grid == goal_pos:
                self.set_state("REWINDING")
                print("⏰ KÍCH HOẠT REWIND!")
            else:
                self.set_state("IDLE")

    def check_rewind_completion(self, sim_manager, reset_camera_callback):
        """Kết thúc tua ngược và chuyển sang Phase BOSS."""
        if self.state == "REWINDING" and sim_manager.is_rewind_finished():
            self.set_state("IDLE")
            self.dashboard.set_phase("BOSS")
            reset_camera_callback()
            print("👹 CHUYỂN SANG PHASE 2: BOSS ARCHITECT!")