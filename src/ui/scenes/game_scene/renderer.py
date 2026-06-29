"""
📄 src/ui/scenes/game_scene/renderer.py
* Cập nhật: Khắc phục lỗi bóng mờ bằng cách clear màn hình trước khi vẽ Global Background.
"""
import pygame
import random
from src.ui.components.vfx_manager import VFXManager
from src.ui.components.ui_theme import UITheme

class GameRenderer:
    def __init__(self, scene):
        self.scene = scene
        self.particles = []

    def spawn_particles(self, grid_x, grid_y, color):
        cx = grid_x * self.scene.tile_size + self.scene.tile_size // 2
        cy = grid_y * self.scene.tile_size + self.scene.tile_size // 2
        for _ in range(10):
            self.particles.append({
                "x": cx, "y": cy,
                "vx": random.uniform(-2, 2), "vy": random.uniform(-3, 1),
                "radius": random.uniform(2, 6),
                "life": 255,
                "color": color
            })

    def update_particles(self):
        for p in self.particles[:]:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['radius'] -= 0.1
            p['life'] -= 10
            if p['life'] <= 0 or p['radius'] <= 0:
                self.particles.remove(p)

    def draw_hover_preview(self, surface):
        scene = self.scene
        if scene.dashboard.current_phase != "BOSS" or scene.phase_manager.state != "PREPARING":
            return

        mouse_x, mouse_y = pygame.mouse.get_pos()
        if not (scene.view_x <= mouse_x <= scene.view_x + scene.view_w and scene.view_y <= mouse_y <= scene.view_y + scene.view_h):
            return

        offset = scene.camera.get_offset() if hasattr(scene.camera, 'get_offset') else scene.camera.offset
        zoom = getattr(scene.camera, 'zoom', getattr(scene.camera, 'current_zoom', 1.0))

        real_x = (mouse_x - scene.view_x - offset.x) / zoom
        real_y = (mouse_y - scene.view_y - offset.y) / zoom
        grid_x, grid_y = int(real_x // scene.tile_size), int(real_y // scene.tile_size)

        start_pos = getattr(scene, 'start_spawn', getattr(scene, 'hero_start', (0,0)))

        if (grid_x, grid_y) == (start_pos[0], start_pos[1]) or (grid_x, grid_y) == scene.goal_pos:
            return

        hover_surf = pygame.Surface((scene.tile_size, scene.tile_size), pygame.SRCALPHA)
        if scene.game_map.is_walkable(grid_x, grid_y) and scene.dashboard.walls_placed < scene.dashboard.max_walls:
            hover_surf.fill((46, 204, 113, 100))
        else:
            hover_surf.fill((231, 76, 60, 100))

        surface.blit(hover_surf, (grid_x * scene.tile_size, grid_y * scene.tile_size))

    def render(self, surface):
        scene = self.scene

        # [QUAN TRỌNG NHẤT]: Xóa sạch màn hình bằng màu đen nhạt trước khi vẽ nền 50% opacity
        surface.fill((10, 10, 12))

        # 1. VẼ NỀN TỔNG (GLOBAL BACKGROUND)
        bg_img = getattr(UITheme, 'bg_boss' if scene.dashboard.current_phase == "BOSS" else 'bg_hero', None)
        if bg_img:
            scaled_bg = pygame.transform.smoothscale(bg_img, (scene.manager.screen_w, scene.manager.screen_h))
            surface.blit(scaled_bg, (0, 0))

        # --- Vẽ nội dung thế giới game (World Surface) ---
        world_surface = pygame.Surface((scene.map_pixel_w, scene.map_pixel_h))
        world_surface.fill((30, 30, 35))

        scene.game_map.render_bottom(world_surface)

        if scene.dashboard.current_phase == "BOSS":
            grid_surf = pygame.Surface((scene.map_pixel_w, scene.map_pixel_h), pygame.SRCALPHA)
            grid_color = (0, 180, 255, 120)
            line_thickness = 2
            for x in range(0, scene.map_pixel_w, scene.tile_size):
                pygame.draw.line(grid_surf, grid_color, (x, 0), (x, scene.map_pixel_h), line_thickness)
            for y in range(0, scene.map_pixel_h, scene.tile_size):
                pygame.draw.line(grid_surf, grid_color, (0, y), (scene.map_pixel_w, y), line_thickness)
            world_surface.blit(grid_surf, (0, 0))

        grid = scene.game_map.grid
        for r in range(len(grid)):
            for c in range(len(grid[0])):
                if grid[r][c] == 4:
                    fog_surf = pygame.Surface((scene.tile_size, scene.tile_size), pygame.SRCALPHA)
                    fog_surf.fill((60, 65, 75, 220))
                    pygame.draw.line(fog_surf, (100, 105, 115, 100), (0, 10), (scene.tile_size, 15), 2)
                    pygame.draw.line(fog_surf, (100, 105, 115, 100), (0, 25), (scene.tile_size, 20), 2)
                    world_surface.blit(fog_surf, (c * scene.tile_size, r * scene.tile_size))

        if scene.phase_manager.state in ["EXECUTING", "MOVING", "PAUSED", "REWINDING"]:
            if hasattr(scene, 'sim_manager'):
                scene.sim_manager.draw(world_surface)
            # [MỚI] Vẽ lưới quét của thuật toán 2
            if getattr(scene.dashboard, 'is_vs_mode', False) and hasattr(scene, 'sim_manager_2'):
                scene.sim_manager_2.draw(world_surface)

        pygame.draw.rect(world_surface, (231, 76, 60),
                         (scene.goal_pos[0] * scene.tile_size, scene.goal_pos[1] * scene.tile_size, scene.tile_size, scene.tile_size))

        if hasattr(scene, 'trap_objects'):
            for trap in scene.trap_objects:
                trap.draw(world_surface, offset_x=0, offset_y=0)

        # Vẽ Hero 1
        scene.hero.draw(world_surface, offset_x=0, offset_y=0)

        # [MỚI] Vẽ Hero 2 dưới dạng Bóng Ma
        if getattr(scene.dashboard, 'is_vs_mode', False) and hasattr(scene, 'hero_2'):
            scene.hero_2.draw(world_surface, offset_x=0, offset_y=0)

        self.draw_hover_preview(world_surface)

        if hasattr(scene, 'boss'):
            scene.boss.draw(world_surface, offset_x=0, offset_y=0)

        scene.game_map.render_top(world_surface)

        self.update_particles()
        for p in self.particles:
            temp_surf = pygame.Surface((int(p['radius']*2), int(p['radius']*2)), pygame.SRCALPHA)
            pygame.draw.circle(temp_surf, (*p['color'], max(0, p['life'])), (int(p['radius']), int(p['radius'])), int(p['radius']))
            world_surface.blit(temp_surf, (p['x'] - p['radius'], p['y'] - p['radius']))

        zoom = getattr(scene.camera, 'zoom', getattr(scene.camera, 'current_zoom', 1.0))
        scaled_w = int(scene.map_pixel_w * zoom)
        scaled_h = int(scene.map_pixel_h * zoom)
        scaled_world = pygame.transform.smoothscale(world_surface, (scaled_w, scaled_h))

        offset = scene.camera.get_offset() if hasattr(scene.camera, 'get_offset') else scene.camera.offset
        offset = pygame.math.Vector2(offset.x, offset.y)
        if scene.phase_manager.state == "REWINDING":
            jx, jy = VFXManager.get_camera_jitter()
            offset.x += jx
            offset.y += jy

        view_surface = pygame.Surface((scene.view_w, scene.view_h))
        view_surface.fill((10, 10, 10))
        view_surface.blit(scaled_world, (offset.x, offset.y))

        if scene.phase_manager.state == "REWINDING":
            VFXManager.apply_rewind_glitch(view_surface)

        # 2. VẼ BẢN ĐỒ VÀ BỌC KHUNG
        surface.blit(view_surface, (scene.view_x, scene.view_y))

        frame_img = getattr(UITheme, 'frame_boss' if scene.dashboard.current_phase == "BOSS" else 'frame_hero', None)
        if frame_img:
            pad_x, pad_y = 1, 1
            scaled_main_frame = pygame.transform.smoothscale(frame_img, (scene.view_w + pad_x*2, scene.view_h + pad_y*2))
            surface.blit(scaled_main_frame, (scene.view_x - pad_x, scene.view_y - pad_y))
        else:
            border_color = (255, 50, 50) if scene.dashboard.current_phase == "BOSS" else (0, 150, 255)
            pygame.draw.rect(surface, border_color, (scene.view_x, scene.view_y, scene.view_w, scene.view_h), 2)

        # 3. VẼ GIAO DIỆN
        scene.dashboard.draw(surface, current_timer_val=scene.phase_manager.timer, timer_state=scene.phase_manager.state)
        current_palette = UITheme.PALETTES.get(scene.dashboard.current_phase, UITheme.PALETTES["HERO"])
        scene.fly_notify.draw(surface, current_palette)

        if scene.phase_manager.state == "FAIL_SCREEN" or getattr(scene.failure_overlay, 'is_active', False):
            scene.failure_overlay.draw(surface)
        if scene.settings_overlay.is_open:
            scene.settings_overlay.render(surface)