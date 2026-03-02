FROM python:3.12-alpine

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=1000:1000 watcher.py .

USER 1000

CMD ["python", "watcher.py"]
