"""
📄 src/core/game_rules/hazard_manager.py
* Vai trò: Quản lý logic va chạm bẫy, trượt băng, trừ thể lực.
* Cập nhật: Thêm Hồi sinh bẫy tử thần (Nhớ bẫy, tự tính lại đường, hiệu ứng chết lâm sàng 2s).
"""
import random

class HazardManager:
    @staticmethod
    def process_hero_tile(scene, pos):
        grid = scene.game_map.grid
        cell_val = grid[pos[1]][pos[0]]
        rows, cols = len(grid), len(grid[0])

        # 1. BẪY TỬ THẦN (99) - CƠ CHẾ HỒI SINH
        if cell_val == 99:
            # Chỉ hồi sinh nếu còn lượt (trap_resurrects được định nghĩa bên main.py)
            if getattr(scene, 'trap_resurrects', 0) > 0:
                scene.trap_resurrects -= 1
                print(f"🔥 KÍCH HOẠT HỒI SINH TẠI CHỖ! (Còn {scene.trap_resurrects} lần)")

                # [QUAN TRỌNG]: Đánh dấu bẫy này thành "Tường" (1) trên lưới logic
                # Để lần sau thuật toán tính đường sẽ tự động né nó ra!
                grid[pos[1]][pos[0]] = 1

                # 1. Bắn hạt màu đỏ/đen tại ô bẫy để báo hiệu bị dính sát thương chí mạng
                if hasattr(scene.renderer, 'spawn_particles'):
                    scene.renderer.spawn_particles(pos[0], pos[1], (255, 50, 50))

                # 2. Bắn hạt màu vàng ở ô an toàn trước để báo trước vị trí sẽ hồi sinh
                if hasattr(scene.renderer, 'spawn_particles'):
                    scene.renderer.spawn_particles(scene.hero_last_pos[0], scene.hero_last_pos[1], (255, 200, 50))

                # 3. Bắt đầu quá trình chết lâm sàng 2 giây (delay=2.0)
                # Hàm trigger_resurrect đã được thêm bên class Agent (agent.py)
                scene.hero.trigger_resurrect(scene.hero_last_pos, delay=2.0)

                return False # Trả về False để hero_last_pos không bị cập nhật vào bẫy
            else:
                # Nếu hết lượt hồi sinh -> Chết thật
                scene.hero.die()
                scene.phase_manager.trigger_death("MẮC BẪY TỬ THẦN! HẾT LƯỢT HỒI SINH.", is_boss_win=(scene.phase_manager.current_phase == "BOSS"))
                return False

        # 2. Cộng Cost (Thể lực) - Chỉ cộng nếu không phải Sương Mù (4)
        if cell_val != 4:
            cost = 5.0 if cell_val == 5 else (3.0 if cell_val == 3 else 1.0)
            scene.hero_current_cost += cost

            if scene.hero_current_cost > scene.level_manager.get_current_config().get("max_cost", 9999):
                scene.hero.die()
                scene.phase_manager.trigger_death("KIỆT SỨC!", is_boss_win=(scene.phase_manager.current_phase == "BOSS"))
                return False

        # 3. Trượt Băng (3) - 30% tỷ lệ
        if cell_val == 3 and not getattr(scene.hero, 'is_slipping', False):
            if random.random() < 0.30:
                valid_neighbors = []
                for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                    nx, ny = pos[0] + dx, pos[1] + dy
                    # Kiểm tra biên an toàn (chống crash game khi ở lề)
                    if 0 <= ny < rows and 0 <= nx < cols:
                        if grid[ny][nx] != 1:
                            valid_neighbors.append((nx, ny))

                if valid_neighbors:
                    slip_target = random.choice(valid_neighbors)
                    scene.hero.trigger_slip(slip_target)
                    if hasattr(scene.renderer, 'spawn_particles'):
                        scene.renderer.spawn_particles(pos[0], pos[1], (173, 216, 230))

        return True