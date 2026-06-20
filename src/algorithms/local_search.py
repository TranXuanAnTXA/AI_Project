"""Local search algorithms."""


"""Local search and evolutionary algorithms."""
import math
import random
from utils.node import Node

# ==========================================
# 1. HILL CLIMBING (Leo Đồi / Tử Thủ)
# Đặc điểm: Chỉ nhìn các ô xung quanh, nhảy vào ô an toàn nhất. 
# Nhược điểm: Dễ bị kẹt ở "đỉnh cục bộ" (chỗ an toàn giả).
# ==========================================
class HillClimbing:
    def find_path(self, start_node, game_map):
        current_node = start_node

        while True:
            # Lấy danh sách các ô láng giềng
            neighbors = game_map.get_neighbors(current_node)
            if not neighbors:
                break

            best_neighbor = None
            # Khởi tạo mức an toàn bằng với ô đang đứng
            max_safety = game_map.get_safety_score(current_node)

            # Quét xung quanh để tìm ô có chỉ số phòng thủ (safety) cao nhất
            for neighbor in neighbors:
                safety = game_map.get_safety_score(neighbor)
                
                # Nếu tìm thấy ô an toàn hơn ô hiện tại
                if safety > max_safety:
                    max_safety = safety
                    best_neighbor = neighbor

            # Nếu không có ô nào xung quanh an toàn hơn -> Đã đến "đỉnh đồi"
            if best_neighbor is None:
                break # Kẹt ở đỉnh cục bộ, quyết định tử thủ tại đây!

            # Di chuyển sang ô an toàn hơn
            best_neighbor.parent = current_node
            current_node = best_neighbor

        return current_node # Trả về điểm tử thủ cuối cùng


# ==========================================
# 2. SIMULATED ANNEALING (Luyện Kim / Lối Đi Hỗn Loạn)
# Đặc điểm: Khắc tinh của bẫy rập. Đầu game đi lung tung liều mạng (Nhiệt độ cao), 
# cuối game mới chốt vị trí phòng thủ (Nhiệt độ thấp).
# ==========================================
class SimulatedAnnealing:
    def find_path(self, start_node, game_map):
        current_node = start_node
        temperature = 1000.0   # Nhiệt độ khởi điểm (Độ "điên" của thuật toán)
        cooling_rate = 0.95    # Tốc độ nguội dần mỗi lượt (95%)
        min_temperature = 1.0  # Ngưỡng dừng

        while temperature > min_temperature:
            neighbors = game_map.get_neighbors(current_node)
            if not neighbors:
                break

            # Bốc ĐẠI một ô láng giềng thay vì tìm ô tốt nhất
            next_node = random.choice(neighbors)
            
            current_safety = game_map.get_safety_score(current_node)
            next_safety = game_map.get_safety_score(next_node)
            
            # Tính độ chênh lệch an toàn
            delta = next_safety - current_safety

            # TH1: Ô tiếp theo an toàn hơn -> Nhảy vào luôn!
            if delta > 0:
                next_node.parent = current_node
                current_node = next_node
            
            # TH2: Ô tiếp theo NGUY HIỂM HƠN -> Tung xúc xắc liều mạng
            else:
                # delta âm, nên (delta/temp) sẽ âm. math.exp(âm) ra xác suất từ 0.0 -> 1.0
                # Nhiệt độ càng cao -> Xác suất liều mạng đâm vào chỗ chết càng lớn
                acceptance_probability = math.exp(delta / temperature)
                
                if random.random() < acceptance_probability:
                    next_node.parent = current_node
                    current_node = next_node # Chấp nhận đi lùi / đi vào bẫy
            
            # Giảm nhiệt độ (Agent bớt "điên" dần)
            temperature *= cooling_rate

        return current_node


# ==========================================
# 3. GENETIC ALGORITHM (Thuật Toán Di Truyền)
# Đặc điểm: Tung ra bầy mini-bots (Chuỗi gen). Cá thể nào đi xa + nhiều máu thì giữ lại, 
# cho lai ghép để sinh ra thế hệ tiếp theo thông minh hơn.
# ==========================================
class GeneticAlgorithm:
    def find_path(self, start_node, target_node, game_map):
        population_size = 50   # Số lượng mini-bots trong 1 thế hệ
        generations = 100      # Số đời tiến hóa
        mutation_rate = 0.1    # Tỉ lệ đột biến gen (10%)
        dna_length = 30        # Mỗi bot được đi tối đa 30 bước

        # 1. Khởi tạo quần thể ban đầu (Ngẫu nhiên)
        population = self.init_population(population_size, dna_length)

        for gen in range(generations):
            # 2. Chấm điểm Fitness (Độ thích nghi) cho từng con bot
            scored_population = []
            for dna in population:
                fitness = self.calculate_fitness(dna, start_node, target_node, game_map)
                scored_population.append((fitness, dna))
            
            # Sắp xếp từ giỏi nhất đến kém nhất
            scored_population.sort(key=lambda x: x[0], reverse=True)
            
            best_dna = scored_population[0][1]
            
            # Nếu con giỏi nhất đã chạm đích -> Dừng tiến hóa
            if self.is_target_reached(best_dna, start_node, target_node, game_map):
                return self.decode_dna_to_path(best_dna, start_node, game_map)

            # 3. Chọn lọc tự nhiên (Elitism): Giữ lại 20% con tinh anh nhất
            elite_count = int(population_size * 0.2)
            elites = [item[1] for item in scored_population[:elite_count]]

            # 4. Lai ghép & Đột biến sinh ra thế hệ mới
            new_population = elites[:] # Đưa các con tinh anh thẳng vào thế hệ sau
            while len(new_population) < population_size:
                parent1 = random.choice(elites)
                parent2 = random.choice(elites)
                child = self.crossover(parent1, parent2)
                child = self.mutate(child, mutation_rate)
                new_population.append(child)

            population = new_population

        # Trả về đường đi của cá thể giỏi nhất sau 100 vòng tiến hóa
        best_overall_dna = population[0]
        return self.decode_dna_to_path(best_overall_dna, start_node, game_map)

    # --- CÁC HÀM HỖ TRỢ CHO DI TRUYỀN (HELPER FUNCTIONS) ---
    
    def init_population(self, size, length):
        # DNA là một chuỗi các lệnh di chuyển: ['UP', 'DOWN', 'LEFT', 'RIGHT']
        directions = [(0, 1), (0, -1), (-1, 0), (1, 0)]
        return [[random.choice(directions) for _ in range(length)] for _ in range(size)]

    def calculate_fitness(self, dna, start_node, target_node, game_map):
        # Mô phỏng cho bot chạy theo DNA. Tính điểm dựa trên: Càng gần đích + Càng ít mất máu = Điểm càng cao
        current_x, current_y = start_node.x, start_node.y
        hp = 100

        for move_x, move_y in dna:
            next_x, next_y = current_x + move_x, current_y + move_y
            # Nếu đụng tường -> Trừ nặng điểm (Penalty)
            if not game_map.is_walkable(next_x, next_y):
                hp -= 10
                continue # Đứng im
            
            current_x, current_y = next_x, next_y
            # Có thể trừ thêm HP nếu giẫm trúng bẫy: hp -= game_map.get_trap_damage(current_x, current_y)

        # Công thức Fitness = HP còn lại + Phần thưởng dựa trên khoảng cách đến đích
        distance_to_target = abs(current_x - target_node.x) + abs(current_y - target_node.y)
        fitness = hp + (1000 / (distance_to_target + 1)) 
        return fitness

    def crossover(self, parent1, parent2):
        # Cắt đôi gen của bố và mẹ để ghép lại (Single-point crossover)
        mid = len(parent1) // 2
        return parent1[:mid] + parent2[mid:]

    def mutate(self, dna, rate):
        directions = [(0, 1), (0, -1), (-1, 0), (1, 0)]
        mutated_dna = []
        for gene in dna:
            if random.random() < rate:
                mutated_dna.append(random.choice(directions)) # Đột biến rẽ hướng khác
            else:
                mutated_dna.append(gene)
        return mutated_dna

    def is_target_reached(self, dna, start_node, target_node, game_map):
        # Logic mô phỏng tương tự tính fitness, check xem (current_x, current_y) == target hay không
        return False # (Giản lược để tập trung cấu trúc thuật toán)

    def decode_dna_to_path(self, dna, start_node, game_map):
        # Hàm này sẽ chạy chuỗi gen chiến thắng và trả về Node cuối cùng với tập hợp `.parent` hoàn chỉnh
        # để View có thể vẽ lại đường đi.
        return start_node 


# ==========================================
# HÀM BỌC (WRAPPER FUNCTIONS)
# ==========================================

def hill_climbing(start_node, game_map, *args, **kwargs):
    """ Hàm bọc gọi thuật toán Hill Climbing. """
    solver = HillClimbing()
    return solver.find_path(start_node, game_map)

def simulated_annealing(start_node, game_map, *args, **kwargs):
    """ Hàm bọc gọi thuật toán Simulated Annealing. """
    solver = SimulatedAnnealing()
    return solver.find_path(start_node, game_map)

def genetic_algorithm(start_node, target_node, game_map, *args, **kwargs):
    """ Hàm bọc gọi thuật toán Genetic Algorithm. Yêu cầu thêm tham số target_node. """
    solver = GeneticAlgorithm()
    return solver.find_path(start_node, target_node, game_map)