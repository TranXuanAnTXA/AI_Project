"""
📄 src/ui/scenes/game_scene/adversarial_scene.py
* Cập nhật: Kiến trúc Hybrid. Hỗ trợ Real-time (Adversarial) và Vẽ Lưới (BFS, DFS...).
* Cập nhật 2: Thêm bộ nhớ (History) để chống đi vòng tròn.
* Cập nhật 3: Hệ thống Bẫy (Object Traps) độc lập cho thuật toán Đối kháng, tích hợp VFX và Debuff.
"""
import pygame
import math
import random
from collections import deque
from src.algorithms.adversarial import get_best_action_minimax, get_best_action_alphabeta, get_best_action_expectimax, get_updated_grid, compute_distance_map
from src.algorithms.algorithm_registry import get_algorithm
from src.core.grid_map import GridMap
from src.entities.agent import Agent
from src.entities.boss import Boss
from src.entities.trap import Trap
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

from src.algorithms.adversarial import get_best_action_minimax, get_best_action_alphabeta, get_best_action_expectimax

# Danh sách các thuật toán Đối kháng (Không cần vẽ lưới)
ADV_ALGOS = ["ALPHA_BETA", "MINIMAX", "EXPECTIMAX"]

class AdversarialScene(BaseScene):
    def __init__(self, manager, level_to_load=6):
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

        self.hero_start = self.game_map.start_points[0] if self.game_map.start_points else (4, 25)
        self.goal_pos = self.game_map.goal_point if self.game_map.goal_point else (1, 3)

        self.boss_start = self.game_map.boss_spawn if self.game_map.boss_spawn else (10, 10)

        hero_sprites = {
            "idle": {"path": "assets/sprites/Swordsman_lvl3_Idle_without_shadow.png", "cols": 10},
            "run": {"path": "assets/sprites/hero.png", "cols": 8},
            "death": {"path": "assets/sprites/Swordsman_lvl3_Death_without_shadow.png", "cols": 7},
            "hurt": {"path": "assets/sprites/Swordsman_lvl3_Hurt_without_shadow.png", "cols": 5}
        }
        self.hero = Agent(self.hero_start[0], self.hero_start[1], self.tile_size, hero_sprites)
        self.hero.teleport_effect_callback = lambda gx, gy: self.renderer.spawn_particles(gx, gy, (180, 50, 255))

        self.boss = Boss(self.boss_start[0], self.boss_start[1], self.tile_size, self.game_map)

        self.hero_current_cost = 0
        self.trap_resurrects = 3
        self.hero_last_pos = tuple(self.hero_start)

        self.hero_recent_history = deque(maxlen=4)

        # Khởi tạo bẫy chông (Object Traps)
        raw_traps = getattr(self.game_map, 'trap_objects', [])
        self.trap_objects = []
        for t in raw_traps:
            self.trap_objects.append(Trap(t.get("grid_x", 0), t.get("grid_y", 0), t.get("grid_width", 1), t.get("grid_height", 1), self.tile_size))
        self.known_traps = []

        self.is_desperate = False
        self.desperation_timer = 0.0
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
        self.hero.is_dead = False
        self.hero.state = "idle"
        self.hero.reset_movement()
        self.hero_recent_history.clear()

        if self.dashboard.selected_algo in ADV_ALGOS:
            self.sim_manager.path.clear()
            self.phase_manager.set_state("MOVING")
        else:
            algo_func = get_algorithm(self.dashboard.selected_algo)
            self.sim_manager.start(algo_func, self.game_map.grid, (self.hero.grid_pos[1], self.hero.grid_pos[0]), (self.goal_pos[1], self.goal_pos[0]))

    def _reset_board_for_retry(self):
        self.hero.hard_reset(self.hero_start[0], self.hero_start[1])
        self.boss.grid_pos = list(self.boss_start)
        self.boss.pixel_pos = [self.boss_start[0] * self.tile_size, self.boss_start[1] * self.tile_size]
        self.boss.state = "patrol"
        self.boss.path = []
        self.boss.target_grid_pos = None
        self.boss.last_seen_hero_pos = None

        self.trap_resurrects = 3
        self.hero_current_cost = 0
        self.hero_last_pos = tuple(self.hero_start)
        self.hero_recent_history.clear()
        self.known_traps.clear()

        # Reset toàn bộ bẫy chông về lại hình dạng ban đầu
        for t_obj in self.trap_objects:
            t_obj.state = "idle"
            t_obj.is_triggered_fully = False
            t_obj.current_frame = 0.0
            t_obj.image = t_obj.frames[0]

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
        Đảm bảo xóa sạch bộ nhớ AI, tường cũ, bẫy cũ.
        """
        # Import cục bộ để tránh lỗi vòng lặp import (circular import)
        from src.ui.scenes.splash_scene import SplashScene

        # 1. Đóng các menu hiện tại
        self.settings_overlay.is_open = False
        self.failure_overlay.hide()

        # 2. Lấy thông tin Level hiện tại để truyền cho SplashScene
        current_lvl = self.level_manager.current_level
        level_info = self.level_manager.get_current_config()

        # 3. Chuyển cảnh!
        # Cảnh AdversarialScene HIỆN TẠI sẽ bị hủy.
        # SplashScene sẽ tự động tạo ra 1 AdversarialScene MỚI TINH sau khi Loading xong.
        self.manager.switch_scene(SplashScene, level_info=level_info, level_to_load=current_lvl)

    def _quit_game_logic(self):
        """QUIT GAME: Trở về Menu chính"""
        from src.ui.scenes.menu_scene import MenuScene
        self.settings_overlay.is_open = False
        # Chuyển về Menu cũng sẽ hủy Scene hiện tại. Lần sau Play sẽ tự động qua Splash.
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
            "ram": ram_usage, "ram_max": self.level_manager.get_current_config().get("ram_max", 9999),
            "cpu": self.sim_manager.cpu_usage, "cpu_max": self.level_manager.get_current_config().get("cpu_max", 9999),
            "cost": self.hero_current_cost, "cost_max": self.level_manager.get_current_config().get("max_cost", 9999)
        }

        if self.phase_manager.update(time_delta, game_stats, self.dashboard.current_speed) or \
                self.phase_manager.sync_with_ui(self.dashboard.algo_state, self.dashboard.selected_algo):
            self._start_simulation_callback()

        state = self.phase_manager.state
        algo = self.dashboard.selected_algo

        # ========================================================
        # PHÂN LUỒNG LOGIC: THEO LƯỢT (Simulation) vs THỜI GIAN THỰC
        # ========================================================

        # TRƯỜNG HỢP 1: THUẬT TOÁN THƯỜNG (Có lưới quét)
        if algo not in ADV_ALGOS:
            if state == "EXECUTING":
                self.sim_manager.process_execution(self)
                self.boss.update(time_delta, self.hero.grid_pos, self.dashboard.current_speed)

            elif state == "MOVING":
                # 1. Cập nhật vị trí
                self.hero.update(time_delta, self.dashboard.current_speed)
                self.boss.update(time_delta, self.hero.grid_pos, self.dashboard.current_speed)

                # 2. Kiểm tra Môi trường (Hazard)
                if not getattr(self.hero, 'is_resurrecting', False):
                    if not self.hero.is_dead and tuple(self.hero.grid_pos) != self.hero_last_pos:
                        if HazardManager.process_hero_tile(self, self.hero.grid_pos):
                            self.hero_last_pos = tuple(self.hero.grid_pos)

                # 3. Kiểm tra Boss bắt Hero
                if not self.hero.is_dead and not getattr(self.hero, 'is_resurrecting', False):
                    dist = abs(self.hero.grid_pos[0] - self.boss.grid_pos[0]) + abs(self.hero.grid_pos[1] - self.boss.grid_pos[1])
                    if dist == 0:
                        self.hero.die()
                        self.phase_manager.trigger_death("BỊ ORC BẮT KỊP!", is_boss_win=True)

                # 4. CHỐT CHẶN TRẠNG THÁI (State Guard)
                if self.hero.is_dead:
                    # Nếu Hero đã chết (bởi Hazard hoặc Boss), KHÔNG LÀM GÌ THÊM.
                    # Nhường quyền cho vòng lặp update tiếp theo chuyển sang state "DYING".
                    pass

                elif not getattr(self.hero, 'is_resurrecting', False):
                    # Chỉ khi còn sống và không trong trạng thái bay hồi sinh mới kiểm tra đích
                    self.phase_manager.check_goal_collision(self.hero, self.goal_pos)

                    # Nếu đã di chuyển xong 1 bước, cho phép thuật toán tính toán bước tiếp theo
                    if not self.hero.is_moving and self.dashboard.selected_algo in ["HILL_CLIMBING", "SIMULATED_ANNEALING", "LOCAL_BEAM", "LRTA_STAR"]:
                        self.phase_manager.set_state("EXECUTING")

        # TRƯỜNG HỢP 2: THUẬT TOÁN ĐỐI KHÁNG (Không lưới quét, rượt đuổi Real-time)
        else:
            if state in ["EXECUTING", "MOVING"]:
                if not self.hero.is_dead:
                    self.boss.update(time_delta, self.hero.grid_pos, self.dashboard.current_speed)

                if not self.hero.is_dead and not getattr(self.hero, 'is_resurrecting', False):
                    dist_to_boss = abs(self.hero.grid_pos[0] - self.boss.grid_pos[0]) + abs(self.hero.grid_pos[1] - self.boss.grid_pos[1])
                    if dist_to_boss == 0:
                        self.hero.die()
                        self.phase_manager.trigger_death("BỊ ORC BẮT KỊP!", is_boss_win=True)
                        self.renderer.spawn_particles(self.hero.grid_pos[0], self.hero.grid_pos[1], (255, 0, 0))

                if not self.hero.is_moving and not self.hero.is_dead and not getattr(self.hero, 'is_resurrecting', False):
                    history_list = list(self.hero_recent_history)
                    all_traps = getattr(self.game_map, 'trap_objects', [])

                    # 1. HỆ THỐNG THỊ GIÁC: Quét xung quanh, thấy bẫy thì lưu vào não (known_traps)
                    hx, hy = self.hero.grid_pos
                    for trap in all_traps:
                        tx, ty = trap.get("grid_x", -1), trap.get("grid_y", -1)
                        if abs(hx - tx) + abs(hy - ty) <= 2:
                            if trap not in self.known_traps:
                                self.known_traps.append(trap)

                    # --- [MỚI] HỆ THỐNG TÂM LÝ TUYỆT VỌNG (DESPERATION) ---
                    # Kiểm tra xem có còn đường nào về đích mà KHÔNG đi qua bẫy không
                    safe_grid = get_updated_grid(self.game_map.grid, self.known_traps)
                    dist_map = compute_distance_map(safe_grid, self.goal_pos)

                    if dist_map[hy][hx] == math.inf:
                        # Hết đường an toàn!
                        if not self.is_desperate:
                            self.is_desperate = True
                            self.desperation_timer = 3.0 # Khựng lại 3 giây
                    else:
                        self.is_desperate = False
                        self.desperation_timer = 0.0

                    action = "STOP"

                    if self.is_desperate:
                        dist_to_boss = abs(hx - self.boss.grid_pos[0]) + abs(hy - self.boss.grid_pos[1])

                        # Đứng im chờ 3s. NHƯNG nếu Boss tới quá gần (<=2 ô) thì bỏ qua chờ đợi!
                        if self.desperation_timer > 0 and dist_to_boss > 4:
                            self.desperation_timer -= time_delta * self.dashboard.current_speed

                            # VFX: Toát mồ hôi hột (Màu vàng) vì hoảng sợ
                            if random.random() < 0.15:
                                self.renderer.spawn_particles(hx, hy, (255, 255, 50))
                        else:
                            # Hết 3 giây HOẶC Boss kề dao vào cổ -> Nhắm mắt làm liều!
                            # Bí quyết: Truyền mảng bẫy RỖNG để thuật toán tự tin đạp lên bẫy
                            if algo == "MINIMAX":
                                action = get_best_action_minimax(self.game_map.grid, tuple(self.hero.grid_pos), tuple(self.boss.grid_pos), self.goal_pos, history_list, self.known_traps)
                            elif algo == "EXPECTIMAX":
                                action = get_best_action_expectimax(self.game_map.grid, tuple(self.hero.grid_pos), tuple(self.boss.grid_pos), self.goal_pos, history_list, [])
                            else:
                                action = get_best_action_alphabeta(self.game_map.grid, tuple(self.hero.grid_pos), tuple(self.boss.grid_pos), self.goal_pos, history_list, self.known_traps)
                    else:
                        # 2. CHUYỂN BẪY TỪ BỘ NHỚ CHO AI (Hoạt động bình thường)
                        if algo == "MINIMAX":
                            action = get_best_action_minimax(self.game_map.grid, tuple(self.hero.grid_pos), tuple(self.boss.grid_pos), self.goal_pos, history_list, self.known_traps)
                        elif algo == "EXPECTIMAX":
                            action = get_best_action_expectimax(self.game_map.grid, tuple(self.hero.grid_pos), tuple(self.boss.grid_pos), self.goal_pos, history_list, self.known_traps)
                        else:
                            action = get_best_action_alphabeta(self.game_map.grid, tuple(self.hero.grid_pos), tuple(self.boss.grid_pos), self.goal_pos, history_list, self.known_traps)
                    # --------------------------------------------------------

                    hx, hy = self.hero.grid_pos
                    # ... (Giữ nguyên phần code if action == "UP"... phía dưới)
                    if action == "UP": hy -= 1
                    elif action == "DOWN": hy += 1
                    elif action == "LEFT": hx -= 1
                    elif action == "RIGHT": hx += 1

                    if (hx, hy) != tuple(self.hero.grid_pos):
                        self.hero_recent_history.append(tuple(self.hero.grid_pos))
                        self.sim_manager.path.append(tuple(self.hero.grid_pos))
                        self.hero.set_path([tuple(self.hero.grid_pos), (hx, hy)])

                self.hero.update(time_delta, self.dashboard.current_speed)

                # [ĐÃ FIX]: Cập nhật animation bẫy liên tục mỗi frame ở vòng ngoài cùng
                for t_obj in self.trap_objects:
                    t_obj.update(time_delta, self.dashboard.current_speed)

                if not getattr(self.hero, 'is_resurrecting', False):
                    if not self.hero.is_dead and tuple(self.hero.grid_pos) != self.hero_last_pos:

                        traps_list = getattr(self.game_map, 'trap_objects', [])
                        hx, hy = self.hero.grid_pos

                        for trap in traps_list:
                            tx, ty = trap.get("grid_x", -1), trap.get("grid_y", -1)
                            tw, th = trap.get("grid_width", 1), trap.get("grid_height", 1)

                            if tx <= hx < tx + tw and ty <= hy < ty + th:

                                # Kích hoạt chông đâm lên
                                for t_obj in self.trap_objects:
                                    if t_obj.grid_x == tx and t_obj.grid_y == ty:
                                        t_obj.trigger()

                                roll = random.random()

                                if roll < 0.10:
                                    self.hero.die()
                                    self.phase_manager.trigger_death("SẬP BẪY TỬ THẦN! KHÔNG THỂ HỒI SINH.", is_boss_win=True)
                                    self.renderer.spawn_particles(hx, hy, (255, 0, 0))
                                elif roll < 0.40:
                                    self.hero.debuffs.apply_root(3.0)
                                    self.renderer.spawn_particles(hx, hy, (255, 200, 50))
                                elif roll < 0.70:
                                    self.hero.debuffs.slow_factor = 0.5
                                    self.hero.debuffs.apply_slow(3.0)
                                    self.renderer.spawn_particles(hx, hy, (50, 150, 255))

                                break

                        if not self.hero.is_dead:
                            self.hero_last_pos = tuple(self.hero.grid_pos)

                self.phase_manager.check_goal_collision(self.hero, self.goal_pos)

        # ========================================================

        if state == "DYING":
            if not self.hero.is_dead: self.hero.die()
            self.hero.update(time_delta, self.dashboard.current_speed)
        elif state == "REWINDING":
            rewind_node = self.sim_manager.rewind_step()
            if rewind_node:
                self.hero.grid_pos = list(rewind_node)
                self.hero.pixel_pos = [rewind_node[0] * self.tile_size, rewind_node[1] * self.tile_size]
            else:
                self.hero.hard_reset(self.hero_start[0], self.hero_start[1])
                self.hero_current_cost = 0
            self.phase_manager.check_rewind_completion(self.sim_manager, self._reset_camera_to_hero)

        # Thêm boss=self.boss ở cuối
        self.cam_controller.update_cinematic(time_delta, self.dashboard.current_speed, self.dashboard.current_phase, state, self.dashboard.selected_algo, self.sim_manager.visited, self.hero, self.view_h, self.tile_size, boss=self.boss)
        self.dashboard.update(time_delta, game_stats)