FROM python:3.13-slim

# Убери apt-get install если он не нужен!
# Flask обычно не требует системных пакетов
RUN apt-get update && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN groupadd -r appuser && useradd --no-log-init -r -g appuser appuser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8080  

CMD ["python", "app.py"]
