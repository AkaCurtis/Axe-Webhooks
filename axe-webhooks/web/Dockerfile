FROM python:3.12-alpine

WORKDIR /app

RUN pip install --no-cache-dir flask

COPY --chown=1000:1000 app.py .
COPY --chown=1000:1000 templates templates/

USER 1000

EXPOSE 3456

CMD ["python", "app.py"]
