"""
📄 Tên File: fixed_map.py (Nằm trong tests/fixtures/)
* Vai trò: Cung cấp một ma trận 10x10 cố định, chứa các bức tường cản đường hóc búa
  để làm bài kiểm tra (Unit Test) cho các thuật toán.
"""

# Ma trận 10x10 (0 là đất trống đi được, 1 là tường vật cản)
FIXED_GRID = [
    [0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
    [0, 1, 1, 0, 1, 0, 1, 1, 1, 0],
    [0, 1, 0, 0, 0, 0, 0, 0, 1, 0],
    [0, 1, 0, 1, 1, 1, 1, 0, 1, 0],
    [0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
    [0, 1, 1, 1, 1, 0, 1, 1, 1, 0],
    [0, 0, 0, 0, 1, 0, 0, 0, 1, 0],
    [0, 1, 1, 0, 1, 1, 1, 0, 1, 0],
    [0, 1, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 1, 1, 1, 1, 1, 1, 0],
]

START_NODE = (0, 0)   # Tọa độ xuất phát: Góc trên cùng bên trái
GOAL_NODE = (9, 9)    # Tọa độ đích: Góc dưới cùng bên phải