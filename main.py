from src.ui.scene_manager import SceneManager
from src.ui.scenes.splash_scene import SplashScene

if __name__ == "__main__":
    app = SceneManager(1280, 720)
    # Nạp tiền sảnh Splash trước
    app.switch_scene(SplashScene)
    app.run()