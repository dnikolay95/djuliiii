# Telegram New Year Bot

Простой бот на Python 3.11 и aiogram 3.x. При старте показывает кнопку, по нажатию отправляет случайное поздравление с Новым годом. Добавлен каркас backend (FastAPI, порт 8011) и frontend (Vite React) для админки.

## Запуск локально
- `python -m venv .venv`
- Активируйте виртуальное окружение:
  - Windows PowerShell: `.venv\\Scripts\\Activate.ps1`
  - Linux/macOS: `source .venv/bin/activate`
- `pip install -r requirements.txt`
- `copy env.example .env` (Windows) или `cp env.example .env` (Linux/macOS) и задайте переменные:
  - `BOT_TOKEN` — токен бота
  - `AUTH_SECRET` — секрет для авторизации в вебке
  - `DB_PATH` — путь к SQLite (по умолчанию `./data/bot.db`)
  - `BACKEND_PORT` — порт backend (по умолчанию 8011)
- Запуск бота: `python -m app.main`
- Запуск backend (порт 8011): `uvicorn backend.main:app --host 0.0.0.0 --port 8011 --reload`
- Запуск frontend (порт 5173):
  - `cd frontend`
  - `npm install`
  - `npm run dev -- --host --port 5173`

## Запуск в Docker
- Собрать образ: `docker build -t tg-ny-bot .`
- Запустить: `docker run --rm -e BOT_TOKEN=ВАШ_ТОКЕН tg-ny-bot`
- Можно использовать файл `.env`: `docker run --rm --env-file .env tg-ny-bot`

## Docker Compose (бот + веб backend)
- Поднять оба сервиса:
  - `docker compose up --build -d`
- Бот: контейнер `tg-ny-bot`.
- Backend: контейнер `tg-ny-backend`, порт `8011` (health: `http://localhost:8011/health`).
- Авторизация: `ADMIN_LOGIN`/`ADMIN_PASSWORD` (по умолчанию admin/admin2), кука-сессия.
- API: `/api/auth/login|logout|me`, `/api/users`, `/api/users/{tg_user_id}`, `/api/greetings`, `/api/messages`, `/api/stats`.
- Realtime: WebSocket `ws://localhost:8011/ws` (использует auth cookie), события user_upserted, message_received, greeting_sent.
- Данные/БД: общий volume `./data:/app/data`.

## Команды бота
- `/info` — О боте
- `/greet` — Случайное поздравление

## Важно
- Никогда не коммитьте реальные токены и содержимое `.env`.


