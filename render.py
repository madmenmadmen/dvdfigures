 # render.py
import math
from config import *

CUSTOM_MODELS = {}

def rotate_vertex(v, angle_x, angle_y, angle_z):
    """Вращение вершины в 3D пространстве"""
    # Вращение вокруг оси X
    y1 = v[1] * math.cos(angle_x) - v[2] * math.sin(angle_x)
    z1 = v[1] * math.sin(angle_x) + v[2] * math.cos(angle_x)
    
    # Вращение вокруг оси Y
    x2 = v[0] * math.cos(angle_y) - z1 * math.sin(angle_y)
    z2 = v[0] * math.sin(angle_y) + z1 * math.cos(angle_y)
    
    # Вращение вокруг оси Z
    x3 = x2 * math.cos(angle_z) - y1 * math.sin(angle_z)
    y3 = x2 * math.sin(angle_z) + y1 * math.cos(angle_z)
    
    return [x3, y3, z2]

def project_vertex(v, pos):
    """Проекция 3D вершины на 2D плоскость"""
    factor = RENDER_SCALE / (v[2] + CAMERA_DISTANCE)
    x2d = v[0] * factor + pos[0]
    y2d = v[1] * factor + pos[1]
    return [x2d, y2d]
    
def create_stick():
    """Создает палку (вытянутый куб)"""
    length = 4.0    # Длина палки
    width = 0.4     # Ширина/толщина
    height = 0.4    # Высота
    
    l = length / 2
    w = width / 2
    h = height / 2
    
    # Вершины палки
    vertices = [
        # Задний конец (отрицательный X)
        [-l, -w, -h],  # 0: задний-нижний-левый
        [-l, -w,  h],  # 1: задний-нижний-правый
        [-l,  w,  h],  # 2: задний-верхний-правый
        [-l,  w, -h],  # 3: задний-верхний-левый
        
        # Передний конец (положительный X)
        [ l, -w, -h],  # 4: передний-нижний-левый
        [ l, -w,  h],  # 5: передний-нижний-правый
        [ l,  w,  h],  # 6: передний-верхний-правый
        [ l,  w, -h],  # 7: передний-верхний-левый
    ]
    
    # Грани (6 граней как у куба)
    faces = [
        [0, 1, 2, 3],  # Задний торец
        [4, 5, 6, 7],  # Передний торец
        [0, 1, 5, 4],  # Нижняя грань
        [2, 3, 7, 6],  # Верхняя грань
        [0, 3, 7, 4],  # Левая боковая
        [1, 2, 6, 5]   # Правая боковая
    ]
    
    return vertices, faces
    
import os
import json

def load_model_from_file(model_name):
    """Загружает модель из файла"""
    # Ищем файл в папке models
    models_dir = "models"
    
    # Пробуем разные расширения
    possible_files = [
        f"{model_name}.json",
        f"{model_name}.obj",
        f"{model_name}.txt",
        f"{model_name}.model"
    ]
    
    for filename in possible_files:
        filepath = os.path.join(models_dir, filename)
        if os.path.exists(filepath):
            print(f"📁 Найден файл модели: {filename}")
            
            if filename.endswith('.json'):
                return load_json_model(model_name)
            elif filename.endswith('.obj'):
                return load_obj_model(filepath)
            elif filename.endswith('.txt'):
                return load_txt_model(filepath)
    
    print(f"❌ Файл модели {model_name} не найден")
    return [], []

def load_json_model(model_name):
    """Загружает JSON модель из конструктора"""
    try:
        models_dir = "models"
        filepath = os.path.join(models_dir, f"{model_name}.json")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        all_vertices = []
        all_faces = []
        vertex_offset = 0
        
        for prim_data in data:
            vertices = prim_data.get("vertices", [])
            faces = prim_data.get("faces", [])
            
            # Применяем трансформации
            x = prim_data.get("x", 0)
            y = prim_data.get("y", 0)
            z = prim_data.get("z", 0)
            rx = prim_data.get("rx", 0)
            ry = prim_data.get("ry", 0)
            rz = prim_data.get("rz", 0)
            scale = prim_data.get("scale", 1.0)
            
            # Преобразуем вершины
            transformed = []
            for v in vertices:
                vx, vy, vz = v
                
                # Масштаб
                vx *= scale
                vy *= scale
                vz *= scale
                
                # Вращение
                vy, vz = (vy * math.cos(rx) - vz * math.sin(rx),
                         vy * math.sin(rx) + vz * math.cos(rx))
                vx, vz = (vx * math.cos(ry) - vz * math.sin(ry),
                         vx * math.sin(ry) + vz * math.cos(ry))
                vx, vy = (vx * math.cos(rz) - vy * math.sin(rz),
                         vx * math.sin(rz) + vy * math.cos(rz))
                
                # Позиция
                vx += x
                vy += y
                vz += z
                
                transformed.append([vx, vy, vz])
            
            # Добавляем вершины
            all_vertices.extend(transformed)
            
            # Корректируем индексы граней
            for face in faces:
                adjusted_face = [idx + vertex_offset for idx in face]
                all_faces.append(adjusted_face)
            
            vertex_offset += len(vertices)
        
        print(f"✅ JSON модель загружена: {model_name} ({len(all_vertices)} вершин, {len(all_faces)} граней)")
        return all_vertices, all_faces
        
    except Exception as e:
        print(f"❌ Ошибка загрузки JSON модели {model_name}: {e}")
        return [], []

def load_obj_model(filepath):
    """Загружает OBJ модель"""
    try:
        vertices = []
        faces = []
        
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if line.startswith('v '):
                    parts = line.split()
                    if len(parts) >= 4:
                        x = float(parts[1])
                        y = float(parts[2])
                        z = float(parts[3])
                        vertices.append([x, y, z])
                        
                elif line.startswith('f '):
                    face_vertices = []
                    parts = line.split()
                    for part in parts[1:]:
                        vertex_idx = part.split('/')[0]
                        if vertex_idx:
                            face_vertices.append(int(vertex_idx) - 1)  # OBJ индексы с 1
                    
                    if face_vertices:
                        faces.append(face_vertices)
        
        print(f"✅ OBJ модель загружена: {os.path.basename(filepath)} ({len(vertices)} вершин, {len(faces)} граней)")
        return vertices, faces
        
    except Exception as e:
        print(f"❌ Ошибка загрузки OBJ {filepath}: {e}")
        return [], []

def load_txt_model(filepath):
    """Загружает простой текстовый формат модели"""
    try:
        vertices = []
        faces = []
        section = None
        
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                if line == "VERTICES":
                    section = "vertices"
                    continue
                elif line == "FACES":
                    section = "faces"
                    continue
                
                if section == "vertices":
                    parts = line.split()
                    if len(parts) >= 3:
                        x = float(parts[0])
                        y = float(parts[1])
                        z = float(parts[2])
                        vertices.append([x, y, z])
                
                elif section == "faces":
                    parts = line.split()
                    if parts:
                        face = [int(p) for p in parts]
                        faces.append(face)
        
        print(f"✅ TXT модель загружена: {os.path.basename(filepath)} ({len(vertices)} вершин, {len(faces)} граней)")
        return vertices, faces
        
    except Exception as e:
        print(f"❌ Ошибка загрузки TXT {filepath}: {e}")
        return [], []
        
def add_custom_model_from_file(filename):
    """Загружает модель из файла и добавляет в систему"""
    model_name = os.path.splitext(filename)[0]
    custom_id = f"model_{model_name}"
    
    if custom_id in SHAPES:
        print(f"⚠️ Модель {model_name} уже загружена")
        return custom_id
    
    # Загружаем модель
    vertices, faces = load_model_from_file(model_name)
    
    if vertices and faces:
        # Добавляем в кэш
        CUSTOM_MODELS[custom_id] = (vertices, faces)
        
        # Добавляем в SHAPES если еще нет
        if custom_id not in SHAPES:
            SHAPES.append(custom_id)
            SHAPE_NAMES.append(f"МОДЕЛЬ: {model_name}")
            print(f"✅ Модель добавлена как фигура #{len(SHAPES)-1}")
        
        return custom_id
    
    return None

def create_vertices_and_faces(shape_type, **params):
    """Создание вершин и граней для различных фигур"""
    vertices = []
    faces = []
    
    """Создание вершин и граней для различных фигур"""
    # Проверяем, это кастомная модель?
    if shape_type.startswith("custom_"):
        if shape_type in CUSTOM_MODELS:
            return CUSTOM_MODELS[shape_type]
        else:
            print(f"⚠️ Кастомная модель {shape_type} не найдена, используем куб")
            return create_vertices_and_faces("cube")
    
    # Проверяем, это загруженная модель?
    if shape_type.startswith("model_"):
        model_name = shape_type[6:]  # Убираем "model_"
        return load_model_from_file(model_name)
    
    if shape_type == "stick":
    	return create_stick()

    elif shape_type == 'dodecahedron':

        # Додекаэдр с триангуляцией — 36 треугольников

        φ = (1 + math.sqrt(5)) / 2  # 1.618...

        vertices = [

            # 0–7: (±1, ±1, ±1)

            [-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],

            [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1],

            # 8–11: (0, ±1/φ, ±φ)

            [0, -1 / φ, -φ], [0, 1 / φ, -φ], [0, -1 / φ, φ], [0, 1 / φ, φ],

            # 12–15: (±1/φ, ±φ, 0)

            [-1 / φ, -φ, 0], [1 / φ, -φ, 0], [-1 / φ, φ, 0], [1 / φ, φ, 0],

            # 16–19: (±φ, 0, ±1/φ)

            [-φ, 0, -1 / φ], [φ, 0, -1 / φ], [-φ, 0, 1 / φ], [φ, 0, 1 / φ]

        ]

        # ИСХОДНЫЕ ПЯТИУГОЛЬНИКИ (12 штук)

        pentagons = [

            [0, 8, 9, 2, 3],

            [0, 3, 14, 7, 4],

            [0, 4, 10, 11, 8],

            [1, 5, 7, 14, 12],

            [1, 12, 13, 6, 2],

            [1, 2, 9, 16, 17],

            [4, 7, 15, 11, 10],

            [5, 6, 13, 19, 18],

            [5, 18, 19, 17, 7],

            [6, 15, 14, 3, 2],

            [8, 11, 15, 6, 9],

            [16, 9, 6, 17, 19]

        ]

        # ТРИАНГУЛЯЦИЯ

        faces = []

        for pent in pentagons:
            # Берём первые 3 вершины как первый треугольник

            faces.append([pent[0], pent[1], pent[2]])

            # Второй треугольник

            faces.append([pent[0], pent[2], pent[3]])

            # Третий треугольник

            faces.append([pent[0], pent[3], pent[4]])

        return vertices, faces
    
    if shape_type == 'cube':
        vertices = CUBE_VERTICES.copy()
        faces = CUBE_FACES.copy()
        
    elif shape_type == 'sphere':
        segments = params.get('segments', SPHERE_SEGMENTS)
        rings = params.get('rings', SPHERE_RINGS)
        
        for i in range(rings + 1):
            phi = math.pi * i / rings
            for j in range(segments + 1):
                theta = 2 * math.pi * j / segments
                x = math.sin(phi) * math.cos(theta)
                y = math.cos(phi)
                z = math.sin(phi) * math.sin(theta)
                vertices.append([x, y, z])
        
        for i in range(rings):
            for j in range(segments):
                a = i * (segments + 1) + j
                b = a + segments + 1
                c = a + 1
                d = b + 1
                faces.append([a, b, c])
                faces.append([c, b, d])
                
    elif shape_type == 'cone':
        segments = params.get('segments', CONE_SEGMENTS)
        
        vertices.append([0, 1.5, 0])
        for i in range(segments):
            theta = 2 * math.pi * i / segments
            x = math.cos(theta)
            z = math.sin(theta)
            vertices.append([x, -1, z])
        
        for i in range(segments):
            next_i = (i + 1) % segments
            faces.append([0, i + 1, next_i + 1])
        
        center_index = len(vertices)
        vertices.append([0, -1, 0])
        for i in range(segments):
            next_i = (i + 1) % segments
            faces.append([center_index, next_i + 1, i + 1])
            
    elif shape_type == 'cylinder':
        segments = params.get('segments', CYLINDER_SEGMENTS)
        
        for y in [1, -1]:
            for i in range(segments):
                theta = 2 * math.pi * i / segments
                x = math.cos(theta)
                z = math.sin(theta)
                vertices.append([x, y, z])
        
        for i in range(segments):
            next_i = (i + 1) % segments
            faces.append([i, i + segments, next_i])
            faces.append([next_i, i + segments, next_i + segments])
        
        top_center = len(vertices)
        vertices.append([0, 1, 0])
        for i in range(segments):
            next_i = (i + 1) % segments
            faces.append([top_center, next_i, i])
        
        bottom_center = len(vertices)
        vertices.append([0, -1, 0])
        for i in range(segments):
            next_i = (i + 1) % segments
            faces.append([bottom_center, i + segments, next_i + segments])
            
    elif shape_type == 'pyramid':
        vertices = [
            [0, 1.5, 0],
            [-1, -1, -1],
            [1, -1, -1],
            [1, -1, 1],
            [-1, -1, 1]
        ]
        
        faces = [
            [0, 1, 2],
            [0, 2, 3],
            [0, 3, 4],
            [0, 4, 1],
            [1, 2, 3, 4]
        ]
        
    elif shape_type == 'torus':
        tube_radius = params.get('tube_radius', 0.4)
        ring_radius = params.get('ring_radius', 1.0)
        ring_segments = params.get('ring_segments', TORUS_RING_SEGMENTS)
        tube_segments = params.get('tube_segments', TORUS_TUBE_SEGMENTS)
        
        for i in range(ring_segments):
            ring_angle = 2 * math.pi * i / ring_segments
            cos_ring = math.cos(ring_angle)
            sin_ring = math.sin(ring_angle)
            
            for j in range(tube_segments):
                tube_angle = 2 * math.pi * j / tube_segments
                cos_tube = math.cos(tube_angle)
                sin_tube = math.sin(tube_angle)
                
                x = (ring_radius + tube_radius * cos_tube) * cos_ring
                y = tube_radius * sin_tube
                z = (ring_radius + tube_radius * cos_tube) * sin_ring
                
                vertices.append([x, y, z])
        
        for i in range(ring_segments):
            next_i = (i + 1) % ring_segments
            for j in range(tube_segments):
                next_j = (j + 1) % tube_segments
                
                a = i * tube_segments + j
                b = next_i * tube_segments + j
                c = i * tube_segments + next_j
                d = next_i * tube_segments + next_j
                
                faces.append([a, b, c])
                faces.append([c, b, d])
                
    elif shape_type == 'octahedron':
        vertices = [
            [0, 1, 0],   # 0 - верх
            [1, 0, 0],   # 1 - право
            [0, 0, 1],   # 2 - вперед
            [-1, 0, 0],  # 3 - лево
            [0, 0, -1],  # 4 - назад
            [0, -1, 0]   # 5 - низ
        ]
        
        faces = [
            [0, 1, 2], [0, 2, 3], [0, 3, 4], [0, 4, 1],
            [5, 2, 1], [5, 3, 2], [5, 4, 3], [5, 1, 4]
        ]
        
    elif shape_type == 'cut_torus':
        tube_radius = params.get('tube_radius', 0.4)
        ring_radius = params.get('ring_radius', 1.0)
        ring_segments = params.get('ring_segments', 32)
        tube_segments = params.get('tube_segments', 12)
        cut_angle = params.get('cut_angle', 270)  # градусы!
    
        max_angle = math.radians(cut_angle)
    
        for i in range(ring_segments):
         ring_angle = max_angle * i / ring_segments
         cos_ring = math.cos(ring_angle)
         sin_ring = math.sin(ring_angle)
        
         for j in range(tube_segments):
            tube_angle = 2 * math.pi * j / tube_segments
            cos_tube = math.cos(tube_angle)
            sin_tube = math.sin(tube_angle)
            
            x = (ring_radius + tube_radius * cos_tube) * cos_ring
            y = tube_radius * sin_tube
            z = (ring_radius + tube_radius * cos_tube) * sin_ring
            
            vertices.append([x, y, z])
    
        for i in range(ring_segments - 1):
         next_i = i + 1
         for j in range(tube_segments):
            next_j = (j + 1) % tube_segments
            
            a = i * tube_segments + j
            b = next_i * tube_segments + j
            c = i * tube_segments + next_j
            d = next_i * tube_segments + next_j
            
            faces.append([a, b, c])
            faces.append([c, b, d])        
        
    elif shape_type == 'tetrahedron':
        vertices = [
            [0, 1, 0],
            [0.94, -0.33, 0],
            [-0.47, -0.33, 0.82],
            [-0.47, -0.33, -0.82]
        ]
        
        faces = [
            [0, 1, 2],
            [0, 2, 3],
            [0, 3, 1],
            [1, 3, 2]
        ]
        
    elif shape_type == 'prism':
        sides = max(3, params.get('sides', PRISM_SIDES))
        height = 1.0
        
        # Верхние вершины
        for i in range(sides):
            angle = 2 * math.pi * i / sides
            x = math.cos(angle)
            z = math.sin(angle)
            vertices.append([x, height/2, z])
        
        # Нижние вершины
        for i in range(sides):
            angle = 2 * math.pi * i / sides
            x = math.cos(angle)
            z = math.sin(angle)
            vertices.append([x, -height/2, z])
        
        # Боковые грани
        for i in range(sides):
            next_i = (i + 1) % sides
            faces.append([i, i + sides, next_i + sides])
            faces.append([i, next_i + sides, next_i])
        
        # Верхнее основание
        for i in range(1, sides - 1):
            faces.append([0, i, i + 1])
        
        # Нижнее основание
        for i in range(1, sides - 1):
            faces.append([sides, sides + i + 1, sides + i])
            
    elif shape_type == 'cuboid':
        w = params.get('width', CUBOID_WIDTH)
        h = params.get('height', CUBOID_HEIGHT)
        d = params.get('depth', CUBOID_DEPTH)
        
        vertices = [
            [-w, -h, -d], [w, -h, -d], [w, h, -d], [-w, h, -d],
            [-w, -h, d], [w, -h, d], [w, h, d], [-w, h, d]
        ]
        
        faces = [
            [0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4],
            [2, 3, 7, 6], [0, 3, 7, 4], [1, 2, 6, 5]
        ]
        
    elif shape_type == 'star':
        outer_radius = 1.0
        inner_radius = 0.5
        height = 0.3
        points = params.get('points', STAR_POINTS)
        
        # Создаем верхние и нижние вершины
        for i in range(points):
            angle = 2 * math.pi * i / points
            radius = outer_radius if i % 2 == 0 else inner_radius
            
            # Верхние вершины
            x_top = radius * math.cos(angle)
            y_top = height
            z_top = radius * math.sin(angle)
            vertices.append([x_top, y_top, z_top])
            
            # Нижние вершины
            x_bottom = radius * math.cos(angle)
            y_bottom = -height
            z_bottom = radius * math.sin(angle)
            vertices.append([x_bottom, y_bottom, z_bottom])
        
        # Центральные вершины
        vertices.append([0, height * 1.5, 0])    # Верхний центр
        vertices.append([0, -height * 1.5, 0])   # Нижний центр
        
        # Грани для верхней звезды
        for i in range(0, points * 2, 2):
            next_i = (i + 2) % (points * 2)
            faces.append([i, next_i, points * 2])  # Треугольники к верхнему центру
        
        # Грани для нижней звезды
        for i in range(1, points * 2, 2):
            next_i = (i + 2) % (points * 2)
            faces.append([i, points * 2 + 1, next_i])  # Треугольники к нижнему центру
        
        # Боковые грани
        for i in range(0, points * 2, 2):
            top = i
            bottom = i + 1
            next_top = (i + 2) % (points * 2)
            next_bottom = (i + 3) % (points * 2)
            
            faces.append([top, next_top, next_bottom, bottom])
            
    elif shape_type == 'crystal':
        top_height = 1.2
        middle_radius = 0.8
        bottom_height = -1.0
        facets = params.get('facets', CRYSTAL_FACETS)
        
        # Верхняя вершина
        vertices.append([0, top_height, 0])
        
        # Средние вершины (верхнее кольцо)
        for i in range(facets):
            angle = 2 * math.pi * i / facets
            x = math.cos(angle) * middle_radius * 0.7
            z = math.sin(angle) * middle_radius * 0.7
            y = top_height * 0.3
            vertices.append([x, y, z])
        
        # Средние вершины (нижнее кольцо)
        for i in range(facets):
            angle = 2 * math.pi * i / facets + math.pi/facets
            x = math.cos(angle) * middle_radius
            z = math.sin(angle) * middle_radius
            y = -0.2
            vertices.append([x, y, z])
        
        # Нижняя вершина
        vertices.append([0, bottom_height, 0])
        
        # Грани от верхней вершины к верхнему кольцу
        for i in range(facets):
            next_i = (i + 1) % facets
            faces.append([0, i + 1, next_i + 1])
        
        # Боковые грани между кольцами
        for i in range(facets):
            top_i = i + 1
            bottom_i = i + facets + 1
            next_top_i = (i + 1) % facets + 1
            next_bottom_i = (i + 1) % facets + facets + 1
            
            faces.append([top_i, bottom_i, next_bottom_i, next_top_i])
        
        # Грани от нижнего кольца к нижней вершине
        bottom_vertex = len(vertices) - 1
        for i in range(facets):
            bottom_i = i + facets + 1
            next_bottom_i = (i + 1) % facets + facets + 1
            faces.append([bottom_vertex, next_bottom_i, bottom_i])
        
        # Добавляем дополнительные диагональные грани
        for i in range(facets):
            if i % 2 == 0:
                top_i = i + 1
                next_top_i = (i + 2) % facets + 1
                bottom_i = (i + 1) % facets + facets + 1
                faces.append([top_i, next_top_i, bottom_i])
    
    elif shape_type == 'icosahedron':
        # Икосаэдр - 20 треугольных граней
        radius = params.get('radius', ICOSAHEDRON_RADIUS)
        t = (1.0 + math.sqrt(5.0)) / 2.0
        
        vertices = [
            [-1, t, 0], [1, t, 0], [-1, -t, 0], [1, -t, 0],
            [0, -1, t], [0, 1, t], [0, -1, -t], [0, 1, -t],
            [t, 0, -1], [t, 0, 1], [-t, 0, -1], [-t, 0, 1]
        ]
        
        # Нормализуем вершины к заданному радиусу
        for i in range(len(vertices)):
            v = vertices[i]
            length = math.sqrt(v[0]**2 + v[1]**2 + v[2]**2)
            vertices[i] = [v[0]/length*radius, v[1]/length*radius, v[2]/length*radius]
        
        faces = [
            [0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11],
            [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8],
            [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9],
            [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1]
        ]
                
    elif shape_type == 'frustum':
        # Усеченная пирамида (конус с отрезанной верхушкой)
        top_radius = params.get('top_radius', FRUSTUM_TOP_RADIUS)
        bottom_radius = params.get('bottom_radius', FRUSTUM_BOTTOM_RADIUS)
        height = params.get('height', FRUSTUM_HEIGHT)
        segments = params.get('segments', 16)
        
        # Верхнее кольцо
        for i in range(segments):
            theta = 2 * math.pi * i / segments
            x = math.cos(theta) * top_radius
            z = math.sin(theta) * top_radius
            vertices.append([x, height/2, z])
        
        # Нижнее кольцо
        for i in range(segments):
            theta = 2 * math.pi * i / segments
            x = math.cos(theta) * bottom_radius
            z = math.sin(theta) * bottom_radius
            vertices.append([x, -height/2, z])
        
        # Боковые грани
        for i in range(segments):
            next_i = (i + 1) % segments
            faces.append([i, i + segments, next_i])
            faces.append([next_i, i + segments, next_i + segments])
        
        # Верхнее основание
        top_center = len(vertices)
        vertices.append([0, height/2, 0])
        for i in range(segments):
            next_i = (i + 1) % segments
            faces.append([top_center, next_i, i])
        
        # Нижнее основание
        bottom_center = len(vertices)
        vertices.append([0, -height/2, 0])
        for i in range(segments):
            next_i = (i + 1) % segments
            faces.append([bottom_center, i + segments, next_i + segments])
            
    elif shape_type == 'ellipsoid':
        # Эллипсоид (растянутая сфера)
        rx = params.get('radius_x', ELLIPSOID_RADIUS_X)
        ry = params.get('radius_y', ELLIPSOID_RADIUS_Y)
        rz = params.get('radius_z', ELLIPSOID_RADIUS_Z)
        segments = params.get('segments', 16)
        rings = params.get('rings', 12)
        
        for i in range(rings + 1):
            phi = math.pi * i / rings
            for j in range(segments + 1):
                theta = 2 * math.pi * j / segments
                x = math.sin(phi) * math.cos(theta) * rx
                y = math.cos(phi) * ry
                z = math.sin(phi) * math.sin(theta) * rz
                vertices.append([x, y, z])
        
        for i in range(rings):
            for j in range(segments):
                a = i * (segments + 1) + j
                b = a + segments + 1
                c = a + 1
                d = b + 1
                faces.append([a, b, c])
                faces.append([c, b, d])
                
    elif shape_type == 'mobius':
        segments = params.get('segments', MOBIUS_SEGMENTS)
        width = params.get('width', MOBIUS_WIDTH)
        radius = params.get('radius', MOBIUS_RADIUS)
        
        # Создаем вершины ленты Мёбиуса
        for i in range(segments + 1):
            u = 2 * math.pi * i / segments
            for j in range(2):  # Два края ленты
                v = -width/2 + j * width
                
                # Параметрическое уравнение ленты Мёбиуса
                x = (radius + v * math.cos(u/2)) * math.cos(u)
                y = (radius + v * math.cos(u/2)) * math.sin(u)
                z = v * math.sin(u/2)
                
                vertices.append([x, y, z])
        
        # Создаем грани (треугольники)
        for i in range(segments):
            a = i * 2
            b = i * 2 + 1
            c = ((i + 1) % segments) * 2
            d = ((i + 1) % segments) * 2 + 1
            
            # Два треугольника образуют четырехугольник
            faces.append([a, b, c])
            faces.append([c, b, d])
            
    elif shape_type == 'spiral':
        turns = params.get('turns', SPIRAL_TURNS)
        height = params.get('height', SPIRAL_HEIGHT)
        radius = params.get('radius', SPIRAL_RADIUS)
        segments = params.get('segments', SPIRAL_SEGMENTS)
        tube_radius = 0.2
        
        # Создаем вершины спирали
        for i in range(segments + 1):
            t = turns * 2 * math.pi * i / segments
            for j in range(8):  # 8 сегментов вокруг трубы
                theta = 2 * math.pi * j / 8
                
                # Положение центра трубы вдоль спирали
                x_center = radius * math.cos(t)
                y_center = -height/2 + height * i / segments
                z_center = radius * math.sin(t)
                
                # Вектор касательной к спирали
                dx = -radius * math.sin(t)
                dy = height / (segments / turns)
                dz = radius * math.cos(t)
                
                # Нормализуем касательный вектор
                length = math.sqrt(dx**2 + dy**2 + dz**2)
                dx /= length
                dy /= length
                dz /= length
                
                # Произвольный вектор, не коллинеарный с касательным
                if abs(dx) > 0.1:
                    bx, by, bz = 0, 1, 0
                else:
                    bx, by, bz = 1, 0, 0
                
                # Векторное произведение для получения бинормали
                nx = by * dz - bz * dy
                ny = bz * dx - bx * dz
                nz = bx * dy - by * dx
                
                # Нормализуем нормаль
                length_n = math.sqrt(nx**2 + ny**2 + nz**2)
                nx /= length_n
                ny /= length_n
                nz /= length_n
                
                # Векторное произведение нормали на касательную для получения другого вектора
                ux = ny * dz - nz * dy
                uy = nz * dx - nx * dz
                uz = nx * dy - ny * dx
                
                # Вершина на поверхности трубы
                x = x_center + tube_radius * (math.cos(theta) * nx + math.sin(theta) * ux)
                y = y_center + tube_radius * (math.cos(theta) * ny + math.sin(theta) * uy)
                z = z_center + tube_radius * (math.cos(theta) * nz + math.sin(theta) * uz)
                
                vertices.append([x, y, z])
        
        # Создаем грани
        for i in range(segments):
            for j in range(8):
                next_j = (j + 1) % 8
                a = i * 8 + j
                b = i * 8 + next_j
                c = ((i + 1) % (segments + 1)) * 8 + j
                d = ((i + 1) % (segments + 1)) * 8 + next_j
                
                faces.append([a, b, c])
                faces.append([c, b, d])
    
    return vertices, faces

def render_shape_generic(shape_type, pos, angle_x, angle_y, angle_z, scale=1.0, **params):
    """Общая функция рендеринга любой фигуры"""
    # Создаем вершины и грани
    vertices, faces = create_vertices_and_faces(shape_type, **params)
    
    scaled_vertices = []
    for v in vertices:
        scaled_vertices.append([v[0] * scale, v[1] * scale, v[2] * scale])
    
    # Вращаем вершины
    rotated_vertices = []
    cos_x = math.cos(angle_x)
    sin_x = math.sin(angle_x)
    cos_y = math.cos(angle_y)
    sin_y = math.sin(angle_y)
    cos_z = math.cos(angle_z)
    sin_z = math.sin(angle_z)
    
    for v in scaled_vertices:
        y1 = v[1] * cos_x - v[2] * sin_x
        z1 = v[1] * sin_x + v[2] * cos_x
        
        x2 = v[0] * cos_y - z1 * sin_y
        z2 = v[0] * sin_y + z1 * cos_y
        
        x3 = x2 * cos_z - y1 * sin_z
        y3 = x2 * sin_z + y1 * cos_z
        
        rotated_vertices.append([x3, y3, z2])
    
    # Проецируем вершины на 2D
    projected_vertices = []
    for v in rotated_vertices:
        factor = RENDER_SCALE / (v[2] + CAMERA_DISTANCE)
        x2d = v[0] * factor + pos[0]
        y2d = v[1] * factor + pos[1]
        projected_vertices.append([x2d, y2d])
    
    # Для остальных фигур используем обычную сортировку по глубине
    face_depths = []
    for i, face in enumerate(faces):
          z_sum = sum(rotated_vertices[v][2] for v in face)
          face_depths.append((z_sum / len(face), i))
        
    face_depths.sort(reverse=True)
    return projected_vertices, face_depths, faces

def render_shape(shape_idx, pos, angle_x, angle_y, angle_z, scale=1.0):
    """Рендеринг конкретной фигуры по индексу"""
    shape_type = SHAPES[shape_idx]
    
    # Параметры для различных фигур
    params = {}
    
    if shape_type == 'sphere':
        params = {'segments': SPHERE_SEGMENTS, 'rings': SPHERE_RINGS}
    elif shape_type == 'cone':
        params = {'segments': CONE_SEGMENTS}
    elif shape_type == 'cylinder':
        params = {'segments': CYLINDER_SEGMENTS}
    elif shape_type == 'torus':
        params = {
            'ring_segments': TORUS_RING_SEGMENTS,
            'tube_segments': TORUS_TUBE_SEGMENTS
        }
    elif shape_type == 'prism':
        params = {'sides': PRISM_SIDES}
    elif shape_type == 'cuboid':
        params = {
            'width': CUBOID_WIDTH,
            'height': CUBOID_HEIGHT,
            'depth': CUBOID_DEPTH
        }
    elif shape_type == 'star':
        params = {'points': STAR_POINTS}
    elif shape_type == 'crystal':
        params = {'facets': CRYSTAL_FACETS}
    elif shape_type == 'icosahedron':
        params = {'radius': ICOSAHEDRON_RADIUS}
    elif shape_type == 'frustum':
        params = {
            'top_radius': FRUSTUM_TOP_RADIUS,
            'bottom_radius': FRUSTUM_BOTTOM_RADIUS,
            'height': FRUSTUM_HEIGHT,
            'segments': 16
        }
    elif shape_type == 'ellipsoid':
        params = {
            'radius_x': ELLIPSOID_RADIUS_X,
            'radius_y': ELLIPSOID_RADIUS_Y,
            'radius_z': ELLIPSOID_RADIUS_Z,
            'segments': 16,
            'rings': 12
        }
        
    elif shape_type == 'mobius':
        params = {
            'segments': MOBIUS_SEGMENTS,
            'width': MOBIUS_WIDTH,
            'radius': MOBIUS_RADIUS
        }
    elif shape_type == 'spiral':
        params = {
            'turns': SPIRAL_TURNS,
            'height': SPIRAL_HEIGHT,
            'radius': SPIRAL_RADIUS,
            'segments': SPIRAL_SEGMENTS
        }
    
    return render_shape_generic(shape_type, pos, angle_x, angle_y, angle_z, scale, **params)
    
def lerp(a, b, t):
    """Линейная интерполяция"""
    return a + (b - a) * t

def ease_in_out(t):
    """Плавное ускорение и замедление"""
    return t * t * (3 - 2 * t)

# Модифицируем существующую функцию render_shape:
def render_vertices(vertices, faces, pos, angle_x, angle_y, angle_z, scale=1.0):
    """Рендеринг готовых вершин и граней (для морфинга)"""
    
    # Масштабируем
    scaled_vertices = []
    for v in vertices:
        scaled_vertices.append([v[0] * scale, v[1] * scale, v[2] * scale])
    
    # Вращаем
    rotated_vertices = [rotate_vertex(v, angle_x, angle_y, angle_z) for v in scaled_vertices]
    
    # Проецируем
    projected_vertices = []
    for v in rotated_vertices:
        factor = RENDER_SCALE / (v[2] + CAMERA_DISTANCE)
        x2d = v[0] * factor + pos[0]
        y2d = v[1] * factor + pos[1]
        projected_vertices.append([x2d, y2d])
    
    # Сортируем грани
    face_depths = []
    for i, face in enumerate(faces):
        z_sum = 0
        count = 0
        for v_idx in face:
            if v_idx < len(rotated_vertices):
                z_sum += rotated_vertices[v_idx][2]
                count += 1
        if count > 0:
            face_depths.append((z_sum / count, i))
    
    face_depths.sort(reverse=True)
    
    return projected_vertices, face_depths, faces

def render_shape_with_morph(shape_idx_a, shape_idx_b, morph_progress, pos, angle_x, angle_y, angle_z, scale=1.0):
    """
    Рендеринг с плавной трансформацией между двумя фигурами
    morph_progress: от 0 (фигура A) до 1 (фигура B)
    """
    # Получаем вершины обеих фигур
    vertices_a, faces_a = create_vertices_and_faces(SHAPES[shape_idx_a])
    vertices_b, faces_b = create_vertices_and_faces(SHAPES[shape_idx_b])
    
    # Плавное изменение t
    t = ease_in_out(max(0, min(1, morph_progress)))
    
    # Создаём промежуточные вершины
    morphed_vertices = []
    
    # Используем ту фигуру, у которой больше вершин
    max_vertices = max(len(vertices_a), len(vertices_b))
    
    for i in range(max_vertices):
        if i < len(vertices_a) and i < len(vertices_b):
            # Обе фигуры имеют эту вершину - интерполируем
            x = lerp(vertices_a[i][0], vertices_b[i][0], t)
            y = lerp(vertices_a[i][1], vertices_b[i][1], t)
            z = lerp(vertices_a[i][2], vertices_b[i][2], t)
        elif i < len(vertices_a):
            # Вершина есть только в A - исчезает
            x = vertices_a[i][0] * (1 - t)
            y = vertices_a[i][1] * (1 - t)
            z = vertices_a[i][2] * (1 - t)
        else:
            # Вершина есть только в B - появляется
            x = vertices_b[i][0] * t
            y = vertices_b[i][1] * t
            z = vertices_b[i][2] * t
        
        morphed_vertices.append([x, y, z])
    
    # Для граней используем faces от фигуры B при t > 0.5
    if t > 0.5:
        faces = faces_b
    else:
        faces = faces_a
    
    return render_vertices(morphed_vertices, faces, pos, angle_x, angle_y, angle_z, scale)