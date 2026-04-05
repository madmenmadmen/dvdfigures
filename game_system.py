# game_system.py
import pygame
from config import WIDTH, HEIGHT
from control_classes import Button


class Game:
    def __init__(self, game_state):
            self.game_state = game_state
            self.initialized = True
            self.console_messages = []
            self.max_messages = 20
            self.input_buffer = ""
            self.input_active = False
            self.input_callback = None

            self.console_rect = pygame.Rect(10, HEIGHT - 200, 400, 150)  # x, y, ширина, высота
            self.console_visible = False
            self.font_size = 18
            self.font = pygame.font.Font(None, self.font_size)

            self.dragging = False
            self.drag_offset_x = 0
            self.drag_offset_y = 0
            self.resizing = False
            self.resize_edge = None  # "top", "bottom", "left", "right", "corner"
            self.min_width = 200
            self.min_height = 100

            self.bg_color = (20, 20, 30, 200)  # полупрозрачный
            self.border_color = (100, 100, 150)
            self.text_color = (220, 220, 220)
            self.input_color = (100, 255, 100)

            self.clear_btn_rect = None  # будет обновляться при отрисовке

            # Кнопка для показа/скрытия консоли
            self.toggle_btn = Button(
                20, 600,  # координаты
                170, 60,
                "ПОКАЗАТЬ",
                (100, 80, 150)
            )

            # Сохраняем ссылку в game_state для доступа из других мест
            game_state["console_toggle_btn"] = self.toggle_btn

    def handle_click(self, mouse_pos):
        """Обработка клика по кнопке консоли"""
        if self.toggle_btn.check_click(mouse_pos):
            self.toggle_console()
            # Обновляем текст кнопки
            if self.console_visible:
                self.toggle_btn.text = "КОНСОЛЬ"
            else:
                self.toggle_btn.text = "ПОКАЗАТЬ"
            return True
        return False

    def draw_ui(self, screen):
        """Отрисовка элементов UI консоли"""
        self.toggle_btn.draw(screen)

        # Если консоль видна, рисуем и её
        if self.console_visible:
            self.draw_console(screen)

    def clear_console(self):
        """Очистка консоли"""
        self.console_messages = []

    def toggle_console(self):
        """Включить/выключить видимость консоли"""
        self.console_visible = not self.console_visible

    def handle_mouse(self, event, mouse_pos):
        """Обработка мыши для перемещения и масштабирования"""
        if not self.console_visible:
            return False

        mouse_x, mouse_y = mouse_pos

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Проверяем клик по кнопке очистки
            if self.clear_btn_rect and self.clear_btn_rect.collidepoint(mouse_pos):
                self.clear_console()
                return True

            # Проверяем, попали ли в край для изменения размера
            edge = self.get_resize_edge(mouse_pos)
            if edge:
                self.resizing = True
                self.resize_edge = edge
                self.resize_start_x = mouse_x
                self.resize_start_y = mouse_y
                self.resize_start_rect = self.console_rect.copy()
                return True

            # Проверяем, попали ли в заголовок для перемещения
            title_rect = pygame.Rect(self.console_rect.x, self.console_rect.y,
                                     self.console_rect.width, 20)
            if title_rect.collidepoint(mouse_pos):
                self.dragging = True
                self.drag_offset_x = mouse_x - self.console_rect.x
                self.drag_offset_y = mouse_y - self.console_rect.y
                return True

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
            self.resizing = False
            self.resize_edge = None

        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                # Перемещение консоли
                new_x = mouse_x - self.drag_offset_x
                new_y = mouse_y - self.drag_offset_y
                # Ограничиваем краями экрана
                new_x = max(0, min(WIDTH - self.console_rect.width, new_x))
                new_y = max(0, min(HEIGHT - self.console_rect.height, new_y))
                self.console_rect.x = new_x
                self.console_rect.y = new_y
                return True

            elif self.resizing:
                # Изменение размера
                self.resize_console(mouse_x, mouse_y)
                return True

        return False

    def get_resize_edge(self, mouse_pos):
        """Определяет, за какой край тянут"""
        if not self.console_rect.collidepoint(mouse_pos):
            return None

        mouse_x, mouse_y = mouse_pos
        threshold = 10  # чувствительность в пикселях

        # Углы (приоритетнее)
        if (abs(mouse_x - self.console_rect.right) < threshold and
                abs(mouse_y - self.console_rect.bottom) < threshold):
            return "corner"
        if (abs(mouse_x - self.console_rect.left) < threshold and
                abs(mouse_y - self.console_rect.bottom) < threshold):
            return "corner"
        if (abs(mouse_x - self.console_rect.right) < threshold and
                abs(mouse_y - self.console_rect.top) < threshold):
            return "corner"
        if (abs(mouse_x - self.console_rect.left) < threshold and
                abs(mouse_y - self.console_rect.top) < threshold):
            return "corner"

        # Края
        if abs(mouse_x - self.console_rect.right) < threshold:
            return "right"
        if abs(mouse_x - self.console_rect.left) < threshold:
            return "left"
        if abs(mouse_y - self.console_rect.bottom) < threshold:
            return "bottom"
        if abs(mouse_y - self.console_rect.top) < threshold:
            return "top"

        return None

    def resize_console(self, mouse_x, mouse_y):
        """Изменение размера консоли"""
        new_rect = self.resize_start_rect.copy()

        if self.resize_edge == "right" or self.resize_edge == "corner":
            new_width = max(self.min_width, mouse_x - self.resize_start_rect.x)
            new_rect.width = new_width

        if self.resize_edge == "left" or self.resize_edge == "corner":
            new_width = max(self.min_width, self.resize_start_rect.right - mouse_x)
            if new_width > self.min_width:
                new_rect.x = mouse_x
                new_rect.width = new_width

        if self.resize_edge == "bottom" or self.resize_edge == "corner":
            new_height = max(self.min_height, mouse_y - self.resize_start_rect.y)
            new_rect.height = new_height

        if self.resize_edge == "top" or self.resize_edge == "corner":
            new_height = max(self.min_height, self.resize_start_rect.bottom - mouse_y)
            if new_height > self.min_height:
                new_rect.y = mouse_y
                new_rect.height = new_height

        # Ограничиваем экраном
        if new_rect.right > WIDTH:
            new_rect.width = WIDTH - new_rect.x
        if new_rect.bottom > HEIGHT:
            new_rect.height = HEIGHT - new_rect.y
        if new_rect.x < 0:
            new_rect.width += new_rect.x
            new_rect.x = 0
        if new_rect.y < 0:
            new_rect.height += new_rect.y
            new_rect.y = 0

        self.console_rect = new_rect

    def handle_input(self, event):
        """Обработка ввода (вызывать из основного цикла)"""
        if not self.input_active:
            return False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                if self.input_callback:
                    self.input_callback(self.input_buffer)
                self.input_active = False
                self.input_buffer = ""
                return True
            elif event.key == pygame.K_BACKSPACE:
                self.input_buffer = self.input_buffer[:-1]
            elif event.key == pygame.K_ESCAPE:
                self.input_active = False
                self.input_buffer = ""
                if self.input_callback:
                    self.input_callback(None)
                return True
            else:
                if event.unicode:
                    self.input_buffer += event.unicode
        return True

    def draw_console(self, screen):
        """Отрисовка консоли"""
        if not self.console_visible:
            return

        # Фон консоли
        console_bg = pygame.Surface((self.console_rect.width, self.console_rect.height), pygame.SRCALPHA)
        console_bg.fill(self.bg_color)
        screen.blit(console_bg, (self.console_rect.x, self.console_rect.y))

        # Заголовок с кнопками
        title_rect = pygame.Rect(self.console_rect.x, self.console_rect.y,
                                 self.console_rect.width, 25)  # чуть выше для кнопок
        pygame.draw.rect(screen, (40, 40, 60), title_rect)
        pygame.draw.line(screen, self.border_color,
                         (self.console_rect.x, self.console_rect.y + 25),
                         (self.console_rect.x + self.console_rect.width, self.console_rect.y + 25))

        # Текст заголовка
        title_text = self.font.render("Консоль", True, (150, 150, 180))
        screen.blit(title_text, (self.console_rect.x + 5, self.console_rect.y + 5))

        btn_size = 16
        self.clear_btn_rect = pygame.Rect(
            self.console_rect.right - btn_size - 5,
            self.console_rect.y + 5,
            btn_size, btn_size
        )
        # Крестик для очистки
        pygame.draw.rect(screen, (150, 100, 100), self.clear_btn_rect)
        pygame.draw.line(screen, (255, 255, 255),
                         (self.clear_btn_rect.x + 3, self.clear_btn_rect.y + 3),
                         (self.clear_btn_rect.right - 3, self.clear_btn_rect.bottom - 3), 2)
        pygame.draw.line(screen, (255, 255, 255),
                         (self.clear_btn_rect.right - 3, self.clear_btn_rect.y + 3),
                         (self.clear_btn_rect.x + 3, self.clear_btn_rect.bottom - 3), 2)

        # Границы с индикаторами изменения размера
        pygame.draw.rect(screen, self.border_color, self.console_rect, 2)

        # Маркеры изменения размера
        marker_size = 5
        # Углы
        pygame.draw.rect(screen, self.border_color,
                         (self.console_rect.right - marker_size, self.console_rect.bottom - marker_size,
                          marker_size, marker_size))
        pygame.draw.rect(screen, self.border_color,
                         (self.console_rect.x, self.console_rect.bottom - marker_size,
                          marker_size, marker_size))
        pygame.draw.rect(screen, self.border_color,
                         (self.console_rect.right - marker_size, self.console_rect.y,
                          marker_size, marker_size))

        # Сообщения
        y = self.console_rect.y + 30
        for msg in self.console_messages[-10:]:
            text = self.font.render(str(msg), True, self.text_color)
            # Обрезаем текст если слишком длинный
            if text.get_width() > self.console_rect.width - 20:
                text = self.font.render(str(msg)[:40] + "...", True, self.text_color)
            screen.blit(text, (self.console_rect.x + 5, y))
            y += 20
            if y > self.console_rect.bottom - 30:
                break

        if self.input_active:
            # Поле ввода
            input_y = self.console_rect.bottom - 25
            input_text = self.font.render(f"> {self.input_buffer}_", True, self.input_color)
            screen.blit(input_text, (self.console_rect.x + 5, input_y))

            # Индикатор ввода
            if pygame.time.get_ticks() % 1000 < 500:
                pygame.draw.circle(screen, self.input_color,
                                   (self.console_rect.x + 5, input_y - 5), 3)

    def print(self, text):
        """Вывод сообщения в консоль игры"""
        message = str(text)
        self.console_messages.append(message)
        if len(self.console_messages) > self.max_messages:
            self.console_messages.pop(0)
        print(f"[GAME] {message}")

    def input(self, prompt, callback):
        """Запрос ввода от пользователя"""
        self.print(prompt)
        self.input_active = True
        self.input_buffer = ""
        self.input_callback = callback

    def draw_text(self, text, x, y, color=(255, 255, 255), size=24):
        """Рисование текста на экране"""
        font = pygame.font.Font(None, size)

        # Преобразуем ВСЁ в нормальные Python типы
        text_str = str(text)

        # Преобразуем координаты в числа
        try:
            x_pos = float(x) if hasattr(x, 'to_primitive') else float(str(x))
            y_pos = float(y) if hasattr(y, 'to_primitive') else float(str(y))
        except:
            x_pos = 400  # центр экрана по умолчанию
            y_pos = 300

        # Преобразуем цвет
        if isinstance(color, (list, tuple)):
            color_tuple = []
            for c in color[:3]:
                try:
                    val = float(c) if hasattr(c, 'to_primitive') else float(str(c))
                    color_tuple.append(int(val))
                except:
                    color_tuple.append(255)
            color_tuple = tuple(color_tuple)
        else:
            color_tuple = (255, 255, 255)

        try:
            text_surf = font.render(text_str, True, color_tuple)
            screen = self.game_state.get("screen")
            if screen:
                screen_rect = screen.get_rect()
                if screen_rect.collidepoint(int(x_pos), int(y_pos)):
                    screen.blit(text_surf, (int(x_pos), int(y_pos)))
        except Exception as e:
            print(f"Ошибка рисования текста: {e}")