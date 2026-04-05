import socket
import json
import threading
import time
from dataclasses import dataclass

@dataclass
class MultiplayerState:
    connected: bool = False
    in_room: bool = False
    room_name: str = ""
    is_host: bool = False
    players: int = 0
    max_players: int = 0

class MultiplayerClient:
    def __init__(self, game_state = None, host='localhost', port=5555):
        self.game_state = game_state
        self.host = host
        self.port = port
        self.socket = None
        self.running = False
        self.thread = None
        self.state = MultiplayerState()
        self.callbacks = []
        self.server_addr = (host, port)
        # 🟢 ДОБАВЛЯЕМ ограничение частоты
        self.last_update_time = 0
        self.update_delay = 0.05  # 50 миллисекунд (20 обновлений в секунду)
        self._lock = threading.Lock()  # Блокировка для потокобезопасности
        self._socket_valid = False  # Флаг валидности сокета
        self.on_response = None  # Добавляем callback для UI
        self.on_state_update = None  # Добавляем callback для обновлений

    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.settimeout(0.1)
            with self._lock:
                self._socket_valid = True
                self.running = True
            self.state.connected = True
            self.thread = threading.Thread(target=self._listen)
            self.thread.daemon = True
            self.thread.start()
            return True
        except Exception as e:
            print(f"Ошибка подключения: {e}")
            return False

    def disconnect(self):
        with self._lock:
            self.running = False
            self._socket_valid = False
            self.state.connected = False
            self.state.in_room = False
            if self.socket:
                try:
                    self.socket.close()
                except:
                    pass
                self.socket = None

    def create_room(self, room_name, password, max_players=2):
        """Создание комнаты"""
        if not self.state.connected:
            print("❌ Не подключен к серверу")
            return False

        print(f"\n🏠 СОЗДАНИЕ КОМНАТЫ: {room_name}")
        msg = {
            "cmd": "create_room",
            "room": room_name,
            "password": password,
            "max_players": max_players
        }
        print(f"📤 Отправка: {msg}")
        result = self._send(msg)
        print(f"📬 Результат отправки: {result}")
        return result

    def join_room(self, room_name, password):
        """Подключение к комнате"""
        if not self.state.connected:
            print("❌ Не подключен к серверу")
            return False

        print(f"\n🔌 ПОДКЛЮЧЕНИЕ К КОМНАТЕ: {room_name}")
        msg = {
            "cmd": "join_room",
            "room": room_name,
            "password": password
        }
        print(f"📤 Отправка: {msg}")
        result = self._send(msg)
        print(f"📬 Результат отправки: {result}")
        return result

    def update_state(self):
        # 🟢 ПРОВЕРЯЕМ, не слишком ли часто
        current_time = time.time()
        if current_time - self.last_update_time < self.update_delay:
            return  # Слишком часто, пропускаем

        if not self.state.in_room:
            return

        if self.game_state is None:
            return

        data = {
            "current_shape": self.game_state["current_shape"],
            "is_morphing": self.game_state["is_morphing"],
            "morph_progress": self.game_state["morph_progress"],
            "with_karkas": self.game_state["with_karkas"],
            "draw_faces": self.game_state["draw_faces"],
            "draw_points": self.game_state["draw_points"],
            "auto_rotate": self.game_state["auto_rotate"],
            "dvd_mode": self.game_state["dvd_mode"],
            "show_cube": self.game_state["show_cube"],
            "scale": self.game_state["scale"],
            "angle_x": self.game_state["angle_x"],
            "angle_y": self.game_state["angle_y"],
            "angle_z": self.game_state["angle_z"],
            "pos_x": self.game_state["cube_pos"][0],
            "pos_y": self.game_state["cube_pos"][1],
            "vel_x": self.game_state["cube_velocity"][0],
            "vel_y": self.game_state["cube_velocity"][1]
        }

        self._send({"cmd": "update_state", "data": data})
        self.last_update_time = current_time

    def _send(self, data):
        """Отправка данных на сервер"""
        # Проверяем валидность сокета под блокировкой
        with self._lock:
            if not self._socket_valid or not self.socket or not self.running:
                print(f"⚠️ Сокет не валиден, отправка невозможна")
                return False

            # Делаем копию сокета для использования вне блокировки
            sock = self.socket

        try:
            message = json.dumps(data).encode()
            print(f"📤 Отправка {len(message)} байт: {data}")
            sock.sendto(message, self.server_addr)
            return True
        except socket.error as e:
            print(f"❌ Ошибка сокета при отправке: {e}")
            # Сигнализируем о проблеме
            with self._lock:
                self._socket_valid = False
                self.disconnect()
            return False
        except Exception as e:
            print(f"❌ Ошибка отправки: {e}")
            return False

    def _listen(self):
        """Поток для приема сообщений"""
        while True:
            # Проверяем состояние под блокировкой
            with self._lock:
                if not self.running or not self._socket_valid or not self.socket:
                    print("👋 Поток _listen завершается")
                    break
                sock = self.socket

            try:
                data, _ = sock.recvfrom(4096)
                msg = json.loads(data.decode())
                print(f"📥 UI ПОЛУЧИЛ: {msg}")
                self._handle_message(msg)

            except socket.timeout:
                continue
            except socket.error as e:
                print(f"❌ Ошибка сокета в _listen: {e}")
                # Критическая ошибка - помечаем сокет как невалидный
                with self._lock:
                    self._socket_valid = False
                    self.disconnect()
                break
            except Exception as e:
                print(f"❌ Ошибка UI _listen: {e}")
                with self._lock:
                    self._socket_valid = False
                    self.disconnect()
                break

    def stop(self):
        """Полная остановка клиента"""
        self.running = False
        with self._lock:
            self._socket_valid = False
        time.sleep(0.1)  # даем время потоку _listen завершиться
        self.disconnect()

    def _handle_message(self, msg):
        """Обработка полученных сообщений"""
        print(f"🔄 Обработка сообщения: {msg}")

        if msg.get("type") == "state_update":
            data = msg["data"]
            if self.on_state_update:
                self.on_state_update(data)
            print(f"📊 Обновление состояния: {data}")

            # Обновляем game_state
            self.game_state["auto_rotate"] = data["auto_rotate"]
            self.game_state["dvd_mode"] = data["dvd_mode"]
            self.game_state["show_cube"] = data["show_cube"]
            self.game_state["current_shape"] = data["current_shape"]
            self.game_state["scale"] = data["scale"]
            self.game_state["angle_x"] = data["angle_x"]
            self.game_state["angle_y"] = data["angle_y"]
            self.game_state["angle_z"] = data["angle_z"]
            self.game_state["cube_pos"][0] = data["pos_x"]
            self.game_state["cube_pos"][1] = data["pos_y"]
            self.game_state["cube_velocity"][0] = data["vel_x"]
            self.game_state["cube_velocity"][1] = data["vel_y"]
            self.game_state["with_karkas"] = data["with_karkas"]
            self.game_state["draw_faces"] = data["draw_faces"]
            self.game_state["draw_points"] = data["draw_points"]
            self.game_state["morph_progress"] = data["morph_progress"]
            self.game_state["is_morphing"] = data["is_morphing"]

            print(f"✅ Состояние обновлено")

        elif msg.get("status") == "ok":
            print(f"✅ СТАТУС OK: {msg}")

            if self.on_response:
                self.on_response(True, msg)

            if "room" in msg:
                self.state.in_room = True
                self.state.room_name = msg["room"]
                print(f"🎉 УСПЕШНО! Подключено к комнате {msg['room']}")

                # Если есть состояние, применяем его
                if "state" in msg:
                    data = msg["state"]
                    print(f"📥 Применяем состояние комнаты: {data}")
                    # Обновляем game_state...
                    # (код обновления как выше)

        elif msg.get("status") == "error":
            print(f"❌ СТАТУС ERROR: {msg}")
            reason = msg.get('reason', 'неизвестная ошибка')
            print(f"⛔ Причина: {reason}")