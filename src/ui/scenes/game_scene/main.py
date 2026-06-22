"""
📄 src/ui/scenes/game_scene/main.py
* Vai trò: Bộ điều khiển trung tâm (Controller). Đã được tối ưu dung lượng.
"""
import random
import pygame

from src.algorithms.algorithm_registry import get_algorithm
from src.core.grid_map import GridMap
from src.entities.agent import Agent
from src.ui.components.dashboard import Dashboard
from src.ui.scenes.base_scene import BaseScene

from src.ui.components.camera import Camera
from src.core.phase_manager import PhaseManager
from src.core.simulation_manager import SimulationManager
from src.ui.overlays.settings_overlay import SettingsOverlay
from src.core.level_manager import LevelManager

from src.ui.overlays.fly_notification import FlyNotification
from src.ui.overlays.failure_overlay import FailureOverlay

# Nạp 2 Component vừa tạo
from .input_handler import GameInputHandler
from .renderer import GameRenderer


class GameScene(BaseScene):
    def __init__(self, manager):
        super().__init__(manager)
        self.screen_w = self.manager.screen_w
        self.screen_h = self.manager.screen_h
        self.tile_size = 32

        # Ủy quyền cho 2 Component phụ trách Render và Input
        self.input_handler = GameInputHandler(self)
        self.renderer = GameRenderer(self)

        self.view_x, self.view_y = 25, 40
        self.view_w, self.view_h = self.screen_w - 450, self.screen_h - 220

        # Khôi phục: Bản đồ TMX và Map Caching
        self.level_manager = LevelManager()
        self.level_manager.set_level(1)
        map_file = self.level_manager.get_current_config().get("map_file", "assets/maps/dungeon_map_1.tmx")
        self.game_map = GridMap(map_file, scale=2)

        self.map_pixel_w = self.game_map.width * self.tile_size
        self.map_pixel_h = self.game_map.height * self.tile_size

        self.map_cache = pygame.Surface((self.map_pixel_w, self.map_pixel_h))
        self.map_cache.fill((40, 40, 40))
        self.game_map.render(self.map_cache, pygame.Vector2(0, 0))

        # Khôi phục: Vị trí ngẫu nhiên
        self.start_spawn = random.choice([(4, 25), (14, 25), (24, 25)])
        self.hero = Agent(self.start_spawn[0], self.start_spawn[1], self.tile_size, "assets/sprites/hero.png")
        self.goal_pos = (1, 3)

        self.camera = Camera(self.view_w, self.view_h, self.map_pixel_w, self.map_pixel_h)
        self._reset_camera_to_hero()

        self.dashboard = Dashboard(self.screen_w, self.screen_h, self.level_manager)
        self.phase_manager = PhaseManager(self.dashboard, self.level_manager)
        self.sim_manager = SimulationManager(self.tile_size)
        self.sim_speed_counter = 0

        # Khôi phục: Callbacks
        self.settings_overlay = SettingsOverlay(
            self.screen_w, self.screen_h, show_game_tab=True,
            on_restart=self._restart_game_logic, on_quit=self._quit_game_logic
        )
        self.fly_notify = FlyNotification(self.screen_w, self.screen_h)
        self.failure_overlay = FailureOverlay(self.screen_w, self.screen_h)

        self.phase_manager.reset_for_new_level()
        self.previous_phase = "HERO"

    def _reset_camera_to_hero(self):
        init_x = self.hero.pixel_pos[0] + self.tile_size // 2
        init_y = self.hero.pixel_pos[1] + self.tile_size // 2
        if hasattr(self.camera, 'current_center'):
            self.camera.current_center = pygame.math.Vector2(init_x, init_y)
            self.camera.set_target(init_x, init_y, target_zoom=1.0)
        else:
            self.camera.update(init_x, init_y)

    def _start_simulation_callback(self):
        if self.dashboard.current_phase == "BOSS":
            self.dashboard.selected_algo = self.phase_manager.hero_history_algo

        start_node = (self.hero.grid_pos[1], self.hero.grid_pos[0])
        goal_node = (self.goal_pos[1], self.goal_pos[0])
        algo_func = get_algorithm(self.dashboard.selected_algo)
        self.sim_manager.start(algo_func, self.game_map.grid, start_node, goal_node)

    def _reset_board_for_retry(self):
        self.hero.grid_pos = list(self.start_spawn)
        self.hero.pixel_pos = [self.start_spawn[0] * self.tile_size, self.start_spawn[1] * self.tile_size]
        self.hero.path = []
        self.sim_manager.visited.clear()
        self.sim_manager.frontier.clear()
        self.sim_manager.path.clear()
        self.sim_manager.history.clear()
        self.sim_speed_counter = 0
        self._reset_camera_to_hero()

    def _restart_game_logic(self):
        self.level_manager.set_level(self.level_manager.current_level)
        self._reset_board_for_retry()
        self.phase_manager.reset_for_new_level()
        self.dashboard.refresh_algorithms()
        if hasattr(self.camera, 'target_zoom'):
            self.camera.target_zoom = 1.0
        self.settings_overlay.is_open = False
        self.failure_overlay.hide()

    def _quit_game_logic(self):
        from src.ui.scenes.menu_scene import MenuScene
        self.settings_overlay.is_open = False
        self.manager.switch_scene(MenuScene)

    # Đẩy Event sang Component Input xử lý
    def process_event(self, event):
        self.input_handler.process_event(event)

    # Đẩy Graphic sang Component Renderer xử lý
    def render(self, surface):
        self.renderer.render(surface)

    def update(self, time_delta):
        if self.settings_overlay.is_open:
            self.settings_overlay.update(time_delta)
            return

        self.fly_notify.update(time_delta)
        self.failure_overlay.update(time_delta)

        # Chỉnh Viewport động cho Camera
        self.view_x, self.view_y = 25, 40
        self.view_w, self.view_h = self.screen_w - 450, self.screen_h - 220

        self.camera.viewport_width = self.view_w
        self.camera.viewport_height = self.view_h

        if self.previous_phase != self.dashboard.current_phase:
            if self.dashboard.current_phase == "BOSS" and hasattr(self.camera, 'zoom_to_fit'):
                self.camera.zoom_to_fit()
            self.previous_phase = self.dashboard.current_phase

        state = self.phase_manager.state

        if state == "ANNOUNCING":
            if self.fly_notify.state == "IDLE":
                task = "Tìm đường tới lõi năng lượng" if self.phase_manager.current_phase == "HERO" else "Thiết kế bẫy chặn Ghost Hero"
                self.fly_notify.start(self.level_manager.current_level, self.phase_manager.current_round, self.phase_manager.current_phase, task)
            elif self.fly_notify.state == "DONE":
                self.phase_manager.set_state("PREPARING")
                self.fly_notify.state = "IDLE"

        elif state == "FAIL_SCREEN":
            if not self.failure_overlay.is_active:
                self.failure_overlay.show(self.phase_manager.failure_reason)

        # Khôi phục: Logic Hệ Thống Chuyển Màn & Phá Đảo
        elif state == "LEVEL_COMPLETE":
            has_next = self.level_manager.advance_level()
            if has_next:
                from src.ui.scenes.splash_scene import SplashScene
                new_config = self.level_manager.get_current_config()
                self.manager.switch_scene(SplashScene, level_info=new_config)
            else:
                print("🏆 PHÁ ĐẢO TOÀN BỘ GAME!")
                self._quit_game_logic()
            return

        game_stats = {
            "ram": len(self.sim_manager.frontier),
            "ram_max": self.level_manager.get_current_config().get("ram_max", 200),
            "cpu": len(self.sim_manager.visited),
            "cpu_max": self.level_manager.get_current_config().get("cpu_max", 500)
        }

        should_auto_start = self.phase_manager.update(time_delta, game_stats)
        if should_auto_start or self.phase_manager.sync_with_ui(self.dashboard.algo_state, self.dashboard.selected_algo):
            self._start_simulation_callback()

        state = self.phase_manager.state

        if state == "EXECUTING":
            self.sim_speed_counter += self.dashboard.current_speed
            while self.sim_speed_counter >= 1.0:
                self.sim_speed_counter -= 1.0
                path_found = self.sim_manager.step()

                if path_found:
                    self.hero.set_path(self.sim_manager.path)
                    self.phase_manager.set_state("MOVING")
                    self.sim_speed_counter = 0
                    break
                elif not self.sim_manager.frontier:
                    if self.phase_manager.current_phase == "HERO":
                        self.phase_manager.trigger_failure("PATH NOT FOUND: VÉT CẠN BẢN ĐỒ")
                    else:
                        self.phase_manager.trigger_success()
                    self.sim_speed_counter = 0
                    break

        elif state == "MOVING":
            self.hero.update()
            self.phase_manager.check_goal_collision(self.hero, self.goal_pos)

        elif state == "REWINDING":
            rewind_node = self.sim_manager.rewind_step()
            if rewind_node:
                self.hero.grid_pos = list(rewind_node)
                self.hero.pixel_pos = [rewind_node[0] * self.tile_size, rewind_node[1] * self.tile_size]
            else:
                self.hero.grid_pos = list(self.start_spawn)
                self.hero.pixel_pos = [self.start_spawn[0] * self.tile_size, self.start_spawn[1] * self.tile_size]

            self.phase_manager.check_rewind_completion(self.sim_manager, self._reset_camera_to_hero)

        # Khôi phục: Camera bám theo Hero động
        if self.dashboard.current_phase == "HERO" and state not in ["PREPARING", "ANNOUNCING", "LEVEL_COMPLETE"]:
            if state == "EXECUTING" and hasattr(self.camera, 'focus_on_area'):
                self.camera.focus_on_area(list(self.sim_manager.visited), self.tile_size)
            else:
                hero_x = self.hero.pixel_pos[0] + self.tile_size // 2
                hero_y = self.hero.pixel_pos[1] + self.tile_size // 2
                if hasattr(self.camera, 'set_target'):
                    self.camera.set_target(hero_x, hero_y, target_zoom=1.0)

        if hasattr(self.camera, 'update'):
            try:
                self.camera.update(time_delta)
            except TypeError:
                self.camera.update()

        self.dashboard.update(time_delta, game_stats)