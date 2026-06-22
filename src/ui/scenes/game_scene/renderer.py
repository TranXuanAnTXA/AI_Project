"""
📄 src/ui/scenes/game_scene/renderer.py
* Vai trò: Tách biệt engine vẽ đồ họa và tối ưu FPS (Map Caching).
"""
import pygame
from src.ui.components.vfx_manager import VFXManager
from src.ui.components.ui_theme import UITheme

class GameRenderer:
    def __init__(self, scene):
        self.scene = scene

    def render(self, surface):
        scene = self.scene
        surface.fill((15, 15, 18))

        # 1. Vẽ Bản đồ từ Cache và Simulation
        world_surface = scene.map_cache.copy()

        if scene.phase_manager.state in ["EXECUTING", "MOVING", "PAUSED", "REWINDING"]:
            scene.sim_manager.draw(world_surface)

        pygame.draw.rect(world_surface, (231, 76, 60),
                         (scene.goal_pos[0] * scene.tile_size, scene.goal_pos[1] * scene.tile_size, scene.tile_size, scene.tile_size))
        scene.hero.draw(world_surface, offset_x=0, offset_y=0)

        # 2. Xử lý Camera Zoom và Nội suy (Lerp)
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

        # 3. Cắt Viewport và dán vào Màn hình chính
        view_surface = pygame.Surface((scene.view_w, scene.view_h))
        view_surface.fill((10, 10, 10))
        view_surface.blit(scaled_world, (offset.x, offset.y))

        if scene.phase_manager.state == "REWINDING":
            VFXManager.apply_rewind_glitch(view_surface)

        border_color = (255, 50, 50) if scene.phase_manager.state == "REWINDING" or scene.dashboard.current_phase == "BOSS" else (0, 150, 255)
        pygame.draw.rect(view_surface, border_color, (0, 0, scene.view_w, scene.view_h), 2)
        surface.blit(view_surface, (scene.view_x, scene.view_y))

        # 4. Vẽ Lớp giao diện UI đè lên trên cùng
        scene.dashboard.draw(surface, current_timer_val=scene.phase_manager.timer, timer_state=scene.phase_manager.state)

        current_palette = UITheme.PALETTES.get(scene.dashboard.current_phase, UITheme.PALETTES["HERO"])
        scene.fly_notify.draw(surface, current_palette)

        if scene.phase_manager.state == "FAIL_SCREEN" or getattr(scene.failure_overlay, 'is_active', False):
            scene.failure_overlay.draw(surface)

        if scene.settings_overlay.is_open:
            scene.settings_overlay.render(surface)