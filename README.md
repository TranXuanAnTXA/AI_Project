# Self-Defeating Dungeon
Dự án được thực hiện bởi Nông Hoàng Anh và Trần Xuân An

# Mô tả
Nơi chạy và so sánh các thuật toán tìm kiếm

# Chủ đề
Lấy
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

## Chạy test thuật toán

Giao diện test thuật toán đã được gắn vào `main.py`. Khi chạy lệnh trên, bạn sẽ thấy một cửa sổ Pygame để chọn BFS, DFS, A* hoặc Greedy trên map cố định.

Nếu muốn chạy test tự động:

```bash
pytest tests/test_algorithms.py -q
```

## Dữ liệu test cố định

- Grid cố định: `src/core/fixed_maps.py`
- Bộ test contract: `tests/test_algorithms.py`
- Fixture của test: `tests/fixtures/fixed_map.py`
