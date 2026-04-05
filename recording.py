import cv2
import numpy as np
import pygame
import time
import os
import threading
import subprocess
import sounddevice as sd
import soundfile as sf
from config import *

# Глобальные переменные
_video_writer = None
_recording = False
_frame_count = 0
_start_time = 0
_filename = None
_audio_frames = []
_audio_stream = None
_temp_video = ""
_temp_audio = ""


def start_recording(game_state):
    global _video_writer, _recording, _frame_count, _start_time, _filename
    global _audio_frames, _audio_stream, _temp_video, _temp_audio

    try:
        if _recording:
            stop_recording(game_state)

        os.makedirs("videos", exist_ok=True)

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        _filename = f"videos/madmen_{timestamp}.mp4"
        _temp_video = f"videos/temp_video_{timestamp}.avi"
        _temp_audio = f"videos/temp_audio_{timestamp}.wav"

        # Видео (временный AVI)
        fps = 60
        width, height = WIDTH, HEIGHT
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        _video_writer = cv2.VideoWriter(_temp_video, fourcc, fps, (width, height))

        # Аудио
        _audio_frames = []
        _audio_stream = sd.InputStream(
            samplerate=44100,
            channels=2,
            callback=_audio_callback
        )
        _audio_stream.start()

        _recording = True
        _frame_count = 0
        _start_time = time.time()
        game_state["is_recording"] = True
        game_state["recorded_frames"] = 0

        print(f"🎬 Запись начата...")
        return True

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


def _audio_callback(indata, frames, time, status):
    global _recording, _audio_frames
    if _recording:
        _audio_frames.append(indata.copy())


def stop_recording(game_state):
    global _video_writer, _recording, _frame_count
    global _audio_stream, _audio_frames, _temp_video, _temp_audio, _filename

    if not _recording:
        return

    print("⏹️ Остановка записи...")

    # Останавливаем аудио
    if _audio_stream:
        _audio_stream.stop()
        _audio_stream.close()

    # Останавливаем видео
    if _video_writer:
        _video_writer.release()
        _video_writer = None

    _recording = False
    game_state["is_recording"] = False

    # Сохраняем аудио
    if _audio_frames and _temp_audio:
        audio_data = np.concatenate(_audio_frames, axis=0)
        sf.write(_temp_audio, audio_data, 44100)

    # Склеиваем через ffmpeg
    try:
        print("🔄 Склеивание видео и аудио...")
        cmd = [
            "ffmpeg", "-y",
            "-i", _temp_video,
            "-i", _temp_audio,
            "-c:v", "libx264",
            "-c:a", "aac",
            "-shortest",
            _filename
        ]
        subprocess.run(cmd, capture_output=True)

        # Удаляем временные файлы
        os.remove(_temp_video)
        os.remove(_temp_audio)

        print(f"✅ Готово: {_filename}")
    except Exception as e:
        print(f"❌ Ошибка склейки: {e}")


def capture_frame(screen, game_state):
    global _video_writer, _recording, _frame_count, _start_time

    if not _recording or not _video_writer:
        return

    try:
        # === ПРИВЯЗКА К РЕАЛЬНОМУ ВРЕМЕНИ ===
        elapsed = time.time() - _start_time
        expected_frames = int(elapsed * 60)  # сколько кадров должно быть по времени

        if _frame_count < expected_frames:
            # Нужно дублировать кадры (замедляем видео)
            for _ in range(expected_frames - _frame_count):
                _write_frame(screen)
        else:
            # Пишем один кадр
            _write_frame(screen)
        game_state["recorded_frames"] = _frame_count
        game_state["recorded_seconds"] = _frame_count // 60

    except Exception as e:
        print(f"⚠️ Ошибка кадра: {e}")


def _write_frame(screen):
    global _video_writer, _frame_count
    frame = pygame.surfarray.array3d(screen)
    frame = frame.swapaxes(0, 1)
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    _video_writer.write(frame)
    _frame_count += 1