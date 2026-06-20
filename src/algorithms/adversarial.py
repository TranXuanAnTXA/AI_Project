"""Adversarial search algorithms for Boss AI."""
import math
import random

# ==========================================
# 1. MINIMAX
# ==========================================
class Minimax:
    def get_best_move(self, game_state, max_depth):
        best_move = None
        max_score = -math.inf

        # Lượt của Boss (Maximizer) ở hiện tại: Thử từng nước đi
        for move in game_state.get_boss_legal_moves():
            next_state = game_state.execute_move(move)
            
            # Kêu Agent chơi thử trong tưởng tượng để xem nước đi này tốt đến đâu
            score = self.min_value(next_state, max_depth - 1)
            
            if score > max_score:
                max_score = score
                best_move = move

        return best_move

    def min_value(self, state, depth):
        """ Lượt của Agent (Minimizer) """
        if depth == 0 or state.is_game_over():
            return state.evaluate_score() # Hàm đánh giá điểm: Boss càng gần Agent điểm càng cao
            
        min_score = math.inf
        for move in state.get_agent_legal_moves():
            next_state = state.execute_move(move)
            min_score = min(min_score, self.max_value(next_state, depth - 1))
            
        return min_score
        
    def max_value(self, state, depth):
        """ Lượt tiếp theo của Boss (Maximizer) """
        if depth == 0 or state.is_game_over():
            return state.evaluate_score()
            
        max_score = -math.inf
        for move in state.get_boss_legal_moves():
            next_state = state.execute_move(move)
            max_score = max(max_score, self.min_value(next_state, depth - 1))
            
        return max_score


# ==========================================
# 2. ALPHA-BETA PRUNING 
# ==========================================
class AlphaBeta:
    def get_best_move(self, game_state, max_depth):
        best_move = None
        alpha = -math.inf # Alpha: Điểm TỐT NHẤT mà Boss (Max) đã nắm chắc trong tay
        beta = math.inf   # Beta: Điểm TỒI NHẤT mà Agent (Min) có thể ép Boss phải chịu
        max_score = -math.inf

        for move in game_state.get_boss_legal_moves():
            next_state = game_state.execute_move(move)
            score = self.min_value(next_state, max_depth - 1, alpha, beta)
            
            if score > max_score:
                max_score = score
                best_move = move
                
            # Cập nhật giới hạn dưới an toàn của Boss
            alpha = max(alpha, max_score)

        return best_move

    def min_value(self, state, depth, alpha, beta):
        if depth == 0 or state.is_game_over():
            return state.evaluate_score()
            
        min_score = math.inf
        for move in state.get_agent_legal_moves():
            next_state = state.execute_move(move)
            min_score = min(min_score, self.max_value(next_state, depth - 1, alpha, beta))
            
            # CẮT TỈA (PRUNING): Nếu điểm này tồi tệ hơn mức an toàn (Alpha) của Boss
            # Agent biết Boss sẽ không bao giờ chọn nhánh này ngay từ đầu -> Khỏi tính tiếp!
            if min_score <= alpha:
                return min_score 
                
            beta = min(beta, min_score)
            
        return min_score
        
    def max_value(self, state, depth, alpha, beta):
        if depth == 0 or state.is_game_over():
            return state.evaluate_score()
            
        max_score = -math.inf
        for move in state.get_boss_legal_moves():
            next_state = state.execute_move(move)
            max_score = max(max_score, self.min_value(next_state, depth - 1, alpha, beta))
            
            # CẮT TỈA: Nếu điểm này quá cao so với mức chịu đựng (Beta) của Agent
            # Boss biết Agent sẽ không bao giờ cho phép Boss đi đến bước này -> Khỏi tính!
            if max_score >= beta:
                return max_score
                
            alpha = max(alpha, max_score)
            
        return max_score


# ==========================================
# 3. EXPECTIMAX 
# ==========================================
class Expectimax:
    def get_best_move(self, game_state, max_depth):
        best_move = None
        max_score = -math.inf

        for move in game_state.get_boss_legal_moves():
            next_state = game_state.execute_move(move)
            # Khác với Minimax, đây là lượt của Môi trường ngẫu nhiên (Chance Node)
            score = self.expected_value(next_state, max_depth - 1) 
            
            if score > max_score:
                max_score = score
                best_move = move

        return best_move

    def expected_value(self, state, depth):
        """ Lượt của Môi trường (Chance). Tính Giá trị Kỳ vọng (Trung bình cộng) """
        if depth == 0 or state.is_game_over():
            return state.evaluate_score()
            
        legal_moves = state.get_random_environment_events()
        if not legal_moves:
            return state.evaluate_score()
            
        total_score = 0
        probability = 1.0 / len(legal_moves) # Giả sử các biến cố có xác suất xảy ra bằng nhau
        
        for move in legal_moves:
            next_state = state.execute_move(move)
            total_score += probability * self.max_value(next_state, depth - 1)
            
        return total_score
        
    def max_value(self, state, depth):
        if depth == 0 or state.is_game_over():
            return state.evaluate_score()
            
        max_score = -math.inf
        for move in state.get_boss_legal_moves():
            next_state = state.execute_move(move)
            max_score = max(max_score, self.expected_value(next_state, depth - 1))
            
        return max_score


# ==========================================
# 4. MONTE CARLO TREE SEARCH - MCTS
# ==========================================
class MCTSNode:
    def __init__(self, state, parent=None, move=None):
        self.state = state
        self.parent = parent
        self.move = move
        self.children = []
        self.untried_moves = state.get_boss_legal_moves() # Các nước chưa thử
        self.visits = 0
        self.wins = 0

class MCTS:
    def get_best_move(self, game_state, num_simulations=1000):
        root = MCTSNode(state=game_state)

        for _ in range(num_simulations):
            node = root
            temp_state = game_state.clone()

            # 1. SELECTION (Chọn lọc): Đi xuống các nhánh đã biết bằng công thức UCB1
            while not node.untried_moves and node.children:
                node = self.select_child(node)
                temp_state = temp_state.execute_move(node.move)

            # 2. EXPANSION (Mở rộng): Nếu còn nước chưa thử, thử 1 nước mới
            if node.untried_moves:
                move = random.choice(node.untried_moves)
                node.untried_moves.remove(move)
                temp_state = temp_state.execute_move(move)
                child_node = MCTSNode(state=temp_state, parent=node, move=move)
                node.children.append(child_node)
                node = child_node

            # 3. SIMULATION (Mô phỏng): Đánh bừa (Random playout) cho đến khi Game Over
            while not temp_state.is_game_over():
                # Ở mô phỏng, cả Boss và Agent đều đi ngẫu nhiên cho lẹ
                moves = temp_state.get_all_legal_moves() 
                if not moves: break
                temp_state = temp_state.execute_move(random.choice(moves))

            # 4. BACKPROPAGATION (Lan truyền ngược): Cập nhật kết quả thắng/thua lên gốc
            win_score = temp_state.evaluate_win_loss() # 1: Boss thắng, 0: Thua
            while node is not None:
                node.visits += 1
                node.wins += win_score
                node = node.parent

        # Cuối cùng, chọn nước đi có TỈ LỆ THẮNG cao nhất ở cây gốc
        best_child = max(root.children, key=lambda c: c.wins / c.visits if c.visits > 0 else 0)
        return best_child.move

    def select_child(self, node):
        """ Công thức UCB1: Cân bằng giữa Khai thác (Tỉ lệ thắng cao) và Khám phá (Ít được thăm) """
        exploration_weight = 1.41 # Hằng số C
        best_score = -math.inf
        best_child = None
        
        for child in node.children:
            if child.visits == 0:
                return child
            # Công thức: (Win Rate) + C * sqrt( ln(Parent Visits) / Child Visits )
            ucb1 = (child.wins / child.visits) + exploration_weight * math.sqrt(math.log(node.visits) / child.visits)
            if ucb1 > best_score:
                best_score = ucb1
                best_child = child
                
        return best_child


# ==========================================
# HÀM BỌC (WRAPPER FUNCTIONS)
# ==========================================

def minimax(game_state, max_depth=3, *args, **kwargs):
    solver = Minimax()
    return solver.get_best_move(game_state, max_depth)

def alpha_beta(game_state, max_depth=4, *args, **kwargs):
    # Alpha-Beta tính nhanh hơn nên có thể cho độ sâu (tầm nhìn) lớn hơn Minimax
    solver = AlphaBeta()
    return solver.get_best_move(game_state, max_depth)

def expectimax(game_state, max_depth=3, *args, **kwargs):
    solver = Expectimax()
    return solver.get_best_move(game_state, max_depth)

def mcts(game_state, num_simulations=1000, *args, **kwargs):
    solver = MCTS()
    return solver.get_best_move(game_state, num_simulations)