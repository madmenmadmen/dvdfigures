# В начало main.py добавьте:
import socket
import threading
import json
import time
import traceback

from config import SHAPES, SHAPE_NAMES, DVD_COLORS

class ScriptServer:
    def __init__(self, game_state, port=9999):
        self.game_state = game_state
        self.port = port
        self.server = None
        self.running = False
        self.thread = None
        self.clients = []
        self.current_script = None
        self.script_running = False
        self.script_thread = None

    def start(self):
        """Запуск сервера в отдельном потоке"""
        self.running = True
        self.thread = threading.Thread(target=self._server_loop)
        self.thread.daemon = True
        self.thread.start()
        print(f"📡 Script server started on port {self.port}")

    def _server_loop(self):
        """Основной цикл сервера"""
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(('localhost', self.port))
        self.server.listen(5)
        self.server.settimeout(1.0)

        while self.running:
            try:
                client, addr = self.server.accept()
                print(f"📱 Editor connected from {addr}")
                client_handler = threading.Thread(
                    target=self._handle_client,
                    args=(client,)
                )
                client_handler.daemon = True
                client_handler.start()
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"Server error: {e}")

    def _handle_client(self, client):
        """Обработка подключенного редактора"""
        self.clients.append(client)
        try:
            while self.running:
                data = client.recv(65536)
                if not data:
                    break

                msg = json.loads(data.decode())
                self._handle_message(msg, client)

        except Exception as e:
            print(f"Client error: {e}")
        finally:
            if client in self.clients:
                self.clients.remove(client)
            client.close()

    def _handle_message(self, msg, client):
        """Обработка сообщений от редактора"""
        cmd = msg.get("cmd")

        if cmd == "execute_script":
            script = msg.get("script", "")
            self.current_script = script
            try:
                self._execute_script(script)
                client.send(json.dumps({"status": "ok", "message": "Script started"}).encode())
            except Exception as e:
                error_msg = str(e)
                print(f"Script error: {error_msg}")
                client.send(json.dumps({
                    "status": "error",
                    "error": error_msg
                }).encode())

        elif cmd == "stop_script":
            self.script_running = False

        elif cmd == "get_status":
            response = {
                "status": "ok",
                "script_running": self.script_running,
                "game_state": self._get_game_state()
            }
            client.send(json.dumps(response).encode())

    def _get_game_state(self):
        """Получить текущее состояние для отображения в редакторе"""
        return {
            "angle_x": self.game_state["angle_x"],
            "angle_y": self.game_state["angle_y"],
            "angle_z": self.game_state["angle_z"],
            "pos_x": self.game_state["cube_pos"][0],
            "pos_y": self.game_state["cube_pos"][1],
            "scale": self.game_state["scale"],
            "current_shape": self.game_state["current_shape"],
            "auto_rotate": self.game_state["auto_rotate"],
            "dvd_mode": self.game_state["dvd_mode"],
            "face_alpha": self.game_state.get("face_alpha", 255)
        }

    def _execute_script(self, script):
        """Выполнить JavaScript скрипт"""
        if self.script_running:
            self.script_running = False
            time.sleep(0.1)

        self.script_running = True
        self.script_thread = threading.Thread(
            target=self._run_script,
            args=(script,)
        )
        self.script_thread.daemon = True
        self.script_thread.start()

    def trigger_collision(self, idx1, idx2):
        """Вызывает on_collision в скрипте (если он есть)"""
        if not self.script_running:
            return

        # Сохраняем индексы для обработки в основном потоке скрипта
        if not hasattr(self, '_pending_collisions'):
            self._pending_collisions = []
        self._pending_collisions.append((idx1, idx2))

    def _get_full_state_for_js(self):
        # Создаем ПОЛНЫЙ объект состояния для JS
        state = {
            # Углы вращения
            'angle_x': float(self.game_state['angle_x']),
            'angle_y': float(self.game_state['angle_y']),
            'angle_z': float(self.game_state['angle_z']),

            # Позиция и скорость
            'pos_x': float(self.game_state['cube_pos'][0]),
            'pos_y': float(self.game_state['cube_pos'][1]),
            'vel_x': float(self.game_state['cube_velocity'][0]),
            'vel_y': float(self.game_state['cube_velocity'][1]),

            # Масштаб и форма
            'scale': float(self.game_state['scale']),
            'current_shape': int(self.game_state['current_shape']),

            # Режимы отображения (булевы значения)
            'auto_rotate': bool(self.game_state['auto_rotate']),
            'dvd_mode': bool(self.game_state['dvd_mode']),
            'show_cube': bool(self.game_state['show_cube']),
            'with_karkas': bool(self.game_state['with_karkas']),
            'draw_faces': bool(self.game_state['draw_faces']),
            'draw_points': bool(self.game_state['draw_points']),
            'trail_mode': bool(self.game_state.get('trail_mode', False)),

            # Цвета
            'current_dvd_color': int(self.game_state.get('current_dvd_color', 0)),

            # Скорости
            'rotation_speed': float(self.game_state.get('rotation_speed', 0.01)),
            'move_speed': float(self.game_state.get('move_speed', 3.0)),

            # Морфинг
            'is_morphing': bool(self.game_state.get('is_morphing', False)),
            'morph_progress': float(self.game_state.get('morph_progress', 0.0)),

            "multi_mode": bool(self.game_state.get("multi_mode", False)),
            "objects": [
                {
                    "shape": obj["shape"],
                    "x": float(obj["x"]),
                    "y": float(obj["y"]),
                    "vx": float(obj.get("vx", 0)),
                    "vy": float(obj.get("vy", 0)),
                    "scale": float(obj["scale"]),
                    "ax": float(obj["ax"]),
                    "ay": float(obj["ay"]),
                    "az": float(obj["az"])
                }
                for obj in self.game_state.get("objects", [])
            ],
            "input": {
                "keys": self.game_state.get("_input_keys", {}),
                "mouse": {
                    "x": self.game_state.get("_mouse_x", 0),
                    "y": self.game_state.get("_mouse_y", 0),
                    "left": self.game_state.get("_mouse_left", False),
                    "right": self.game_state.get("_mouse_right", False)
                }
            }
        }
        if "game_system" in self.game_state:
            game = self.game_state["game_system"]
            # Создаем JS-объект с методами
            js_game = {
                "print": lambda text: game.print(text),
                "input": lambda prompt, callback=None: game.input(prompt, callback),
                "draw_text": lambda text, x, y, color=None: game.draw_text(
                    text, x, y, color if color else (255, 255, 255)
                )
            }
            state['game'] = js_game
        return state

    def _apply_js_state_to_game(self, new_state):
        # Углы вращения
        if 'angle_x' in new_state:
            self.game_state['angle_x'] = float(str(new_state['angle_x']))
        if 'angle_y' in new_state:
            self.game_state['angle_y'] = float(str(new_state['angle_y']))
        if 'angle_z' in new_state:
            self.game_state['angle_z'] = float(str(new_state['angle_z']))

        # Позиция и скорость
        if 'pos_x' in new_state:
            self.game_state['cube_pos'][0] = float(str(new_state['pos_x']))
        if 'pos_y' in new_state:
            self.game_state['cube_pos'][1] = float(str(new_state['pos_y']))
        if 'vel_x' in new_state:
            self.game_state['cube_velocity'][0] = float(str(new_state['vel_x']))
        if 'vel_y' in new_state:
            self.game_state['cube_velocity'][1] = float(str(new_state['vel_y']))

        # Масштаб
        if 'scale' in new_state:
            self.game_state['scale'] = float(str(new_state['scale']))

        # Режимы отображения (булевы)
        if 'auto_rotate' in new_state:
            new_val = bool(new_state['auto_rotate'])
            if new_val != self.game_state['auto_rotate']:
                self.game_state['auto_rotate'] = new_val
                # Обновляем текст кнопки
                if 'rotate_toggle' in self.game_state:
                    self.game_state['rotate_toggle'].text = "АВТО: ВКЛ" if new_val else "АВТО: ВЫКЛ"

        if 'dvd_mode' in new_state:
            new_val = bool(new_state['dvd_mode'])
            if new_val != self.game_state['dvd_mode']:
                self.game_state['dvd_mode'] = new_val
                if new_val:  # Если ВКЛЮЧАЕМ DVD-режим
                    from config import INITIAL_CUBE_VELOCITY
                    self.game_state['cube_velocity'] = INITIAL_CUBE_VELOCITY.copy()
                else:  # Если ВЫКЛЮЧАЕМ
                    self.game_state['cube_velocity'] = [0, 0]
                if 'dvd_toggle' in self.game_state:
                    self.game_state['dvd_toggle'].text = "DVD: ВКЛ" if new_val else "DVD: ВЫКЛ"

        if 'show_cube' in new_state:
            new_val = bool(new_state['show_cube'])
            if new_val != self.game_state['show_cube']:
                self.game_state['show_cube'] = new_val
                if 'mode_toggle_btn' in self.game_state:
                    self.game_state['mode_toggle_btn'].text = "3D РЕЖИМ" if new_val else "DVD РЕЖИМ"

        if 'with_karkas' in new_state:
            new_val = bool(new_state['with_karkas'])
            if new_val != self.game_state['with_karkas']:
                self.game_state['with_karkas'] = new_val
                if 'wireframe_toggle' in self.game_state:
                    self.game_state['wireframe_toggle'].text = "КАРКАС: ВКЛ" if new_val else "КАРКАС: ВЫКЛ"
                    self.game_state['wireframe_toggle'].color = (100, 200, 100) if new_val else (80, 80, 100)

        if 'draw_faces' in new_state:
            new_val = bool(new_state['draw_faces'])
            if new_val != self.game_state['draw_faces']:
                self.game_state['draw_faces'] = new_val
                if 'faces_toggle' in self.game_state:
                    self.game_state['faces_toggle'].text = "ГРАНИ: ВКЛ" if new_val else "ГРАНИ: ВЫКЛ"
                    self.game_state['faces_toggle'].color = (100, 150, 200) if new_val else (80, 80, 100)

        if 'draw_points' in new_state:
            new_val = bool(new_state['draw_points'])
            if new_val != self.game_state['draw_points']:
                self.game_state['draw_points'] = new_val
                if 'points_toggle' in self.game_state:
                    self.game_state['points_toggle'].text = "ТОЧКИ: ВКЛ" if new_val else "ТОЧКИ: ВЫКЛ"
                    self.game_state['points_toggle'].color = (200, 100, 200) if new_val else (80, 80, 100)

        if 'trail_mode' in new_state:
            new_val = bool(new_state['trail_mode'])
            if new_val != self.game_state.get('trail_mode', False):
                self.game_state['trail_mode'] = new_val
                if 'trail_btn' in self.game_state:
                    self.game_state['trail_btn'].text = "🎨 TRAIL: ВКЛ" if new_val else "🎨 TRAIL: ВЫКЛ"
                    self.game_state['trail_btn'].color = (200, 100, 255) if new_val else (150, 100, 200)

        # Цвет DVD
        if 'current_dvd_color' in new_state:
            new_val = int(float(str(new_state['current_dvd_color']))) % len(DVD_COLORS)
            self.game_state['current_dvd_color'] = new_val

        # Скорости
        if 'rotation_speed' in new_state:
            self.game_state['rotation_speed'] = float(str(new_state['rotation_speed']))
        if 'move_speed' in new_state:
            self.game_state['move_speed'] = float(str(new_state['move_speed']))
            # Обновляем слайдер если есть
            if 'speed_slider' in self.game_state:
                self.game_state['speed_slider'].value = self.game_state['move_speed']

        if 'face_alpha' in new_state:
            alpha = float(str(new_state['face_alpha']))
            # Ограничиваем 0-255
            alpha = max(0, min(255, alpha))
            self.game_state['face_alpha'] = int(alpha)

        # Обработка списка объектов
        if 'objects' in new_state:
            try:
                updated_objects = []
                for obj_js in new_state['objects']:
                    updated_objects.append({
                        "shape": int(float(str(obj_js.get("shape", 0)))),
                        "x": float(str(obj_js.get("x", 500))),
                        "y": float(str(obj_js.get("y", 350))),
                        "vx": float(str(obj_js.get("vx", 0))),  # ← скорость!
                        "vy": float(str(obj_js.get("vy", 0))),
                        "scale": float(str(obj_js.get("scale", 1.0))),
                        "ax": float(str(obj_js.get("ax", 0))),
                        "ay": float(str(obj_js.get("ay", 0))),
                        "az": float(str(obj_js.get("az", 0)))
                    })
                self.game_state["objects"] = updated_objects
            except Exception as e:
                print(f"⚠️ Ошибка обновления objects: {e}")

        # Обработка смены формы с морфингом
        if 'current_shape' in new_state:
            new_shape = int(float(str(new_state['current_shape']))) % len(SHAPES)
            if new_shape != self.game_state['current_shape']:
                # Запускаем морфинг
                self.game_state['prev_shape'] = self.game_state['current_shape']
                self.game_state['current_shape'] = new_shape
                self.game_state['is_morphing'] = True
                self.game_state['morph_progress'] = 0.0

                # Обновляем текст кнопки формы
                if 'shape_toggle_btn' in self.game_state:
                    self.game_state['shape_toggle_btn'].text = f"ФОРМА: {SHAPE_NAMES[new_shape]}"

    def _get_script_time(self):
        return time.time() - self.script_start_time

    def _run_script(self, script):
        """Запуск скрипта в отдельном потоке"""
        try:
            import js2py
            import time

            self.script_start_time = time.time()
            js = js2py.EvalJs()

            # Создаём заглушку для game
            js.execute("""
                var game = {
                    print: function(text) {},
                    input: function(prompt, callback) {},
                    draw_text: function(text, x, y, color) {}
                };
            """)

            js.execute(script)

            # Проверяем наличие функций
            js.execute("""
                hasStart = typeof start === 'function';
                hasUpdate = typeof update === 'function';
                hasOnBounce = typeof on_bounce === 'function';
            """)
            has_start = bool(js.hasStart)
            has_update = bool(js.hasUpdate)
            has_on_bounce = bool(js.hasOnBounce)

            # === ОБРАБОТКА КОЛЛИЗИЙ ===
            if hasattr(self, '_pending_collisions') and self._pending_collisions:
                if js.execute("typeof on_collision === 'function'"):
                    try:
                        # Берём первую коллизию (можно расширить до всех)
                        idx1, idx2 = self._pending_collisions.pop(0)

                        # Получаем объекты
                        obj1 = self.game_state["objects"][idx1] if idx1 < len(self.game_state["objects"]) else {}
                        obj2 = self.game_state["objects"][idx2] if idx2 < len(self.game_state["objects"]) else {}

                        # Передаём в JS как словари
                        js.obj1 = obj1
                        js.obj2 = obj2
                        js.t = self._get_script_time()
                        js.state = self._get_full_state_for_js()

                        # Вызываем on_collision(state, obj1, obj2)
                        js.execute("on_collision(state, obj1, obj2);")

                        # Применяем изменения из state
                        self._apply_js_state_to_game(js.state)

                    except Exception as e:
                        print(f"⚠️ Ошибка в on_collision(): {e}")

                # Очищаем очередь (или оставляем остальные для следующих кадров)
                self._pending_collisions = []

            if has_start:
                try:
                    # Получаем реальный game
                    real_state = self._get_full_state_for_js()
                    if 'game' in real_state:
                        js.game = real_state['game']
                    js.t = self._get_script_time()
                    js.state = real_state
                    js.start()
                    self._apply_js_state_to_game(js.state)
                except Exception as e:
                    print(f"⚠️ Ошибка в start(): {e}")

            if not has_update:
                print("✅ Скрипт выполнен (только start), остановка.")
                self.script_running = False
                return

            # СВОЙ СОБСТВЕННЫЙ ФЛАГ ДЛЯ ОТСЛЕЖИВАНИЯ
            last_bounced = self.game_state.get("bounced", False)

            morph_start_time = 0
            morph_duration = 1.0  # Длительность морфинга в секундах

            while self.script_running:
                # В каждом кадре обновляем game и state
                real_state = self._get_full_state_for_js()
                if 'game' in real_state:
                    js.game = real_state['game']
                # СБРАСЫВАЕМ bounced В НАЧАЛЕ КАДРА
                current_bounced = self.game_state.get("bounced", False)

                js.state = real_state
                js.t = self._get_script_time()  # ← актуальное время

                if has_on_bounce and current_bounced and not last_bounced:
                    try:
                        js.t = self._get_script_time()
                        js.state = self._get_full_state_for_js()
                        js.on_bounce(js.state)
                        self._apply_js_state_to_game(js.state)
                        print("🔄 on_bounce() вызван")
                    except Exception as e:
                        print(f"⚠️ Ошибка в on_bounce(): {e}")

                last_bounced = current_bounced

                # Сбрасываем флаг ПОСЛЕ того, как все обработчики отработали
                if current_bounced:
                    self.game_state["bounced"] = False

                result = js.update(js.state, js.t)

                # Преобразуем результат
                if hasattr(result, 'to_dict'):
                    new_state = result.to_dict()
                elif isinstance(result, dict):
                    new_state = result
                else:
                    time.sleep(0.05)
                    continue
                self._apply_js_state_to_game(new_state)

                # Применяем изменения
                shape_changed = False

                # Обновляем прогресс морфинга если он идет
                if self.game_state.get('is_morphing', False):
                    if not shape_changed:  # Если форму не меняли в этом кадре
                        morph_time = time.time() - morph_start_time
                        self.game_state['morph_progress'] = min(1.0, morph_time / morph_duration)

                        if self.game_state['morph_progress'] >= 1.0:
                            self.game_state['is_morphing'] = False
                            self.game_state['morph_progress'] = 0.0

                time.sleep(0.05)  # 20 FPS

        except Exception as e:
            error_msg = str(e)
            print(f"Script error: {error_msg}")
            # Отправляем ошибку всем клиентам
            for client in self.clients:
                try:
                    client.send(json.dumps({
                        "status": "error",
                        "error": error_msg
                    }).encode())
                except:
                    pass
            traceback.print_exc()
        finally:
            self.script_running = False
            # Сбрасываем морфинг при остановке
            self.game_state['is_morphing'] = False
            self.game_state['morph_progress'] = 0.0

    def stop(self):
        """Остановка сервера"""
        self.running = False
        self.script_running = False
        for client in self.clients:
            try:
                client.close()
            except:
                pass
        if self.server:
            self.server.close()