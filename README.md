# Self-Defeating Dungeon

Dự án game Pygame với kiến trúc tách rõ giữa logic AI, core game, entity và UI.

## Cấu trúc

- `main.py`: điểm khởi động game
- `src/algorithms`: BFS, DFS, A*, Greedy, local search, adversarial search
- `src/core`: trạng thái game, bản đồ lưới, quản lý level
- `src/entities`: agent, boss, trap
- `src/ui`: dashboard, renderer, màn hình
- `src/utils`: hằng số và heuristics

## Cài đặt

```bash
pip install -r requirements.txt
```

## Chạy game

```bash
python main.py
```
