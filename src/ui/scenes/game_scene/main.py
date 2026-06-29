"""
📄 src/ui/scenes/game_scene/main.py
* BẢN FULL CHI TIẾT: Tích hợp HazardManager, Logic RAM/CPU, và đầy đủ các State (Moving, Dying, Rewinding).
* Cập nhật: Sửa triệt để lỗi Phase 2 (Auto-Reset), dùng hard_reset() thay thế reset thủ công.
* Sửa lỗi State Override: Ngăn chặn LRTA* giật ngược state khi Hero đang chết/hồi sinh.
"""
import random
import pygame

from src.algorithms.algorithm_registry import get_algorithm
from src.core.grid_map import GridMap
from src.entities.agent import Agent
from src.ui.components.dashboard import Dashboard
from src.ui.scenes.base_scene import BaseScene
from src.ui.components.camera import Camera
from src.ui.components.camera_controller import CameraController
from src.core.phase_manager import PhaseManager
from src.core.simulation_manager import SimulationManager
from src.core.level_manager import LevelManager
from src.ui.components.ui_manager import UIManager
from src.core.game_rules.hazard_manager import HazardManager
from .input_handler import GameInputHandler
from .renderer import GameRenderer

class GameScene(BaseScene):
    def __init__(self, manager, level_to_load=1):
        super().__init__(manager)
        self.screen_w = self.manager.screen_w
        self.screen_h = self.manager.screen_h
        self.tile_size = 32

        self.input_handler = GameInputHandler(self)
        self.renderer = GameRenderer(self)
        self.view_x, self.view_y = 25, 40
        self.view_w, self.view_h = self.screen_w - 450, self.screen_h - 220

        self.level_manager = LevelManager()
        self.level_manager.set_level(level_to_load)

        config = self.level_manager.get_current_config()
        maps_data = config.get("maps", [])
        map_file = maps_data[0].get("file", "assets/maps/dungeon_map_1.tmx") if maps_data else config.get("map_file", "assets/maps/dungeon_map_1.tmx")

        self.game_map = GridMap(map_file, scale=2)
        self.map_pixel_w = self.game_map.width * self.tile_size
        self.map_pixel_h = self.game_map.height * self.tile_size

        self.start_spawn = self.game_map.start_points[0] if self.game_map.start_points else (4, 25)
        self.goal_pos = self.game_map.goal_point if self.game_map.goal_point else (1, 3)

        sprite_configs = {
            "idle": {"path": "assets/sprites/Swordsman_lvl3_Idle_without_shadow.png", "cols": 10},
            "run": {"path": "assets/sprites/hero.png", "cols": 8},
            "death": {"path": "assets/sprites/Swordsman_lvl3_Death_without_shadow.png", "cols": 7},
            "hurt": {"path": "assets/sprites/Swordsman_lvl3_Hurt_without_shadow.png", "cols": 5}
        }
        self.hero = Agent(self.start_spawn[0], self.start_spawn[1], self.tile_size, sprite_configs)
        self.hero.teleport_effect_callback = lambda gx, gy: self.renderer.spawn_particles(gx, gy, (180, 50, 255))

        self.hero_current_cost = 0
        self.trap_resurrects = 3
        self.hero_last_pos = tuple(self.start_spawn)

        # ====================================================
        # [MỚI] KHỞI TẠO HERO 2 & SIMULATION 2 CHO VS MODE
        # ====================================================
        self.hero_2 = Agent(self.start_spawn[0], self.start_spawn[1], self.tile_size, sprite_configs)
        self.hero_2.is_ghost = True  # Kích hoạt hiệu ứng bóng mờ trong agent.py
        self.hero_2.teleport_effect_callback = lambda gx, gy: self.renderer.spawn_particles(gx, gy, (50, 150, 255)) # Hạt dịch chuyển màu xanh dương

        self.sim_manager_2 = SimulationManager(self.tile_size)
        self.hero_2_current_cost = 0
        self.hero_2_last_pos = tuple(self.start_spawn)

        self.sim_speed_counter_2 = 0
        self.hero1_status = "SEARCHING" # SEARCHING, MOVING, REACHED, FAILED, DEAD
        self.hero2_status = "SEARCHING"

        self.camera = Camera(self.view_w, self.view_h, self.map_pixel_w, self.map_pixel_h)
        self.cam_controller = CameraController(self.camera)
        self._reset_camera_to_hero()

        self.dashboard = Dashboard(self.screen_w, self.screen_h, self.level_manager)
        self.phase_manager = PhaseManager(self.dashboard, self.level_manager)
        self.sim_manager = SimulationManager(self.tile_size)
        self.sim_speed_counter = 0

        self.ui_manager = UIManager(self)
        self.failure_overlay = self.ui_manager.failure_overlay
        self.victory_overlay = self.ui_manager.victory_overlay
        self.settings_overlay = self.ui_manager.settings_overlay
        self.fly_notify = self.ui_manager.fly_notify

        self._board_reset_done = False
        self.phase_manager.reset_for_new_level()

    def _reset_camera_to_hero(self):
        self.cam_controller.reset_to_hero(self.hero, self.view_h, self.tile_size)

    def _start_simulation_callback(self):
        if self.dashboard.current_phase == "BOSS":
            self.dashboard.selected_algo = self.phase_manager.hero_history_algo

        self.hero.is_dead = False
        self.hero.state = "idle"
        self.hero.reset_movement()

        algo_func = get_algorithm(self.dashboard.selected_algo)
        self.sim_manager.start(algo_func, self.game_map.grid, (self.hero.grid_pos[1], self.hero.grid_pos[0]), (self.goal_pos[1], self.goal_pos[0]))

        if self.dashboard.is_vs_mode and hasattr(self, 'hero_2'):
            self.hero_2.is_dead = False
            self.hero_2.state = "idle"
            self.hero_2.reset_movement()
            algo_func_2 = get_algorithm(self.dashboard.selected_algo_2)
            self.sim_manager_2.start(algo_func_2, self.game_map.grid, (self.hero_2.grid_pos[1], self.hero_2.grid_pos[0]), (self.goal_pos[1], self.goal_pos[0]))

        if getattr(self.dashboard, 'is_vs_mode', False) and hasattr(self, 'hero_2'):
            self.hero_2.is_dead = False
            self.hero_2.state = "idle"
            self.hero_2.reset_movement()
            algo_func_2 = get_algorithm(self.dashboard.selected_algo_2)
            self.sim_manager_2.start(algo_func_2, self.game_map.grid, (self.hero_2.grid_pos[1], self.hero_2.grid_pos[0]), (self.goal_pos[1], self.goal_pos[0]))

        # [MỚI ĐƯỢC THÊM]: Reset cờ trạng thái VS Mode
        self.hero1_status = "SEARCHING"
        self.hero2_status = "SEARCHING"
        self.sim_speed_counter_2 = 0

    def _safe_process_execution(self, sim_manager, target_hero, algo_name):
        """Môi trường Sandbox ảo: Cho AI tính toán đường đi mà không làm nhiễu State chung"""
        orig_trigger_success = self.phase_manager.trigger_success
        orig_trigger_failure = self.phase_manager.trigger_failure
        orig_set_state = self.phase_manager.set_state
        orig_hero = self.hero

        # [SỬA LỖI LOCAL SEARCH]: Tạm thời đánh lừa Dashboard
        orig_algo = self.dashboard.selected_algo_1
        self.dashboard.selected_algo_1 = algo_name

        outcome = "SEARCHING"

        # Đánh lừa (Mock) các hàm thay đổi State
        def mock_success(*args, **kwargs): nonlocal outcome; outcome = "REACHED"
        def mock_failure(*args, **kwargs): nonlocal outcome; outcome = "FAILED"
        def mock_set_state(new_state):
            nonlocal outcome
            if new_state == "MOVING" and outcome == "SEARCHING":
                outcome = "MOVING"

        self.phase_manager.trigger_success = mock_success
        self.phase_manager.trigger_failure = mock_failure
        self.phase_manager.set_state = mock_set_state
        self.hero = target_hero

        # Chạy logic thuật toán lõi
        sim_manager.process_execution(self)

        # Trả mọi thứ về nguyên bản
        self.hero = orig_hero
        self.phase_manager.trigger_success = orig_trigger_success
        self.phase_manager.trigger_failure = orig_trigger_failure
        self.phase_manager.set_state = orig_set_state

        self.dashboard.selected_algo_1 = orig_algo
        return outcome

    def _update_hero_movement(self, target_hero, target_id, time_delta):
        """Xử lý vật lý và va chạm bẫy độc lập cho từng Hero"""
        target_hero.update(time_delta, self.dashboard.current_speed)

        # Lấy tên thuật toán hiện tại của Slot đang chạy
        algo = self.dashboard.selected_algo_1 if target_id == 1 else self.dashboard.selected_algo_2

        if not getattr(target_hero, 'is_resurrecting', False):
            last_pos = self.hero_last_pos if target_id == 1 else self.hero_2_last_pos
            if not target_hero.is_dead and tuple(target_hero.grid_pos) != last_pos:

                # --- THỦ THUẬT TRÁO ĐỔI (ĐÃ FIX LỖI THỂ LỰC & HỒI SINH) ---
                orig_hero = self.hero
                orig_cost_1 = self.hero_current_cost
                orig_resurrects = self.trap_resurrects

                # 1. Tước quyền hồi sinh nếu không phải thuật toán học (LRTA*)
                if algo != "LRTA_STAR":
                    self.trap_resurrects = 0

                # 2. Đổi danh tính và túi tiền
                self.hero = target_hero
                self.hero_current_cost = orig_cost_1 if target_id == 1 else self.hero_2_current_cost

                # 3. Kích hoạt Bẫy
                if HazardManager.process_hero_tile(self, target_hero.grid_pos):
                    if target_id == 1: self.hero_last_pos = tuple(target_hero.grid_pos)
                    else: self.hero_2_last_pos = tuple(target_hero.grid_pos)

                # 4. Trừ tiền đúng người
                if target_id == 1:
                    new_cost_1 = self.hero_current_cost
                else:
                    self.hero_2_current_cost = self.hero_current_cost
                    new_cost_1 = orig_cost_1 # Hero 1 không bị trừ tiền oan

                # 5. Trả lại toàn bộ trạng thái gốc
                self.trap_resurrects = orig_resurrects
                self.hero_current_cost = new_cost_1
                self.hero = orig_hero
                # ------------------------------------------------------------

        if target_hero.is_dead:
            return "DEAD"

        elif getattr(target_hero, 'just_finished_slip', False):
            if not target_hero.is_moving:
                target_hero.just_finished_slip = False

                # ========================================================
                # [ĐÃ SỬA LỖI TRƯỢT BĂNG VS MODE]: Reset lại não của AI
                # ========================================================
                algo_func = get_algorithm(algo)
                sim_mgr = self.sim_manager if target_id == 1 else self.sim_manager_2

                # Bắt AI xóa dữ liệu cũ, nạp lại lưới từ tọa độ hiện tại
                sim_mgr.start(algo_func, self.game_map.grid, (target_hero.grid_pos[1], target_hero.grid_pos[0]), (self.goal_pos[1], self.goal_pos[0]))

                # Reset bộ đếm tốc độ quét để không bị giật cục
                if target_id == 1: self.sim_speed_counter = 0
                else: self.sim_speed_counter_2 = 0

                return "SEARCHING"

        elif tuple(target_hero.grid_pos) == self.goal_pos and not target_hero.is_moving and not getattr(target_hero, 'is_resurrecting', False):
            return "REACHED"

        elif not target_hero.is_moving and not getattr(target_hero, 'is_resurrecting', False):
            if algo in ["HILL_CLIMBING", "SIMULATED_ANNEALING", "LOCAL_BEAM", "LRTA_STAR"]:
                return "SEARCHING"

        return "MOVING"

    def _reset_board_for_retry(self):
        self.hero.hard_reset(self.start_spawn[0], self.start_spawn[1])
        self.trap_resurrects = 3
        self.hero_current_cost = 0
        self.hero_last_pos = tuple(self.start_spawn)
        self.sim_manager.visited.clear()
        self.sim_manager.frontier.clear()
        self.sim_manager.path.clear()
        self.sim_manager.history.clear()
        self.sim_speed_counter = 0
        self._reset_camera_to_hero()
        if hasattr(self, 'hero_2'):
            self.hero_2.hard_reset(self.start_spawn[0], self.start_spawn[1])
            self.hero_2_current_cost = 0
            self.hero_2_last_pos = tuple(self.start_spawn)
            self.sim_manager_2.visited.clear()
            self.sim_manager_2.frontier.clear()
            self.sim_manager_2.path.clear()
            self.sim_manager_2.history.clear()
        self.sim_speed_counter = 0
        self._reset_camera_to_hero()

    def _restart_game_logic(self):
        """
        HARD RESET (Thua hoàn toàn hoặc bấm Restart từ Setting):
        Hủy hoàn toàn ván chơi hiện tại, quay về màn hình Splash để nạp lại từ đầu.
        Đảm bảo xóa sạch bộ nhớ AI, lưới tìm kiếm và các bức tường cũ.
        """
        from src.ui.scenes.splash_scene import SplashScene

        # 1. Đóng các menu/overlay hiện tại
        self.settings_overlay.is_open = False
        self.failure_overlay.hide()

        # 2. Lấy thông tin Level hiện tại để truyền cho SplashScene
        current_lvl = self.level_manager.current_level
        level_info = self.level_manager.get_current_config()

        # 3. Chuyển cảnh về màn hình Loading (SplashScene)
        # Quá trình này sẽ hủy bỏ GameScene hiện tại. Sau khi Loading xong,
        # SplashScene sẽ tạo ra một GameScene hoàn toàn mới, đọc lại map gốc.
        self.manager.switch_scene(SplashScene, level_info=level_info, level_to_load=current_lvl)

    def _quit_game_logic(self):
        """QUIT GAME: Trở về Menu chính"""
        from src.ui.scenes.menu_scene import MenuScene
        self.settings_overlay.is_open = False
        self.manager.switch_scene(MenuScene)

    def process_event(self, event):
        if self.phase_manager.state == "VS_SELECTION":
            if hasattr(self.ui_manager, 'vs_overlay') and self.ui_manager.vs_overlay.process_event(event):
                return
        if self.ui_manager.process_event(event): return
        self.input_handler.process_event(event)

    def render(self, surface):
        self.renderer.render(surface)
        if self.phase_manager.state == "LEVEL_COMPLETE": self.victory_overlay.draw(surface)
        if self.settings_overlay.is_open: self.settings_overlay.render(surface)
        if self.phase_manager.state == "VS_SELECTION":
            if hasattr(self.ui_manager, 'vs_overlay'):
                self.ui_manager.vs_overlay.show()
                self.ui_manager.vs_overlay.draw(surface)

    def update(self, time_delta):
        if self.ui_manager.update(time_delta): return

        self.view_x, self.view_y = 25, 40
        self.view_w, self.view_h = self.screen_w - 450, self.screen_h - 220
        self.camera.viewport_width = self.view_w
        self.camera.viewport_height = self.view_h

        if self.phase_manager.state == "ANNOUNCING":
            if not getattr(self, '_board_reset_done', False):
                self._reset_board_for_retry()
                self._board_reset_done = True
        else:
            self._board_reset_done = False

        ram_usage = sum(5 if self.game_map.grid[fy][fx] == 4 else 1 for fx, fy in self.sim_manager.frontier)
        game_stats = {
            "ram": ram_usage,
            "ram_max": self.level_manager.get_current_config().get("ram_max", 200),
            "cpu": self.sim_manager.cpu_usage,
            "cpu_max": self.level_manager.get_current_config().get("cpu_max", 500),
            "cost": self.hero_current_cost,
            "cost_max": self.level_manager.get_current_config().get("max_cost", 9999)
        }
        if self.dashboard.is_vs_mode:
            game_stats["hero2_ram"] = sum(5 if self.game_map.grid[fy][fx] == 4 else 1 for fx, fy in self.sim_manager_2.frontier)
            game_stats["hero2_cpu"] = self.sim_manager_2.cpu_usage
            game_stats["hero2_cost"] = self.hero_2_current_cost

        if self.phase_manager.update(time_delta, game_stats, self.dashboard.current_speed) or \
                self.phase_manager.sync_with_ui(self.dashboard.algo_state, self.dashboard.selected_algo):
            self._start_simulation_callback()

        state = self.phase_manager.state

        if state in ["EXECUTING", "MOVING"]:
            if getattr(self.dashboard, 'is_vs_mode', False):
                # ==========================================
                # LUỒNG CHẠY SONG SONG (VS MODE)
                # ==========================================
                # 1. Update Hero 1
                if self.hero1_status == "SEARCHING":
                    new_status = self._safe_process_execution(self.sim_manager, self.hero, self.dashboard.selected_algo_1)
                    if new_status != "SEARCHING": self.hero1_status = new_status
                elif self.hero1_status == "MOVING":
                    self.hero1_status = self._update_hero_movement(self.hero, 1, time_delta)

                # 2. Update Hero 2
                if self.hero2_status == "SEARCHING":
                    # Tráo đổi sim_speed_counter để Hero 2 chạy đúng tốc độ
                    temp_counter = self.sim_speed_counter
                    self.sim_speed_counter = self.sim_speed_counter_2

                    new_status = self._safe_process_execution(self.sim_manager_2, self.hero_2, self.dashboard.selected_algo_2)

                    self.sim_speed_counter_2 = self.sim_speed_counter
                    self.sim_speed_counter = temp_counter

                    if new_status != "SEARCHING": self.hero2_status = new_status
                elif self.hero2_status == "MOVING":
                    self.hero2_status = self._update_hero_movement(self.hero_2, 2, time_delta)

                # 3. Quản trị Kết quả Cuối cùng
                active_states = ["SEARCHING", "MOVING"]
                if self.hero1_status not in active_states and self.hero2_status not in active_states:
                    h1_win = (self.hero1_status == "REACHED")
                    h2_win = (self.hero2_status == "REACHED")

                    if h1_win or h2_win:
                        # [ĐÃ SỬA LỖI 0 THỐNG KÊ]: Chụp lại toàn bộ dữ liệu TRƯỚC KHI tua ngược xóa sạch
                        self.vs_stats = {
                            "hero1": {
                                "cpu": self.sim_manager.cpu_usage,
                                "ram": sum(5 if self.game_map.grid[fy][fx] == 4 else 1 for fx, fy in self.sim_manager.frontier),
                                "cost": self.hero_current_cost,
                                "status": self.hero1_status
                            },
                            "hero2": {
                                "cpu": self.sim_manager_2.cpu_usage,
                                "ram": sum(5 if self.game_map.grid[fy][fx] == 4 else 1 for fx, fy in self.sim_manager_2.frontier),
                                "cost": self.hero_2_current_cost,
                                "status": self.hero2_status
                            }
                        }
                        self.phase_manager.trigger_success()
                    else:
                        self.phase_manager.trigger_failure("CẢ 2 THUẬT TOÁN ĐỀU GỤC NGÃ!")

            else:
                # ==========================================
                # LUỒNG CHẠY ĐƠN LẺ BÌNH THƯỜNG (Giữ nguyên code cũ)
                # ==========================================
                if state == "EXECUTING":
                    self.sim_manager.process_execution(self)

                elif state == "MOVING":
                    self.hero.update(time_delta, self.dashboard.current_speed)

                    if not getattr(self.hero, 'is_resurrecting', False):
                        if not self.hero.is_dead and tuple(self.hero.grid_pos) != self.hero_last_pos:
                            if HazardManager.process_hero_tile(self, self.hero.grid_pos):
                                self.hero_last_pos = tuple(self.hero.grid_pos)

                    if self.hero.is_dead:
                        pass
                    elif getattr(self.hero, 'just_finished_slip', False):
                        if not self.hero.is_moving:
                            self.hero.just_finished_slip = False
                            self.sim_speed_counter = 0
                            self._start_simulation_callback()
                            self.phase_manager.set_state("EXECUTING")
                    elif not getattr(self.hero, 'is_resurrecting', False):
                        # [SỬA LỖI 1]: Phục hồi lại hàm kiểm tra đích cho Normal Mode
                        self.phase_manager.check_goal_collision(self.hero, self.goal_pos)

                        if not self.hero.is_moving and self.dashboard.selected_algo in ["HILL_CLIMBING", "SIMULATED_ANNEALING", "LOCAL_BEAM", "LRTA_STAR"]:
                            self.phase_manager.set_state("EXECUTING")





        elif state == "DYING":
            if not self.hero.is_dead: self.hero.die()
            self.hero.update(time_delta, self.dashboard.current_speed)
            if self.dashboard.is_vs_mode and hasattr(self, 'hero_2'):
                if not self.hero_2.is_dead: self.hero_2.die()
                self.hero_2.update(time_delta, self.dashboard.current_speed)

        elif state == "REWINDING":
            rewind_node = self.sim_manager.rewind_step()
            if rewind_node:
                self.hero.grid_pos = list(rewind_node)
                self.hero.pixel_pos = [rewind_node[0] * self.tile_size, rewind_node[1] * self.tile_size]
            else:
                self.hero.hard_reset(self.start_spawn[0], self.start_spawn[1])
                self.hero_current_cost = 0

            if self.dashboard.is_vs_mode and hasattr(self, 'hero_2'):
                rewind_node_2 = self.sim_manager_2.rewind_step()
                if rewind_node_2:
                    self.hero_2.grid_pos = list(rewind_node_2)
                    self.hero_2.pixel_pos = [rewind_node_2[0] * self.tile_size, rewind_node_2[1] * self.tile_size]
                else:
                    self.hero_2.hard_reset(self.start_spawn[0], self.start_spawn[1])
                    self.hero_2_current_cost = 0

                # [ĐÃ SỬA LỖI]: Truyền thêm self.sim_manager_2 vào cuối để ép game chờ cả 2 tua xong
                self.phase_manager.check_rewind_completion(self.sim_manager, self._reset_camera_to_hero, self.sim_manager_2)
            else:
                self.phase_manager.check_rewind_completion(self.sim_manager, self._reset_camera_to_hero)

        self.cam_controller.update_cinematic(
            time_delta,
            self.dashboard.current_speed,
            self.dashboard.current_phase,
            state,
            self.dashboard.selected_algo,
            self.sim_manager.visited,
            self.hero,
            self.view_h,
            self.tile_size,
            boss=None,
            hero_2=getattr(self, 'hero_2', None),
            is_vs_mode=getattr(self.dashboard, 'is_vs_mode', False)
        )

        self.dashboard.update(time_delta, game_stats)