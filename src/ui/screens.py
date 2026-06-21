"""Compatibility wrapper for the legacy window-style game entrypoint.

The gameplay logic now lives in `src.ui.scenes.game_scene.GameScene`, which is
managed by `SceneManager`. This module keeps the old `GameWindow` name intact
for any code that still imports it directly.
"""

from src.ui.scene_manager import SceneManager
from src.ui.scenes.game_scene import GameScene


class GameWindow:
    def __init__(self):
        self.manager = SceneManager(1280, 720)
        self.manager.switch_scene(GameScene)

    def run(self):
        self.manager.run()
