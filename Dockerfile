FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Preserve game_data.db outside the volume mount point so it survives mount
RUN cp data/game_data.db /app/game_data_shipped.db

ENV PYTHONUNBUFFERED=1
ENV DATA_DIR=/app/data

EXPOSE 8080

CMD ["gunicorn", "server.main:app", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "4", "--timeout", "300"]
