"""
📄 Tên File: phase_manager.py (Nằm trong src/core/)
* Vai trò: Quản lý vòng lặp Game (Round, Phase), đếm ngược thời gian, và xử lý Thắng/Thua/Retry.
"""

class PhaseManager:
    def __init__(self, dashboard, level_manager):
        self.dashboard = dashboard
        self.level_manager = level_manager

        # Các trạng thái: IDLE, ANNOUNCING, PREPARING, EXECUTING, MOVING, PAUSED, REWINDING, FAIL_SCREEN, LEVEL_COMPLETE
        self.state = "IDLE"

        self.current_phase = "HERO"
        self.current_round = 1
        self.retry_count = 1

        self.timer = 0.0
        self.prep_time = 30.0  # 30s chọn thuật toán / đặt bẫy
        self.exec_time = 60.0  # 60s để thuật toán chạy VÀ Hero đi bộ đến đích

        self.hero_history_algo = ""
        self.failure_reason = ""

    def reset_for_new_level(self):
        cfg = self.level_manager.get_current_config()
        self.current_round = 1
        self.current_phase = "HERO"
        self.retry_count = cfg.get("retries", 1)

        self.dashboard.current_round = self.current_round
        self.dashboard.set_phase(self.current_phase)
        self.set_state("ANNOUNCING")

    def set_state(self, new_state):
        self.state = new_state

        if new_state == "PREPARING":
            self.timer = self.prep_time
            self.dashboard.algo_state = "IDLE"

        elif new_state == "EXECUTING":
            self.timer = self.exec_time
            self.dashboard.algo_state = "RUNNING"

        elif new_state in ["IDLE", "FAIL_SCREEN", "LEVEL_COMPLETE", "ANNOUNCING"]:
            self.dashboard.algo_state = "IDLE"

    def update(self, time_delta, game_stats):
        """Đếm lùi thời gian. Trả về True nếu cần tự động khởi chạy."""
        # [SỬA LỖI]: Bổ sung trạng thái "MOVING" vào danh sách đếm lùi thời gian
        if self.state in ["PREPARING", "EXECUTING", "MOVING"]:
            self.timer -= time_delta

            # 1. KIỂM TRA HẾT GIỜ (TIMEOUT)
            if self.timer <= 0:
                if self.state == "PREPARING":
                    print("⏳ Hết 30s chuẩn bị! Tự động khởi chạy...")
                    self.set_state("EXECUTING")
                    return True

                    # Hết giờ khi thuật toán đang duyệt hoặc Hero đang đi -> THUA
                elif self.state in ["EXECUTING", "MOVING"]:
                    self.handle_timeout()

            # 2. KIỂM TRA QUÁ TẢI (RAM / CPU) CHỈ KHI THUẬT TOÁN ĐANG CHẠY
            if self.state == "EXECUTING":
                ram = game_stats.get("ram", 0)
                cpu = game_stats.get("cpu", 0)
                cfg = self.level_manager.get_current_config()

                # Bảo vệ bằng get() phòng khi JSON thiếu trường
                if ram > cfg.get("ram_max", 9999):
                    self.trigger_failure("OUT OF MEMORY: RAM MAXED OUT")
                elif cpu > cfg.get("cpu_max", 9999):
                    self.trigger_failure("SYSTEM OVERLOAD: CPU MAXED OUT")

        return False

    def handle_timeout(self):
        if self.current_phase == "HERO":
            self.trigger_failure("TIMEOUT: FAILED TO REACH GOAL IN 60S")
        elif self.current_phase == "BOSS":
            print("💀 GHOST HERO HẾT GIỜ! BOSS DEFENDED SUCCESSFULLY.")
            self.trigger_success()

    def sync_with_ui(self, ui_algo_state, selected_algo):
        if self.state == "PREPARING" and ui_algo_state == "RUNNING":
            if self.current_phase == "HERO":
                self.hero_history_algo = selected_algo
            self.set_state("EXECUTING")
            return True

            # Cho phép STOP cả lúc đang đi
        if self.state in ["EXECUTING", "MOVING", "PAUSED"] and ui_algo_state == "IDLE":
            self.set_state("PREPARING")

        if self.state in ["EXECUTING", "MOVING"] and ui_algo_state == "PAUSED":
            self.state = "PAUSED"
        elif self.state == "PAUSED" and ui_algo_state == "RUNNING":
            # Resume lại trạng thái tương ứng
            self.state = "EXECUTING" if getattr(self, '_was_executing', True) else "MOVING"

        return False

    def check_goal_collision(self, hero, goal_pos):
        # [SỬA LỖI]: Bắt va chạm đích khi đang ở trạng thái MOVING
        if self.state == "MOVING":
            # Chuyển toạ độ về list/tuple để so sánh an toàn
            hero_coord = (hero.grid_pos[0], hero.grid_pos[1])
            goal_coord = (goal_pos[0], goal_pos[1])

            if hero_coord == goal_coord:
                if self.current_phase == "HERO":
                    self.trigger_success() # Kích hoạt chuyển phase
                elif self.current_phase == "BOSS":
                    self.trigger_failure("DEFENSE BROKEN: GHOST REACHED THE GOAL")

    def trigger_success(self):
        print(f"✅ PHASE {self.current_phase} HOÀN THÀNH!")
        self.set_state("REWINDING")

    def trigger_failure(self, reason):
        print(f"❌ THẤT BẠI: {reason}")
        self.failure_reason = reason
        self.set_state("FAIL_SCREEN")

    def process_retry(self):
        self.retry_count -= 1
        if self.retry_count < 0:
            return False
        else:
            self.set_state("ANNOUNCING")
            return True

            # [MỚI]: Hàm đón tín hiệu hoàn thành Rewind từ game_scene
    def check_rewind_completion(self, sim_manager, reset_cam_callback):
        # Nếu mảng lịch sử (history) đã bị rút hết sạch, nghĩa là đã lùi về vạch đích
        if not sim_manager.history:
            reset_cam_callback() # Kéo camera về lại vị trí Hero (Start)
            self.advance_phase_or_round()

    def advance_phase_or_round(self):
        cfg = self.level_manager.get_current_config()

        if self.current_phase == "HERO":
            self.current_phase = "BOSS"
        else:
            self.current_phase = "HERO"
            self.current_round += 1

            if self.current_round > cfg.get("max_rounds", 3):
                print("🏆 HOÀN THÀNH TOÀN BỘ ROUND! LÊN LEVEL MỚI...")
                self.set_state("LEVEL_COMPLETE")
                return

        self.dashboard.set_phase(self.current_phase)
        self.dashboard.current_round = self.current_round
        self.set_state("ANNOUNCING")