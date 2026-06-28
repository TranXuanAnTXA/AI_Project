"""
📄 src/ui/components/ui_manager.py
* Vai trò: Quản lý tập trung toàn bộ các lớp phủ UI (Overlays) như Settings, Victory, Failure, Notifications.
"""
from src.ui.overlays.settings_overlay import SettingsOverlay
from src.ui.overlays.fly_notification import FlyNotification
from src.ui.overlays.failure_overlay import FailureOverlay
from src.ui.overlays.victory_overlay import VictoryOverlay

class UIManager:
    def __init__(self, scene):
        self.scene = scene
        self.victory_overlay = VictoryOverlay(scene.screen_w, scene.screen_h)
        self.settings_overlay = SettingsOverlay(
            scene.screen_w, scene.screen_h, show_game_tab=True,
            on_restart=scene._restart_game_logic, on_quit=scene._quit_game_logic
        )
        self.fly_notify = FlyNotification(scene.screen_w, scene.screen_h)
        self.failure_overlay = FailureOverlay(scene.screen_w, scene.screen_h)

    def process_event(self, event):
        """Trả về True nếu UI đã tiêu thụ event và cần block các thao tác click khác của Game."""
        scene = self.scene

        # Logic nút bấm của Màn hình Chiến thắng (Level Complete)
        if scene.phase_manager.state == "LEVEL_COMPLETE" and self.victory_overlay.is_active:
            action = self.victory_overlay.process_event(event)
            if action == "NEXT_LEVEL":
                has_next = scene.level_manager.advance_level()
                if has_next:
                    from src.ui.scenes.splash_scene import SplashScene
                    new_config = scene.level_manager.get_current_config()
                    scene.manager.switch_scene(SplashScene, level_info=new_config, level_to_load=scene.level_manager.current_level)
                else:
                    print("🏆 PHÁ ĐẢO TOÀN BỘ GAME!")
                    scene._quit_game_logic()
            elif action == "LEVEL_MENU":
                from src.ui.scenes.level_menu_scene import LevelMenuScene
                scene.manager.switch_scene(LevelMenuScene)
            return True # Đã xử lý xong event

        return False

    def update(self, time_delta):
        """Trả về True nếu game cần TẠM DỪNG cập nhật vật lý/thuật toán (Ví dụ: đang mở bảng Settings)."""
        scene = self.scene

        # 1. Update Settings Overlay
        if self.settings_overlay.is_open:
            self.settings_overlay.update(time_delta)
            return True # Tạm dừng game phía sau

        # 2. Update Animations của các bảng thông báo
        self.fly_notify.update(time_delta)
        self.failure_overlay.update(time_delta)
        self.victory_overlay.update(time_delta)

        # 3. Lắng nghe State từ PhaseManager để kích hoạt/tắt UI tương ứng
        state = scene.phase_manager.state

        if state == "ANNOUNCING":
            if self.fly_notify.state == "IDLE":
                task = "Tìm đường tới đích" if scene.phase_manager.current_phase == "HERO" else "Thiết kế bẫy chặn Hero"
                self.fly_notify.start(scene.level_manager.current_level, scene.phase_manager.current_round, scene.phase_manager.current_phase, task)
            elif self.fly_notify.state == "DONE":
                scene.phase_manager.set_state("PREPARING")
                self.fly_notify.state = "IDLE"

        elif state == "FAIL_SCREEN":
            if not self.failure_overlay.is_active:
                self.failure_overlay.show(scene.phase_manager.failure_reason)

        elif state == "LEVEL_COMPLETE":
            if not self.victory_overlay.is_active:
                scene.level_manager.unlock_next_level()
                self.victory_overlay.show()
            return True # Dừng cập nhật game ngầm khi thắng

        return False