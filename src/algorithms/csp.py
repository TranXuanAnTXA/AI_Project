"""Constraint Satisfaction Problem (CSP) algorithms for minigames."""
import random

# ==========================================
# Cấu trúc dữ liệu đại diện cho bài toán Giải mã (CSP)
# ==========================================
class CSP:
    def __init__(self, variables, domains, neighbors):
        """
        variables: Danh sách các ô năng lượng (VD: ['A', 'B', 'C'])
        domains: Từ điển chứa các màu có thể điền vào ô (VD: {'A': ['Đỏ', 'Xanh', 'Vàng'], ...})
        neighbors: Từ điển chứa các ô kề nhau, không được trùng màu (VD: {'A': ['B', 'C'], ...})
        """
        self.variables = variables
        self.domains = domains
        self.neighbors = neighbors

    def is_consistent(self, var, value, assignment):
        """Kiểm tra xem nếu điền 'value' vào 'var' thì có bị trùng với hàng xóm không."""
        for neighbor in self.neighbors.get(var, []):
            if neighbor in assignment and assignment[neighbor] == value:
                return False
        return True


# ==========================================
# 1. BACKTRACKING SEARCH
# ==========================================
def BacktrackingCSP(grid, start, goal):
    """
    CSP Online Search: Hero trực tiếp dò đường.
    ĐÃ ÁP DỤNG FIX CỦA BOSS: 
    1. Tách biệt Explored và Current Path để UI vẽ đúng 1 đường Backtrack (Không bị loang).
    2. Đồng bộ tọa độ (Row, Col) để SimulationManager nhận chuẩn xác mà không cần sửa file core.
    """
    max_cost = getattr(grid, 'max_cost', 9999)
    max_cpu = getattr(grid, 'cpu_max', 5000)

    def get_step_cost(pos):
        return getattr(grid, 'get_cost', lambda p: 1)(pos)

    def get_step_cpu(pos):
        return getattr(grid, 'get_cpu', lambda p: 1)(pos)

    def get_neighbors(pos):
        x, y = pos
        directions = [(0, -1), (1, 0), (0, 1), (-1, 0)] # Trái, Xuống, Phải, Lên
        valid = []
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= ny < len(grid) and 0 <= nx < len(grid[0]):
                if grid[ny][nx] != 1:  # Né Tường cứng
                    valid.append((nx, ny))
        return valid

    stack = [(start, 0)] 
    
    # [TÁCH BIỆT LOGIC]: global_explored chỉ dùng để AI KHÔNG ĐI LẠI ĐƯỜNG CŨ
    # Tuyệt đối không gửi cái này cho UI vẽ!
    global_explored = set([start]) 
    
    hero_pos = start
    metrics = {'cpu': 0, 'ram': 0, 'cost': 0, 'backtracks': 0}

    # Hàm tiện ích: Gói dữ liệu và LẬT TỌA ĐỘ sang (Row, Col) cho SimulationManager
    def yield_state(target_path):
        # 1. UI CHỈ VẼ STACK HIỆN TẠI (Đường dây thừng đang đi)
        # Chuyển (X, Y) thành (Y, X) VÀ GIỮ NGUYÊN LÀ LIST (để SimulationManager.history lưu đúng thứ tự)
        current_active_path_rc = [(s[0][1], s[0][0]) for s in stack]
        
        # 2. Dịch target_path thành (Y, X)
        pygame_path_rc = [(p[1], p[0]) for p in target_path] if target_path else []
        
        # 3. current_node (Hero Pos) cũng phải là (Y, X)
        current_node_rc = (hero_pos[1], hero_pos[0])
        
        # [QUAN TRỌNG]: Đưa [] vào vị trí frontier_rc (tham số thứ 3) để tắt hoàn toàn màu vàng (tránh loang)
        return current_node_rc, current_active_path_rc, [], pygame_path_rc, metrics

    while stack:
        target_node, target_path_cost = stack[-1] 

        # -----------------------------------------------------------
        # ĐI LÙI (BACKTRACKING)
        # -----------------------------------------------------------
        if hero_pos != target_node:
            step_path = [hero_pos, target_node]
            hero_pos = target_node
            
            metrics['cost'] = target_path_cost 
            metrics['backtracks'] += 1
            metrics['cpu'] += 5
            
            yield yield_state(step_path)
            continue

        if hero_pos == goal:
            yield yield_state([hero_pos])
            break

        # -----------------------------------------------------------
        # TÌM ĐƯỜNG MỚI (CHỈ CHỌN 1 ĐƯỜNG)
        # -----------------------------------------------------------
        neighbors = get_neighbors(hero_pos)
        valid_next_step = None

        for neighbor in neighbors:
            if neighbor not in global_explored: 
                next_cost = metrics['cost'] + get_step_cost(neighbor)
                next_cpu = metrics['cpu'] + get_step_cpu(neighbor)
                
                if next_cost <= max_cost and next_cpu <= max_cpu:
                    valid_next_step = neighbor
                    break # Đi đúng 1 nhánh

        # -----------------------------------------------------------
        # THỰC THI (TIẾN LÊN HOẶC RÚT LUI)
        # -----------------------------------------------------------
        if valid_next_step:
            global_explored.add(valid_next_step)
            new_cost = metrics['cost'] + get_step_cost(valid_next_step)
            
            stack.append((valid_next_step, new_cost))
            
            step_path = [hero_pos, valid_next_step]
            hero_pos = valid_next_step
            
            metrics['cost'] = new_cost
            metrics['cpu'] += 1
            
            yield yield_state(step_path)
            
        else:
            # Ngõ cụt -> Rút nhánh khỏi Stack. Vòng lặp sau UI sẽ tự xóa màu ô này!
            stack.pop()
# ==========================================
# 2. AC-3 (Arc Consistency 3 - Lan truyền Ràng buộc)
# ==========================================
class AC3:
    def preprocess(self, csp):
        # Tạo hàng đợi chứa tất cả các "cung" (cặp ô kề nhau)
        queue = [(xi, xj) for xi in csp.variables for xj in csp.neighbors[xi]]
        
        while queue:
            xi, xj = queue.pop(0)
            
            # Nếu tập màu của xi bị thu hẹp
            if self.revise(csp, xi, xj):
                if not csp.domains[xi]:
                    return False # Bị thu hẹp đến mức ô xi không còn màu nào -> Game Over
                
                # Lan truyền ngược lại cho các hàng xóm của xi (trừ xj)
                for xk in csp.neighbors[xi]:
                    if xk != xj:
                        queue.append((xk, xi))
        return True # Xử lý thành công, domains đã được làm sạch

    def revise(self, csp, xi, xj):
        """Xóa các màu của xi nếu không có màu nào của xj tương thích với nó."""
        revised = False
        for x_value in csp.domains[xi][:]:
            # Có bất kỳ màu y nào của xj khác với màu x không?
            conflict = True
            for y_value in csp.domains[xj]:
                if x_value != y_value:
                    conflict = False
                    break
            
            if conflict:
                csp.domains[xi].remove(x_value) # Gạch bỏ màu vô lý
                revised = True
        return revised


# ==========================================
# 3. MIN-CONFLICTS
# ==========================================
class MinConflicts:
    def find_solution(self, csp, max_steps=1000):
        # BƯỚC 1: Điền bừa ngẫu nhiên toàn bộ các ô
        current_assignment = {var: random.choice(csp.domains[var]) for var in csp.variables}

        for _ in range(max_steps):
            # Tìm danh sách các ô đang bị lỗi (trùng màu với hàng xóm)
            conflicted_vars = self.get_conflicted_vars(current_assignment, csp)
            
            if not conflicted_vars:
                return current_assignment # Không còn lỗi -> Mở cửa!

            # Chọn ngẫu nhiên 1 ô đang bị lỗi
            var = random.choice(conflicted_vars)
            
            # Đổi sang màu làm giảm số lượng lỗi xuống thấp nhất
            best_value = self.minimize_conflicts_for_var(var, current_assignment, csp)
            current_assignment[var] = best_value

        return None # Thất bại sau max_steps

    def get_conflicted_vars(self, assignment, csp):
        conflicts = []
        for var in csp.variables:
            for neighbor in csp.neighbors[var]:
                if assignment[var] == assignment[neighbor]:
                    conflicts.append(var)
                    break # Chỉ cần tính biến này bị lỗi 1 lần là đủ
        return conflicts

    def minimize_conflicts_for_var(self, var, assignment, csp):
        """Tìm màu nào thay vào sẽ ít bị trùng với hàng xóm nhất"""
        best_val = assignment[var]
        min_conflicts = float('inf')

        for value in csp.domains[var]:
            conflicts = 0
            for neighbor in csp.neighbors[var]:
                if assignment[neighbor] == value:
                    conflicts += 1
            
            if conflicts < min_conflicts:
                min_conflicts = conflicts
                best_val = value

        return best_val


# ==========================================
# HÀM BỌC (WRAPPER FUNCTIONS)
# ==========================================

# 1. Hàm dành cho Hệ thống Tìm đường (Pathfinding / Walker)
def csp_backtracking(grid, start, goal):
    """Đổi tên lại để file algorithm_registry.py có thể gọi đúng tên"""
    return BacktrackingCSP(grid, start, goal)

# 2. Các hàm dành cho Hệ thống Minigame (Giải mã màu sắc/Sudoku)
def ac3_preprocess(csp, *args, **kwargs):
    solver = AC3()
    return solver.preprocess(csp)

def min_conflicts_search(csp, *args, **kwargs):
    solver = MinConflicts()
    return solver.find_solution(csp)