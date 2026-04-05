# main.py
import sys
from events import handle_mouse_click, create_buttons, create_speed_slider, handle_multi_click
from render import render_shape, render_shape_with_morph
import math
from recording import *
import pygame.mixer
from script_server import *

# Инициализация Pygame
pygame.init()
# Вместо обычного pygame окна
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.NOFRAME)
pygame.display.set_caption("3D Shapes ↔ DVD")
clock = pygame.time.Clock()

last_time = pygame.time.get_ticks()

text_cache = {}

dragging = False
drag_offset_x = 0
drag_offset_y = 0

def draw_titlebar():
    # Полоска заголовка
    pygame.draw.rect(screen, (50, 50, 60), (0, 0, WIDTH, 30))
    pygame.draw.line(screen, (100, 100, 120), (0, 30), (WIDTH, 30), 1)

    # Текст
    font = pygame.font.Font(None, 20)
    title = font.render("Madmen 3D Viewer", True, (200, 200, 220))
    screen.blit(title, (10, 7))

    # Кнопка закрытия
    close_rect = pygame.Rect(WIDTH - 30, 5, 20, 20)
    pygame.draw.rect(screen, (200, 60, 60), close_rect)
    pygame.draw.line(screen, (255, 255, 255), (WIDTH - 25, 10), (WIDTH - 15, 20), 2)
    pygame.draw.line(screen, (255, 255, 255), (WIDTH - 15, 10), (WIDTH - 25, 20), 2)

    return close_rect  # возвращаем область кнопки закрытия

# Загрузка DVD логотипа
def load_dvd_logo():
    for path in DVD_LOGO_PATHS:
        try:
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                img = pygame.transform.scale(img, (120, 60))
                return create_colors(img)
        except:
            continue
    
    return None

def create_colors(original):
    variants = []
    for color in DVD_COLORS:
        colored = original.copy()
        for x in range(colored.get_width()):
            for y in range(colored.get_height()):
                pixel = colored.get_at((x, y))
                if pixel[3] > 0:
                    if sum(pixel[:3]) > 0:
                        brightness = sum(pixel[:3]) / 3 / 255.0
                    else:
                        brightness = 1.0
                    new_r = int(color[0] * brightness)
                    new_g = int(color[1] * brightness)
                    new_b = int(color[2] * brightness)
                    colored.set_at((x, y), (new_r, new_g, new_b, pixel[3]))
        variants.append(colored)
    return variants

# Глобальное состояние игры
game_state = {
    "angle_x": INITIAL_ANGLES[0],
    "angle_y": INITIAL_ANGLES[1],
    "angle_z": INITIAL_ANGLES[2],
    "cube_pos": INITIAL_CUBE_POS.copy(),
    "cube_velocity": INITIAL_CUBE_VELOCITY.copy(),
    "auto_rotate": True,
    "rotation_speed": INITIAL_ROTATION_SPEED,
    "show_cube": True,
    "current_shape": 0,
    "dvd_mode": True,
    "current_dvd_color": 2,
    "face_colors": [RED, GREEN, BLUE, YELLOW, PURPLE, CYAN],
    "with_karkas": False,
    "draw_faces": True,
    "move_speed": DEFAULT_SPEED,  # Скорость движения
    "speed_slider_dragging": False,  # Перетаскивается ли слайдер
    "draw_points": False,
    "bg_color": (0, 0, 0),
    "scale": 1.0,              # Масштаб фигуры (1.0 = 100%)
    "is_zooming": False,       # Режим зумирования
    "zoom_start_y": 0,         # Начальная позиция Y для зума
    "zoom_start_scale": 1.0,   # Начальный масштаб при начале зума,
    "ui_visible": True,
        # Добавляем для трансформаций:
    "is_morphing": False,          # Идёт ли сейчас трансформация
    "morph_progress": 0.0,         # Прогресс от 0 до 1
    "prev_shape": 0,
     "is_recording": False,
    "video_writer": None,
    "frame_queue": None,
    "recording_thread": None,
    "recorded_frames": 0,
    "max_record_seconds": 30,  # Максимум 30 секунд
    "recording_available": True,
    "webcam_on": False,
    "webcam_cap": None,
    "webcam_frame": None,
    "webcam_fullscreen": False,
    "webcam_hold_activated": False,
    "webcam_hold_start": 0,
    "voice_size_mode": False,
    "voice_size_original": 1.0,
    "voice_threshold": 0.01,  # минимальная громкость
    "voice_max_scale": 3.0,
    "trail_mode": False,
    "multiplayer": None,
    "multiplayer_ui": False,
    "face_alpha": 255,  # прозрачность граней (0-255)
    "alpha_min": 50,  # минимальная прозрачность
    "alpha_max": 255,  # максимальная прозрачность
    "bounced": False,  # ← добавь эту строку,
    "multi_mode": False,
    "objects": []
}

# Загрузка логотипов и создание кнопок
dvd_logos = load_dvd_logo()
buttons = create_buttons(game_state)

# ДОБАВЬТЕ ЭТУ СТРОЧКУ:
from events import add_recording_button
if game_state["recording_available"]:
    add_recording_button(buttons, game_state)

speed_slider = create_speed_slider(game_state)
game_state["speed_slider"] = speed_slider

from voice import VoiceController

voice = VoiceController(game_state)
game_state["voice"] = voice

# В main.py, после создания game_state добавьте:
from game_system import Game

game_state["game_system"] = Game(game_state)
game_state["screen"] = screen  # передаем экран для рисования

# В main.py после создания game_state добавьте:
script_server = ScriptServer(game_state)
script_server.start()
game_state["script_server"] = script_server

pygame.mixer.init()
pygame.mixer.music.load("sounds/background.mp3")
pygame.mixer.music.play(-1)

def load_custom_models():
    """Загружает кастомные модели и обновляет списки"""
    import os
    
    models_dir = "models"
    if not os.path.exists(models_dir):
        print(f"📁 Папка {models_dir} не найдена")
        return
    
    # Сканируем все файлы моделей
    supported_extensions = ['.json', '.obj', '.txt', '.model']
    
    for filename in os.listdir(models_dir):
        if any(filename.endswith(ext) for ext in supported_extensions):
            model_name = os.path.splitext(filename)[0]
            
            # Пробуем загрузить
            from render import add_custom_model_from_file
            result = add_custom_model_from_file(model_name)
            
            if result:
                print(f"  ✅ {filename}")
            else:
                print(f"  ❌ {filename} (ошибка загрузки)")
    
    print(f"📁 Загружено моделей: {len(SHAPES) - len(BASE_SHAPES)}")

load_custom_models()

def get_dvd_real_size():
    """Возвращает реальные размеры DVD с учетом масштаба"""
    if not dvd_logos or game_state["current_dvd_color"] >= len(dvd_logos):
        return 120, 60  # Дефолтные размеры
    
    logo = dvd_logos[game_state["current_dvd_color"]]
    
    # Масштабируем логотип
    scaled_width = int(logo.get_width() * game_state["scale"])
    scaled_height = int(logo.get_height() * game_state["scale"])
    
    # Сохраняем пропорции, но ограничиваем разумные размеры
    scaled_width = max(20, min(300, scaled_width))
    scaled_height = max(10, min(150, scaled_height))
    
    return scaled_width, scaled_height   

def draw_3d_shape():    
    if game_state.get("is_morphing", False):
        # Используем рендеринг с морфингом
        projected_vertices, face_depths, shape_faces = render_shape_with_morph(
            game_state["prev_shape"],      # Из какой фигуры
            game_state["current_shape"],   # В какую фигуру
            game_state["morph_progress"],  # Прогресс трансформации (0.0 - 1.0)
            game_state["cube_pos"],
            game_state["angle_x"], 
            game_state["angle_y"], 
            game_state["angle_z"],
            game_state["scale"]
        )
    else:
        # Обычный рендеринг
        projected_vertices, face_depths, shape_faces = render_shape(
            game_state["current_shape"],
            game_state["cube_pos"],
            game_state["angle_x"], 
            game_state["angle_y"], 
            game_state["angle_z"],
            game_state["scale"]
        )
    
    if not projected_vertices:
        return []

    if game_state["draw_faces"]:
        for depth, face_idx in face_depths:
            face = shape_faces[face_idx]
            color_idx = face_idx % len(game_state["face_colors"])
            base_color = game_state["face_colors"][color_idx]

            points_2d = [projected_vertices[v] for v in face]

            if len(face) >= 3:
                # Добавляем прозрачность
                alpha = game_state.get("face_alpha", 255)

                # Создаем цвет с прозрачностью
                if alpha < 255:
                    # Для прозрачности нужно создать Surface
                    if len(points_2d) >= 3:
                        # Создаем временную поверхность
                        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                        color_with_alpha = (*base_color, alpha)
                        pygame.draw.polygon(s, color_with_alpha, points_2d)
                        screen.blit(s, (0, 0))
                else:
                    # Без прозрачности - обычная отрисовка
                    color = (
                        int(base_color[0]),
                        int(base_color[1]),
                        int(base_color[2])
                    )
                    pygame.draw.polygon(screen, color, points_2d)
    
    # Рисуем каркас поверх граней (если включено)
    if game_state["with_karkas"]:
        for depth, face_idx in face_depths:
            if face_idx >= len(shape_faces):
                continue
                
            face = shape_faces[face_idx]
            points = []
            
            for v_idx in face:
                if v_idx < len(projected_vertices):
                    points.append(projected_vertices[v_idx])
            
            if len(points) >= 3:
                pygame.draw.polygon(screen, WHITE, points, 2)
    
    # Рисуем вершины ПОВЕРХ всего (если включено)
    if game_state["draw_points"]:
        for i, vertex in enumerate(projected_vertices):
            if game_state.get("is_morphing", False):
                progress = game_state["morph_progress"]
                # Точки пульсируют во время морфинга
                pulse = 1.0 + 0.5 * math.sin(progress * math.pi * 4)
                size = int(2 * pulse)
                
                # Меняем цвет точек во время морфинга
                if progress < 0.3:
                    color = (255, 200, 100)  # Оранжевый в начале
                elif progress < 0.7:
                    color = (200, 200, 200)  # Серый в середине
                else:
                    color = (100, 200, 255)  # Голубой в конце
            else:
                color = (255, 255, 255)
                size = 2
            
            pygame.draw.circle(screen, color, 
                             (int(vertex[0]), int(vertex[1])), 
                             size)
    
    # Рисуем рамку вокруг фигуры если активно масштабирование
    if game_state["is_zooming"]:
        # Находим границы фигуры
        if projected_vertices:
            min_x = min(v[0] for v in projected_vertices)
            max_x = max(v[0] for v in projected_vertices)
            min_y = min(v[1] for v in projected_vertices)
            max_y = max(v[1] for v in projected_vertices)
           
            # ВЫБОР ЦВЕТА РАМКИ ДЛЯ РАЗВЁРТКИ
            if game_state.get("is_unfolded", False):
                border_color = (200, 100, 255)  # Фиолетовый для развёртки
            elif game_state.get("is_morphing", False):
                border_color = (255, 200, 0)  # Жёлтый при морфинге
            else:
                border_color = (255, 255, 0)  # Жёлтый
            
            # Рисуем прямоугольник
            rect = pygame.Rect(min_x, min_y, max_x - min_x, max_y - min_y)
            pygame.draw.rect(screen, border_color, rect, 3)
    
    # Возвращаем вершины для проверки столкновений
    return projected_vertices

def draw_dvd_logo():
    """Отрисовка DVD логотипа с масштабом"""
    if dvd_logos and game_state["current_dvd_color"] < len(dvd_logos):
        # Используем ту же функцию для размеров
        dvd_width, dvd_height = get_dvd_real_size()
        
        # Получаем оригинальный логотип
        logo = dvd_logos[game_state["current_dvd_color"]]
        
        # Масштабируем до расчетных размеров
        if dvd_width != logo.get_width() or dvd_height != logo.get_height():
            logo = pygame.transform.scale(logo, (dvd_width, dvd_height))
        
        # Позиционируем по центру
        logo_rect = logo.get_rect(center=game_state["cube_pos"])
        screen.blit(logo, logo_rect)
        
        # Рисуем рамку вокруг логотипа если активно масштабирование
        if game_state["is_zooming"]:
            pygame.draw.rect(screen, (255, 255, 0), logo_rect, 3)
            
def draw_ui_toggle_indicator():
    """Рисует индикатор скрытия UI в правом верхнем углу"""
    # Область клика (50x50 пикселей)
    toggle_rect = pygame.Rect(WIDTH - 50, 30, 50, 50)
    
    # Цвет в зависимости от состояния UI
    if game_state.get("ui_visible", True):
        color = (100, 150, 100)  # Зеленый когда UI виден
        text = "ON"
    else:
        color = (150, 100, 100)  # Красный когда UI скрыт
        text = "OFF"
    
    # Фон индикатора
    pygame.draw.rect(screen, color, toggle_rect, border_radius=8)
    
    # РАМКА ВОКРУГ ЗОНЫ (добавьте эту строку)
    pygame.draw.rect(screen, WHITE, toggle_rect, 2, border_radius=8)
    
    # Текст (значок)
    font = pygame.font.Font(None, 36)
    text_surf = font.render(text, True, WHITE)
    text_rect = text_surf.get_rect(center=toggle_rect.center)
    screen.blit(text_surf, text_rect)

def get_cached_text(font, text, color):
    """Кэширование только текста"""
    key = (text, color)
    if key not in text_cache:
        text_cache[key] = font.render(text, True, color)
    return text_cache[key]

def draw_buttons():
    """Оптимизированная отрисовка кнопок"""
    if not game_state.get("ui_visible", True):
        return
    
    # Всегда рисуем кнопки (это не тяжело)
    button_names = [
        "exit_button", "rotate_toggle", "dvd_toggle", "speed_up_btn",
        "speed_down_btn", "color_next_btn", "color_prev_btn", "shape_toggle_btn",
        "wireframe_toggle", "faces_toggle", "points_toggle",
        "bg_color_btn", "mode_toggle_btn", "screenshot_btn", "record_button",
        "webcam_btn", "voice_size_btn", "trail_btn", "alpha_down_btn",
        "alpha_up_btn", "multi_toggle"
    ]
    
    for name in button_names:
        if name in game_state:
            game_state[name].draw(screen)
    
    # Слайдер всегда рисуем
    if "speed_slider" in game_state:
        game_state["speed_slider"].draw(screen)
    
    if game_state["show_cube"] and "rotate_buttons" in game_state:
        for btn in game_state["rotate_buttons"]:
            btn.draw(screen)

def draw_info():
    font = pygame.font.Font(None, 28)

    # Скорость вращения
    speed_text = font.render(f"Скорость: {game_state['rotation_speed']:.3f}", True, WHITE)
    screen.blit(speed_text, (WIDTH - 170, 90))

    # Индикатор записи
    if game_state.get("is_recording", False):
        # Красная полоска сверху
        pygame.draw.rect(screen, (255, 50, 50), (0, 0, WIDTH, 5))

        # Текст с таймером (ИСПРАВЛЕНО: 60 FPS)
        seconds = game_state['recorded_frames'] // 60  # 60 FPS в OpenCV

        timer_text = font.render(
            f"● ЗАПИСЬ {seconds // 60:02d}:{seconds % 60:02d}",
            True,
            (255, 100, 100)
        )
        screen.blit(timer_text, (WIDTH - 200, 30))

def get_object_bounds(obj, game_state):
    """Возвращает (min_x, max_x, min_y, max_y) для объекта"""
    # Сохраняем текущее состояние
    old_shape = game_state["current_shape"]
    old_pos = game_state["cube_pos"].copy()
    old_scale = game_state["scale"]
    old_ax = game_state["angle_x"]
    old_ay = game_state["angle_y"]
    old_az = game_state["angle_z"]

    # Подменяем
    game_state["current_shape"] = obj["shape"]
    game_state["cube_pos"] = [obj["x"], obj["y"]]
    game_state["scale"] = obj["scale"]
    game_state["angle_x"] = obj["ax"]
    game_state["angle_y"] = obj["ay"]
    game_state["angle_z"] = obj["az"]

    # Получаем проекцию
    if game_state.get("is_morphing", False):
        projected_vertices, _, _ = render_shape_with_morph(
            game_state["prev_shape"],
            game_state["current_shape"],
            game_state["morph_progress"],
            game_state["cube_pos"],
            game_state["angle_x"],
            game_state["angle_y"],
            game_state["angle_z"],
            game_state["scale"]
        )
    else:
        projected_vertices, _, _ = render_shape(
            game_state["current_shape"],
            game_state["cube_pos"],
            game_state["angle_x"],
            game_state["angle_y"],
            game_state["angle_z"],
            game_state["scale"]
        )

    # Восстанавливаем
    game_state["current_shape"] = old_shape
    game_state["cube_pos"] = old_pos
    game_state["scale"] = old_scale
    game_state["angle_x"] = old_ax
    game_state["angle_y"] = old_ay
    game_state["angle_z"] = old_az

    if not projected_vertices:
        return None

    min_x = min(v[0] for v in projected_vertices)
    max_x = max(v[0] for v in projected_vertices)
    min_y = min(v[1] for v in projected_vertices)
    max_y = max(v[1] for v in projected_vertices)

    return min_x, max_x, min_y, max_y

def get_object_at_pos(mouse_x, mouse_y, objects, game_state):
    """Возвращает индекс объекта, на который кликнули"""
    for i, obj in enumerate(objects):
        # Сохраняем состояние
        old_shape = game_state["current_shape"]
        old_pos = game_state["cube_pos"].copy()
        old_scale = game_state["scale"]

        # Подменяем
        game_state["current_shape"] = obj["shape"]
        game_state["cube_pos"] = [obj["x"], obj["y"]]
        game_state["scale"] = obj["scale"]

        # Получаем проекцию
        projected_vertices, _, _ = render_shape(
            game_state["current_shape"],
            game_state["cube_pos"],
            obj["ax"], obj["ay"], obj["az"],
            game_state["scale"]
        )

        # Восстанавливаем
        game_state["current_shape"] = old_shape
        game_state["cube_pos"] = old_pos
        game_state["scale"] = old_scale

        if not projected_vertices:
            continue

        # Проверяем попадание в bounding box
        min_x = min(v[0] for v in projected_vertices)
        max_x = max(v[0] for v in projected_vertices)
        min_y = min(v[1] for v in projected_vertices)
        max_y = max(v[1] for v in projected_vertices)

        if min_x <= mouse_x <= max_x and min_y <= mouse_y <= max_y:
            return i
    return -1


def draw_ui():
    if not game_state.get("ui_visible", True):
        return

    if game_state["multi_mode"]:
        # Рисуем мульти-кнопки
        for btn in game_state["multi_buttons"].values():
            btn.draw(screen)
        # Выделение выбранной фигуры
        idx = game_state.get("selected_object_index", -1)
        if idx >= 0:
            # Можно нарисовать рамку вокруг выбранной фигуры
            pass
    else:
        # Обычные кнопки
        draw_buttons()
        draw_info()

def get_object_aabb(obj):
    """Возвращает [min_x, max_x, min_y, max_y] для объекта"""
    # Аппроксимация: используем scale для размера
    size = 50 * obj.get("scale", 1.0)  # базовый размер 50px
    x, y = obj["x"], obj["y"]
    return [x - size, x + size, y - size, y + size]

def check_aabb_collision(aabb1, aabb2):
    """Проверяет пересечение двух AABB"""
    return not (aabb1[1] < aabb2[0] or aabb2[1] < aabb1[0] or
                aabb1[3] < aabb2[2] or aabb2[3] < aabb1[2])

# Основной игровой цикл с исправлениями
running = True
while running:
    mouse_pos = pygame.mouse.get_pos()
    mouse_buttons = pygame.mouse.get_pressed()

    game_state["_mouse_x"] = mouse_pos[0]
    game_state["_mouse_y"] = mouse_pos[1]
    game_state["_mouse_left"] = mouse_buttons[0]
    game_state["_mouse_right"] = mouse_buttons[2]

    # Получаем состояние клавиш
    keys = pygame.key.get_pressed()

    # Формируем словарь нажатых клавиш
    key_state = {
        "w": bool(keys[pygame.K_w]),
        "a": bool(keys[pygame.K_a]),
        "s": bool(keys[pygame.K_s]),
        "d": bool(keys[pygame.K_d]),
        "up": bool(keys[pygame.K_UP]),
        "down": bool(keys[pygame.K_DOWN]),
        "left": bool(keys[pygame.K_LEFT]),
        "right": bool(keys[pygame.K_RIGHT]),
        "space": bool(keys[pygame.K_SPACE]),
        "enter": bool(keys[pygame.K_RETURN]),
        "shift": bool(keys[pygame.K_LSHIFT]) or bool(keys[pygame.K_RSHIFT]),
        "ctrl": bool(keys[pygame.K_LCTRL]) or bool(keys[pygame.K_RCTRL]),
        "esc": bool(keys[pygame.K_ESCAPE])
    }

    game_state["_input_keys"] = key_state
    
    current_time = pygame.time.get_ticks()
    delta_time = (current_time - last_time) / 1000.0
    last_time = current_time

    if game_state.get("webcam_on", False):
        webcam_btn_rect = game_state["webcam_btn"].rect

        # Если кнопка зажата
        if webcam_btn_rect.collidepoint(mouse_pos) and mouse_buttons[0]:
            # Если только что зажали — запоминаем время
            if game_state["webcam_hold_start"] == 0:
                game_state["webcam_hold_start"] = pygame.time.get_ticks()

            # Если держим больше 0.3 секунды — активируем режим
            if pygame.time.get_ticks() - game_state["webcam_hold_start"] > 300:
                if not game_state["webcam_hold_activated"]:
                    game_state["webcam_hold_activated"] = True
                    game_state["webcam_fullscreen"] = True
                    game_state["webcam_btn"].text = "⬛ ВЕБКА ФОН"
        else:
            # Кнопка не зажата — сбрасываем таймер
            game_state["webcam_hold_start"] = 0

    # Обработка событий Pygame
    for event in pygame.event.get():
        if game_state["game_system"].handle_input(event):
            continue
        if game_state["game_system"].handle_mouse(event, mouse_pos):
            continue  # событие обработано консолью
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if game_state["game_system"].handle_click(mouse_pos):
                continue  # клик обработан
            if event.button == 1:
                mouse_x, mouse_y = event.pos

                # Проверяем клик по крестику в заголовке
                close_btn_rect = pygame.Rect(WIDTH - 30, 5, 20, 20)
                if close_btn_rect.collidepoint(mouse_pos):
                    running = False
                    continue

                if mouse_y < 30:
                    dragging = True
                    drag_offset_x = mouse_x
                    drag_offset_y = mouse_y
                    continue

                if game_state["multi_mode"]:
                    # Обработка мульти-кнопок
                    if handle_multi_click(mouse_pos, game_state):
                        continue
                    # Выбор фигуры
                    idx = get_object_at_pos(mouse_pos[0], mouse_pos[1],
                                            game_state["objects"], game_state)
                    game_state["selected_object_index"] = idx
                else:
                    # Проверяем слайдер
                    if speed_slider.handle_event(event, mouse_pos):
                        game_state["speed_slider_dragging"] = True
                        game_state["move_speed"] = speed_slider.get_value()
                        if game_state["cube_velocity"][0] != 0 or game_state["cube_velocity"][1] != 0:
                            direction_x = 1 if game_state["cube_velocity"][0] > 0 else -1 if game_state["cube_velocity"][0] < 0 else 1
                            direction_y = 1 if game_state["cube_velocity"][1] > 0 else -1 if game_state["cube_velocity"][1] < 0 else 1
                            game_state["cube_velocity"][0] = direction_x * game_state["move_speed"]
                            game_state["cube_velocity"][1] = direction_y * game_state["move_speed"]
                    else:
                        running = handle_mouse_click(mouse_pos, buttons, game_state, screen)

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                dragging = False
                speed_slider.handle_event(event, mouse_pos)
                game_state["speed_slider_dragging"] = False

        elif event.type == pygame.MOUSEMOTION:
            if dragging:
                x, y = event.pos
                dx = x - drag_offset_x
                dy = y - drag_offset_y

                hwnd = pygame.display.get_wm_info()['window']
                import win32gui
                import win32con

                win32gui.SetWindowPos(hwnd, 0,
                                      win32gui.GetWindowRect(hwnd)[0] + dx,
                                      win32gui.GetWindowRect(hwnd)[1] + dy,
                                      0, 0, win32con.SWP_NOSIZE)
            if game_state["speed_slider_dragging"]:
                speed_slider.handle_event(event, mouse_pos)
                game_state["move_speed"] = speed_slider.get_value()
                if game_state["cube_velocity"][0] != 0 or game_state["cube_velocity"][1] != 0:
                    direction_x = 1 if game_state["cube_velocity"][0] > 0 else -1 if game_state["cube_velocity"][0] < 0 else 1
                    direction_y = 1 if game_state["cube_velocity"][1] > 0 else -1 if game_state["cube_velocity"][1] < 0 else 1
                    game_state["cube_velocity"][0] = direction_x * game_state["move_speed"]
                    game_state["cube_velocity"][1] = direction_y * game_state["move_speed"]

    if mouse_buttons[0]:
        if game_state["show_cube"]:
            dvd_width, dvd_height = get_dvd_real_size()
            object_rect = pygame.Rect(
                game_state["cube_pos"][0] - dvd_width/2,
                game_state["cube_pos"][1] - dvd_height/2,
                dvd_width,
                dvd_height
            )
            is_over_object = object_rect.collidepoint(mouse_pos)
        else:
            if dvd_logos and game_state["current_dvd_color"] < len(dvd_logos):
                dvd_width, dvd_height = get_dvd_real_size()
                logo_rect = pygame.Rect(
                    game_state["cube_pos"][0] - dvd_width/2,
                    game_state["cube_pos"][1] - dvd_height/2,
                    dvd_width,
                    dvd_height
                )
                is_over_object = logo_rect.collidepoint(mouse_pos)
            else:
                is_over_object = False
        
        if is_over_object:
            if not game_state["is_zooming"]:
                game_state["is_zooming"] = True
                game_state["zoom_start_y"] = mouse_pos[1]
                game_state["zoom_start_scale"] = game_state["scale"]
    else:
        game_state["is_zooming"] = False
    
    # Применение зума
    if game_state["is_zooming"]:
        delta_y = game_state["zoom_start_y"] - mouse_pos[1]
        sensitivity = 0.008 if game_state["show_cube"] else 0.012
        zoom_factor = 1.0 + delta_y * sensitivity
        
        if game_state["show_cube"]:
            new_scale = game_state["zoom_start_scale"] * zoom_factor
            game_state["scale"] = max(0.1, min(3.0, new_scale))
        else:
            new_scale = game_state["zoom_start_scale"] * zoom_factor
            game_state["scale"] = max(0.2, min(5.0, new_scale))
    
    # ОБНОВЛЕНИЕ ТРАНСФОРМАЦИИ:
    if game_state.get("is_morphing", False):
       # Увеличиваем прогресс
       game_state["morph_progress"] += delta_time * 2.0
    
       if game_state["morph_progress"] >= 1.0:
          game_state["is_morphing"] = False
          game_state["morph_progress"] = 0.0
    
    # Обновление позиции
    if not game_state["multi_mode"]:
        game_state["cube_pos"][0] += game_state["cube_velocity"][0] * delta_time * 60
        game_state["cube_pos"][1] += game_state["cube_velocity"][1] * delta_time * 60

    if game_state["auto_rotate"] and game_state["show_cube"] and game_state["multi_mode"] is False:
        game_state["angle_x"] += game_state["rotation_speed"] * 0.8 * delta_time
        game_state["angle_y"] += game_state["rotation_speed"] * delta_time
        game_state["angle_z"] += game_state["rotation_speed"] * 0.5 * delta_time
    
    # ОТРИСОВКА
    # Сначала фон
    if game_state.get("webcam_fullscreen", False) and game_state.get("webcam_frame_full"):
        screen.blit(game_state["webcam_frame_full"], (0, 0))
    else:
        # ОТРИСОВКА
        if not game_state.get("trail_mode", False):
            screen.fill(game_state["bg_color"])
        # если trail_mode включён — НЕ очищаем экран
    
    draw_ui_toggle_indicator()

    # === ОБНОВЛЕНИЕ ПОЗИЦИИ ===
    if game_state["multi_mode"]:
        # Физика для каждого объекта
        for obj in game_state["objects"]:
            # Обновляем позицию
            obj["x"] += obj["vx"]
            obj["y"] += obj["vy"]

            # Получаем реальные границы
            bounds = get_object_bounds(obj, game_state)
            if bounds is None:
                continue

            min_x, max_x, min_y, max_y = bounds

            bounced = False

            # Отскок по X
            if min_x < 0 or max_x > WIDTH:
                obj["vx"] *= -1
                bounced = True

            # Отскок по Y
            if min_y < 0 or max_y > HEIGHT:
                obj["vy"] *= -1
                bounced = True

            if bounced:
                game_state["bounced"] = True

                # Коррекция позиции, чтобы не залезало за край
                if min_x < 0:
                    obj["x"] -= min_x
                elif max_x > WIDTH:
                    obj["x"] -= (max_x - WIDTH)

                if min_y < 0:
                    obj["y"] -= min_y
                elif max_y > HEIGHT:
                    obj["y"] -= (max_y - HEIGHT)

        # === КОЛЛИЗИИ МЕЖДУ ОБЪЕКТАМИ ===
        objects = game_state["objects"]
        for i in range(len(objects)):
            for j in range(i + 1, len(objects)):
                obj1 = objects[i]
                obj2 = objects[j]

                bounds1 = get_object_bounds(obj1, game_state)
                bounds2 = get_object_bounds(obj2, game_state)

                if not (bounds1 and bounds2):
                    continue

                min_x1, max_x1, min_y1, max_y1 = bounds1
                min_x2, max_x2, min_y2, max_y2 = bounds2

                # Проверяем пересечение
                if max_x1 >= min_x2 and max_x2 >= min_x1 and \
                        max_y1 >= min_y2 and max_y2 >= min_y1:

                    # === 1. ВЫТАЛКИВАНИЕ (разделение) ===
                    # Найдём наименьшее перекрытие
                    overlap_x = min(max_x1 - min_x2, max_x2 - min_x1)
                    overlap_y = min(max_y1 - min_y2, max_y2 - min_y1)

                    if overlap_x < overlap_y:
                        # Разделяем по X
                        if obj1["x"] < obj2["x"]:
                            # obj1 слева → двигаем его влево
                            obj1["x"] -= overlap_x / 2
                            obj2["x"] += overlap_x / 2
                        else:
                            obj1["x"] += overlap_x / 2
                            obj2["x"] -= overlap_x / 2
                    else:
                        # Разделяем по Y
                        if obj1["y"] < obj2["y"]:
                            obj1["y"] -= overlap_y / 2
                            obj2["y"] += overlap_y / 2
                        else:
                            obj1["y"] += overlap_y / 2
                            obj2["y"] -= overlap_y / 2

                    # === 2. ОТСКОК (только если есть скорость) ===
                    # Сохраняем старые скорости
                    vx1, vy1 = obj1["vx"], obj1["vy"]
                    vx2, vy2 = obj2["vx"], obj2["vy"]

                    # Отскок по нормали (упрощённо — обмен скоростями)
                    obj1["vx"] = vx2
                    obj1["vy"] = vy2
                    obj2["vx"] = vx1
                    obj2["vy"] = vy1

                    # === 3. СОБЫТИЕ ===
                    if "script_server" in game_state:
                        game_state["script_server"].trigger_collision(i, j)

        for obj in objects:
            old_shape = game_state["current_shape"]
            old_pos = game_state["cube_pos"].copy()
            old_scale = game_state["scale"]
            old_ax = game_state["angle_x"]
            old_ay = game_state["angle_y"]
            old_az = game_state["angle_z"]

            # Подменяем
            game_state["current_shape"] = obj["shape"]
            game_state["cube_pos"] = [obj["x"], obj["y"]]
            game_state["scale"] = obj["scale"]
            game_state["angle_x"] = obj["ax"]
            game_state["angle_y"] = obj["ay"]
            game_state["angle_z"] = obj["az"]

            draw_3d_shape()

            # Восстанавливаем
            game_state["current_shape"] = old_shape
            game_state["cube_pos"] = old_pos
            game_state["scale"] = old_scale
            game_state["angle_x"] = old_ax
            game_state["angle_y"] = old_ay
            game_state["angle_z"] = old_az
    else:
        if game_state["show_cube"]:
            projected_vertices = draw_3d_shape()

            if game_state["dvd_mode"] and projected_vertices:
                min_x = min(v[0] for v in projected_vertices)
                max_x = max(v[0] for v in projected_vertices)
                min_y = min(v[1] for v in projected_vertices)
                max_y = max(v[1] for v in projected_vertices)

                if min_x < 0 or max_x > WIDTH:
                    game_state["cube_velocity"][0] = -game_state["cube_velocity"][0]
                    game_state["bounced"] = True  # ← здесь
                    if min_x < 0:
                        game_state["cube_pos"][0] += -min_x
                    else:
                        game_state["cube_pos"][0] -= max_x - WIDTH

                if min_y < 0 or max_y > HEIGHT:
                    game_state["cube_velocity"][1] = -game_state["cube_velocity"][1]
                    game_state["bounced"] = True  # ← здесь
                    if min_y < 0:
                        game_state["cube_pos"][1] += -min_y
                    else:
                        game_state["cube_pos"][1] -= max_y - HEIGHT
        else:
            draw_dvd_logo()

            if dvd_logos and game_state["current_dvd_color"] < len(dvd_logos):
                dvd_width, dvd_height = get_dvd_real_size()
                left_edge = game_state["cube_pos"][0] - dvd_width/2
                right_edge = game_state["cube_pos"][0] + dvd_width/2
                top_edge = game_state["cube_pos"][1] - dvd_height/2
                bottom_edge = game_state["cube_pos"][1] + dvd_height/2
            
                if left_edge < 0 or right_edge > WIDTH:
                    game_state["cube_velocity"][0] = -game_state["cube_velocity"][0]
                    game_state["current_dvd_color"] = (game_state["current_dvd_color"] + 1) % len(DVD_COLORS)
                    game_state["bounced"] = True  # ← здесь
                    if left_edge < 0:
                        game_state["cube_pos"][0] = dvd_width/2 + 1
                    else:
                        game_state["cube_pos"][0] = WIDTH - dvd_width/2 - 1
            
                if top_edge < 0 or bottom_edge > HEIGHT:
                    game_state["cube_velocity"][1] = -game_state["cube_velocity"][1]
                    game_state["current_dvd_color"] = (game_state["current_dvd_color"] + 1) % len(DVD_COLORS)
                    game_state["bounced"] = True  # ← здесь
                    if top_edge < 0:
                        game_state["cube_pos"][1] = dvd_height/2 + 1
                    else:
                        game_state["cube_pos"][1] = HEIGHT - dvd_height/2 - 1

    # В конце цикла, после отрисовки
    if game_state.get("multiplayer") and game_state["multiplayer"].state.in_room:
        game_state["multiplayer"].update_state()

        # Обновляем текст кнопок в соответствии с текущим состоянием
        if "wireframe_toggle" in game_state:
            game_state["wireframe_toggle"].text = "КАРКАС: ВКЛ" if game_state["with_karkas"] else "КАРКАС: ВЫКЛ"

        if "faces_toggle" in game_state:
            game_state["faces_toggle"].text = "ГРАНИ: ВКЛ" if game_state["draw_faces"] else "ГРАНИ: ВЫКЛ"

        if "points_toggle" in game_state:
            game_state["points_toggle"].text = "ТОЧКИ: ВКЛ" if game_state["draw_points"] else "ТОЧКИ: ВЫКЛ"

        if "dvd_toggle" in game_state:
            game_state["dvd_toggle"].text = "DVD: ВКЛ" if game_state["dvd_mode"] else "DVD: ВЫКЛ"

        if "rotate_toggle" in game_state:
            game_state["rotate_toggle"].text = "АВТО: ВКЛ" if game_state["auto_rotate"] else "АВТО: ВЫКЛ"

        if "shape_toggle_btn" in game_state:
            game_state["shape_toggle_btn"].text = f"ФОРМА: {SHAPE_NAMES[game_state['current_shape']]}"

        # Обновляем цвета кнопок (опционально)
        game_state["wireframe_toggle"].color = (100, 200, 100) if game_state["with_karkas"] else (80, 80, 100)
        game_state["faces_toggle"].color = (100, 150, 200) if game_state["draw_faces"] else (80, 80, 100)
        game_state["points_toggle"].color = (200, 100, 200) if game_state["draw_points"] else (80, 80, 100)

    draw_ui()

    if game_state.get("trail_mode", False):
        fade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        fade.fill((0, 0, 0, 8))  # слабое затемнение каждый кадр
        screen.blit(fade, (0, 0))

    if game_state.get("webcam_on", False) and game_state.get("webcam_frame") and not game_state.get("webcam_fullscreen", False):
        webcam_rect = pygame.Rect(WIDTH - 180, HEIGHT - 220, 160, 120)
        screen.blit(game_state["webcam_frame"], webcam_rect)
        pygame.draw.rect(screen, (0, 255, 0), webcam_rect, 2)
        
    font = pygame.font.Font(None, 24)
    fps_text = font.render(f"FPS: {int(clock.get_fps())}", True, WHITE)
    screen.blit(fps_text, (10, 40))

    if game_state.get("webcam_on", False) and game_state["webcam_cap"]:
        ret, frame = game_state["webcam_cap"].read()
        if ret:
            if game_state.get("webcam_fullscreen", False):
                frame = cv2.resize(frame, (WIDTH, HEIGHT))
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = np.rot90(frame)
                frame = np.flipud(frame)
                game_state["webcam_frame_full"] = pygame.surfarray.make_surface(frame)
                game_state["webcam_frame"] = None
            else:
                frame = cv2.resize(frame, (160, 120))
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = np.rot90(frame)
                game_state["webcam_frame"] = pygame.surfarray.make_surface(frame)
                game_state["webcam_frame_full"] = None

    draw_titlebar()

    if "game_system" in game_state:
        game_state["game_system"].draw_ui(screen)

    if game_state.get("is_recording", False):
        capture_frame(screen, game_state)

    clock.tick(FPS)
    pygame.display.flip()

# Останавливаем запись если она идет
if game_state.get("is_recording", False):
    stop_recording(game_state)
pygame.quit()
sys.exit()