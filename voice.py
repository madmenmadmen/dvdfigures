import numpy as np
import sounddevice as sd
import threading
from scipy import signal


class VoiceController:
    def __init__(self, game_state):
        self.game_state = game_state
        self.running = False
        self.thread = None
        self.sample_rate = 44100

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._listen)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()

    def _listen(self):
        def callback(indata, frames, time, status):
            if not self.running or not self.game_state.get("voice_size_mode", False):
                return

            # Применяем полосовой фильтр (85-255 Гц)
            sos = signal.butter(4, [85, 255], 'bandpass', fs=self.sample_rate, output='sos')
            filtered = signal.sosfilt(sos, indata[:, 0])

            # Вычисляем RMS отфильтрованного сигнала
            rms = np.sqrt(np.mean(filtered ** 2))

            # Игнорируем тихие звуки
            if rms < self.game_state.get("voice_threshold", 0.01):
                return

            # Нормализуем
            volume = min(1.0, rms / 0.1)

            # Применяем к размеру
            self.game_state["scale"] = self.game_state["voice_size_original"] + volume * (
                        self.game_state["voice_max_scale"] - self.game_state["voice_size_original"])

        with sd.InputStream(callback=callback, channels=1, samplerate=self.sample_rate):
            while self.running:
                sd.sleep(100)