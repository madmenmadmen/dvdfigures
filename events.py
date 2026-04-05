import random
import math
import pygame.display
from render import create_vertices_and_faces
from recording import *
from control_classes import *

def is_click_in_ui_toggle_area(mouse_pos):
    """Проверяет, кликнули ли в область переключения UI (правый верхний угол)"""
    toggle_area = pygame.Rect(WIDTH - 50, 30, 50, 50)
    return toggle_area.collidepoint(mouse_pos)

def toggle_ui_visibility(game_state, buttons_list):
    """Переключение видимости всего UI"""
    game_state["ui_visible"] = not game_state.get("ui_visible", True)
    
    # Список всех элементов UI
    ui_elements = []
    
    # Добавляем все кнопки из game_state
    for key, value in game_state.items():
        if isinstance(value, Button):
            ui_elements.append(value)
    
    # Добавляем кнопки из buttons_list
    for btn_info in buttons_list:
        ui_elements.append(btn_info["button"])
    
    # Добавляем слайдер
    if "speed_slider" in game_state:
        ui_elements.append(game_state["speed_slider"])
    
    # Скрываем или показываем все элементы
    for element in ui_elements:
        if game_state["ui_visible"]:
            if hasattr(element, 'show'):
                element.show()
        else:
            if hasattr(element, 'hide'):
                element.hide()
    
    return game_state["ui_visible"]

def _save_screenshot(surface, game_state):
    """Сохраняет скриншот с эффектом вспышки"""
    import datetime
    import os
    
    # Создаем папку если нет
    screenshots_dir = "screenshots"
    if not os.path.exists(screenshots_dir):
        os.makedirs(screenshots_dir)
    
    # Генерируем имя файла
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{screenshots_dir}/screenshot_{timestamp}.png"
    
    # Сохраняем
    pygame.image.save(surface, filename)
    
    # Обновляем счетчик
    if "screenshot_count" not in game_state:
        game_state["screenshot_count"] = 0
    game_state["screenshot_count"] += 1
    
    # Показываем сообщение
    print(f"📸 Скриншот сохранен: {filename}")
    print(f"📁 Папка: {os.path.abspath(screenshots_dir)}")
    
    return filename

def handle_mouse_click(mouse_pos, buttons, game_state, screen):
    """Обработка кликов мыши"""
    if is_click_in_ui_toggle_area(mouse_pos):
         ui_visible = toggle_ui_visibility(game_state, buttons)
    
    # Проверка кнопок
    for button_info in buttons:
        if button_info["button"].check_click(mouse_pos):
            if game_state["ui_visible"] == False:
            	 action = "67"
            else:
            	 action = button_info["action"]
            if action == "exit":
                return False
            elif action == "multi_toggle":
                game_state["multi_mode"] = not game_state["multi_mode"]
                if game_state["multi_mode"]:
                    # Скрываем основную фигуру
                    game_state["show_cube"] = False
                game_state["multi_toggle"].text = "ВЫХОД МУЛЬТИ" if game_state["multi_mode"] else "МУЛЬТИ"
            elif action == "alpha_up":
                game_state["face_alpha"] = min(
                    game_state.get("alpha_max", 255),
                    game_state.get("face_alpha", 255) + 15
                )
                return True
            elif action == "alpha_down":
                game_state["face_alpha"] = max(
                    game_state.get("alpha_min", 50),
                    game_state.get("face_alpha", 255) - 15
                )
                return True
            elif action == "open_multiplayer":
                return True
            elif action == "toggle_trail":
                game_state["trail_mode"] = not game_state["trail_mode"]
                new_text = "🎨 TRAIL: ВКЛ" if game_state["trail_mode"] else "🎨 TRAIL: ВЫКЛ"
                new_color = (200, 100, 255) if game_state["trail_mode"] else (150, 100, 200)

                button_info["button"].text = new_text
                button_info["button"].color = new_color

                if "trail_btn" in game_state:
                    game_state["trail_btn"].text = new_text
                    game_state["trail_btn"].color = new_color
                return True
            elif action == "toggle_voice_size":
                if not game_state.get("voice_size_mode", False):
                    # Включаем
                    game_state["voice_size_original"] = game_state["scale"]
                    game_state["voice_size_mode"] = True
                    game_state["voice"].start()
                    button_info["button"].text = "🎤 ВЫКЛ ГОЛОС"
                else:
                    # Выключаем
                    game_state["voice_size_mode"] = False
                    game_state["voice"].stop()
                    game_state["scale"] = game_state["voice_size_original"]
                    button_info["button"].text = "🎤 РАЗМЕР ОТ ГОЛОСА"
                return True
            elif action == "toggle_webcam":
                if game_state.get("webcam_on", False):
                    # Выключаем вебку
                    if game_state["webcam_cap"]:
                        game_state["webcam_cap"].release()
                    game_state["webcam_cap"] = None
                    game_state["webcam_on"] = False
                    game_state["webcam_btn"].text = "📹 ВЕБКА"

                    game_state["webcam_frame"] = None
                    game_state["webcam_frame_full"] = None

                    # В обработчике toggle_webcam
                    game_state["webcam_hold_start"] = 0
                    game_state["webcam_hold_activated"] = False
                else:
                    # Включаем вебку
                    import cv2
                    cap = cv2.VideoCapture(0)
                    if cap.isOpened():
                        game_state["webcam_cap"] = cap
                        game_state["webcam_on"] = True
                        game_state["webcam_btn"].text = "⏹️ ВЕБКА"
                    else:
                        print("❌ Вебка не открывается")
                return True
            elif action == "take_screenshot":
              # Запускаем эффект вспышки
              game_state["flash_effect"] = True
              game_state["flash_start_time"] = pygame.time.get_ticks()
    
              _save_screenshot(screen, game_state)
              return True
            elif action == "toggle_recording":    
              if game_state.get("is_recording", False):
                stop_recording(game_state)
                if "record_button" in game_state:
                  game_state["record_button"].text = "🎬 ЗАПИСЬ"
                  game_state["record_button"].color = (150, 50, 50)
              else:
               if start_recording(game_state):
                  if "record_button" in game_state:
                    game_state["record_button"].text = "⏹️ СТОП"
                    game_state["record_button"].color = (200, 20, 20)
               return True
            elif action == "toggle_mode":
                 game_state["show_cube"] = not game_state["show_cube"]
                 
                 if game_state["show_cube"] == False:
                 	game_state["cube_pos"] = INITIAL_CUBE_POS
    
                 new_text = "DVD РЕЖИМ" if game_state["show_cube"] else "3D РЕЖИМ"
                 new_color = (200, 150, 100) if game_state["show_cube"] else (100, 150, 200)
    
                 button_info["button"].text = new_text
                 button_info["button"].color = new_color
    
                 if "mode_toggle_btn" in game_state:
                     game_state["mode_toggle_btn"].text = new_text
                     game_state["mode_toggle_btn"].color = new_color
    
                 return True
            elif action == "change_bg_color":
                  from color_picker import UniversalColorPicker
    
                  picker = UniversalColorPicker(game_state["bg_color"])
                  new_color = picker.pick_color()
    
                  if new_color:
                     game_state["bg_color"] = new_color   
                  return True
            elif action == "toggle_points":
                  game_state["draw_points"] = not  game_state["draw_points"]
                  new_text = "ТОЧКИ: ВКЛ" if  game_state["draw_points"] else  "ТОЧКИ: ВЫКЛ"
                  new_color = (200, 100, 200) if game_state["draw_points"] else (80, 80, 100)
    
                  button_info["button"].text = new_text
                  button_info["button"].color = new_color
    
                  if "points_toggle" in game_state:
                     game_state["points_toggle"].text = new_text
                     game_state["points_toggle"].color = new_color

                  if game_state.get("multiplayer") and game_state["multiplayer"].state.in_room:
                      game_state["multiplayer"].update_state()
                  return True
            elif action == "toggle_wireframe":
                # Импортируем и меняем глобальную переменную
                
                # Меняем значение
                game_state["with_karkas"] = not game_state["with_karkas"]
                
                # Обновляем текст кнопки
                new_text = "КАРКАС: ВКЛ" if game_state["with_karkas"] else "КАРКАС: ВЫКЛ"
                new_color = (100, 200, 100) if game_state["with_karkas"] else (80, 80, 100)
                
                button_info["button"].text = new_text
                button_info["button"].color = new_color
                
                # Также обновляем кнопку в game_state
                if "wireframe_toggle" in game_state:
                    game_state["wireframe_toggle"].text = new_text
                    game_state["wireframe_toggle"].color = new_color
                if game_state.get("multiplayer") and game_state["multiplayer"].state.in_room:
                    game_state["multiplayer"].update_state()
                return True
            elif action == "toggle_faces":
                game_state["draw_faces"] = not game_state["draw_faces"]
                
                new_text = "ГРАНИ: ВКЛ" if game_state["draw_faces"] else "ГРАНИ: ВЫКЛ"
                new_color = (100, 150, 200) if game_state["draw_faces"] else (80, 80, 100)
                
                button_info["button"].text = new_text
                button_info["button"].color = new_color
                
                if "faces_toggle" in game_state:
                    game_state["faces_toggle"].text = new_text
                    game_state["faces_toggle"].color = new_color

                if game_state.get("multiplayer") and game_state["multiplayer"].state.in_room:
                    game_state["multiplayer"].update_state()

                return True
            elif action == "toggle_rotate":
                game_state["auto_rotate"] = not game_state["auto_rotate"]
                game_state["rotate_toggle"].text = "АВТО: ВКЛ" if game_state["auto_rotate"] else "АВТО: ВЫКЛ"
            elif action == "toggle_dvd":
                game_state["dvd_mode"] = not game_state["dvd_mode"]
                game_state["dvd_toggle"].text = "DVD: ВКЛ" if game_state["dvd_mode"] else "DVD: ВЫКЛ"
                if not game_state["dvd_mode"]:
                    game_state["cube_velocity"] = [0, 0]
                else:
                    game_state["cube_velocity"] = INITIAL_CUBE_VELOCITY.copy()
            elif action == "speed_up":
                game_state["rotation_speed"] += 0.005
            elif action == "speed_down":
                game_state["rotation_speed"] -= 0.005
            elif action == "color_next":
                game_state["current_dvd_color"] = (game_state["current_dvd_color"] + 1) % len(DVD_COLORS)
            elif action == "color_prev":
                game_state["current_dvd_color"] = (game_state["current_dvd_color"] - 1) % len(DVD_COLORS)
            elif action == "toggle_shape":
                game_state["prev_shape"] = game_state["current_shape"]
                
                game_state["current_shape"] = (game_state["current_shape"] + 1) % len(SHAPES)
                
                game_state["is_morphing"] = True
                game_state["morph_progress"] = 0.0
                
                game_state["shape_toggle_btn"].text = f"ФОРМА: {SHAPE_NAMES[game_state['current_shape']]}"
            elif action.startswith("rotate_"):
                handle_rotation_click(action, game_state)
            return True
    
    # Проверка клика по фигуре
    distance = ((mouse_pos[0] - game_state["cube_pos"][0])**2 + 
                (mouse_pos[1] - game_state["cube_pos"][1])**2)**0.5
    
    if distance < 100:
        if game_state["show_cube"]:
            # Изменяем цвета граней
            vertices, faces = create_vertices_and_faces(SHAPES[game_state["current_shape"]])
            num_faces = len(faces)
            
            # Обновляем массив цветов, если нужно
            while len(game_state["face_colors"]) < num_faces:
                game_state["face_colors"].append(WHITE)
            
            # Меняем цвета
            for i in range(num_faces):
                r = random.randint(50, 255)
                g = random.randint(50, 255)
                b = random.randint(50, 255)
                game_state["face_colors"][i] = (r, g, b)
        else:
            game_state["current_dvd_color"] = (game_state["current_dvd_color"] + 1) % len(DVD_COLORS)
    
    return True

def handle_rotation_click(action, game_state):
    """Обработка нажатий кнопок вращения"""
    if action == "rotate_up":
        game_state["angle_x"] += ROTATION_INCREMENT
    elif action == "rotate_down":
        game_state["angle_x"] -= ROTATION_INCREMENT
    elif action == "rotate_left":
        game_state["angle_y"] += ROTATION_INCREMENT
    elif action == "rotate_right":
        game_state["angle_y"] -= ROTATION_INCREMENT
    elif action == "rotate_z_left":
        game_state["angle_z"] += ROTATION_INCREMENT
    elif action == "rotate_z_right":
        game_state["angle_z"] -= ROTATION_INCREMENT


def handle_multi_click(mouse_pos, game_state):
    buttons = game_state["multi_buttons"]

    # Выход из мульти-режима
    if buttons["exit_multi"].check_click(mouse_pos):
        game_state["multi_mode"] = False
        game_state["show_cube"] = True
        game_state["multi_toggle"].text = "ВЫХОД МУЛЬТИ" if game_state["multi_mode"] else "МУЛЬТИ"
        return True

    # Добавить объект
    if buttons["add_object"].check_click(mouse_pos):
        shape = game_state.get("multi_selected_shape", 0)
        game_state["objects"].append({
            "shape": shape,
            "x": 500, "y": 350,
            "vx": 0, "vy": 0,
            "scale": 1.0,
            "ax": 0, "ay": 0, "az": 0
        })
        return True

    # Удалить объект
    if buttons["remove_object"].check_click(mouse_pos):
        idx = game_state.get("selected_object_index", -1)
        if idx >= 0 and idx < len(game_state["objects"]):
            game_state["objects"].pop(idx)
            game_state["selected_object_index"] = -1
        return True

    # Выбор формы
    if buttons["shape_selector"].check_click(mouse_pos):
        current = game_state.get("multi_selected_shape", 0)
        next_shape = (current + 1) % len(SHAPE_NAMES)
        game_state["multi_selected_shape"] = next_shape
        buttons["shape_selector"].text = f"ФОРМА: {SHAPE_NAMES[next_shape]}"
        return True

    return False

def create_buttons(game_state):
    """Создание всех кнопок интерфейса"""
    buttons = []
    
    exit_button = Button(420, 105, 150, 60, "ВЫХОД", BUTTON_RED)
    rotate_toggle = Button(20, 30, 200, 60, "АВТО: ВКЛ")
    dvd_toggle = Button(20, 105, 200, 60, "DVD: ВКЛ")
    speed_up_btn = Button(20, 180, 100, 60, "СКОР+")
    speed_down_btn = Button(130, 180, 100, 60, "СКОР-")
    color_next_btn = Button(420, 180, 170, 60, "ЦВЕТ+")
    color_prev_btn = Button(420, 30, 170, 60, "ЦВЕТ-")
    shape_toggle_btn = Button(580, 105, 170, 60, f"ФОРМА: {SHAPE_NAMES[0]}", (150, 100, 255))
    
    # Кнопки вращения
    rotate_buttons = [
        Button(WIDTH - 280, HEIGHT - 180, 80, 80, "W"),
        Button(WIDTH - 280, HEIGHT - 80, 80, 80, "S"),
        Button(WIDTH - 380, HEIGHT - 80, 80, 80, "A"),
        Button(WIDTH - 180, HEIGHT - 80, 80, 80, "D"),
        Button(WIDTH - 480, HEIGHT - 80, 80, 80, "Q"),
        Button(WIDTH - 80, HEIGHT - 80, 80, 80, "E"),
    ]
    
    wireframe_text = "КАРКАС: ВКЛ" if game_state["with_karkas"] else "КАРКАС: ВЫКЛ"
    wireframe_color = (100, 200, 100) if game_state["with_karkas"] else (80, 80, 100)
    wireframe_toggle = Button(240, 30, 170, 60, wireframe_text, wireframe_color)
    
    faces_text = "ГРАНИ: ВКЛ" if game_state["draw_faces"] else "ГРАНИ: ВЫКЛ"
    faces_color = (100, 150, 200) if game_state["draw_faces"] else (80, 80, 100)
    faces_toggle = Button(240, 105, 170, 60, faces_text, faces_color)  # Под кнопкой каркаса
    
    points_text = "ТОЧКИ: ВКЛ" if game_state["draw_points"] else "ТОЧКИ: ВЫКЛ"
    points_color = (200, 100, 200) if game_state["draw_points"] else (80, 80, 100)
    points_toggle = Button(240, 180, 170, 60, points_text, points_color)  # Под другими кнопками
    
    bg_color_btn = Button(20, 250, 170, 60, "ФОН", (150, 150, 200))
    
    mode_text = "DVD РЕЖИМ" if game_state["show_cube"] else "3D РЕЖИМ"
    mode_color = (200, 150, 100) if game_state["show_cube"] else (100, 150, 200)
    mode_toggle_btn = Button(200, 250, 170, 60, mode_text, mode_color) 
    
    screenshot_btn = Button(
    380,  # X
    250, # Y (над кнопкой записи)
    170, 60,
    "СНИМОК",
    (100, 200, 255)  # Голубой цвет
    )

    game_state["screenshot_btn"] = screenshot_btn

    buttons.append({"button": screenshot_btn, "action": "take_screenshot"})

    webcam_btn = Button(
        20,  # X
        390,  # Y
        170, 60,
        "ВЕБКА",
        (100, 150, 200)  # синеватый
    )
    buttons.append({"button": webcam_btn, "action": "toggle_webcam"})
    game_state["webcam_btn"] = webcam_btn

    voice_size_btn = Button(
        200,  # X
        320,  # Y
        170, 60,
        "РАЗМЕР ОТ ГОЛОСА",
        (100, 150, 200)  # синеватый
    )
    buttons.append({"button": voice_size_btn, "action": "toggle_voice_size"})
    game_state["voice_size_btn"] = voice_size_btn

    trail_btn = Button(
        20,  # X
        460,  # Y (под кнопкой вебки)
        170, 60,
        "TRAIL: ВЫКЛ",
        (150, 100, 200)  # фиолетовый
    )
    buttons.append({"button": trail_btn, "action": "toggle_trail"})
    game_state["trail_btn"] = trail_btn

    # Кнопки прозрачности
    alpha_up_btn = Button(
        290,  # X
        390,  # Y (подстройте под ваш интерфейс)
        80, 60,
        "α+",
        (100, 150, 200)
    )

    alpha_down_btn = Button(
        200,  # X
        390,  # Y
        80, 60,
        "α-",
        (100, 150, 200)
    )

    multi_toggle = Button(
        20, 530, 110, 30,
        "МУЛЬТИ", (100, 180, 100)
    )

    # Кнопки мульти-режима (создаются один раз)
    multi_buttons = {
        "exit_multi": Button(WIDTH - 100, 40, 90, 30, "ВЫХОД", (200, 60, 60)),
        "add_object": Button(10, 70, 120, 30, "➕ ДОБАВИТЬ", (80, 150, 200)),
        "remove_object": Button(140, 70, 140, 30, "🗑️ УДАЛИТЬ", (200, 100, 60)),
        "shape_selector": Button(290, 70, 200, 30, f"ФОРМА: {SHAPE_NAMES[0]}", (100, 180, 100))
    }
    game_state["multi_buttons"] = multi_buttons
    game_state["selected_object_index"] = -1  # индекс выбранной фигуры

    # Добавляем в game_state
    game_state["alpha_up_btn"] = alpha_up_btn
    game_state["alpha_down_btn"] = alpha_down_btn
    game_state["multi_toggle"] = multi_toggle

    # Добавляем в buttons список
    buttons.append({"button": alpha_up_btn, "action": "alpha_up"})
    buttons.append({"button": alpha_down_btn, "action": "alpha_down"})
    buttons.append({"button": multi_toggle, "action": "multi_toggle"})

    # Сохраняем ссылки на кнопки в game_state
    game_state.update({
        "exit_button": exit_button,
        "rotate_toggle": rotate_toggle,
        "dvd_toggle": dvd_toggle,
        "speed_up_btn": speed_up_btn,
        "speed_down_btn": speed_down_btn,
        "color_next_btn": color_next_btn,
        "color_prev_btn": color_prev_btn,
        "shape_toggle_btn": shape_toggle_btn,
        "rotate_buttons": rotate_buttons,
        "wireframe_toggle": wireframe_toggle,
        "faces_toggle": faces_toggle,
        "points_toggle": points_toggle,
        "bg_color_btn": bg_color_btn,
        "mode_toggle_btn": mode_toggle_btn
    })
    
    # Добавляем кнопки в список с действиями
    buttons.append({"button": exit_button, "action": "exit"})
    buttons.append({"button": rotate_toggle, "action": "toggle_rotate"})
    buttons.append({"button": dvd_toggle, "action": "toggle_dvd"})
    buttons.append({"button": speed_up_btn, "action": "speed_up"})
    buttons.append({"button": speed_down_btn, "action": "speed_down"})
    buttons.append({"button": color_next_btn, "action": "color_next"})
    buttons.append({"button": color_prev_btn, "action": "color_prev"})
    buttons.append({"button": shape_toggle_btn, "action": "toggle_shape"})
    
    # Кнопки вращения
    rotate_actions = ["rotate_up", "rotate_down", "rotate_left", 
                     "rotate_right", "rotate_z_left", "rotate_z_right"]
    for i, btn in enumerate(rotate_buttons):
        buttons.append({"button": btn, "action": rotate_actions[i]})
    
    # Добавляем в список кнопок с действием
    buttons.append({"button": wireframe_toggle, "action": "toggle_wireframe"})
    buttons.append({"button": faces_toggle, "action": "toggle_faces"})
    # В buttons список
    buttons.append({"button": points_toggle, "action": "toggle_points"})
    buttons.append({"button": bg_color_btn, "action": "change_bg_color"})
    buttons.append({"button": mode_toggle_btn, "action": "toggle_mode"})
    
    return buttons
    
# ====== ВИДЕОЗАПИСЬ ======

class RecordButton(Button):
    """Кнопка записи видео с индикатором"""
    def __init__(self, x, y, width, height, text, color=None, game_state_ref=None):
        super().__init__(x, y, width, height, text, color)
        self.game_state = game_state_ref
        self.recording_color = (255, 50, 50)  # Красный при записи
        
    def draw(self, surface):
        # Рисуем стандартную кнопку
        super().draw(surface)
        
        # Добавляем индикатор записи если идет запись
        if self.game_state and self.game_state.get("is_recording", False):
            # Красная точка в углу кнопки
            indicator_radius = 8
            indicator_pos = (self.rect.right - 15, self.rect.top + 15)
            pygame.draw.circle(surface, self.recording_color, indicator_pos, indicator_radius)
            
            # Анимация пульсации
            pulse = abs(pygame.time.get_ticks() % 1000 - 500) / 500.0
            pulse_radius = int(indicator_radius * (1.0 + 0.3 * pulse))
            pygame.draw.circle(surface, self.recording_color, indicator_pos, pulse_radius, 2)

def add_recording_button(buttons, game_state):
    """Добавляет кнопку записи видео в интерфейс"""
    record_btn = RecordButton(
        20,  # Позиция X (рядом с кнопкой формы)
        320,  # Позиция Y (над кнопками вращения)
        170, 60, 
        "ЗАПИСЬ",
        (150, 50, 50),  # Темно-красный
        game_state
    )
    
    # Сохраняем ссылку в game_state
    game_state["record_button"] = record_btn
    
    # Добавляем в список кнопок
    buttons.append({"button": record_btn, "action": "toggle_recording"})
    
    return record_btn
    
# В events.py добавьте создание слайдера
def create_speed_slider(game_state):
    """Создание слайдера скорости"""
    slider_x = 240  # Рядом с другими кнопками
    slider_y = 670  # Под кнопками граней/каркаса
    
    slider = SpeedSlider(
        slider_x, slider_y, 
        SPEED_SLIDER_WIDTH, SPEED_SLIDER_HEIGHT,
        MIN_SPEED, MAX_SPEED, 
        game_state.get("move_speed", DEFAULT_SPEED)
    )
    slider.game_state = game_state  # ← ВОТ ЭТА СТРОКА
    return slider