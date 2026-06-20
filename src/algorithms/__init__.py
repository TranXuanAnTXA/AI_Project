"""Algorithm implementations for game AI."""
"""
Đây là file khởi tạo cho package algorithms.
Nó đóng vai trò như một "trạm điều phối", gom tất cả các thuật toán
từ các file con (modules) để export ra ngoài một cách gọn gàng nhất.
"""

# 1. Nhóm Dò đường Cơ bản
from .uninformed import bfs, dfs, ucs

# 2. Nhóm Tìm kiếm Tối ưu
from .informed import a_star, greedy, ida_star, bidirectional

# 3. Nhóm Tìm kiếm Cục bộ & Đột biến
from .local_search import hill_climbing, simulated_annealing, genetic_algorithm

# 4. Nhóm Môi trường Động
from .dynamic_env import lrta_star, and_or_search

# 5. Nhóm Giải mã CSP
from .csp import backtracking_search, ac3_preprocess, min_conflicts_search

# 6. Nhóm Đối kháng (Đánh Boss)
from .adversarial import minimax, alpha_beta, expectimax, mcts


# __all__ định nghĩa chính xác những hàm nào sẽ được cung cấp ra bên ngoài.
# Bất kỳ ai import từ thư mục 'algorithms' sẽ chỉ nhìn thấy các hàm này, 
# chứ không nhìn thấy các Class nội bộ (như BFS, AStar, MCTSNode...)
__all__ = [
    # Uninformed
    "bfs", "dfs", "ucs",
    
    # Informed
    "a_star", "greedy", "ida_star", "bidirectional",
    
    # Local & Mutation
    "hill_climbing", "simulated_annealing", "genetic_algorithm",
    
    # Dynamic
    "lrta_star", "and_or_search",
    
    # CSP
    "backtracking_search", "ac3_preprocess", "min_conflicts_search",
    
    # Adversarial
    "minimax", "alpha_beta", "expectimax", "mcts"
]