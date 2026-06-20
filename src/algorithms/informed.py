"""Informed search algorithms."""
import heapq
import math
from collections import deque
from utils.node import Node
from utils.heuristics import manhattan

# ==========================================
# 1. GREEDY BEST-FIRST SEARCH
# ==========================================
class GreedyBestFirst:
    def __init__(self, heuristic_fn=manhattan):
        self.heuristic_fn = heuristic_fn

    def find_path(self, start_node, target_node, game_map):
        open_set = []
        closed_set = set()

        # Greedy chỉ quan tâm đến h_score (ước lượng đến đích)
        start_node.h_score = self.calculate_heuristic(start_node, target_node)
        heapq.heappush(open_set, (start_node.h_score, id(start_node), start_node))

        while open_set:
            _, _, current_node = heapq.heappop(open_set)

            if current_node.x == target_node.x and current_node.y == target_node.y:
                return current_node

            closed_set.add((current_node.x, current_node.y))

            for neighbor in game_map.get_neighbors(current_node):
                coords = (neighbor.x, neighbor.y)
                
                if coords not in closed_set:
                    neighbor.parent = current_node
                    neighbor.h_score = self.calculate_heuristic(neighbor, target_node)
                    
                    # Đưa vào hàng đợi ưu tiên và đánh dấu đã xem xét
                    heapq.heappush(open_set, (neighbor.h_score, id(neighbor), neighbor))
                    closed_set.add(coords) 
                    
        return None

    def calculate_heuristic(self, node_a, node_b):
        return self.heuristic_fn(node_a, node_b)


# ==========================================
# 2. A* SEARCH
# ==========================================
class AStar:
    def __init__(self, heuristic_fn=manhattan):
        self.heuristic_fn = heuristic_fn

    def find_path(self, start_node, target_node, game_map):
        open_set = []
        closed_set = set()

        start_node.g_score = 0
        start_node.h_score = self.calculate_heuristic(start_node, target_node)
        start_node.f_score = start_node.g_score + start_node.h_score
        
        heapq.heappush(open_set, (start_node.f_score, id(start_node), start_node))

        while open_set:
            _, _, current_node = heapq.heappop(open_set)

            if current_node.x == target_node.x and current_node.y == target_node.y:
                return current_node

            closed_set.add((current_node.x, current_node.y))

            for neighbor in game_map.get_neighbors(current_node):
                if (neighbor.x, neighbor.y) in closed_set:
                    continue

                tentative_g_score = current_node.g_score + 1 # Chi phí đi 1 ô
                
                if tentative_g_score < neighbor.g_score or neighbor.g_score == 0:
                    neighbor.parent = current_node
                    neighbor.g_score = tentative_g_score
                    neighbor.h_score = self.calculate_heuristic(neighbor, target_node)
                    neighbor.f_score = neighbor.g_score + neighbor.h_score
                    
                    heapq.heappush(open_set, (neighbor.f_score, id(neighbor), neighbor))

        return None

    def calculate_heuristic(self, node_a, node_b):
        return self.heuristic_fn(node_a, node_b)


# ==========================================
# 3. IDA*
# ==========================================
class IDAStar:
    def __init__(self, heuristic_fn=manhattan):
        self.heuristic_fn = heuristic_fn

    def find_path(self, start_node, target_node, game_map):
        # Giới hạn ban đầu chính là khoảng cách chim bay từ Start đến Target
        threshold = self.calculate_heuristic(start_node, target_node)

        while True:
            # Gọi hàm đệ quy tìm sâu với giới hạn hiện tại
            result_node, new_threshold = self.search(start_node, 0, threshold, target_node, game_map)
            
            if result_node is not None:
                return result_node # Tìm thấy đích
                
            if new_threshold == math.inf:
                return None # Hết đường đi
                
            # Nới rộng giới hạn cho lần quét tiếp theo
            threshold = new_threshold 

    def search(self, current_node, g_score, threshold, target_node, game_map):
        f_score = g_score + self.calculate_heuristic(current_node, target_node)

        # Nếu vượt quá giới hạn RAM/Cost cho phép -> Trả về giới hạn mới
        if f_score > threshold:
            return None, f_score

        if current_node.x == target_node.x and current_node.y == target_node.y:
            return current_node, f_score

        min_exceeded_threshold = math.inf

        for neighbor in game_map.get_neighbors(current_node):
            neighbor.parent = current_node
            
            # Đệ quy đi sâu xuống
            result_node, new_threshold = self.search(neighbor, g_score + 1, threshold, target_node, game_map)

            if result_node is not None:
                return result_node, new_threshold

            if new_threshold < min_exceeded_threshold:
                min_exceeded_threshold = new_threshold

        return None, min_exceeded_threshold

    def calculate_heuristic(self, node_a, node_b):
        return self.heuristic_fn(node_a, node_b)


# ==========================================
# 4. BIDIRECTIONAL SEARCH 
# ==========================================
class BidirectionalSearch:
    def find_path(self, start_node, target_node, game_map):
        # Sử dụng 2 hàng đợi lan tỏa từ 2 đầu
        forward_queue = deque([start_node])
        backward_queue = deque([target_node])

        # Dictionary lưu tọa độ và object Node để biết đã đi qua đâu
        forward_visited = {(start_node.x, start_node.y): start_node}
        backward_visited = {(target_node.x, target_node.y): target_node}

        while forward_queue and backward_queue:
            # Lan tỏa 1 bước từ phía Agent
            intersect_node = self.expand_frontier(forward_queue, forward_visited, backward_visited, game_map, is_forward=True)
            if intersect_node:
                return self.build_path(intersect_node) # Trả về điểm chạm nhau

            # Lan tỏa 1 bước từ phía Target (Con tin/Hacker)
            intersect_node = self.expand_frontier(backward_queue, backward_visited, forward_visited, game_map, is_forward=False)
            if intersect_node:
                return self.build_path(intersect_node)

        return None

    def expand_frontier(self, queue, my_visited, opponent_visited, game_map, is_forward):
        current_node = queue.popleft()

        for neighbor in game_map.get_neighbors(current_node):
            n_coords = (neighbor.x, neighbor.y)

            # Nếu ô này đối phương đã giẫm lên -> Chạm mặt nhau!
            if n_coords in opponent_visited:
                if is_forward:
                    neighbor.parent = current_node
                else:
                    # Nếu là luồng đi ngược, phải đảo ngược parent để tạo thành một đường liền mạch từ Start -> Target
                    current_node.parent = neighbor 
                return neighbor

            # Nếu ô này trống, tiếp tục lan tỏa
            if n_coords not in my_visited:
                neighbor.parent = current_node
                my_visited[n_coords] = neighbor
                queue.append(neighbor)

        return None

    def build_path(self, intersect_node):
        return intersect_node

# ==========================================
# HÀM BỌC (WRAPPER FUNCTIONS)
# ==========================================

def a_star(start_node, target_node, game_map, *args, **kwargs):
    """
    Hàm bọc (Wrapper) gọi thuật toán A* Search.
    """
    heuristic_fn = kwargs.get("heuristic_fn", manhattan)
    solver = AStar(heuristic_fn=heuristic_fn)
    return solver.find_path(start_node, target_node, game_map)


def greedy(start_node, target_node, game_map, *args, **kwargs):
    """
    Hàm bọc (Wrapper) gọi thuật toán Greedy Best-First Search.
    """
    heuristic_fn = kwargs.get("heuristic_fn", manhattan)
    solver = GreedyBestFirst(heuristic_fn=heuristic_fn)
    return solver.find_path(start_node, target_node, game_map)


def ida_star(start_node, target_node, game_map, *args, **kwargs):
    """
    Hàm bọc (Wrapper) gọi thuật toán IDA*.
    """
    heuristic_fn = kwargs.get("heuristic_fn", manhattan)
    solver = IDAStar(heuristic_fn=heuristic_fn)
    return solver.find_path(start_node, target_node, game_map)


def bidirectional(start_node, target_node, game_map, *args, **kwargs):
    """
    Hàm bọc (Wrapper) gọi thuật toán Bidirectional Search.
    """
    solver = BidirectionalSearch()
    return solver.find_path(start_node, target_node, game_map)
