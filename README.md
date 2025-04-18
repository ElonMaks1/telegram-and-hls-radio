## 📖 Описание

`radio.py` — это консольное приложение на Python, которое превращает ваш каталог аудио-дорожек в полноценную интернет-радиостанцию с динамическим плейлистом и настройкой по настроению.

Благодаря гибкому блоку расписания `SCHEDULE`, скрипт автоматически определяет текущий временной интервал и подбирает музыку под заданные настроения: утреннюю бодрость, дневной драйв, вечернюю романтику или спокойную ночную трансляцию.

Основные возможности:
- **Автоматический подбор треков** в зависимости от времени суток и настроений.
- **Промо-перебивки (PRBV)**: случайные джинглы и рекламные блоки с настраиваемыми интервалами.
- **Генерация HLS-потока** для веб-трансляции и одновременная отправка аудио на локальный и удалённый RTMP-сервер (локально и в Telegram).
- **Конфигурация через переменные окружения** (директории, пути вывода, ссылки RTMP) для гибкой настройки без правки кода.
- **Подробное логирование** всех операций и ошибок в консоль и файл `radio.log`.

Приложение легко масштабируется и интегрируется в любые DevOps-пайплайны, а также подходит для самостоятельного запуска на сервере или домашнем компьютере.

## 🚀 Особенности

- Автоматический выбор треков по текущему времени и настроению
- Перебивки (PRBV) через случайные интервалы
- Генерация HLS-потока и трансляция в RTMP (локально и в Telegram)
- Логирование всех событий и ошибок
- Шаблон расписания с возможностью донастройки

## 📂 Структура файлов

```text
├── .github/
│   └── workflows/            # GitHub Actions (CI/CD)
├── docs/                     # Документация (GitHub Pages)
├── songs/                    # Папка с музыкой по настроениям
│   └── Спокойное/
│   └── Энергичное/
│   ...
├── prbv/                     # Папка с перебивками
├── radio.py                  # Основной скрипт приложения
├── README.md                 # Настоящий файл
└── LICENSE                   # Лицензия MIT
```

## ⚙️ Установка и запуск

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/ElonMaks1/telegram-and-hls-radio.git
   cd radio-python
   ```
   
2. Создайте структуру папок и добавьте треки:
   ```bash
   mkdir -p songs/ prbv/
   # Поместите аудио-файлы в соответствующие папки
   ```
3. Настройте переменные окружения (опционально):
   ```bash
   export SONGS_DIR=./songs
   export PRBV_DIR=./prbv
   export HLS_OUTPUT=/tmp/hls
   export LOCAL_RTMP=rtmp://localhost/live/stream
   export TELEGRAM_RTMP=rtmps://dc4-1.rtmp.t.me/...
   ```
4. Запустите приложение:
   ```bash
   python radio.py
   ```

## 📑 Конфигурация расписания

В файле `radio.py` укажите блок `SCHEDULE` с временными слотами и соответствующими настроениями:

```python
SCHEDULE = [
    {"time": "06:00-07:00", "moods": ["Спокойное", "Ностальгическое"]},
    ...
]
```

## 🔧 Логирование

Логи пишутся в файл `radio.log` и выводятся в консоль. Формат:
```
2025-04-18 12:34:56,789 - INFO - 🎵 Основной трек: song.mp3
```

## 🤝 Вклад и обратная связь

1. Сделайте fork репозитория
2. Создайте ветку для вашей фичи: `git checkout -b feature/your-feature`
3. Напишите код и тесты
4. Откройте Pull Request
