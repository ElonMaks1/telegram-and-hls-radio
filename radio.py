import os
import random
import subprocess
import time
import logging
from datetime import datetime
from collections import deque
from signal import signal, SIGINT, SIGTERM

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('radio.log'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


SONGS_DIR = os.getenv('SONGS_DIR', 'songs')
PRBV_DIR = os.getenv('PRBV_DIR', os.path.join(SONGS_DIR, 'prbv'))
HLS_OUTPUT = os.getenv('HLS_OUTPUT', '/tmp/hls')
LOCAL_RTMP = os.getenv('LOCAL_RTMP', 'rtmp://localhost/live/stream')
TELEGRAM_RTMP = os.getenv('TELEGRAM_RTMP', 'RTMP adress here') #change it
CURRENT_TRACK_FILE = os.getenv('CURRENT_TRACK_FILE', 'current_track.txt')
MAX_HISTORY_SIZE = 30

SCHEDULE = [
    {"time": "06:00-07:00", "moods": ["Спокойное", "Ностальгическое"]},
    {"time": "07:00-09:00", "moods": ["Весёлое", "Нейтральное"]},
    {"time": "09:00-11:00", "moods": ["Весёлое", "Энергичное"]},
    {"time": "11:00-13:00", "moods": ["Танцевальное", "Энергичное"]},
    {"time": "13:00-15:00", "moods": ["Нейтральное", "Романтическое"]},
    {"time": "15:00-17:00", "moods": ["Танцевальное", "Агрессивное"]},
    {"time": "17:00-19:00", "moods": ["Романтическое", "Спокойное"]},
    {"time": "19:00-19:50", "moods": ["Спокойное", "Ностальгическое", "Нейтральное"]},
    {"time": "19:50-20:10", "moods": ["Специальный"]},
    {"time": "20:10-21:00", "moods": ["Спокойное", "Ностальгическое", "Нейтральное"]},
    {"time": "21:00-00:00", "moods": ["Грустноватое", "Нейтральное", "Ностальгическое"]},
    {"time": "00:00-06:00", "moods": ["Спокойное", "Нейтральное"]}
]


history = deque(maxlen=MAX_HISTORY_SIZE)

def get_minutes(time_str):
    """Преобразует 'ЧЧ:ММ' в минуты."""
    try:
        h, m = map(int, time_str.split(':'))
        return h * 60 + m
    except (ValueError, AttributeError):
        logger.error(f"Некорректное время в расписании: {time_str}")
        return 0

def get_current_schedule():
    """Возвращает текущие настроения по расписанию."""
    now = datetime.now()
    current_minutes = now.hour * 60 + now.minute

    for slot in SCHEDULE:
        start_str, end_str = slot["time"].split('-')
        start = get_minutes(start_str)
        end = get_minutes(end_str)

        if start <= end:
            if start <= current_minutes < end:
                return slot["moods"]
        else:
            if current_minutes >= start or current_minutes < end:
                return slot["moods"]
    return []

def list_tracks_from_moods(moods):
    """Возвращает треки по настроению."""
    tracks = []
    for mood in moods:
        mood_path = os.path.join(SONGS_DIR, mood)
        if not os.path.isdir(mood_path):
            logger.warning(f"Папка настроения {mood_path} не найдена!")
            continue
        try:
            for file in os.listdir(mood_path):
                if file.lower().endswith(('.mp3', '.aac', '.wav', '.flac', '.ogg')):
                    tracks.append(os.path.join(mood_path, file))
        except OSError as e:
            logger.error(f"Ошибка чтения папки {mood_path}: {e}")
    return tracks

def list_prbv_tracks():
    """Треки для перебивок."""
    if not os.path.isdir(PRBV_DIR):
        logger.error(f"Папка перебивок {PRBV_DIR} не найдена!")
        return []
    return [
        os.path.join(PRBV_DIR, f) 
        for f in os.listdir(PRBV_DIR) 
        if f.lower().endswith(('.mp3', '.aac', '.wav', '.flac', '.ogg'))
    ]

def write_current_track(track_path):

    try:
        with open(CURRENT_TRACK_FILE, 'w', encoding='utf-8') as f:
            f.write(f"Сейчас играет: {os.path.basename(track_path)}")
    except IOError as e:
        logger.error(f"Не удалось записать текущий трек: {e}")

def play_with_ffmpeg(input_file):

    if not os.path.isfile(input_file):
        logger.error(f"Трек {input_file} не найден!")
        return False

    hls_path = os.path.join(HLS_OUTPUT, "stream.m3u8")
    tee_output = (
        f"[f=hls:hls_time=4:hls_list_size=5:hls_flags=delete_segments]{hls_path}|"
        f"[f=flv]{LOCAL_RTMP}|"
        f"[f=flv]{TELEGRAM_RTMP}"
    )

    cmd = [
        "ffmpeg",
        "-re",
        "-i", input_file,
        "-c:a", "aac",
        "-b:a", "128k",
        "-ar", "44100",
        "-ac", "2",
        "-f", "tee",
        "-map", "0:a",
        "-hls_allow_cache", "0", 
        tee_output
    ]

    try:
        logger.info(f"Запуск ffmpeg для файла: {input_file}")
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg завершился с ошибкой: {e}")
        return False

def graceful_shutdown(signum, frame):
    """Обработчик для SIGINT/SIGTERM."""
    logger.info("Получен сигнал завершения. Завершаюсь...")
    raise SystemExit(0)

def main():
    signal(SIGINT, graceful_shutdown)
    signal(SIGTERM, graceful_shutdown)
    os.makedirs(HLS_OUTPUT, exist_ok=True)
    os.makedirs(SONGS_DIR, exist_ok=True)
    os.makedirs(PRBV_DIR, exist_ok=True)


    prbv_tracks = list_prbv_tracks()
    if not prbv_tracks:
        logger.error("Нет треков для перебивок. Работать не с чем!")
        return

    main_track_counter = 0
    next_prbv_interval = random.randint(10, 15)

    try:
        while True:
            moods = get_current_schedule()
            if not moods:
                logger.warning("Нет расписания для текущего времени. Жду 60 сек...")
                time.sleep(60)
                continue
            tracks = list_tracks_from_moods(["Специальный"] if "Специальный" in moods else moods)
            if not tracks:
                logger.warning(f"Нет треков для настроений {moods}. Жду 30 сек...")
                time.sleep(30)
                continue

            if main_track_counter >= next_prbv_interval:
                selected = random.choice(prbv_tracks)
                logger.info(f"▶️ Перебивка: {os.path.basename(selected)}")
                write_current_track(selected)
                if not play_with_ffmpeg(selected):
                    continue
                main_track_counter = 0
                next_prbv_interval = random.randint(10, 15)
            else:
                available = [t for t in tracks if t not in history]
                selected = random.choice(available if available else tracks)
                logger.info(f"🎵 Основной трек: {os.path.basename(selected)}")
                write_current_track(selected)
                if not play_with_ffmpeg(selected):
                    continue
                history.append(selected)
                main_track_counter += 1
    except Exception as e:
        logger.critical(f"💥 Критическая ошибка: {e}", exc_info=True)

if __name__ == "__main__":
    main()
