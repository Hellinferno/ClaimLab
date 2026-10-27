FROM python:3.12-slim

RUN groupadd -r runner && useradd -r -g runner -u 10001 runner

WORKDIR /app
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/src /app/src
COPY infra/runner/entrypoint.py /app/entrypoint.py
ENV PYTHONPATH=/app/src

USER runner
ENTRYPOINT ["python", "/app/entrypoint.py"]
