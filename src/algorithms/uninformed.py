"""Uninformed search algorithms."""
from collections import deque
import heapq
from utils.node import Node
# ==========================================
# 1. BFS
# ==========================================
class BFS:
    def find_path(self, start_node, game_map):
        # queue: Hàng đợi duyệt theo chiều rộng
        queue = deque([start_node])
        visited = set()
        
        visited.add((start_node.x, start_node.y))

        while queue:
            current_node = queue.popleft() # Lấy node ở đầu hàng đợi

            if game_map.is_target(current_node):
                return current_node

            # Quét các node lân cận
            for neighbor in game_map.get_neighbors(current_node):
                coords = (neighbor.x, neighbor.y)
                
                if coords not in visited:
                    visited.add(coords)
                    neighbor.parent = current_node
                    queue.append(neighbor) # Đẩy vào cuối hàng đợi
                    
        return None
# ==========================================
# 2. DFS
# ==========================================
class DFS:
    def find_path(self, start_node, game_map):
        # stack: Ngăn xếp duyệt theo chiều sâu
        stack = [start_node] 
        visited = set()

        while stack:
            current_node = stack.pop() # Lấy node ở đỉnh ngăn xếp
            coords = (current_node.x, current_node.y)

            if game_map.is_target(current_node):
                return current_node

            if coords not in visited:
                visited.add(coords)
                
                # Đi sâu vào nhánh vừa tìm thấy
                for neighbor in game_map.get_neighbors(current_node):
                    neighbor.parent = current_node
                    stack.append(neighbor)
                    
        return None
# ==========================================
# 3. UCS
# ==========================================
class UCS:
    def find_path(self, start_node, game_map):
        # priority_queue: Hàng đợi ưu tiên dựa trên chi phí g(n)
        priority_queue = []
        visited = set()

        start_node.f_score = 0 # UCS chỉ dùng g_score (gán vào f_score để dùng chung __lt__)
        heapq.heappush(priority_queue, (start_node.f_score, id(start_node), start_node))

        while priority_queue:
            _, _, current_node = heapq.heappop(priority_queue) 
            
            if game_map.is_target(current_node):
                return current_node
                
            coords = (current_node.x, current_node.y)
            if coords in visited:
                continue
            visited.add(coords)

            for neighbor in game_map.get_neighbors(current_node):
                if (neighbor.x, neighbor.y) not in visited:
                    # Tính tổng độ nguy hiểm
                    danger_level = game_map.get_danger_level(neighbor)
                    neighbor.f_score = current_node.f_score + danger_level
                    neighbor.parent = current_node
                    
                    heapq.heappush(priority_queue, (neighbor.f_score, id(neighbor), neighbor))
                    
        return None

# ==========================================
# HÀM BỌC (WRAPPER FUNCTIONS)
# ==========================================

def bfs(start_node, game_map, *args, **kwargs):
    """
    Hàm bọc gọi thuật toán Breadth-First Search (BFS).
    """
    solver = BFS() # Khởi tạo cỗ máy dò đường bằng chiều rộng
    return solver.find_path(start_node, game_map) # Bấm nút chạy và trả về kết quả


def dfs(start_node, game_map, *args, **kwargs):
    """
    Hàm bọc gọi thuật toán Depth-First Search (DFS).
    """
    solver = DFS() # Khởi tạo cỗ máy dò đường bằng chiều sâu
    return solver.find_path(start_node, game_map)


def ucs(start_node, game_map, *args, **kwargs):
    """
    Hàm bọc gọi thuật toán Uniform Cost Search (UCS).
    """
    solver = UCS() # Khởi tạo cỗ máy dò đường ưu tiên chi phí sinh tồn
    return solver.find_path(start_node, game_map)
