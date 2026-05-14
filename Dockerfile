FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN python - <<'PY'
from pathlib import Path
src = Path('/app/requirements.txt')
text = src.read_text(encoding='utf-16')
Path('/tmp/requirements-utf8.txt').write_text(text, encoding='utf-8')
PY
RUN pip install --no-cache-dir -r /tmp/requirements-utf8.txt

COPY . /app

EXPOSE 8002

CMD ["python", "main.py"]
