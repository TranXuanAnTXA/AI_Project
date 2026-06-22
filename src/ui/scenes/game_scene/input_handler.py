"""
📄 src/ui/scenes/game_scene/input_handler.py
* Vai trò: Tách biệt hoàn toàn logic xử lý sự kiện (Event) cho gọn gàng.
"""
import pygame

class GameInputHandler:
    def __init__(self, scene):
        self.scene = scene

    def process_event(self, event):
        scene = self.scene

        # 1. Bật/Tắt Settings bằng ESC
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

        # 2. Bấm Retry khi Thất bại
        if scene.phase_manager.state == "FAIL_SCREEN":
            action = scene.failure_overlay.process_event(event)
            if action == "RETRY_CLICKED":
                if scene.phase_manager.process_retry():
                    scene._reset_board_for_retry()
                    scene.failure_overlay.hide()
                else:
                    scene._restart_game_logic()
            return

        # 3. Chuyển Event xuống Dashboard
        if scene.phase_manager.state not in ["REWINDING", "ANNOUNCING"]:
            scene.dashboard.process_events(event)

        # 4. Điều khiển Camera tự do (Phase Boss = Bất cứ lúc nào / Phase Hero = Chỉ lúc chuẩn bị)
        if scene.dashboard.current_phase == "BOSS":
            scene.camera.handle_input(event, scene.view_x, scene.view_y)
        elif scene.phase_manager.state == "PREPARING":
            scene.camera.handle_input(event, scene.view_x, scene.view_y)