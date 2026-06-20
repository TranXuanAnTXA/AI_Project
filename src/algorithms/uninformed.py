"""Uninformed search algorithms."""
from collections import deque
import heapq
import sys
import os

# Robust imports to support both sys.path environments
try:
    from utils.node import Node
except ModuleNotFoundError:
    from src.utils.node import Node

try:
    from algorithms.common import PathSearchResult
except ModuleNotFoundError:
    from src.algorithms.common import PathSearchResult

# ==========================================
# ADAPTER CLASS
# ==========================================

class GridMapAdapter:
    """Adapts a grid matrix to the game_map interface required by the core algorithms."""
    def __init__(self, grid: list[list[int]], goal_coords: tuple[int, int]) -> None:
        self.grid = grid
        self.goal_coords = goal_coords

    def is_target(self, node: Node) -> bool:
        return (node.x, node.y) == self.goal_coords

    def get_neighbors(self, node: Node) -> list[Node]:
        neighbors = []
        offsets = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for dx, dy in offsets:
            nx, ny = node.x + dx, node.y + dy
            if 0 <= nx < len(self.grid) and 0 <= ny < len(self.grid[0]):
                if self.grid[nx][ny] != 1:
                    neighbors.append(Node(nx, ny))
        return neighbors

    def get_danger_level(self, node: Node) -> float:
        val = self.grid[node.x][node.y]
        return float(val) if val > 0 else 1.0

def reconstruct_path_from_node(node: Node | None) -> list[tuple[int, int]]:
    path = []
    curr = node
    while curr is not None:
        path.append((curr.x, curr.y))
        curr = curr.parent
    path.reverse()
    return path

# ==========================================
# 1. BFS
# ==========================================
class BFS:
    def __init__(self) -> None:
        self.visited_order: list[tuple[int, int]] = []
        self.expanded_nodes: int = 0
        self.frontier_max_size: int = 0

    def find_path(self, start_node: Node, game_map: GridMapAdapter) -> Node | None:
        # queue: Hàng đợi duyệt theo chiều rộng
        queue = deque([start_node])
        visited = set()
        
        visited.add((start_node.x, start_node.y))

        self.visited_order = []
        self.expanded_nodes = 0
        self.frontier_max_size = 1

        while queue:
            self.frontier_max_size = max(self.frontier_max_size, len(queue))
            current_node = queue.popleft() # Lấy node ở đầu hàng đợi
            self.expanded_nodes += 1
            self.visited_order.append((current_node.x, current_node.y))

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
    def __init__(self) -> None:
        self.visited_order: list[tuple[int, int]] = []
        self.expanded_nodes: int = 0
        self.frontier_max_size: int = 0

    def find_path(self, start_node: Node, game_map: GridMapAdapter) -> Node | None:
        # stack: Ngăn xếp duyệt theo chiều sâu
        stack = [start_node] 
        visited = set()

        self.visited_order = []
        self.expanded_nodes = 0
        self.frontier_max_size = 1

        while stack:
            self.frontier_max_size = max(self.frontier_max_size, len(stack))
            current_node = stack.pop() # Lấy node ở đỉnh ngăn xếp
            coords = (current_node.x, current_node.y)

            if coords in visited:
                continue

            visited.add(coords)
            self.expanded_nodes += 1
            self.visited_order.append(coords)

            if game_map.is_target(current_node):
                return current_node

            # Đi sâu vào nhánh vừa tìm thấy
            for neighbor in game_map.get_neighbors(current_node):
                neighbor.parent = current_node
                stack.append(neighbor)
                    
        return None

# ==========================================
# 3. UCS
# ==========================================
class UCS:
    def __init__(self) -> None:
        self.visited_order: list[tuple[int, int]] = []
        self.expanded_nodes: int = 0
        self.frontier_max_size: int = 0

    def find_path(self, start_node: Node, game_map: GridMapAdapter) -> Node | None:
        # priority_queue: Hàng đợi ưu tiên dựa trên chi phí g(n)
        priority_queue = []
        visited = set()

        start_node.f_score = 0.0 # UCS chỉ dùng g_score (gán vào f_score để dùng chung __lt__)
        heapq.heappush(priority_queue, (start_node.f_score, id(start_node), start_node))

        self.visited_order = []
        self.expanded_nodes = 0
        self.frontier_max_size = 1

        while priority_queue:
            self.frontier_max_size = max(self.frontier_max_size, len(priority_queue))
            _, _, current_node = heapq.heappop(priority_queue) 
            
            coords = (current_node.x, current_node.y)
            if coords in visited:
                continue
            visited.add(coords)
            self.expanded_nodes += 1
            self.visited_order.append(coords)

            if game_map.is_target(current_node):
                return current_node
                
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

def bfs(arg1, arg2, *args, **kwargs) -> PathSearchResult | Node | None:
    if isinstance(arg1, list) or (hasattr(arg1, '__len__') and not hasattr(arg1, 'x')):
        # Format 1: bfs(grid, start, goal)
        grid = arg1
        start_coords = arg2
        goal_coords = args[0] if args else kwargs.get("goal")
        
        start_node = Node(start_coords[0], start_coords[1])
        game_map = GridMapAdapter(grid, goal_coords)
        
        solver = BFS()
        goal_node = solver.find_path(start_node, game_map)
        found = goal_node is not None
        path = reconstruct_path_from_node(goal_node) if found else []
        
        return PathSearchResult(
            path=path,
            visited_order=solver.visited_order,
            expanded_nodes=solver.expanded_nodes,
            frontier_max_size=solver.frontier_max_size,
            found=found
        )
    else:
        # Format 2: bfs(start_node, game_map, *args, **kwargs)
        start_node = arg1
        game_map = arg2
        solver = BFS()
        return solver.find_path(start_node, game_map)


def dfs(arg1, arg2, *args, **kwargs) -> PathSearchResult | Node | None:
    if isinstance(arg1, list) or (hasattr(arg1, '__len__') and not hasattr(arg1, 'x')):
        # Format 1: dfs(grid, start, goal)
        grid = arg1
        start_coords = arg2
        goal_coords = args[0] if args else kwargs.get("goal")
        
        start_node = Node(start_coords[0], start_coords[1])
        game_map = GridMapAdapter(grid, goal_coords)
        
        solver = DFS()
        goal_node = solver.find_path(start_node, game_map)
        found = goal_node is not None
        path = reconstruct_path_from_node(goal_node) if found else []
        
        return PathSearchResult(
            path=path,
            visited_order=solver.visited_order,
            expanded_nodes=solver.expanded_nodes,
            frontier_max_size=solver.frontier_max_size,
            found=found
        )
    else:
        # Format 2: dfs(start_node, game_map, *args, **kwargs)
        start_node = arg1
        game_map = arg2
        solver = DFS()
        return solver.find_path(start_node, game_map)


def ucs(arg1, arg2, *args, **kwargs) -> PathSearchResult | Node | None:
    if isinstance(arg1, list) or (hasattr(arg1, '__len__') and not hasattr(arg1, 'x')):
        # Format 1: ucs(grid, start, goal)
        grid = arg1
        start_coords = arg2
        goal_coords = args[0] if args else kwargs.get("goal")
        
        start_node = Node(start_coords[0], start_coords[1])
        game_map = GridMapAdapter(grid, goal_coords)
        
        solver = UCS()
        goal_node = solver.find_path(start_node, game_map)
        found = goal_node is not None
        path = reconstruct_path_from_node(goal_node) if found else []
        
        return PathSearchResult(
            path=path,
            visited_order=solver.visited_order,
            expanded_nodes=solver.expanded_nodes,
            frontier_max_size=solver.frontier_max_size,
            found=found
        )
    else:
        # Format 2: ucs(start_node, game_map, *args, **kwargs)
        start_node = arg1
        game_map = arg2
        solver = UCS()
        return solver.find_path(start_node, game_map)
