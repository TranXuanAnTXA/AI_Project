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
        if self.ui_manager.process_event(event): return
        self.input_handler.process_event(event)

    def render(self, surface):
        self.renderer.render(surface)
        if self.phase_manager.state == "LEVEL_COMPLETE": self.victory_overlay.draw(surface)
        if self.settings_overlay.is_open: self.settings_overlay.render(surface)

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

        if self.phase_manager.update(time_delta, game_stats, self.dashboard.current_speed) or \
                self.phase_manager.sync_with_ui(self.dashboard.algo_state, self.dashboard.selected_algo):
            self._start_simulation_callback()

        state = self.phase_manager.state

        if state == "EXECUTING":
            self.sim_manager.process_execution(self)

        elif state == "MOVING":
            self.hero.update(time_delta, self.dashboard.current_speed)

            # 1. Khóa HazardManager khi Hero đang trong quá trình bay về ô an toàn
            if not getattr(self.hero, 'is_resurrecting', False):
                if not self.hero.is_dead and tuple(self.hero.grid_pos) != self.hero_last_pos:
                    if HazardManager.process_hero_tile(self, self.hero.grid_pos):
                        self.hero_last_pos = tuple(self.hero.grid_pos)

            # [ĐÃ SỬA] 2. KIỂM TRA PHÂN CẤP ƯU TIÊN TRẠNG THÁI (Tránh bị đè State)
            if self.hero.is_dead:
                # Nếu Hero vừa bị Hazard phán chết (Max Cost), để yên cho game tự nhảy sang Phase DYING
                pass

            elif getattr(self.hero, 'just_finished_slip', False):
                # Ưu tiên reset thuật toán sau khi trượt băng hoặc hồi sinh xong
                if not self.hero.is_moving:
                    self.hero.just_finished_slip = False
                    self.sim_speed_counter = 0
                    self._start_simulation_callback()
                    self.phase_manager.set_state("EXECUTING")

            elif not getattr(self.hero, 'is_resurrecting', False):
                # Chỉ khi Hero hoàn toàn bình thường mới kiểm tra Goal và kích hoạt LRTA* đi tiếp
                self.phase_manager.check_goal_collision(self.hero, self.goal_pos)

                if not self.hero.is_moving and self.dashboard.selected_algo in ["HILL_CLIMBING", "SIMULATED_ANNEALING", "LOCAL_BEAM", "LRTA_STAR"]:
                    self.phase_manager.set_state("EXECUTING")

        elif state == "DYING":
            if not self.hero.is_dead: self.hero.die()
            self.hero.update(time_delta, self.dashboard.current_speed)

        elif state == "REWINDING":
            rewind_node = self.sim_manager.rewind_step()
            if rewind_node:
                self.hero.grid_pos = list(rewind_node)
                self.hero.pixel_pos = [rewind_node[0] * self.tile_size, rewind_node[1] * self.tile_size]
            else:
                self.hero.hard_reset(self.start_spawn[0], self.start_spawn[1])
                self.hero_current_cost = 0
            self.phase_manager.check_rewind_completion(self.sim_manager, self._reset_camera_to_hero)

        self.cam_controller.update_cinematic(time_delta, self.dashboard.current_speed, self.dashboard.current_phase, state, self.dashboard.selected_algo, self.sim_manager.visited, self.hero, self.view_h, self.tile_size)
        self.dashboard.update(time_delta, game_stats)