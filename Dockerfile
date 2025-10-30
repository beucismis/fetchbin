FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

ENV FETCHBIN_DATA_DIR=/data

COPY . .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir hatchling && \
    pip install --no-cache-dir .

EXPOSE 8000

CMD ["uvicorn", "fetchbin.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
