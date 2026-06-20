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
class BacktrackingCSP:
    def find_solution(self, csp):
        # Bắt đầu với một bảng mã trống (chưa điền ô nào)
        return self.backtrack({}, csp)

    def backtrack(self, assignment, csp):
        # Nếu đã điền đủ tất cả các ô -> Mở khóa thành công!
        if len(assignment) == len(csp.variables):
            return assignment

        # 1. Heuristic MRV & Degree: Chọn ô khó nhằn nhất để giải quyết trước
        var = self.select_unassigned_variable(assignment, csp)

        # 2. Heuristic LCV: Chọn màu nào ít gây khó dễ cho hàng xóm nhất
        for value in self.order_domain_values(var, assignment, csp):
            if csp.is_consistent(var, value, assignment):
                assignment[var] = value # Thử điền màu này
                
                # Đi tiếp sâu xuống các ô còn lại
                result = self.backtrack(assignment, csp)
                if result is not None:
                    return result
                
                # BACKTRACK: Nếu đi tiếp thất bại, rút màu ra thử màu khác
                del assignment[var] 
                
        return None # Thất bại

    def select_unassigned_variable(self, assignment, csp):
        """ 
        MRV (Minimum Remaining Values): Chọn ô còn ít màu để thử nhất.
        Nếu hòa, dùng Degree Heuristic: Chọn ô có nhiều hàng xóm chưa điền nhất.
        """
        unassigned = [v for v in csp.variables if v not in assignment]
        
        def mrv_degree_key(var):
            # Số màu còn hợp lệ (MRV)
            valid_values = sum(1 for val in csp.domains[var] if csp.is_consistent(var, val, assignment))
            # Số hàng xóm chưa điền (Degree - Đảo dấu âm để sort ưu tiên số lớn)
            unassigned_neighbors = -sum(1 for n in csp.neighbors[var] if n not in assignment)
            return (valid_values, unassigned_neighbors)

        # Trả về biến có giá trị (MRV nhỏ nhất, Degree lớn nhất)
        return min(unassigned, key=mrv_degree_key)

    def order_domain_values(self, var, assignment, csp):
        """
        LCV (Least Constraining Value): Sắp xếp các màu. 
        Màu nào ít làm mất đi sự lựa chọn của hàng xóm sẽ được thử trước.
        """
        def count_conflicts(value):
            conflicts = 0
            for neighbor in csp.neighbors[var]:
                if neighbor not in assignment and value in csp.domains[neighbor]:
                    conflicts += 1
            return conflicts

        # Lọc các màu hợp lệ và sắp xếp theo số lượng xung đột từ thấp đến cao
        valid_values = [val for val in csp.domains[var] if csp.is_consistent(var, val, assignment)]
        return sorted(valid_values, key=count_conflicts)


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

def backtracking_search(csp, *args, **kwargs):
    solver = BacktrackingCSP()
    return solver.find_solution(csp)

def ac3_preprocess(csp, *args, **kwargs):
    solver = AC3()
    return solver.preprocess(csp)

def min_conflicts_search(csp, *args, **kwargs):
    solver = MinConflicts()
    return solver.find_solution(csp)