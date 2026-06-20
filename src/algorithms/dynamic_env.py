"""Dynamic Environment and Contingency Pathfinding Algorithms."""
import math
from utils.node import Node

# ==========================================
# 1. LEARNING REAL-TIME A* (LRTA*)
# ==========================================
import sys

# Robust imports to support both sys.path environments
try:
    from utils.node import Node
    from utils.heuristics import manhattan
except ModuleNotFoundError:
    from src.utils.node import Node
    from src.utils.heuristics import manhattan

try:
    from algorithms.common import PathSearchResult, GridMapAdapter, reconstruct_path_from_node
except ModuleNotFoundError:
    from src.algorithms.common import PathSearchResult, GridMapAdapter, reconstruct_path_from_node


# ==========================================
# 1. LEARNING REAL-TIME A* (LRTA*)
# ==========================================
class LRTAStar:
    """
    Thuật toán LRTA* học Heuristic theo thời gian thực.
    Khác với A* lên kế hoạch toàn bộ đường đi trước khi chạy, LRTA* quyết định 
    bước đi ngay lập tức và cập nhật Heuristic nếu đi vào ngõ cụt.
    """
    def __init__(self, heuristic_fn=manhattan) -> None:
        self.heuristic_fn = heuristic_fn
        self.visited_order: list[tuple[int, int]] = []
        self.expanded_nodes: int = 0
        self.frontier_max_size: int = 1 # LRTA* tìm kiếm cục bộ, không duy trì frontier lớn
        
        # Bảng trí nhớ lưu trữ Heuristic đã cập nhật (H_table)
        self.h_table: dict[tuple[int, int], float] = {}

    def _get_h(self, node: Node, target_node: Node) -> float:
        """Lấy giá trị Heuristic từ bộ nhớ, nếu chưa có thì tính bằng hàm chuẩn."""
        coords = (node.x, node.y)
        if coords not in self.h_table:
            self.h_table[coords] = self.heuristic_fn(node, target_node)
        return self.h_table[coords]

    def find_path(self, start_node: Node, target_node: Node, game_map: GridMapAdapter, max_steps: int = 2000) -> Node | None:
        current_node = start_node
        self.visited_order = [(current_node.x, current_node.y)]
        self.expanded_nodes = 0

        # Vòng lặp Real-time: Agent thực sự di chuyển từng bước
        while not (current_node.x == target_node.x and current_node.y == target_node.y):
            # Cơ chế an toàn (Failsafe) tránh lặp vô tận nếu bị nhốt kín
            if self.expanded_nodes > max_steps:
                return None

            self.expanded_nodes += 1
            neighbors = game_map.get_neighbors(current_node)

            if not neighbors:
                return None  # Ngõ cụt hoàn toàn

            best_neighbor = None
            min_f_value = float('inf')

            # 1. Đánh giá tất cả các bước đi lân cận
            for neighbor in neighbors:
                # f(n) = cost(current -> neighbor) + h(neighbor)
                # Giả sử chi phí di chuyển cơ bản là 1, cộng thêm bẫy nếu có
                cost = 1.0 + game_map.get_danger_level(neighbor)
                f_value = cost + self._get_h(neighbor, target_node)

                if f_value < min_f_value:
                    min_f_value = f_value
                    best_neighbor = neighbor

            if best_neighbor is None:
                return None

            # 2. Học (Cập nhật Heuristic): 
            # Giá trị Heuristic thực tế của ô hiện tại bằng f_value của hàng xóm tốt nhất
            current_coords = (current_node.x, current_node.y)
            # LRTA* chuẩn chỉ cập nhật nếu giá trị mới lớn hơn giá trị cũ
            self.h_table[current_coords] = max(self._get_h(current_node, target_node), min_f_value)

            # 3. Di chuyển
            best_neighbor.parent = current_node
            current_node = best_neighbor
            self.visited_order.append((current_node.x, current_node.y))

        return current_node

# ==========================================
# 2. AND-OR SEARCH
# ==========================================

class AndOrSearch:
    def find_path(self, start_node, target_node, game_map):
        """
        Khác với A*, AND-OR Search trả về một Kế hoạch (Policy Dictionary)
        Ví dụ: {(2,3): "Đi Lên", (2,4): "Nếu có quái thì rẽ Trái, nếu trống thì đi thẳng"}
        """
        visited_states = set()
        plan = self.or_search(start_node, target_node, game_map, visited_states)
        return plan # Trả về cuốn "Cẩm nang sinh tồn" (Policy) thay vì Node cuối

    def or_search(self, current_state, target_node, game_map, path_history):
        """ OR Node: Lượt của Agent. Agent chọn 1 hành động tốt nhất """
        if current_state.x == target_node.x and current_state.y == target_node.y:
            return "ĐÃ ĐẾN ĐÍCH"
            
        coords = (current_state.x, current_state.y)
        if coords in path_history:
            return "THẤT BẠI_VÒNG LẶP" # Đang đi lòng vòng

        # Lấy danh sách các hành động có thể làm (vd: rẽ trái, phải, lên, xuống)
        actions = game_map.get_available_actions(current_state)
        
        for action in actions:
            new_path_history = path_history.copy()
            new_path_history.add(coords)
            
            # Đẩy hành động này cho Môi trường phản hồi (AND Node)
            plan = self.and_search(current_state, action, target_node, game_map, new_path_history)
            
            # Nếu kế hoạch dự phòng thành công cho MỌI trường hợp ngẫu nhiên của môi trường
            if plan != "THẤT BẠI":
                return {action: plan} # Chốt hành động này
                
        return "THẤT BẠI"

    def and_search(self, current_state, action, target_node, game_map, path_history):
        """ AND Node: Lượt của Môi trường. Môi trường tung xúc xắc sinh ra các biến cố """
        # Giả lập hành động này sẽ dẫn đến bao nhiêu hệ quả ngẫu nhiên?
        # Ví dụ: Bước lên ô sương mù -> 50% ra đường trống, 50% ra bẫy hố
        possible_outcomes = game_map.get_stochastic_outcomes(current_state, action)
        
        contingency_plan = {} # Kế hoạch dự phòng: NẾU ... THÌ ...
        
        for outcome_state in possible_outcomes:
            # Sinh chiến lược cho từng kịch bản
            plan = self.or_search(outcome_state, target_node, game_map, path_history)
            
            if plan == "THẤT BẠI" or plan == "THẤT BẠI_VÒNG LẶP":
                # Kịch bản này dẫn đến cái chết vô phương cứu chữa -> Hành động ban đầu sai
                return "THẤT BẠI"
            
            # Ghi chép lại: "Nếu ra biến cố A, thì làm theo plan này"
            contingency_plan[outcome_state.event_name] = plan
            
        return contingency_plan

# ==========================================
# HÀM BỌC (WRAPPER FUNCTIONS)
# ==========================================

def lrta_star(arg1, arg2, *args, **kwargs) -> PathSearchResult | Node | None:
    """
    Hàm bọc thông minh: Hỗ trợ cả Test Harness và Game Engine.
    """
    heuristic_fn = kwargs.get('heuristic_fn', manhattan)
    
    if isinstance(arg1, list) or (hasattr(arg1, '__len__') and not hasattr(arg1, 'x')):
        # ---------------------------------------------------------
        # KỊCH BẢN 1: FILE TEST ĐANG GỌI -> lrta_star(grid, start, goal)
        # ---------------------------------------------------------
        grid = arg1
        start_coords = arg2
        goal_coords = args[0] if args else kwargs.get("goal")
        
        start_node = Node(start_coords[0], start_coords[1])
        target_node = Node(goal_coords[0], goal_coords[1])
        game_map = GridMapAdapter(grid, goal_coords)
        
        solver = LRTAStar(heuristic_fn=heuristic_fn)
        goal_node = solver.find_path(start_node, target_node, game_map)
        
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
        # ---------------------------------------------------------
        # KỊCH BẢN 2: GAME ENGINE ĐANG GỌI -> lrta_star(start_node, target_node, game_map)
        # ---------------------------------------------------------
        start_node = arg1
        target_node = arg2
        game_map = args[0] if args else kwargs.get("game_map")
        
        solver = LRTAStar(heuristic_fn=heuristic_fn)
        return solver.find_path(start_node, target_node, game_map)

def and_or_search(start_node, target_node, game_map, *args, **kwargs):
    """ Hàm bọc gọi thuật toán AND-OR Search. Trả về Policy (Dict) thay vì Node """
    solver = AndOrSearch()
    return solver.find_path(start_node, target_node, game_map)