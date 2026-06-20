"""Dynamic Environment and Contingency Pathfinding Algorithms."""
import math
from utils.node import Node

# ==========================================
# 1. LEARNING REAL-TIME A* (LRTA*)
# ==========================================
class LRTAStar:
    def __init__(self):
        # Bộ nhớ (Memory) của Agent: Lưu trữ khoảng cách Heuristic cập nhật liên tục
        # Key: (x, y) -> Value: Heuristic estimate
        self.memory_table = {} 

    def find_path(self, start_node, target_node, game_map):
        current_node = start_node
        
        # Biến an toàn để tránh vòng lặp vô tận nếu Agent bị nhốt kín
        max_steps = 2000 
        step_count = 0

        while current_node.x != target_node.x or current_node.y != target_node.y:
            if step_count > max_steps:
                return None # Kẹt cứng không lối thoát
            step_count += 1

            neighbors = game_map.get_neighbors(current_node)
            if not neighbors:
                return None

            best_neighbor = None
            min_f_score = math.inf

            # Bước 1: Nhìn quanh các ô láng giềng và đánh giá
            for neighbor in neighbors:
                coords = (neighbor.x, neighbor.y)
                
                # Nếu ô này từng đi qua và đã được ghi nhớ, lấy dữ liệu từ bộ nhớ. 
                # Nếu chưa đi qua, dùng khoảng cách chim bay (Manhattan) mặc định.
                h_score = self.memory_table.get(coords, self.calculate_heuristic(neighbor, target_node))
                
                # Chi phí đi vào ô đó (giả sử là 1 + độ nguy hiểm của bẫy)
                g_score = 1 + game_map.get_danger_level(neighbor) 
                f_score = g_score + h_score

                if f_score < min_f_score:
                    min_f_score = f_score
                    best_neighbor = neighbor

            # Bước 2: CẬP NHẬT TRÍ NHỚ (Learning Step) CỰC KỲ QUAN TRỌNG
            # Trươc khi rời đi, Agent ghi đè lại mức độ "tồi tệ" của ô đang đứng.
            # Nếu nó là ngõ cụt, min_f_score sẽ rất cao, ô này sẽ bị "đánh dấu" là nguy hiểm.
            self.memory_table[(current_node.x, current_node.y)] = min_f_score

            # Bước 3: Di chuyển
            best_neighbor.parent = current_node
            current_node = best_neighbor

        # Trong LRTA*, đường đi `.parent` có thể ngoằn ngoèo và chứa nhiều vòng lặp 
        # (do Agent đi tới đi lui để thử đường).
        return current_node 

    def calculate_heuristic(self, node_a, node_b):
        return abs(node_a.x - node_b.x) + abs(node_a.y - node_b.y)

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

def lrta_star(start_node, target_node, game_map, *args, **kwargs):
    """ Hàm bọc gọi thuật toán LRTA*. Lưu ý: Thuật toán này có tính duy trì trạng thái (Stateful) """
    # Nếu muốn Agent học qua nhiều lượt chơi, object `solver` này nên được khởi tạo ở cấp Game Manager 
    # thay vì tạo mới mỗi lần chạy để nó giữ lại được biến `memory_table`.
    solver = LRTAStar() 
    return solver.find_path(start_node, target_node, game_map)

def and_or_search(start_node, target_node, game_map, *args, **kwargs):
    """ Hàm bọc gọi thuật toán AND-OR Search. Trả về Policy (Dict) thay vì Node """
    solver = AndOrSearch()
    return solver.find_path(start_node, target_node, game_map)