"""
📄 Tên File: algorithm_registry.py (Nằm trong src/algorithms/)
* Vai trò: Ánh xạ tên thuật toán (String) trên UI thành các hàm Generator thực tế.
"""
from src.algorithms.uninformed import bfs_generator, dfs_generator
# Sau này bạn import thêm các thuật toán khác từ informed.py, local_search.py...
# from src.algorithms.informed import astar_generator, greedy_generator

ALGORITHM_REGISTRY = {
    "BFS": bfs_generator,
    "DFS": dfs_generator,
    # "A*": astar_generator,
    # "Greedy": greedy_generator,
    # Thêm các thuật toán khác vào đây khi bạn code xong
}

def get_algorithm(name: str):
    """Trả về hàm thuật toán dựa trên tên. Mặc định là BFS nếu không tìm thấy."""
    return ALGORITHM_REGISTRY.get(name, bfs_generator)