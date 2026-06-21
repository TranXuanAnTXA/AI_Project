"""Entry point for Self-Defeating Dungeon."""

from src.ui.algorithm_tester import AlgorithmTesterApp


def main() -> None:
    try:
        app = AlgorithmTesterApp()
        app.run()
    except ModuleNotFoundError as error:
        print(f"Missing dependency: {error}")
        print("Install packages with: pip install -r requirements.txt")


if __name__ == "__main__":
    main()
