"""
📄 Tên File: phase_manager.py (Nằm trong src/core/)
* Cập nhật: Thêm trạng thái DYING (Hấp hối) kéo dài 2 giây để Hero kịp chạy animation gục ngã.
* Cập nhật VS Mode: Thêm trạng thái VS_SELECTION và fix lỗi đồng bộ tua ngược (Rewind).
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

        # [MỚI]: Biến phục vụ đếm ngược chờ Animation gục ngã
        self.death_timer = 0.0
        self.pending_reason = ""
        self.is_boss_win_pending = False

    def reset_for_new_level(self):
        cfg = self.level_manager.get_current_config()
        self.current_round = 1
        self.current_phase = "HERO"
        self.retry_count = cfg.get("retries", 1)
        self.dashboard.current_round = self.current_round
        self.dashboard.set_phase(self.current_phase)
        self.set_state("ANNOUNCING")

    def set_state(self, new_state):
        old_state = self.state
        self.state = new_state

        if new_state == "PREPARING":
            self.timer = self.prep_time
            self.dashboard.algo_state = "IDLE"
        elif new_state == "EXECUTING":
            if old_state == "PREPARING":
                self.timer = self.exec_time
            self.dashboard.algo_state = "RUNNING"
        # [ĐÃ SỬA]: Thêm VS_SELECTION vào danh sách reset algo_state
        elif new_state in ["IDLE", "FAIL_SCREEN", "LEVEL_COMPLETE", "ANNOUNCING", "DYING", "VS_SELECTION"]:
            self.dashboard.algo_state = "IDLE"

    # [MỚI]: Kích hoạt trạng thái Hấp Hối (Chờ 2 giây)
    def trigger_death(self, reason, is_boss_win=False):
        print(f"💀 HERO BẮT ĐẦU CHẾT: {reason}")
        self.pending_reason = reason
        self.is_boss_win_pending = is_boss_win
        self.death_timer = 2.0  # Chờ 2 giây để xem animation ngã
        self.set_state("DYING")

    def update(self, time_delta, game_stats, speed_multiplier=1.0):
        # [ĐÃ SỬA]: Xử lý phân cấp phe thắng/thua khi kết thúc hiệu ứng gục ngã
        if self.state == "DYING":
            self.death_timer -= time_delta
            if self.death_timer <= 0:
                if self.is_boss_win_pending:
                    # Orc/Boss là bên giành chiến thắng trong pha va chạm này
                    if self.current_phase == "HERO":
                        self.trigger_failure(self.pending_reason)
                    elif self.current_phase == "BOSS":
                        print("💀 GHOST HERO ĐÃ BỊ TIÊU DIỆT HOÀN TOÀN! BOSS WIN.")
                        self.trigger_success()
                else:
                    self.trigger_failure(self.pending_reason)
            return False

        if self.state in ["PREPARING", "EXECUTING", "MOVING"]:
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
                    self.trigger_death("OUT OF MEMORY: TỔN THƯƠNG NHÃN LỰC (RAM MAXED OUT)", is_boss_win=(self.current_phase == "BOSS"))
                elif cpu > cfg.get("cpu_max", 9999):
                    self.trigger_death("SYSTEM OVERLOAD: TỔN THƯƠNG TRÍ LỰC (CPU MAXED OUT)", is_boss_win=(self.current_phase == "BOSS"))

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

    # [ĐÃ SỬA]: Thêm tham số sim_manager_2 để kiểm tra song song
    def check_rewind_completion(self, sim_manager, reset_cam_callback, sim_manager_2=None):
        is_done = sim_manager.is_rewind_finished()

        # Nếu ở VS Mode, phải chờ cả Hero 2 tua ngược xong mới tính là hoàn thành
        if sim_manager_2:
            is_done = is_done and sim_manager_2.is_rewind_finished()

        if is_done:
            reset_cam_callback()
            self.advance_phase_or_round()

    def advance_phase_or_round(self):
        cfg = self.level_manager.get_current_config()

        if self.current_phase == "HERO":
            # [MỚI] Điểm dừng cho VS Mode: Không nhảy thẳng sang Boss, mà hiện Bảng Overlay
            if getattr(self.dashboard, 'is_vs_mode', False):
                self.set_state("VS_SELECTION")
                return

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

    # [MỚI] Hàm chốt hạ: Được gọi khi người chơi bấm nút "CHỌN" trên Bảng Overlay So sánh
    def confirm_vs_selection(self, selected_algo):
        print(f"🎮 Đã chốt thuật toán: {selected_algo} cho Phase BOSS")
        self.hero_history_algo = selected_algo
        self.dashboard.selected_algo = selected_algo

        # Tắt VS Mode
        self.dashboard.is_vs_mode = False

        # Tiến vào Phase Boss
        self.current_phase = "BOSS"
        self.dashboard.set_phase(self.current_phase)
        self.set_state("ANNOUNCING")