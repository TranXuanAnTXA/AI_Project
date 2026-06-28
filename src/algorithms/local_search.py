"""
📄 src/algorithms/local_search.py
* Chứa các thuật toán tìm kiếm cục bộ: Hill Climbing, Simulated Annealing, Local Beam Search.
* Hỗ trợ cơ chế "Quantum Leap" (Dịch chuyển tức thời) qua tường khi gặp ngõ cụt.
"""
import math
import random

def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def get_neighbors(grid, node):
    neighbors = []
    rows, cols = len(grid), len(grid[0])
    r, c = node
    # Lên, Xuống, Trái, Phải
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    for dr, dc in directions:
        nr, nc = r + dr, c + dc
        # [ĐÃ SỬA]: Chấp nhận mọi ô khác tường (Tường = 1)
        if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] != 1:
            neighbors.append((nr, nc))
    return neighbors

def get_jump_targets(grid, node):
    targets = []
    rows, cols = len(grid), len(grid[0])
    r, c = node
    # Bước nhảy chính xác 2 ô (vượt qua 1 lớp tường)
    directions = [(-2, 0), (2, 0), (0, -2), (0, 2)]
    for dr, dc in directions:
        nr, nc = r + dr, c + dc
        # [ĐÃ SỬA]: Chấp nhận mọi ô khác tường làm điểm đáp
        if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] != 1:
            targets.append((nr, nc))
    return targets

def hill_climbing(grid, start_node, goal_node):
    current = start_node
    came_from = {start_node: None}
    visited = set([start_node])
    jumps_left = 3

    while current != goal_node:
        yield current, visited, [current], []

        neighbors = get_neighbors(grid, current)
        unvisited_neighbors = [n for n in neighbors if n not in visited]
        best_neighbor = None

        # Lựa chọn B: Đi vào ô trống tốt nhất có thể, chấp nhận đi men tường vòng vèo
        # thay vì đứng im khi thấy đích bị che khuất.
        if unvisited_neighbors:
            best_neighbor = min(unvisited_neighbors, key=lambda n: manhattan(n, goal_node))

        # NẾU KẸT TẠI NGÕ CỤT VẬT LÝ (Hết đường đi) -> KÍCH HOẠT DỊCH CHUYỂN
        if best_neighbor is None:
            if jumps_left > 0:
                jump_targets = get_jump_targets(grid, current)
                valid_jumps = [jt for jt in jump_targets if jt not in visited]

                if valid_jumps:
                    best_neighbor = min(valid_jumps, key=lambda n: manhattan(n, goal_node))
                    jumps_left -= 1
                    print(f"⚡ Hill Climbing: Đã Dịch Chuyển Tức Thời! Còn lại {jumps_left} lượt.")
                else:
                    break # Hết đường nhảy -> Kẹt cứng, chịu thua
            else:
                break # Hết lượt nhảy -> Kẹt cứng, chịu thua

        visited.add(best_neighbor)
        came_from[best_neighbor] = current
        current = best_neighbor

    path = []
    frontier = []
    if current == goal_node:
        curr = goal_node
        while curr:
            path.append(curr)
            curr = came_from.get(curr)
        path.reverse()
        frontier = [goal_node]

    yield current, visited, frontier, path

def simulated_annealing(grid, start_node, goal_node):
    current = start_node
    came_from = {start_node: None}
    visited = set([start_node])
    jumps_left = 3

    # Nhiệt độ ban đầu và hệ số làm mát
    T = 100.0
    cooling_rate = 0.95

    while current != goal_node:
        yield current, visited, [current], []

        neighbors = get_neighbors(grid, current)
        unvisited_neighbors = [n for n in neighbors if n not in visited]
        next_node = None

        if unvisited_neighbors:
            # Chọn ngẫu nhiên 1 hàng xóm chưa thăm
            candidate = random.choice(unvisited_neighbors)

            current_cost = manhattan(current, goal_node)
            candidate_cost = manhattan(candidate, goal_node)

            if candidate_cost < current_cost:
                next_node = candidate
            else:
                # Kẻ say rượu: Chấp nhận bước đi tệ hơn (xa đích hơn) dựa trên xác suất nhiệt độ
                probability = math.exp((current_cost - candidate_cost) / T)
                if random.random() < probability:
                    next_node = candidate

            # Nếu xác suất từ chối nhưng chưa kẹt tường, vẫn phải ép đi tiếp ô đó để tiếp tục dò đường
            if next_node is None:
                next_node = candidate

        # NẾU KẸT TẠI NGÕ CỤT
        if next_node is None:
            if jumps_left > 0:
                jump_targets = get_jump_targets(grid, current)
                valid_jumps = [jt for jt in jump_targets if jt not in visited]

                if valid_jumps:
                    next_node = random.choice(valid_jumps) # Say rượu nên nhảy cũng ngẫu nhiên
                    jumps_left -= 1
                    print(f"⚡ Simulated Annealing: Kẻ say rượu Dịch Chuyển! Còn {jumps_left} lượt.")
                else:
                    break
            else:
                break

        visited.add(next_node)
        came_from[next_node] = current
        current = next_node
        T *= cooling_rate # Giảm nhiệt độ dần

    path = []
    frontier = []
    if current == goal_node:
        curr = goal_node
        while curr:
            path.append(curr)
            curr = came_from.get(curr)
        path.reverse()
        frontier = [goal_node]

    yield current, visited, frontier, path

def local_beam_search(grid, start_node, goal_node, k=3):
    # Beam Search duy trì k trạng thái tốt nhất cùng lúc
    current_beams = [start_node]
    came_from = {start_node: None}
    visited = set([start_node])
    jumps_left = 5 # Được cấp nhiều lượt nhảy hơn

    while True:
        # main.py sẽ lấy current_beams[0] để hiển thị Hero
        yield current_beams, visited, current_beams, []

        if goal_node in current_beams:
            break

        if not current_beams:
            break

        all_candidates = []
        for node in current_beams:
            neighbors = get_neighbors(grid, node)
            unvisited_neighbors = [n for n in neighbors if n not in visited]

            if unvisited_neighbors:
                for n in unvisited_neighbors:
                    all_candidates.append((n, node))
            else:
                # Kẹt ngõ cụt -> Tìm đường nhảy
                if jumps_left > 0:
                    jump_targets = get_jump_targets(grid, node)
                    valid_jumps = [jt for jt in jump_targets if jt not in visited]
                    for jt in valid_jumps:
                        all_candidates.append((jt, node))

        if not all_candidates:
            break

        # Chấm điểm và giữ lại đúng k tia sáng tốt nhất
        all_candidates.sort(key=lambda x: manhattan(x[0], goal_node))
        best_k_candidates = all_candidates[:k]

        next_beams = []
        for candidate, parent in best_k_candidates:
            next_beams.append(candidate)
            visited.add(candidate)
            if candidate not in came_from:
                came_from[candidate] = parent

        # Phát hiện xem trong k tia sáng được chọn có tia nào vừa dịch chuyển không
        for candidate, parent in best_k_candidates:
            if manhattan(candidate, parent) > 1:
                jumps_left -= 1
                print(f"⚡ Local Beam: Một tia sáng vừa Dịch Chuyển! Còn {jumps_left} lượt.")
                break # Trừ 1 lần cho lứa beam này để tránh trừ lố

        current_beams = next_beams

    path = []
    frontier = []
    if goal_node in current_beams:
        curr = goal_node
        while curr:
            path.append(curr)
            curr = came_from.get(curr)
        path.reverse()
        frontier = [goal_node]

    yield current_beams, visited, frontier, path