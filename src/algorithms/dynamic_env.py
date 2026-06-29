"""
📄 src/algorithms/dynamic_env.py
* Cập nhật: Fix tương thích hoàn toàn với SimulationManager.
* LRTA* trả về lộ trình tích lũy (actual_path).
* AND-OR trả về kịch bản lý tưởng (happy_path).
"""
import math
import random
from src.algorithms.common import Grid, Coordinate, validate_grid, iter_neighbors

def manhattan(a: Coordinate, b: Coordinate) -> float:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

# ==========================================
# 1. LEARNING REAL-TIME A* (LRTA*)
# ==========================================
def lrta_star_generator(grid: Grid, start: Coordinate, goal: Coordinate, heuristic_fn=manhattan):
    validate_grid(grid)
    h_table: dict[Coordinate, float] = {}
    visit_count: dict[Coordinate, int] = {} # [MỚI] Bộ đếm số lần giẫm lên 1 ô

    def get_h(node: Coordinate) -> float:
        if node not in h_table:
            h_table[node] = float(heuristic_fn(node, goal))
        return h_table[node]

    current = start
    visited = {current}
    actual_path = [current]
    metrics = {current: {'h': get_h(current)}}

    while current != goal:
        # Ghi nhận Hero vừa đứng ở ô này thêm 1 lần
        visit_count[current] = visit_count.get(current, 0) + 1

        neighbors = list(iter_neighbors(grid, current))
        if not neighbors:
            yield current, visited, [], None, metrics
            break

        best_neighbors = []
        min_f = math.inf

        for neighbor in neighbors:
            if neighbor == goal:
                cost = 1.0
            else:
                cost = float(grid[neighbor[1]][neighbor[0]]) if grid[neighbor[1]][neighbor[0]] > 0 else 1.0

            # [QUAN TRỌNG] Phạt nặng những ô đã đi qua nhiều lần (chống đi vòng tròn)
            penalty = visit_count.get(neighbor, 0) * 2.0
            f = cost + get_h(neighbor) + penalty

            # Xử lý sai số float và gom các ô có F tốt ngang nhau vào 1 mảng
            if f < min_f - 0.0001:
                min_f = f
                best_neighbors = [neighbor]
            elif abs(f - min_f) <= 0.0001:
                best_neighbors.append(neighbor)

        # [MỚI] Bốc thăm ngẫu nhiên nếu có nhiều ô điểm tốt ngang nhau
        if best_neighbors:
            best_neighbor = random.choice(best_neighbors)
        else:
            break

            # Cập nhật trí nhớ (Học)
        h_table[current] = max(get_h(current), min_f)

        current = best_neighbor
        visited.add(current)
        actual_path.append(current)

        metrics[current] = {'h': get_h(current)}

        yield current, visited, neighbors, None, metrics

    yield current, visited, [], actual_path, metrics


# ==========================================
# 2. AND-OR GRAPH SEARCH
# ==========================================
def and_or_search_generator(grid, start, goal):
    """
    Thuật toán AND-OR Search chuẩn hóa hệ tọa độ (Row, Col).
    start và goal nhận vào dưới dạng (row, col) từ SimulationManager.
    """
    visited_ui = set()
    frontier_ui = set()
    memo = {}

    ICE_ID = 3
    TRAP_ID = 99

    def get_outcomes(r, c, action):
        """Hành động của Môi trường (AND Node): Trả về các trạng thái (row, col) có thể xảy ra"""
        dr, dc = action
        nr, nc = r + dr, c + dc
        rows, cols = len(grid), len(grid[0])

        # Kiểm tra đập tường hoặc ra ngoài biên map -> Kẹt lại ô cũ (r, c)
        if not (0 <= nr < rows and 0 <= nc < cols) or grid[nr][nc] == 1:
            return [(r, c)]

        outcomes = [(nr, nc)]

        # LOGIC TRƯỢT BĂNG: Nếu bước vào ô băng, có rủi ro trượt thêm 1 ô theo hướng hành động
        if grid[nr][nc] == ICE_ID:
            sr, sc = nr + dr, nc + dc
            if 0 <= sr < rows and 0 <= sc < cols and grid[sr][sc] != 1:
                outcomes.append((sr, sc))

        return outcomes

    def or_search(state, path):
        """Hành động của AI (OR Node): Chọn nước đi tốt nhất. state là tuple (r, c)"""
        visited_ui.add(state)
        if state in frontier_ui:
            frontier_ui.remove(state)

        # CHÚ Ý: Luôn yield None cho path trong quá trình tìm kiếm offline
        yield state, set(visited_ui), list(frontier_ui), None

        if state == goal:
            return ["REACHED"]

        if state in path:
            return "FAILURE"

        if state in memo:
            return memo[state]

        best_plan = "FAILURE"

        # Thứ tự di chuyển theo dòng và cột: Lên, Xuống, Trái, Phải
        # action = (d_row, d_col)
        moves = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        for action in moves:
            dr, dc = action
            nr, nc = state[0] + dr, state[1] + dc

            # Nạp các ô hợp lệ xung quanh vào Frontier để UI vẽ màu vàng
            if 0 <= nr < len(grid) and 0 <= nc < len(grid[0]) and grid[nr][nc] != 1:
                frontier_ui.add((nr, nc))

            outcomes = get_outcomes(state[0], state[1], action)

            if outcomes == [state]:
                continue

            plan = yield from and_search(outcomes, path + [state])

            if plan != "FAILURE":
                best_plan = [action, plan]
                break

        memo[state] = best_plan
        return best_plan

    def and_search(states, path):
        """Xử lý mọi rủi ro của môi trường (Phải tìm đường sống cho cả TH trượt và không trượt)"""
        plan = {}
        for s in states:
            if grid[s[0]][s[1]] == TRAP_ID: # Truy cập mảng grid[row][col] chuẩn xác
                return "FAILURE"

            res = yield from or_search(s, path)
            if res == "FAILURE":
                return "FAILURE"
            plan[s] = res
        return plan

    # ==========================================
    # CHẠY LÕI VÀ TRÍCH XUẤT HAPPY PATH ĐỂ DI CHUYỂN
    # ==========================================
    final_plan = yield from or_search(start, [])

    if final_plan != "FAILURE":
        # Rút trích 'happy path' (Trường hợp lý tưởng không bị trượt) để Hero chạy
        happy_path = [start]
        curr = start
        curr_plan = final_plan

        while curr != goal and curr_plan and curr_plan != ["REACHED"] and curr_plan != "FAILURE":
            action = curr_plan[0]
            nr, nc = curr[0] + action[0], curr[1] + action[1]
            happy_path.append((nr, nc))
            curr = (nr, nc)

            if isinstance(curr_plan[1], dict) and curr in curr_plan[1]:
                curr_plan = curr_plan[1][curr]
            else:
                break

        # Yield kết quả cuối cùng chứa con đường hoàn chỉnh
        yield goal, set(visited_ui), list(frontier_ui), happy_path
    else:
        yield start, set(visited_ui), list(frontier_ui), []