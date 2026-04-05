# color_picker.py
import pygame

pygame.init()

class UniversalColorPicker:
    def __init__(self, current_color=(0, 0, 0)):
        self.current_color = current_color
        self.r, self.g, self.b = current_color
        self.active_input = None  # None, 'R', 'G', или 'B'
        self.input_texts = {'R': str(self.r), 'G': str(self.g), 'B': str(self.b)}
        self.show_keypad = False
        
    def pick_color(self):
        """Выбор цвета через Pygame"""
        # Сохраняем текущее состояние
        
        # Создаем окно для выбора цвета
        picker_screen = pygame.display.set_mode((400, 500))
        pygame.display.set_caption("Выбор цвета фона")
        
        color = self.run_picker_with_keypad(picker_screen)
        
        return color
    
    def run_picker_with_keypad(self, screen):
        """Пикер с числовой клавиатурой"""
        clock = pygame.time.Clock()
        running = True
        
        # Создаем прямоугольники для inputbox
        input_r = pygame.Rect(100, 50, 200, 40)
        input_g = pygame.Rect(100, 100, 200, 40)
        input_b = pygame.Rect(100, 150, 200, 40)
        
        # Кнопки OK и Отмена (над клавиатурой)
        ok_button = pygame.Rect(100, 200, 90, 40)
        cancel_button = pygame.Rect(210, 200, 90, 40)
        
        # Числовая клавиатура
        keypad_buttons = []
        key_labels = [
            '7', '8', '9',
            '4', '5', '6', 
            '1', '2', '3',
            '0', '←', 'OK'
        ]
        
        for i, label in enumerate(key_labels):
            row = i // 3
            col = i % 3
            x = 50 + col * 100
            y = 260 + row * 70
            keypad_buttons.append({
                'rect': pygame.Rect(x, y, 80, 60),
                'label': label,
                'action': label
            })
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return self.current_color
                    
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos
                    
                    if self.show_keypad:
                        # Обработка клавиатуры
                        for button in keypad_buttons:
                            if button['rect'].collidepoint(x, y):
                                action = button['action']
                                current_text = self.input_texts[self.active_input]
                                
                                if action == '←':  # Backspace
                                    if len(current_text) > 0:
                                        self.input_texts[self.active_input] = current_text[:-1]
                                elif action == 'OK':  # Закрыть клавиатуру
                                    self.show_keypad = False
                                elif action.isdigit():  # Цифра
                                    new_text = current_text + action
                                    if len(new_text) <= 3:
                                        try:
                                            if int(new_text) <= 255:
                                                self.input_texts[self.active_input] = new_text
                                        except ValueError:
                                            pass
                                break
                    else:
                        # Проверяем клик по inputbox
                        if input_r.collidepoint(x, y):
                            self.active_input = 'R'
                            self.show_keypad = True
                        elif input_g.collidepoint(x, y):
                            self.active_input = 'G'
                            self.show_keypad = True
                        elif input_b.collidepoint(x, y):
                            self.active_input = 'B'
                            self.show_keypad = True
                        elif ok_button.collidepoint(x, y):
                            # Проверяем и преобразуем значения
                            try:
                                r = max(0, min(255, int(self.input_texts['R'] or '0')))
                                g = max(0, min(255, int(self.input_texts['G'] or '0')))
                                b = max(0, min(255, int(self.input_texts['B'] or '0')))
                                return (r, g, b)
                            except ValueError:
                                return self.current_color
                        elif cancel_button.collidepoint(x, y):
                            return self.current_color
                        else:
                            self.active_input = None
                            self.show_keypad = False
                        
                elif event.type == pygame.KEYDOWN and not self.show_keypad:
                    if self.active_input:
                        if event.key == pygame.K_RETURN:
                            self.active_input = None
                        elif event.key == pygame.K_BACKSPACE:
                            self.input_texts[self.active_input] = self.input_texts[self.active_input][:-1]
                        elif event.key in (pygame.K_0, pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, 
                                         pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9):
                            new_text = self.input_texts[self.active_input] + event.unicode
                            if len(new_text) <= 3:
                                try:
                                    if int(new_text) <= 255:
                                        self.input_texts[self.active_input] = new_text
                                except ValueError:
                                    pass
            
            # Отрисовка
            screen.fill((40, 40, 60))
            
            # Заголовок
            title = self.get_font(28).render("Введите RGB значения:", True, (255, 255, 255))
            screen.blit(title, (50, 20))
            
            # Рисуем inputbox для R
            color_r = (255, 0, 0)
            self.draw_inputbox(screen, input_r, "Red (R):", 
                             self.input_texts['R'], color_r, self.active_input == 'R' and not self.show_keypad)
            
            # Рисуем inputbox для G
            color_g = (0, 255, 0)
            self.draw_inputbox(screen, input_g, "Green (G):", 
                             self.input_texts['G'], color_g, self.active_input == 'G' and not self.show_keypad)
            
            # Рисуем inputbox для B
            color_b = (0, 0, 255)
            self.draw_inputbox(screen, input_b, "Blue (B):", 
                             self.input_texts['B'], color_b, self.active_input == 'B' and not self.show_keypad)
            
            # Предпросмотр цвета
            try:
                preview_color = (
                    max(0, min(255, int(self.input_texts['R'] or '0'))),
                    max(0, min(255, int(self.input_texts['G'] or '0'))),
                    max(0, min(255, int(self.input_texts['B'] or '0')))
                )
            except ValueError:
                preview_color = (0, 0, 0)
            
            preview_rect = pygame.Rect(320, 50, 200, 200)
            pygame.draw.rect(screen, preview_color, preview_rect)
            pygame.draw.rect(screen, (255, 255, 255), preview_rect, 2)
            
            # Текст предпросмотра
            preview_text = self.get_font(18).render(
                f"RGB({preview_color[0]},{preview_color[1]},{preview_color[2]})", 
                True, (255, 255, 255)
            )
            screen.blit(preview_text, (320, 30))
            
            # Кнопки OK и Отмена
            pygame.draw.rect(screen, (100, 200, 100), ok_button, border_radius=8)
            pygame.draw.rect(screen, (255, 255, 255), ok_button, 2, border_radius=8)
            ok_text = self.get_font(24).render("OK", True, (255, 255, 255))
            screen.blit(ok_text, ok_text.get_rect(center=ok_button.center))
            
            pygame.draw.rect(screen, (200, 100, 100), cancel_button, border_radius=8)
            pygame.draw.rect(screen, (255, 255, 255), cancel_button, 2, border_radius=8)
            cancel_text = self.get_font(24).render("Отмена", True, (255, 255, 255))
            screen.blit(cancel_text, cancel_text.get_rect(center=cancel_button.center))
            
            # Числовая клавиатура (если активна)
            if self.show_keypad:
                # Затемняем фон под клавиатурой
                overlay = pygame.Surface((400, 240), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 150))
                screen.blit(overlay, (0, 260))
                
                # Заголовок клавиатуры
                active_label = {'R': 'Красный', 'G': 'Зеленый', 'B': 'Синий'}.get(self.active_input, '')
                keypad_title = self.get_font(22).render(
                    f"Ввод для {active_label} ({self.active_input}):", 
                    True, (255, 255, 200)
                )
                screen.blit(keypad_title, (50, 240))
                
                # Кнопки клавиатуры
                for button in keypad_buttons:
                    # Разные цвета для разных кнопок
                    if button['action'] == 'OK':
                        btn_color = (100, 200, 100)
                    elif button['action'] == '←':
                        btn_color = (200, 150, 100)
                    else:
                        btn_color = (80, 80, 120)
                    
                    pygame.draw.rect(screen, btn_color, button['rect'], border_radius=10)
                    pygame.draw.rect(screen, (200, 200, 255), button['rect'], 2, border_radius=10)
                    
                    label_text = self.get_font(28).render(button['label'], True, (255, 255, 255))
                    label_rect = label_text.get_rect(center=button['rect'].center)
                    screen.blit(label_text, label_rect)
             
            pygame.display.flip()
            clock.tick(30)
        
        return self.current_color
    
    def draw_inputbox(self, screen, rect, label, text, color, active):
        """Рисует одно текстовое поле"""
        # Метка
        label_font = self.get_font(22)
        label_surf = label_font.render(label, True, color)
        screen.blit(label_surf, (rect.x - 90, rect.y + 10))
        
        # Поле ввода
        bg_color = (255, 255, 255) if active else (200, 200, 200)
        border_color = (0, 200, 255) if active else color
        
        pygame.draw.rect(screen, bg_color, rect, border_radius=6)
        pygame.draw.rect(screen, border_color, rect, 3, border_radius=6)
        
        # Текст
        text_font = self.get_font(28)
        text_surf = text_font.render(text, True, (0, 0, 0))
        
        # Обрезаем текст если слишком длинный
        if text_surf.get_width() > rect.width - 10:
            # Показываем только последние символы
            for i in range(len(text)):
                test_text = "..." + text[-i:] if i > 0 else text
                test_surf = text_font.render(test_text, True, (0, 0, 0))
                if test_surf.get_width() <= rect.width - 10:
                    text_surf = test_surf
                    break
        
        text_rect = text_surf.get_rect(midleft=(rect.x + 10, rect.centery))
        screen.blit(text_surf, text_rect)
        
        # Курсор если активно
        if active:
            cursor_x = text_rect.right + 2 if text else rect.x + 10
            pygame.draw.line(screen, (0, 0, 0), 
                           (cursor_x, rect.y + 10),
                           (cursor_x, rect.y + rect.height - 10), 2)
    
    def get_font(self, size):
        """Получение шрифта нужного размера"""
        return pygame.font.Font(None, size)

if __name__ == "__main__":    
    picker = UniversalColorPicker()
    color = picker.pick_color()
    print(color)