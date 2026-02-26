FROM python:3.12-alpine
WORKDIR /app
RUN pip install --no-cache-dir flask
COPY app.py /app/app.py
COPY templates /app/templates
EXPOSE 3456
CMD ["python", "/app/app.py"]