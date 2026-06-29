"""Uninformed search algorithms (Dành riêng cho nhánh hoang_anh để vẽ UI)."""

import heapq
from collections import deque
from src.algorithms.common import Grid, Coordinate, validate_grid, iter_neighbors, reconstruct_path


def ucs_generator(grid: Grid, start: Coordinate, goal: Coordinate):
    """
    Thuật toán Uniform Cost Search (UCS) dạng Generator.
    Tìm đường đi có TỔNG CHI PHÍ thấp nhất.
    Ô sương mù (4) sẽ có chi phí là 5, ô bình thường là 1.
    """
    validate_grid(grid)

    # Hàng đợi ưu tiên: (tổng_chi_phí, bộ_đếm, tọa_độ)
    counter = 0
    frontier = []
    heapq.heappush(frontier, (0, counter, start))

    came_from = {start: None}
    cost_so_far = {start: 0}

    # Dùng set để gửi dữ liệu ra UI vẽ lưới
    visited = set()
    frontier_set = {start}

    while frontier:
        current_cost, _, current = heapq.heappop(frontier)

        # Nếu UI chưa kịp cập nhật mà node này đã bị lấy ra khỏi set thì bỏ qua lỗi
        if current in frontier_set:
            frontier_set.remove(current)

        # Nếu đã duyệt qua node này trước đó (với chi phí thấp hơn) thì bỏ qua
        if current in visited:
            continue

        visited.add(current)

        # Nếu tìm thấy đích -> reconstruct path và yield lần cuối
        if current == goal:
            final_path = reconstruct_path(came_from, goal)
            yield current, visited, list(frontier_set), final_path
            break

        # Duyệt láng giềng
        for neighbor in iter_neighbors(grid, current):
            nx, ny = neighbor

            # [TÍNH CHI PHÍ]: Ô sương mù (4) tốn 5 Thể lực, ô thường tốn 1
            step_cost = 5 if grid[ny][nx] == 4 else 1
            new_cost = cost_so_far[current] + step_cost

            # Nếu chưa từng đi qua ô này, hoặc tìm được đường rẻ hơn tới ô này
            if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                cost_so_far[neighbor] = new_cost
                came_from[neighbor] = current

                counter += 1
                heapq.heappush(frontier, (new_cost, counter, neighbor))
                frontier_set.add(neighbor)

        # Trả dữ liệu ra cho SimulationManager vẽ lên màn hình (Yield Frame)
        yield current, visited, list(frontier_set), []


def ids_generator(grid, start, goal):
    """
    Thuật toán Iterative Deepening Search (IDS).
    Hệ tọa độ: start và goal nhận vào dưới dạng (row, col).
    """
    rows = len(grid)
    cols = len(grid[0])
    max_depth = rows * cols  # Giới hạn an toàn chống lặp vô hạn (vét cạn map)

    for limit in range(max_depth):
        stack = [(start, [start])]
        visited_ui = set()
        frontier_ui = [start]

        # Dictionary lưu độ sâu tối thiểu mà một node từng được truy cập.
        # Giúp tránh duyệt lại một ô nếu đã có đường đi khác ngắn hơn tới nó.
        depth_visited = {start: 0}

        found = False
        final_path = []

        while stack:
            current, path = stack.pop()
            current_depth = len(path) - 1

            visited_ui.add(current)
            if current in frontier_ui:
                frontier_ui.remove(current)

            # [TRỰC QUAN HÓA]: Nhả trạng thái hiện tại ra UI, chưa có path
            yield current, set(visited_ui), list(frontier_ui), None

            if current == goal:
                found = True
                final_path = path
                break

            # Nếu chưa chạm đáy (limit) của vòng lặp hiện tại, tiếp tục đào sâu
            if current_depth < limit:
                # Hướng di chuyển: Lên, Xuống, Trái, Phải
                moves = [(-1, 0), (1, 0), (0, -1), (0, 1)]

                # Đảo ngược mảng moves khi đưa vào stack để DFS ưu tiên quét "Lên" trước
                for dr, dc in reversed(moves):
                    nr, nc = current[0] + dr, current[1] + dc

                    # Kiểm tra ranh giới và va chạm tường (1)
                    if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] != 1:
                        neighbor = (nr, nc)
                        new_depth = current_depth + 1

                        # Điều kiện cắt tỉa: Không đi lùi lại path cũ,
                        # VÀ chỉ duyệt nếu đường này tối ưu hơn hoặc chưa từng duyệt.
                        if neighbor not in path:
                            if neighbor not in depth_visited or new_depth < depth_visited[neighbor]:
                                depth_visited[neighbor] = new_depth
                                stack.append((neighbor, path + [neighbor]))
                                if neighbor not in visited_ui:
                                    frontier_ui.append(neighbor)

        # Nếu đã tìm thấy đích trong mức limit này, nhả ra path và kết thúc
        if found:
            yield goal, set(visited_ui), list(frontier_ui), final_path
            return

        # Nếu chưa tìm thấy đích, vòng lặp for sẽ tự động tăng `limit` lên 1.
        # Vòng lặp mới bắt đầu, visited_ui bị reset, tạo ra hiệu ứng quét lại rất đẹp.

    # Quét sạch giới hạn của map mà không thấy đường -> Vét cạn
    yield start, set(), [], []


def bfs_generator(grid: Grid, start: Coordinate, goal: Coordinate):
    """
    Thuật toán Breadth-First Search dạng Generator.
    Mỗi bước duyệt sẽ yield trạng thái để UI vẽ lên màn hình.
    """
    validate_grid(grid)

    queue = deque([start])
    visited = {start}
    came_from = {start: None}

    while queue:
        current = queue.popleft()

        # Nếu tìm thấy đích, yield kết quả cuối cùng kèm đường đi
        if current == goal:
            final_path = reconstruct_path(came_from, goal)
            yield current, visited, list(queue), final_path
            break

        # Duyệt các ô láng giềng xung quanh
        for neighbor in iter_neighbors(grid, current):
            if neighbor not in visited:
                visited.add(neighbor)
                came_from[neighbor] = current
                queue.append(neighbor)

        # SỬA LỖI 1: Nhả ra mảng rỗng [] thay vì None khi chưa tìm thấy đích
        yield current, visited, list(queue), []

def dfs_generator(grid: Grid, start: Coordinate, goal: Coordinate):
    """
    Thuật toán Depth-First Search dạng Generator.
    """
    validate_grid(grid)

    stack = [start]
    visited = {start}
    came_from = {start: None}

    while stack:
        current = stack.pop()

        if current == goal:
            final_path = reconstruct_path(came_from, goal)
            yield current, visited, stack, final_path
            break

        for neighbor in iter_neighbors(grid, current):
            if neighbor not in visited:
                visited.add(neighbor)
                came_from[neighbor] = current
                stack.append(neighbor)

        # SỬA LỖI 1: Nhả ra mảng rỗng [] thay vì None khi chưa tìm thấy đích
        yield current, visited, stack, []