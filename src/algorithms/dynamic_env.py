"""Advanced algorithms (Dành riêng cho nhánh hoang_anh để vẽ UI)."""

import math
from src.algorithms.common import Grid, Coordinate, validate_grid, iter_neighbors, reconstruct_path

def manhattan(a: Coordinate, b: Coordinate) -> float:
    """Hàm tính khoảng cách heuristic (Manhattan)."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

# ==========================================
# 1. LEARNING REAL-TIME A* (LRTA*)
# ==========================================
def lrta_star_generator(grid: Grid, start: Coordinate, goal: Coordinate, heuristic_fn=manhattan):
    """
    Thuật toán LRTA* dạng Generator.
    Mỗi lần yield, thuật toán sẽ nhả ra vị trí hiện tại của Agent sau khi nó 'bước' 1 bước.
    """
    validate_grid(grid)

    # Bảng trí nhớ (Memory Table) lưu trữ kinh nghiệm của AI
    h_table: dict[Coordinate, float] = {}

    def get_h(node: Coordinate) -> float:
        """Lấy Heuristic từ bộ nhớ, nếu chưa có thì tính mới."""
        if node not in h_table:
            h_table[node] = float(heuristic_fn(node, goal))
        return h_table[node]

    current = start
    visited = {current}

    # Ở LRTA*, đường đi là toàn bộ dấu chân đã bước (có thể ngoằn ngoèo, lặp lại)
    actual_path = [current]

    max_steps = 2000 # Cầu chì an toàn chống lặp vô tận nếu bị nhốt
    step = 0

    while current != goal and step < max_steps:
        step += 1

        # Nhìn ra xung quanh
        neighbors = list(iter_neighbors(grid, current))

        if not neighbors:
            break  # Kẹt cứng hoàn toàn

        # Tìm ô láng giềng tốt nhất
        min_f = math.inf
        best_neighbor = None

        for neighbor in neighbors:
            # f(n) = cost + h(n). Giả sử chi phí di chuyển là 1.0
            f_value = 1.0 + get_h(neighbor)
            if f_value < min_f:
                min_f = f_value
                best_neighbor = neighbor

        # BƯỚC HỌC TẬP (Cập nhật trí nhớ): Cập nhật lại độ khó của ô đang đứng
        h_table[current] = max(get_h(current), min_f)

        # BƯỚC DI CHUYỂN
        current = best_neighbor
        visited.add(current)
        actual_path.append(current)

        # Trả về UI trạng thái hiện tại để vẽ
        yield current, visited, neighbors, None

    # Kết thúc vòng lặp
    if current == goal:
        yield current, visited, [], actual_path
    else:
        yield current, visited, [], []  # Thất bại (hết số bước hoặc kẹt)


# ==========================================
# 2. AND-OR SEARCH (Placeholder Generator)
# ==========================================
def and_or_generator(grid: Grid, start: Coordinate, goal: Coordinate):
    """
    AND-OR Search trả về Policy thay vì Path, rất khó để visualize từng bước.
    Đây là hàm giữ chỗ (stub) để không bị lỗi UI.
    """
    validate_grid(grid)
    visited = {start}

    # Chỉ nhả ra 1 frame duy nhất báo lỗi hoặc chưa hỗ trợ vẽ
    yield start, visited, [], None