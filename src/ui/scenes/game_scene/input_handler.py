"""
📄 src/ui/scenes/game_scene/input_handler.py
* Cập nhật: Bắt tín hiệu chống kẹt đường (BLOCKED) từ BFS và phát sinh hiệu ứng Khói đỏ.
"""
import pygame

class GameInputHandler:
    def __init__(self, scene):
        self.scene = scene

    def process_event(self, event):
        scene = self.scene

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if scene.settings_overlay.is_open:
                scene.settings_overlay.save_settings()
                scene.settings_overlay.is_open = False
            else:
                scene.settings_overlay.is_open = True
            return

        if scene.settings_overlay.is_open:
            scene.settings_overlay.process_event(event)
            return

        if scene.phase_manager.state == "FAIL_SCREEN":
            action = scene.failure_overlay.process_event(event)
            if action == "RETRY_CLICKED":
                if scene.phase_manager.process_retry():
                    scene._reset_board_for_retry()
                    scene.failure_overlay.hide()
                else:
                    scene._restart_game_logic()
            return

        if scene.phase_manager.state not in ["REWINDING", "ANNOUNCING"]:
            scene.dashboard.process_events(event)

        if scene.dashboard.current_phase == "BOSS":
            scene.camera.handle_input(event, scene.view_x, scene.view_y)
        elif scene.phase_manager.state == "PREPARING":
            scene.camera.handle_input(event, scene.view_x, scene.view_y)

        # XÂY VÀ PHÁ TƯỜNG (CỌ VẼ)
        if scene.dashboard.current_phase == "BOSS" and scene.phase_manager.state == "PREPARING":
            if event.type in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION]:
                buttons = pygame.mouse.get_pressed()

                if buttons[0] or buttons[2]:
                    mouse_x, mouse_y = pygame.mouse.get_pos()

                    if scene.view_x <= mouse_x <= scene.view_x + scene.view_w and scene.view_y <= mouse_y <= scene.view_y + scene.view_h:
                        offset = scene.camera.get_offset() if hasattr(scene.camera, 'get_offset') else scene.camera.offset
                        zoom = getattr(scene.camera, 'zoom', getattr(scene.camera, 'current_zoom', 1.0))

                        real_world_x = (mouse_x - scene.view_x - offset.x) / zoom
                        real_world_y = (mouse_y - scene.view_y - offset.y) / zoom

                        grid_x = int(real_world_x // scene.tile_size)
                        grid_y = int(real_world_y // scene.tile_size)

                        if (grid_x, grid_y) == (scene.start_spawn[0], scene.start_spawn[1]) or (grid_x, grid_y) == scene.goal_pos:
                            return

                        # CHUỘT TRÁI: XÂY BẪY + CHỐNG KẸT
                        if buttons[0]:
                            if scene.dashboard.walls_placed < scene.dashboard.max_walls:
                                # Lấy tọa độ lưới của Hero và Goal
                                hero_pos = tuple(scene.hero.grid_pos)
                                goal_pos = scene.goal_pos

                                # Gửi xuống Controller kiểm tra BFS
                                status = scene.game_map.place_boss_wall(grid_x, grid_y, hero_pos, goal_pos)

                                if status == "SUCCESS":
                                    scene.dashboard.walls_placed += 1
                                    scene.renderer.spawn_particles(grid_x, grid_y, (150, 150, 150)) # Khói xám
                                elif status == "BLOCKED":
                                    # CHẶN ĐƯỜNG -> Tường vỡ nát nổ khói ĐỎ
                                    scene.renderer.spawn_particles(grid_x, grid_y, (255, 50, 50))

                                    # CHUỘT PHẢI: XÓA BẪY
                        elif buttons[2]:
                            if scene.game_map.remove_boss_wall(grid_x, grid_y):
                                scene.dashboard.walls_placed -= 1
                                scene.renderer.spawn_particles(grid_x, grid_y, (200, 100, 100)) # Khói đỏ hồng