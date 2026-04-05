import pygame
from config import *

class Button:
    def __init__(self, x, y, width, height, text, color=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color or BUTTON_COLOR
        self.visible = True

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect, border_radius=12)
        pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=12)

        font = pygame.font.SysFont(None, 32, "androidemoji")
        text_surf = font.render(self.text, True, WHITE)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def check_click(self, pos):
        return self.rect.collidepoint(pos)

    def hide(self):
        self.visible = False

    def show(self):
        self.visible = True


class SpeedSlider:
    def __init__(self, x, y, width, height, min_val, max_val, initial_val):
        self.rect = pygame.Rect(x, y, width, height)
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        self.dragging = False
        self.knob_radius = 10
        self.visible = True  # Добавьте эту строку

    def draw(self, surface):
        # Фон слайдера
        pygame.draw.rect(surface, (60, 60, 80), self.rect, border_radius=10)
        pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=10)

        # Линия слайдера
        line_y = self.rect.centery
        pygame.draw.line(surface, (100, 100, 120),
                         (self.rect.left + 5, line_y),
                         (self.rect.right - 5, line_y), 3)

        # Ползунок
        knob_x = self.rect.left + 5 + (self.value - self.min_val) / (self.max_val - self.min_val) * (
                    self.rect.width - 10)
        knob_pos = (knob_x, line_y)

        # Цвет ползунка в зависимости от скорости
        speed_percent = (self.value - self.min_val) / (self.max_val - self.min_val)
        if speed_percent < 0.33:
            knob_color = (100, 200, 100)  # Зеленый - медленно
        elif speed_percent < 0.66:
            knob_color = (200, 200, 100)  # Желтый - средне
        else:
            knob_color = (200, 100, 100)  # Красный - быстро

        pygame.draw.circle(surface, knob_color, knob_pos, self.knob_radius)
        pygame.draw.circle(surface, WHITE, knob_pos, self.knob_radius, 2)

        # Текст значения
        font = pygame.font.SysFont(None, 24, "notoemojji")
        value_text = font.render(f"{self.value:.1f}", True, WHITE)
        surface.blit(value_text, (self.rect.right + 10, self.rect.centery - 10))

        # Текст "Скорость:"
        speed_text = font.render("Скорость:", True, WHITE)
        surface.blit(speed_text, (self.rect.left - 100, self.rect.centery - 10))

    def handle_event(self, event, mouse_pos):
        if not self.visible:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_over_knob(mouse_pos):
                self.dragging = True
                return True

        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
            return False

        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self.update_value_from_mouse(mouse_pos[0])
            return True

        return False

    def is_over_knob(self, mouse_pos):
        knob_x = self.rect.left + 5 + (self.value - self.min_val) / (self.max_val - self.min_val) * (
                    self.rect.width - 10)
        knob_pos = (knob_x, self.rect.centery)
        distance = ((mouse_pos[0] - knob_pos[0]) ** 2 + (mouse_pos[1] - knob_pos[1]) ** 2) ** 0.5
        return distance <= self.knob_radius + 5

    def update_value_from_mouse(self, mouse_x):
        # Ограничиваем мышку границами слайдера
        mouse_x = max(self.rect.left + 5, min(mouse_x, self.rect.right - 5))

        # Преобразуем позицию мыши в значение
        percent = (mouse_x - self.rect.left - 5) / (self.rect.width - 10)
        self.value = self.min_val + percent * (self.max_val - self.min_val)

        # Округляем до 0.1
        self.value = round(self.value * 2) / 2

    def get_value(self):
        return self.value

    # Добавьте эти методы:
    def hide(self):
        self.visible = False

    def show(self):
        self.visible = True