"""
📄 File: src/core/grid_map/map_loader.py
* Vai trò: Tách biệt hoàn toàn logic đọc file TMX bằng XML thuần.
* Tính năng:
  - Tự động quét mọi Layer (Floor, Structure, Foreground,...) giữ nguyên Z-Index.
  - Tự động bóc tách tọa độ từ ObjectGroup (Start, Goal).
"""
import xml.etree.ElementTree as ET

class MapLoader:
    def __init__(self, tmx_filepath: str):
        self.tmx_filepath = tmx_filepath

        # --- CÁC BIẾN LƯU TRỮ CHÍNH ---
        self.layers_data = {}   # Dictionary: { "Tên Layer": [[Mảng 2D]] }
        self.layer_names = []   # List: Lưu thứ tự quét từ trên xuống (Z-Index)
        self.objects = []       # List: Lưu các dictionary chứa thông tin Object

        try:
            tree = ET.parse(self.tmx_filepath)
            self.root = tree.getroot()

            self.raw_width = int(self.root.attrib.get('width', 30))
            self.raw_height = int(self.root.attrib.get('height', 30))
            self.tile_size = int(self.root.attrib.get('tilewidth', 16))

            # Khởi chạy các bộ quét tự động
            self._parse_all_layers()
            self._parse_objects()

            print(f"✅ Đã đọc XML map TMX: {self.tmx_filepath} ({self.raw_width}x{self.raw_height})")

        except Exception as e:
            print(f"❌ Lỗi nạp map TMX: {e}")
            self.root = None
            self.raw_width, self.raw_height, self.tile_size = 30, 30, 16

    def _parse_all_layers(self):
        """Quét tự động mọi thẻ <layer> để lấy dữ liệu ma trận (Auto-Discovery)."""
        if self.root is None: return

        for layer in self.root.findall('layer'):
            name = layer.attrib.get('name')
            if not name: continue

            grid = [[0 for _ in range(self.raw_width)] for _ in range(self.raw_height)]
            data_node = layer.find('data')

            if data_node is not None and data_node.text is not None:
                csv_text = data_node.text.strip()
                lines = [line.strip() for line in csv_text.split('\n') if line.strip()]

                for y, line in enumerate(lines):
                    if y >= self.raw_height: break
                    clean_line = line.rstrip(',')
                    values = clean_line.split(',')

                    for x, val in enumerate(values):
                        if x >= self.raw_width: break
                        grid[y][x] = int(val)

            # Lưu vào bộ nhớ và ghi nhận Z-Index
            self.layers_data[name] = grid
            self.layer_names.append(name)

    def _parse_objects(self):
        """Quét thẻ <objectgroup> để trích xuất tọa độ sinh Point (Start, Goal)."""
        if self.root is None: return

        for obj_group in self.root.findall('objectgroup'):
            for obj in obj_group.findall('object'):
                obj_data = {
                    "name": obj.attrib.get('name', 'Unknown'),
                    # Ép kiểu float vì tọa độ Tiled có thể mang số thập phân
                    "x": float(obj.attrib.get('x', 0)),
                    "y": float(obj.attrib.get('y', 0))
                }
                self.objects.append(obj_data)

    def get_layer(self, name: str) -> list:
        """Hàm Getter an toàn để lấy ma trận của một layer cụ thể."""
        return self.layers_data.get(name, None)


if __name__ == "__main__":
    # ---------------------------------------------------------
    # HÀM MAIN TEST ĐỘC LẬP: KIỂM TRA CHỨC NĂNG MỚI
    # ---------------------------------------------------------
    import os

    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
    test_tmx_path = os.path.join(project_root, "assets", "maps", "dungeon_map_1.tmx")

    print(f"🔍 Đang tìm file TMX tại: {test_tmx_path}\n" + "-"*40)

    if os.path.exists(test_tmx_path):
        loader = MapLoader(test_tmx_path)

        print("\n1. THÔNG SỐ CƠ BẢN")
        print(f"- Kích thước: {loader.raw_width}x{loader.raw_height} | Cỡ tile: {loader.tile_size}px")

        print("\n2. KIỂM TRA Z-INDEX & TỰ ĐỘNG QUÉT LAYER")
        print(f"- Tổng số lớp tìm thấy: {len(loader.layer_names)}")
        print(f"- Thứ tự quét (Sẽ vẽ từ trái qua phải): {loader.layer_names}")

        if "Foreground" in loader.layer_names:
            print("  -> ✅ Lớp 'Foreground' đã được nhận diện thành công!")

        print("\n3. KIỂM TRA OBJECT (Start / Goal)")
        if loader.objects:
            for i, obj in enumerate(loader.objects):
                print(f"- Object {i+1}: {obj['name']} | Tọa độ Pixel (X: {obj['x']}, Y: {obj['y']})")
        else:
            print("- ⚠️ Không tìm thấy Object nào!")

        print("\n4. TRÍCH XUẤT DỮ LIỆU THỬ NGHIỆM (Layer Structure - Góc 5x5)")
        struct_grid = loader.get_layer("Structure")
        if struct_grid:
            for y in range(5):
                print(struct_grid[y][:5])
    else:
        print(f"❌ Không tìm thấy file TMX để test!")