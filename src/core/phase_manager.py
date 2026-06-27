"""
📄 Tên File: phase_manager.py (Nằm trong src/core/)
* Cập nhật: Sửa kẹt Pause, Đồng hồ trôi nhanh theo x2/x3, Fix logic Boss tràn RAM.
"""

class PhaseManager:
    def __init__(self, dashboard, level_manager):
        self.dashboard = dashboard
        self.level_manager = level_manager
        self.state = "IDLE"
        self.current_phase = "HERO"
        self.current_round = 1
        self.retry_count = 1
        self.timer = 0.0
        self.prep_time = 30.0
        self.exec_time = 60.0
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
        old_state = self.state # Lưu lại trạng thái cũ
        self.state = new_state

        if new_state == "PREPARING":
            self.timer = self.prep_time
            self.dashboard.algo_state = "IDLE"
        elif new_state == "EXECUTING":
            # CHỈ RESET ĐỒNG HỒ KHI BẮT ĐẦU TỪ PREPARING
            if old_state == "PREPARING":
                self.timer = self.exec_time
            self.dashboard.algo_state = "RUNNING"
        elif new_state in ["IDLE", "FAIL_SCREEN", "LEVEL_COMPLETE", "ANNOUNCING"]:
            self.dashboard.algo_state = "IDLE"

    # [ĐÃ SỬA]: Nhận tốc độ và Fix logic Boss thắng
    def update(self, time_delta, game_stats, speed_multiplier=1.0):
        if self.state in ["PREPARING", "EXECUTING", "MOVING"]:

            # Nếu đang chạy thuật toán hoặc đi bộ -> Đồng hồ chạy x2, x3. Nếu đang chuẩn bị -> Thời gian thực
            actual_delta = time_delta * speed_multiplier if self.state in ["EXECUTING", "MOVING"] else time_delta
            self.timer -= actual_delta

            if self.timer <= 0:
                if self.state == "PREPARING":
                    print("⏳ Hết 30s chuẩn bị! Tự động khởi chạy...")
                    self.set_state("EXECUTING")
                    return True
                elif self.state in ["EXECUTING", "MOVING"]:
                    self.handle_timeout()

            if self.state == "EXECUTING":
                ram = game_stats.get("ram", 0)
                cpu = game_stats.get("cpu", 0)
                cfg = self.level_manager.get_current_config()

                if ram > cfg.get("ram_max", 9999):
                    if self.current_phase == "HERO":
                        self.trigger_failure("OUT OF MEMORY: RAM MAXED OUT")
                    else: # BOSS PHA: Tràn RAM nghĩa là Boss thắng!
                        print("💀 GHOST HERO HẾT RAM! BOSS WIN.")
                        self.trigger_success()

                elif cpu > cfg.get("cpu_max", 9999):
                    if self.current_phase == "HERO":
                        self.trigger_failure("SYSTEM OVERLOAD: CPU MAXED OUT")
                    else: # BOSS PHA: Quá tải CPU nghĩa là Boss thắng!
                        print("💀 GHOST HERO QUÁ TẢI CPU! BOSS WIN.")
                        self.trigger_success()

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

        if self.state in ["EXECUTING", "MOVING", "PAUSED"] and ui_algo_state == "IDLE":
            self.set_state("PREPARING")

        # [ĐÃ SỬA]: Ghi nhớ trạng thái trước khi Pause để chống kẹt
        if self.state in ["EXECUTING", "MOVING"] and ui_algo_state == "PAUSED":
            self._was_executing = (self.state == "EXECUTING")
            self.state = "PAUSED"

        elif self.state == "PAUSED" and ui_algo_state == "RUNNING":
            self.state = "EXECUTING" if getattr(self, '_was_executing', True) else "MOVING"

        return False

    def check_goal_collision(self, hero, goal_pos):
        if self.state == "MOVING":
            hero_coord = (hero.grid_pos[0], hero.grid_pos[1])
            goal_coord = (goal_pos[0], goal_pos[1])

            if hero_coord == goal_coord:
                if self.current_phase == "HERO":
                    self.trigger_success()
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

    def check_rewind_completion(self, sim_manager, reset_cam_callback):
        if sim_manager.is_rewind_finished():
            reset_cam_callback()
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