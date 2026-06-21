"""
📄 Tên File: game_scene.py
* Vai trò: Scene Controller kết nối Camera, Dashboard, Simulation, Phase, VFX và Settings Overlay.
"""
from __future__ import annotations
import random
import pygame

from src.algorithms.uninformed import bfs_generator
from src.core.grid_map import GridMap
from src.entities.agent import Agent
from src.ui.components.dashboard import Dashboard
from src.ui.scenes.base_scene import BaseScene

# Import các module hệ thống
from src.ui.components.camera import Camera
from src.core.phase_manager import PhaseManager
from src.core.simulation_manager import SimulationManager
from src.ui.components.vfx_manager import VFXManager
from src.ui.overlays.settings_overlay import SettingsOverlay

class GameScene(BaseScene):
    def __init__(self, manager):
        super().__init__(manager)
        self.screen_w = self.manager.screen_w
        self.screen_h = self.manager.screen_h
        self.fps = 60
        self.tile_size = 32

        # 1. SETUP VIEWPORT
        self.view_x, self.view_y = 25, 40
        self.view_w, self.view_h = self.screen_w - 450, self.screen_h - 220

        # 2. SETUP BẢN ĐỒ VÀ NHÂN VẬT
        self.game_map = GridMap("assets/maps/dungeon_map_1.tmx", scale=2)
        self.map_pixel_w = self.game_map.width * self.tile_size
        self.map_pixel_h = self.game_map.height * self.tile_size

        self.map_cache = pygame.Surface((self.map_pixel_w, self.map_pixel_h))
        self.map_cache.fill((40, 40, 40))
        self.game_map.render(self.map_cache, pygame.Vector2(0, 0))

        self.start_spawn = random.choice([(4, 25), (14, 25), (24, 25)])
        self.hero = Agent(self.start_spawn[0], self.start_spawn[1], self.tile_size, "assets/sprites/hero.png")
        self.goal_pos = (1, 3)

        # 3. SETUP CAMERA & UI
        self.dashboard = Dashboard(self.screen_w, self.screen_h)
        self.dashboard.set_phase("HERO")

        self.camera = Camera(self.view_w, self.view_h, self.map_pixel_w, self.map_pixel_h)
        self._reset_camera_to_hero()
        self.cam_dragging = False
        self.cam_drag_last_pos = (0, 0)

        # 4. SETUP CÁC BỘ QUẢN LÝ
        self.phase_manager = PhaseManager(self.dashboard)
        self.sim_manager = SimulationManager(self.tile_size)
        self.sim_speed_counter = 0

        # 5. KHỞI TẠO SETTINGS OVERLAY VỚI TAB GAME ĐỨNG ĐẦU VÀ GẮN CALLBACK ĐIỀU KHIỂN
        self.settings_overlay = SettingsOverlay(
            self.screen_w, self.screen_h,
            show_game_tab=True,
            on_restart=self._restart_game_logic,
            on_quit=self._quit_game_logic
        )

    def _reset_camera_to_hero(self):
        """Đưa camera về vị trí của Hero (Dùng khi Reset hoặc chuyển Phase)"""
        init_x = self.hero.pixel_pos[0] + self.tile_size // 2
        init_y = self.hero.pixel_pos[1] + self.tile_size // 2

        if hasattr(self.camera, 'current_center'):
            self.camera.current_center = pygame.math.Vector2(init_x, init_y)
            self.camera.set_target(init_x, init_y, target_zoom=1.0)
        elif hasattr(self.camera, 'update'):
            self.camera.update(init_x, init_y)

    def _start_simulation_callback(self):
        """Được gọi bởi PhaseManager khi Dashboard chuyển sang RUNNING"""
        if self.dashboard.current_phase == "BOSS":
            print("🔄 RESET VỀ PHASE 1 (HERO) ĐỂ CHẠY ALGO...")
            self.dashboard.set_phase("HERO")
            self._reset_camera_to_hero()

        start_node = (self.hero.grid_pos[1], self.hero.grid_pos[0])
        goal_node = (self.goal_pos[1], self.goal_pos[0])
        self.sim_manager.start(bfs_generator, self.game_map.grid, start_node, goal_node)

    def _restart_game_logic(self):
        """Callback xử lý reset toàn bộ trạng thái màn chơi khi bấm nút Restart trong tab Game"""
        self.start_spawn = random.choice([(4, 25), (14, 25), (24, 25)])
        self.hero = Agent(self.start_spawn[0], self.start_spawn[1], self.tile_size, "assets/sprites/hero.png")

        self.dashboard.set_phase("HERO")
        self.phase_manager.set_state("IDLE")

        self.sim_manager.visited.clear()
        self.sim_manager.frontier.clear()
        self.sim_manager.path.clear()
        self.sim_manager.history.clear()
        self.sim_speed_counter = 0

        # Gọi reset vị trí Camera về Hero
        self._reset_camera_to_hero()

        # SỬA LỖI TẠI ĐÂY: Thay vì gán trực tiếp vào thuộc tính chỉ đọc .zoom,
        # chúng ta sẽ gán an toàn vào các thuộc tính điều hướng nội bộ nếu chúng tồn tại.
        if hasattr(self.camera, 'target_zoom'):
            self.camera.target_zoom = 1.0
        if hasattr(self.camera, '_zoom'):
            try:
                self.camera._zoom = 1.0
            except AttributeError:
                pass

        self.settings_overlay.is_open = False
        print("🔄 Màn chơi đã được khởi động lại thành công!")

    def _quit_game_logic(self):
        """Callback quay trở lại Menu chính khi bấm nút Quit Game trong tab Game"""
        from src.ui.scenes.menu_scene import MenuScene
        self.settings_overlay.is_open = False
        self.manager.switch_scene(MenuScene)
        print("🚪 Đã thoát màn chơi, quay về Menu chính.")

    def process_event(self, event):
        # Kiểm tra đóng mở bảng cài đặt bằng ESC
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.settings_overlay.is_open:
                self.settings_overlay.save_settings()
                self.settings_overlay.is_open = False
            else:
                self.settings_overlay.is_open = True
            return

        # Đóng băng tương tác game nếu cài đặt đang mở
        if self.settings_overlay.is_open:
            self.settings_overlay.process_event(event)
            return

        if self.phase_manager.state != "REWINDING":
            self.dashboard.process_events(event)

        if self.dashboard.current_phase == "BOSS" and self.phase_manager.state == "IDLE":
            self.camera.handle_input(event, self.view_x, self.view_y)

    def update(self, time_delta):
        if self.settings_overlay.is_open:
            self.settings_overlay.update(time_delta)
            return

        self.phase_manager.sync_with_dashboard(self._start_simulation_callback)
        state = self.phase_manager.state

        if state == "SIMULATING":
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
                    self.phase_manager.set_state("IDLE")
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

            def on_rewind_done():
                self.dashboard.set_phase("BOSS")
                self.camera.zoom_to_fit()

            self.phase_manager.check_rewind_completion(self.sim_manager, on_rewind_done)

        # Điều khiển vị trí Focus Camera
        if self.dashboard.current_phase == "HERO":
            if state == "SIMULATING" and hasattr(self.camera, 'focus_on_area'):
                self.camera.focus_on_area(list(self.sim_manager.visited), self.tile_size)
            else:
                hero_x = self.hero.pixel_pos[0] + self.tile_size // 2
                hero_y = self.hero.pixel_pos[1] + self.tile_size // 2
                if hasattr(self.camera, 'set_target'):
                    self.camera.set_target(hero_x, hero_y, target_zoom=1.0)
                else:
                    self.camera.update(hero_x, hero_y)

        if hasattr(self.camera, 'target_center'):
            self.camera.update(time_delta)

        self.dashboard.update(time_delta, {
            "ram": len(self.sim_manager.frontier),
            "ram_max": 200,
            "cpu": len(self.sim_manager.visited),
            "cpu_max": 500
        })

    def render(self, surface):
        surface.fill((15, 15, 18))
        world_surface = self.map_cache.copy()

        if self.phase_manager.state in ["SIMULATING", "MOVING", "PAUSED", "REWINDING"]:
            self.sim_manager.draw(world_surface)

        pygame.draw.rect(world_surface, (231, 76, 60),
                         (self.goal_pos[0] * self.tile_size, self.goal_pos[1] * self.tile_size, self.tile_size, self.tile_size))
        self.hero.draw(world_surface, offset_x=0, offset_y=0)

        zoom = getattr(self.camera, 'zoom', 1.0)
        scaled_w = int(self.map_pixel_w * zoom)
        scaled_h = int(self.map_pixel_h * zoom)
        scaled_world = pygame.transform.smoothscale(world_surface, (scaled_w, scaled_h))

        offset = self.camera.offset if hasattr(self.camera, 'offset') else self.camera.get_offset()

        if self.phase_manager.state == "REWINDING":
            jx, jy = VFXManager.get_camera_jitter()
            offset.x += jx
            offset.y += jy

        view_surface = pygame.Surface((self.view_w, self.view_h))
        view_surface.fill((10, 10, 10))
        view_surface.blit(scaled_world, (offset.x, offset.y))

        if self.phase_manager.state == "REWINDING":
            VFXManager.apply_rewind_glitch(view_surface)

        border_color = (255, 50, 50) if self.phase_manager.state == "REWINDING" or self.dashboard.current_phase == "BOSS" else (0, 150, 255)
        pygame.draw.rect(view_surface, border_color, (0, 0, self.view_w, self.view_h), 2)

        surface.blit(view_surface, (self.view_x, self.view_y))
        self.dashboard.draw(surface)

        if self.settings_overlay.is_open:
            self.settings_overlay.render(surface)