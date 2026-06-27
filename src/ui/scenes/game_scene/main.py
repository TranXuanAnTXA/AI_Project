"""
📄 src/ui/scenes/game_scene/main.py
* Cập nhật: Thêm Lazy Cinematic Camera (Delay 1 giây + Hero ở nửa dưới màn hình).
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

from .input_handler import GameInputHandler
from .renderer import GameRenderer
from src.ui.overlays.victory_overlay import VictoryOverlay

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

        self.victory_overlay = VictoryOverlay(self.screen_w, self.screen_h)

        config = self.level_manager.get_current_config()
        maps_data = config.get("maps", [])
        if maps_data and len(maps_data) > 0:
            map_file = maps_data[0].get("file", "assets/maps/dungeon_map_1.tmx")
        else:
            map_file = config.get("map_file", "assets/maps/dungeon_map_1.tmx")

        self.game_map = GridMap(map_file, scale=2)
        self.map_pixel_w = self.game_map.width * self.tile_size
        self.map_pixel_h = self.game_map.height * self.tile_size

        self.start_spawn = self.game_map.start_points[0] if self.game_map.start_points else (4, 25)
        self.goal_pos = self.game_map.goal_point if self.game_map.goal_point else (1, 3)

        self.hero = Agent(self.start_spawn[0], self.start_spawn[1], self.tile_size, "assets/sprites/hero.png")
        self.hero.teleport_effect_callback = lambda gx, gy: self.renderer.spawn_particles(gx, gy, (180, 50, 255))

        self.camera = Camera(self.view_w, self.view_h, self.map_pixel_w, self.map_pixel_h)
        self._reset_camera_to_hero()

        self.dashboard = Dashboard(self.screen_w, self.screen_h, self.level_manager)
        self.phase_manager = PhaseManager(self.dashboard, self.level_manager)
        self.sim_manager = SimulationManager(self.tile_size)
        self.sim_speed_counter = 0

        # [MỚI]: Đồng hồ đếm thời gian trễ của Camera
        self.camera_timer = 1.0

        self.settings_overlay = SettingsOverlay(
            self.screen_w, self.screen_h, show_game_tab=True,
            on_restart=self._restart_game_logic, on_quit=self._quit_game_logic
        )
        self.fly_notify = FlyNotification(self.screen_w, self.screen_h)
        self.failure_overlay = FailureOverlay(self.screen_w, self.screen_h)

        self.phase_manager.reset_for_new_level()
        self.previous_phase = "HERO"

    def _reset_camera_to_hero(self):
        # [ĐÃ SỬA]: Ngay cả lúc khởi tạo đầu game, Hero cũng phải nằm ở nửa dưới
        init_x = self.hero.pixel_pos[0] + self.tile_size // 2
        init_y = self.hero.pixel_pos[1] + self.tile_size // 2
        offset_y = (self.view_h * 0.15)

        if hasattr(self.camera, 'current_center'):
            self.camera.current_center = pygame.math.Vector2(init_x, init_y - offset_y)
            self.camera.set_target(init_x, init_y - offset_y, target_zoom=1.0)
        else:
            self.camera.update(init_x, init_y - offset_y)

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
        self.hero.reset_movement()
        self.hero.path = []
        self.sim_manager.visited.clear()
        self.sim_manager.frontier.clear()
        self.sim_manager.path.clear()
        self.sim_manager.history.clear()
        self.sim_speed_counter = 0
        self.camera_timer = 1.0 # Bắt camera focus liền
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

    def process_event(self, event):
        if self.phase_manager.state == "LEVEL_COMPLETE" and self.victory_overlay.is_active:
            action = self.victory_overlay.process_event(event)
            if action == "NEXT_LEVEL":
                has_next = self.level_manager.advance_level()
                if has_next:
                    from src.ui.scenes.splash_scene import SplashScene
                    new_config = self.level_manager.get_current_config()
                    self.manager.switch_scene(SplashScene, level_info=new_config, level_to_load=self.level_manager.current_level)
                else:
                    print("🏆 PHÁ ĐẢO TOÀN BỘ GAME!")
                    self._quit_game_logic()
            elif action == "LEVEL_MENU":
                from src.ui.scenes.level_menu_scene import LevelMenuScene
                self.manager.switch_scene(LevelMenuScene)
            return

        self.input_handler.process_event(event)

    def render(self, surface):
        self.renderer.render(surface)
        if self.phase_manager.state == "LEVEL_COMPLETE":
            self.victory_overlay.draw(surface)

    def update(self, time_delta):
        if self.settings_overlay.is_open:
            self.settings_overlay.update(time_delta)
            return

        self.fly_notify.update(time_delta)
        self.failure_overlay.update(time_delta)
        self.victory_overlay.update(time_delta)

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
                task = "Tìm đường tới đích" if self.phase_manager.current_phase == "HERO" else "Thiết kế bẫy chặn Hero"
                self.fly_notify.start(self.level_manager.current_level, self.phase_manager.current_round, self.phase_manager.current_phase, task)
            elif self.fly_notify.state == "DONE":
                self.phase_manager.set_state("PREPARING")
                self.fly_notify.state = "IDLE"

        elif state == "FAIL_SCREEN":
            if not self.failure_overlay.is_active:
                self.failure_overlay.show(self.phase_manager.failure_reason)

        elif state == "LEVEL_COMPLETE":
            if not self.victory_overlay.is_active:
                self.level_manager.unlock_next_level()
                self.victory_overlay.show()
            return

        game_stats = {
            "ram": len(self.sim_manager.frontier),
            "ram_max": self.level_manager.get_current_config().get("ram_max", 200),
            "cpu": len(self.sim_manager.visited),
            "cpu_max": self.level_manager.get_current_config().get("cpu_max", 500)
        }

        current_speed = self.dashboard.current_speed
        should_auto_start = self.phase_manager.update(time_delta, game_stats, speed_multiplier=current_speed)

        if should_auto_start or self.phase_manager.sync_with_ui(self.dashboard.algo_state, self.dashboard.selected_algo):
            self._start_simulation_callback()

        state = self.phase_manager.state

        if state == "EXECUTING":
            self.sim_speed_counter += self.dashboard.current_speed
            while self.sim_speed_counter >= 1.0:
                self.sim_speed_counter -= 1.0
                path_found = self.sim_manager.step()

                local_search_algos = ["HILL_CLIMBING", "SIMULATED_ANNEALING", "LOCAL_BEAM"]

                if self.dashboard.selected_algo in local_search_algos:
                    current_node = self.sim_manager.current

                    has_valid_node = False
                    if current_node is not None:
                        if isinstance(current_node, list):
                            if len(current_node) > 0: has_valid_node = True
                        else:
                            has_valid_node = True

                    if has_valid_node:
                        target_y, target_x = current_node[0] if isinstance(current_node, list) else current_node

                        if (target_x, target_y) != tuple(self.hero.grid_pos):
                            self.hero.set_path([tuple(self.hero.grid_pos), (target_x, target_y)])
                            self.phase_manager.set_state("MOVING")
                            self.sim_speed_counter = 0
                            break

                    if not has_valid_node or not self.sim_manager.frontier:
                        if tuple(self.hero.grid_pos) == self.goal_pos:
                            self.phase_manager.trigger_success()
                        else:
                            if self.phase_manager.current_phase == "HERO":
                                self.phase_manager.trigger_failure("MẮC KẸT VÀ HẾT LƯỢT DỊCH CHUYỂN!")
                            else:
                                print("💀 BOSS CHẶN ĐƯỜNG THÀNH CÔNG!")
                                self.phase_manager.trigger_success()
                        self.sim_speed_counter = 0
                        break

                else:
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
            self.hero.update(time_delta, speed_multiplier=current_speed)
            self.phase_manager.check_goal_collision(self.hero, self.goal_pos)

            if not self.hero.is_moving and not getattr(self.hero, 'is_teleporting', False) and self.phase_manager.state == "MOVING":
                if self.dashboard.selected_algo in ["HILL_CLIMBING", "SIMULATED_ANNEALING", "LOCAL_BEAM"]:
                    self.phase_manager.set_state("EXECUTING")

        elif state == "REWINDING":
            rewind_node = self.sim_manager.rewind_step()

            if rewind_node:
                self.hero.grid_pos = list(rewind_node)
                self.hero.pixel_pos = [rewind_node[0] * self.tile_size, rewind_node[1] * self.tile_size]
            else:
                self.hero.grid_pos = list(self.start_spawn)
                self.hero.pixel_pos = [self.start_spawn[0] * self.tile_size, self.start_spawn[1] * self.tile_size]
                self.hero.reset_movement()

            self.phase_manager.check_rewind_completion(self.sim_manager, self._reset_camera_to_hero)

        # [MỚI]: LOGIC CINEMATIC CAMERA TẠI ĐÂY
        if self.dashboard.current_phase == "HERO" and state not in ["PREPARING", "ANNOUNCING", "LEVEL_COMPLETE"]:
            local_search_algos = ["HILL_CLIMBING", "SIMULATED_ANNEALING", "LOCAL_BEAM"]

            # 1. Nếu là BFS/A* đang chạy tìm đường -> Focus lấy toàn bộ Area
            if state == "EXECUTING" and self.dashboard.selected_algo not in local_search_algos and hasattr(self.camera, 'focus_on_area'):
                self.camera.focus_on_area(list(self.sim_manager.visited), self.tile_size)

            # 2. Nếu là Local Search hoặc Hero đang di chuyển -> Cinematic Camera
            else:
                # Đếm 1 giây trễ (nhân với tốc độ game để không bị lỡ nhịp khi tua nhanh x3)
                self.camera_timer += time_delta * current_speed
                if self.camera_timer >= 1.0:
                    self.camera_timer = 0.0 # Reset đồng hồ

                    hero_x = self.hero.pixel_pos[0] + self.tile_size // 2
                    hero_y = self.hero.pixel_pos[1] + self.tile_size // 2

                    # Tính toán Offset: Kéo tâm Camera lên cao hơn Hero 15% màn hình
                    # Kết quả là khi render, Hero sẽ bị xích xuống nửa dưới của màn hình.
                    offset_y = (self.view_h * 0.15) / self.camera.zoom

                    if hasattr(self.camera, 'set_target'):
                        self.camera.set_target(hero_x, hero_y - offset_y, target_zoom=1.0)

        if hasattr(self.camera, 'update'):
            try:
                self.camera.update(time_delta)
            except TypeError:
                self.camera.update()

        self.dashboard.update(time_delta, game_stats)