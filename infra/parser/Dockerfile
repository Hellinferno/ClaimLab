FROM python:3.12-slim

RUN groupadd -r parser && useradd -r -g parser -u 10002 parser

WORKDIR /app
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir pypdf==5.1.0

COPY backend/src/claimlab/services/pdf_service.py /app/claimlab/services/pdf_service.py
COPY backend/src/claimlab/contracts /app/claimlab/contracts
COPY infra/parser/entrypoint.py /app/entrypoint.py
ENV PYTHONPATH=/app

USER parser
ENTRYPOINT ["python", "/app/entrypoint.py"]
