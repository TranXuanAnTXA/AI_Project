"""Khung kiểm thử (Test harness) thuật toán cho một bản đồ cố định.
Khung kiểm thử tự động (Test harness) để xác minh tính chính xác của các thuật toán tìm đường trên một bản đồ mẫu cố định. Nó đóng vai trò như một "người gác cổng", đảm bảo rằng nếu bạn vô tình sửa sai code thuật toán trong tương lai, hệ thống sẽ báo lỗi ngay lập tức.

Cách hoạt động (How it works): File này thiết lập các "Hợp đồng" (Contracts) định nghĩa rõ đầu vào/đầu ra mong muốn. Nó gọi các thuật toán chạy trên một ma trận mẫu (FIXED_GRID), sau đó dùng lệnh assert để đối chiếu kết quả. Ví dụ: nó kiểm tra xem đường đi có đi xuyên tường không, có bị đứt quãng không, và A* có tìm ra đường đi ngắn đúng bằng BFS không.

Các Hàm/Class chính (Core Functions):

AlgorithmContract (Data Class): Lưu trữ tài liệu (document) mô tả chi tiết đầu vào, đầu ra và các biến được quản lý của từng thuật toán.

is_valid_path(): Hàm kiểm tra tính hợp lệ của đường đi. Đảm bảo đường đi bắt đầu từ điểm Start, kết thúc ở Goal, các bước đi liên tiếp và không dẫm lên Tường (giá trị 1).

run_algorithm(): Hàm hỗ trợ để chạy nhanh một thuật toán dựa trên tên.

test_...(): Các hàm kiểm thử cụ thể (dành cho framework như pytest). Dùng để test BFS, DFS, A*, và Greedy.

Mối liên hệ (Dependencies): Gọi thuật toán từ src.algorithms. Gọi kiểu dữ liệu PathSearchResult từ src.algorithms.common. Lấy dữ liệu ma trận mẫu từ tests.fixtures.fixed_map.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.algorithms import a_star, bfs, dfs, greedy, ucs, bidirectional, ida_star, lrta_star
from src.algorithms.common import PathSearchResult
from tests.fixtures.fixed_map import FIXED_GRID, GOAL_NODE, START_NODE


@dataclass(frozen=True)
class AlgorithmContract:
    """Cấu trúc mô tả hợp đồng của một thuật toán."""
    name: str
    input_spec: str
    output_spec: str
    managed_variables: tuple[str, ...]


# Đăng ký các hợp đồng thuật toán
ALGORITHM_CONTRACTS: dict[str, AlgorithmContract] = {
    "bfs": AlgorithmContract(
        name="bfs",
        input_spec="grid 10x10, start node, goal node",
        output_spec="PathSearchResult(path, visited_order, expanded_nodes, frontier_max_size, found)",
        managed_variables=("queue/frontier", "visited set", "parent map", "expanded count", "frontier peak"),
    ),
    "dfs": AlgorithmContract(
        name="dfs",
        input_spec="grid 10x10, start node, goal node",
        output_spec="PathSearchResult(path, visited_order, expanded_nodes, frontier_max_size, found)",
        managed_variables=("stack/frontier", "visited set", "parent map", "expanded count", "frontier peak"),
    ),
    "a_star": AlgorithmContract(
        name="a_star",
        input_spec="grid 10x10, start node, goal node",
        output_spec="PathSearchResult(path, visited_order, expanded_nodes, frontier_max_size, found)",
        managed_variables=("priority queue", "g_score map", "parent map", "closed set", "expanded count", "frontier peak"),
    ),
    "greedy": AlgorithmContract(
        name="greedy",
        input_spec="grid 10x10, start node, goal node",
        output_spec="PathSearchResult(path, visited_order, expanded_nodes, frontier_max_size, found)",
        managed_variables=("priority queue", "visited set", "parent map", "expanded count", "frontier peak"),
    ),
    "ucs": AlgorithmContract(
        name="ucs",
        input_spec="grid 10x10, start node, goal node",
        output_spec="PathSearchResult(path, visited_order, expanded_nodes, frontier_max_size, found)",
        managed_variables=("priority queue", "visited set", "parent map", "expanded count", "frontier peak"),
    ),
    "bidirectional": AlgorithmContract(
    name="bidirectional",
    input_spec="grid 10x10, start node, goal node",
    output_spec="PathSearchResult(path, visited_order, expanded_nodes, frontier_max_size, found)",
    managed_variables=("forward queue", "backward queue", "visited forward", "visited backward", "expanded count"),
    ),
    "ida_star": AlgorithmContract(
    name="ida_star",
    input_spec="grid 10x10, start node, goal node",
    output_spec="PathSearchResult(path, visited_order, expanded_nodes, frontier_max_size, found)",
    managed_variables=("threshold", "dfs stack/recursion", "expanded count", "frontier peak"),
    ),
    "lrta_star": AlgorithmContract(
        name="lrta_star",
        input_spec="grid 10x10, start node, goal node",
        output_spec="PathSearchResult(path, visited_order, expanded_nodes, frontier_max_size, found)",
        managed_variables=("heuristic table (h_table)", "visited_order", "expanded count", "frontier peak"),
    ),
}

# Bản đồ ánh xạ tên thuật toán với hàm thực thi
ALGORITHMS = {
    "bfs": bfs,
    "dfs": dfs,
    "a_star": a_star,
    "greedy": greedy,
    "ucs": ucs,
    "bidirectional": bidirectional,
    "ida_star": ida_star,
    "lrta_star": lrta_star,
}


def is_valid_path(grid, path) -> bool:
    """Kiểm tra xem một đường đi có hợp lệ trên lưới hay không."""
    if not path:
        return False

    # Phải bắt đầu bằng Start và kết thúc bằng Goal
    if path[0] != START_NODE or path[-1] != GOAL_NODE:
        return False

    # Các bước đi phải liên tiếp nhau và không được đi xuyên tường
    for current, nxt in zip(path, path[1:]):
        row_distance = abs(current[0] - nxt[0])
        col_distance = abs(current[1] - nxt[1])

        # Chỉ cho phép đi ngang dọc (tổng khoảng cách dòng và cột bằng 1)
        if row_distance + col_distance != 1:
            return False

        # Không được đi vào ô tường (giá trị 1)
        if grid[nxt[0]][nxt[1]] == 1:
            return False

    return True


def run_algorithm(name: str) -> PathSearchResult:
    """Chạy một thuật toán cụ thể bằng tên của nó."""
    algorithm = ALGORITHMS[name]
    return algorithm(FIXED_GRID, START_NODE, GOAL_NODE)


def test_contract_registry_matches_available_algorithms() -> None:
    """Kiểm tra: Danh sách hợp đồng phải khớp với danh sách thuật toán hiện có."""
    assert set(ALGORITHM_CONTRACTS) == set(ALGORITHMS)


def test_bfs_finds_shortest_path_on_fixed_map() -> None:
    """Kiểm tra: BFS phải tìm thấy đường đi và đường đi đó phải hợp lệ."""
    result = run_algorithm("bfs")
    assert result.found is True
    assert is_valid_path(FIXED_GRID, result.path)


def test_dfs_finds_a_valid_path_on_fixed_map() -> None:
    """Kiểm tra: DFS phải tìm thấy một đường đi hợp lệ."""
    result = run_algorithm("dfs")
    assert result.found is True
    assert is_valid_path(FIXED_GRID, result.path)


def test_a_star_matches_bfs_path_length() -> None:
    """Kiểm tra: A* phải tìm ra đường đi hợp lệ và có độ dài tối ưu tương đương BFS."""
    bfs_result = run_algorithm("bfs")
    a_star_result = run_algorithm("a_star")
    assert a_star_result.found is True
    assert is_valid_path(FIXED_GRID, a_star_result.path)
    assert len(a_star_result.path) == len(bfs_result.path)

def test_greedy_returns_a_valid_route_if_it_finds_one() -> None:
    """Kiểm tra: Nếu Greedy tìm thấy đường, đường đó bắt buộc phải hợp lệ."""
    result = run_algorithm("greedy")
    if result.found:
        assert is_valid_path(FIXED_GRID, result.path)

def test_ucs_finds_shortest_path_on_fixed_map() -> None:
    """Kiểm tra: UCS phải tìm thấy đường đi hợp lệ và có độ dài tối ưu tương đương BFS."""
    bfs_result = run_algorithm("bfs")
    ucs_result = run_algorithm("ucs")
    assert ucs_result.found is True
    assert is_valid_path(FIXED_GRID, ucs_result.path)
    assert len(ucs_result.path) == len(bfs_result.path)

def test_bidirectional_finds_a_valid_path_on_fixed_map() -> None:
    """Kiểm tra: Bidirectional Search phải tìm thấy một đường đi hợp lệ."""
    result = run_algorithm("bidirectional")
    assert result.found is True
    assert is_valid_path(FIXED_GRID, result.path)

def test_ida_star_matches_bfs_path_length() -> None:
    """Kiểm tra: IDA* phải tìm ra đường đi hợp lệ và có độ dài tối ưu tương đương BFS."""
    bfs_result = run_algorithm("bfs")
    ida_result = run_algorithm("ida_star")
    assert ida_result.found is True
    assert is_valid_path(FIXED_GRID, ida_result.path)
    assert len(ida_result.path) == len(bfs_result.path)
def test_lrta_star_finds_valid_path() -> None:
    """
    Kiểm tra: LRTA* phải tìm được đích đến và đường đi phải tuân thủ luật lưới (không đi xuyên tường).
    Lưu ý: Không so sánh độ dài với BFS vì bản chất LRTA* có thể đi đường vòng vèo 
    trong lần chạy đầu tiên để học Heuristic (exploration).
    """
    result = run_algorithm("lrta_star")
    
    # Kiểm tra xem có tìm thấy đường hay không
    assert result.found is True
    
    # Kiểm tra xem đường đi có hợp lệ (không đứt quãng, không đi xuyên tường) hay không
    assert is_valid_path(FIXED_GRID, result.path)