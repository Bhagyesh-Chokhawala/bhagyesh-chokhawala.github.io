FROM python:3.12-slim

WORKDIR /app

COPY requirements-container.txt ./
RUN pip install --no-cache-dir -r requirements-container.txt

COPY . .

ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT} --workers 1 --access-logfile - --error-logfile - wsgi:app"]
