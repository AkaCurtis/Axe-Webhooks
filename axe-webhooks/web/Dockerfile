FROM python:3.12-alpine AS builder

WORKDIR /build

RUN pip install --no-cache-dir flask

FROM python:3.12-alpine

USER 1000

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --chown=1000:1000 app.py .
COPY --chown=1000:1000 templates templates/

EXPOSE 3456

CMD ["python", "app.py"]
