uvicorn app.main:app --host localhost --port 8000 --reload

docker run -p 6379:6379 --name my-redis -d redis

celery -A config.config.celery_app worker --loglevel=info

docker compose down -v && docker compose up