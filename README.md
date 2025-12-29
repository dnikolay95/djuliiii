# Telegram New Year Bot

Простой бот на Python 3.11 и aiogram 3.x. При старте показывает кнопку, по нажатию отправляет случайное поздравление с Новым годом.

## Запуск локально
- `python -m venv .venv`
- Активируйте виртуальное окружение:
  - Windows PowerShell: `.venv\\Scripts\\Activate.ps1`
  - Linux/macOS: `source .venv/bin/activate`
- `pip install -r requirements.txt`
- `cp .env.example .env` и вставьте свой токен.
- `python -m app.main`

## Запуск в Docker
- Собрать образ: `docker build -t tg-ny-bot .`
- Запустить: `docker run --rm -e BOT_TOKEN=ВАШ_ТОКЕН tg-ny-bot`
- Можно использовать файл `.env`: `docker run --rm --env-file .env tg-ny-bot`

## Команды бота
- `/info` — О боте
- `/greet` — Случайное поздравление

## Важно
- Никогда не коммитьте реальные токены и содержимое `.env`.


