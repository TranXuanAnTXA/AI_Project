"""Informed search algorithms."""
import heapq
import math
import sys
import os
from collections import deque

# Robust imports to support both sys.path environments
try:
    from utils.node import Node
except ModuleNotFoundError:
    from src.utils.node import Node

try:
    from utils.heuristics import manhattan
except ModuleNotFoundError:
    from src.utils.heuristics import manhattan

try:
    from algorithms.common import PathSearchResult
except ModuleNotFoundError:
    from src.algorithms.common import PathSearchResult

try:
    from algorithms.uninformed import GridMapAdapter, reconstruct_path_from_node
except ModuleNotFoundError:
    from src.algorithms.uninformed import GridMapAdapter, reconstruct_path_from_node

# ==========================================
# 1. GREEDY BEST-FIRST SEARCH
# ==========================================
class GreedyBestFirst:
    def __init__(self, heuristic_fn=manhattan) -> None:
        self.heuristic_fn = heuristic_fn
        self.visited_order: list[tuple[int, int]] = []
        self.expanded_nodes: int = 0
        self.frontier_max_size: int = 0

    def find_path(self, start_node: Node, target_node: Node, game_map: GridMapAdapter) -> Node | None:
        open_set = []
        closed_set = set()

        # Greedy chỉ quan tâm đến h_score (ước lượng đến đích)
        start_node.h_score = self.calculate_heuristic(start_node, target_node)
        heapq.heappush(open_set, (start_node.h_score, id(start_node), start_node))

        self.visited_order = []
        self.expanded_nodes = 0
        self.frontier_max_size = 1

        while open_set:
            self.frontier_max_size = max(self.frontier_max_size, len(open_set))
            _, _, current_node = heapq.heappop(open_set)
            coords = (current_node.x, current_node.y)

            if coords in closed_set:
                continue

            closed_set.add(coords)
            self.expanded_nodes += 1
            self.visited_order.append(coords)

            if current_node.x == target_node.x and current_node.y == target_node.y:
                return current_node

            for neighbor in game_map.get_neighbors(current_node):
                coords_n = (neighbor.x, neighbor.y)
                
                if coords_n not in closed_set:
                    neighbor.parent = current_node
                    neighbor.h_score = self.calculate_heuristic(neighbor, target_node)
                    
                    # Đưa vào hàng đợi ưu tiên
                    heapq.heappush(open_set, (neighbor.h_score, id(neighbor), neighbor))
                    
        return None

    def calculate_heuristic(self, node_a: Node, node_b: Node) -> float:
        return float(self.heuristic_fn(node_a, node_b))


# ==========================================
# 2. A* SEARCH
# ==========================================
class AStar:
    def __init__(self, heuristic_fn=manhattan) -> None:
        self.heuristic_fn = heuristic_fn
        self.visited_order: list[tuple[int, int]] = []
        self.expanded_nodes: int = 0
        self.frontier_max_size: int = 0

    def find_path(self, start_node: Node, target_node: Node, game_map: GridMapAdapter) -> Node | None:
        open_set = []
        closed_set = set()

        start_node.g_score = 0.0
        start_node.h_score = self.calculate_heuristic(start_node, target_node)
        start_node.f_score = start_node.g_score + start_node.h_score
        
        heapq.heappush(open_set, (start_node.f_score, id(start_node), start_node))

        self.visited_order = []
        self.expanded_nodes = 0
        self.frontier_max_size = 1

        while open_set:
            self.frontier_max_size = max(self.frontier_max_size, len(open_set))
            _, _, current_node = heapq.heappop(open_set)
            coords = (current_node.x, current_node.y)

            if coords in closed_set:
                continue
            closed_set.add(coords)
            self.expanded_nodes += 1
            self.visited_order.append(coords)

            if current_node.x == target_node.x and current_node.y == target_node.y:
                return current_node

            for neighbor in game_map.get_neighbors(current_node):
                if (neighbor.x, neighbor.y) in closed_set:
                    continue

                tentative_g_score = current_node.g_score + 1.0
                
                if tentative_g_score < neighbor.g_score or neighbor.g_score == 0.0:
                    neighbor.parent = current_node
                    neighbor.g_score = tentative_g_score
                    neighbor.h_score = self.calculate_heuristic(neighbor, target_node)
                    neighbor.f_score = neighbor.g_score + neighbor.h_score
                    
                    heapq.heappush(open_set, (neighbor.f_score, id(neighbor), neighbor))

        return None

    def calculate_heuristic(self, node_a: Node, node_b: Node) -> float:
        return float(self.heuristic_fn(node_a, node_b))


# ==========================================
# 3. IDA*
# ==========================================
class IDAStar:
    def __init__(self, heuristic_fn=manhattan) -> None:
        self.heuristic_fn = heuristic_fn
        self.visited_order: list[tuple[int, int]] = []
        self.expanded_nodes: int = 0
        self.frontier_max_size: int = 0

    def find_path(self, start_node: Node, target_node: Node, game_map: GridMapAdapter) -> Node | None:
        threshold = self.calculate_heuristic(start_node, target_node)
        self.visited_order = []
        self.expanded_nodes = 0
        self.frontier_max_size = 1

        while True:
            result_node, new_threshold = self.search(start_node, 0.0, threshold, target_node, game_map)
            
            if result_node is not None:
                return result_node
                
            if new_threshold == math.inf:
                return None
                
            threshold = new_threshold 

    def search(self, current_node: Node, g_score: float, threshold: float, target_node: Node, game_map: GridMapAdapter) -> tuple[Node | None, float]:
        f_score = g_score + self.calculate_heuristic(current_node, target_node)

        if f_score > threshold:
            return None, f_score

        coords = (current_node.x, current_node.y)
        if coords not in self.visited_order:
            self.visited_order.append(coords)
            self.expanded_nodes += 1

        if current_node.x == target_node.x and current_node.y == target_node.y:
            return current_node, f_score

        min_exceeded_threshold = math.inf

        for neighbor in game_map.get_neighbors(current_node):
            neighbor.parent = current_node
            result_node, new_threshold = self.search(neighbor, g_score + 1.0, threshold, target_node, game_map)

            if result_node is not None:
                return result_node, new_threshold

            if new_threshold < min_exceeded_threshold:
                min_exceeded_threshold = new_threshold

        return None, min_exceeded_threshold

    def calculate_heuristic(self, node_a: Node, node_b: Node) -> float:
        return float(self.heuristic_fn(node_a, node_b))


# ==========================================
# 4. BIDIRECTIONAL SEARCH 
# ==========================================
class BidirectionalSearch:
    def __init__(self) -> None:
        self.visited_order: list[tuple[int, int]] = []
        self.expanded_nodes: int = 0
        self.frontier_max_size: int = 0

    def find_path(self, start_node: Node, target_node: Node, game_map: GridMapAdapter) -> Node | None:
        forward_queue = deque([start_node])
        backward_queue = deque([target_node])

        forward_visited = {(start_node.x, start_node.y): start_node}
        backward_visited = {(target_node.x, target_node.y): target_node}

        self.visited_order = []
        self.expanded_nodes = 0
        self.frontier_max_size = 2

        while forward_queue and backward_queue:
            self.frontier_max_size = max(self.frontier_max_size, len(forward_queue) + len(backward_queue))
            
            intersect_node = self.expand_frontier(forward_queue, forward_visited, backward_visited, game_map, is_forward=True)
            if intersect_node:
                return self.build_path(intersect_node)

            intersect_node = self.expand_frontier(backward_queue, backward_visited, forward_visited, game_map, is_forward=False)
            if intersect_node:
                return self.build_path(intersect_node)

        return None

    def expand_frontier(self, queue: deque[Node], my_visited: dict[tuple[int, int], Node], opponent_visited: dict[tuple[int, int], Node], game_map: GridMapAdapter, is_forward: bool) -> Node | None:
        current_node = queue.popleft()
        coords = (current_node.x, current_node.y)
        self.expanded_nodes += 1
        self.visited_order.append(coords)

        for neighbor in game_map.get_neighbors(current_node):
            n_coords = (neighbor.x, neighbor.y)

            if n_coords in opponent_visited:
                if is_forward:
                    neighbor.parent = current_node
                else:
                    current_node.parent = neighbor 
                return neighbor

            if n_coords not in my_visited:
                neighbor.parent = current_node
                my_visited[n_coords] = neighbor
                queue.append(neighbor)

        return None

    def build_path(self, intersect_node: Node) -> Node:
        return intersect_node

# ==========================================
# HÀM BỌC (WRAPPER FUNCTIONS)
# ==========================================

def a_star(arg1, arg2, *args, **kwargs) -> PathSearchResult | Node | None:
    if isinstance(arg1, list) or (hasattr(arg1, '__len__') and not hasattr(arg1, 'x')):
        # Format 1: a_star(grid, start, goal)
        grid = arg1
        start_coords = arg2
        goal_coords = args[0] if args else kwargs.get("goal")
        
        start_node = Node(start_coords[0], start_coords[1])
        goal_node_obj = Node(goal_coords[0], goal_coords[1])
        game_map = GridMapAdapter(grid, goal_coords)
        
        heuristic_fn = kwargs.get("heuristic_fn", manhattan)
        solver = AStar(heuristic_fn=heuristic_fn)
        goal_node = solver.find_path(start_node, goal_node_obj, game_map)
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
        # Format 2: a_star(start_node, target_node, game_map, *args, **kwargs)
        start_node = arg1
        target_node = arg2
        game_map = args[0] if args else kwargs.get("game_map")
        heuristic_fn = kwargs.get("heuristic_fn", manhattan)
        solver = AStar(heuristic_fn=heuristic_fn)
        return solver.find_path(start_node, target_node, game_map)


def greedy(arg1, arg2, *args, **kwargs) -> PathSearchResult | Node | None:
    if isinstance(arg1, list) or (hasattr(arg1, '__len__') and not hasattr(arg1, 'x')):
        # Format 1: greedy(grid, start, goal)
        grid = arg1
        start_coords = arg2
        goal_coords = args[0] if args else kwargs.get("goal")
        
        start_node = Node(start_coords[0], start_coords[1])
        goal_node_obj = Node(goal_coords[0], goal_coords[1])
        game_map = GridMapAdapter(grid, goal_coords)
        
        heuristic_fn = kwargs.get("heuristic_fn", manhattan)
        solver = GreedyBestFirst(heuristic_fn=heuristic_fn)
        goal_node = solver.find_path(start_node, goal_node_obj, game_map)
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
        # Format 2: greedy(start_node, target_node, game_map, *args, **kwargs)
        start_node = arg1
        target_node = arg2
        game_map = args[0] if args else kwargs.get("game_map")
        heuristic_fn = kwargs.get("heuristic_fn", manhattan)
        solver = GreedyBestFirst(heuristic_fn=heuristic_fn)
        return solver.find_path(start_node, target_node, game_map)


def ida_star(arg1, arg2, *args, **kwargs) -> PathSearchResult | Node | None:
    if isinstance(arg1, list) or (hasattr(arg1, '__len__') and not hasattr(arg1, 'x')):
        # Format 1: ida_star(grid, start, goal)
        grid = arg1
        start_coords = arg2
        goal_coords = args[0] if args else kwargs.get("goal")
        
        start_node = Node(start_coords[0], start_coords[1])
        goal_node_obj = Node(goal_coords[0], goal_coords[1])
        game_map = GridMapAdapter(grid, goal_coords)
        
        heuristic_fn = kwargs.get("heuristic_fn", manhattan)
        solver = IDAStar(heuristic_fn=heuristic_fn)
        goal_node = solver.find_path(start_node, goal_node_obj, game_map)
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
        # Format 2: ida_star(start_node, target_node, game_map, *args, **kwargs)
        start_node = arg1
        target_node = arg2
        game_map = args[0] if args else kwargs.get("game_map")
        heuristic_fn = kwargs.get("heuristic_fn", manhattan)
        solver = IDAStar(heuristic_fn=heuristic_fn)
        return solver.find_path(start_node, target_node, game_map)


def bidirectional(arg1, arg2, *args, **kwargs) -> PathSearchResult | Node | None:
    if isinstance(arg1, list) or (hasattr(arg1, '__len__') and not hasattr(arg1, 'x')):
        # Format 1: bidirectional(grid, start, goal)
        grid = arg1
        start_coords = arg2
        goal_coords = args[0] if args else kwargs.get("goal")
        
        start_node = Node(start_coords[0], start_coords[1])
        goal_node_obj = Node(goal_coords[0], goal_coords[1])
        game_map = GridMapAdapter(grid, goal_coords)
        
        solver = BidirectionalSearch()
        goal_node = solver.find_path(start_node, goal_node_obj, game_map)
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
        # Format 2: bidirectional(start_node, target_node, game_map, *args, **kwargs)
        start_node = arg1
        target_node = arg2
        game_map = args[0] if args else kwargs.get("game_map")
        solver = BidirectionalSearch()
        return solver.find_path(start_node, target_node, game_map)
