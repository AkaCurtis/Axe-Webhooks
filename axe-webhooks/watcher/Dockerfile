FROM python:3.12-alpine
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
COPY watcher.py /app/
CMD ["python", "/app/watcher.py"]
