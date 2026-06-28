"""
📄 Tên File: algorithm_registry.py (Nằm trong src/algorithms/)
* Vai trò: Ánh xạ tên thuật toán (String) trên UI thành các hàm Generator thực tế.
"""
from src.algorithms.uninformed import bfs_generator, dfs_generator
from src.algorithms.informed import astar_generator, greedy_generator, bidirectional_generator, idastar_generator
from src.algorithms.local_search import hill_climbing, local_beam_search, simulated_annealing
from src.algorithms.dynamic_env import lrta_star_generator, and_or_generator

ALGORITHM_REGISTRY = {
    # LEVEL 1: Uninformed Search
    "BFS": bfs_generator,
    "DFS": dfs_generator,

    # LEVEL 2: Informed Search
    "GREEDY": greedy_generator,
    "ASTAR": astar_generator,
    "BIDIRECTIONAL": bidirectional_generator,
    "IDASTAR": idastar_generator,

    # LEVEL 3: Local Search
    "HILL_CLIMBING": hill_climbing,
    "SIMULATED_ANNEALING": simulated_annealing,
    "LOCAL_BEAM": local_beam_search,

    #lv4: dynamic_env
    "LRTA_STAR": lrta_star_generator,
    "AND_OR": and_or_generator
}

def get_algorithm(name: str):
    """Trả về hàm thuật toán dựa trên tên. Mặc định là BFS nếu không tìm thấy."""
    return ALGORITHM_REGISTRY.get(name, bfs_generator)