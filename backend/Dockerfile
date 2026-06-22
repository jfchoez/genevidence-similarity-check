FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

ARG INSTALL_SEMANTIC=false

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY requirements-semantic.txt .
RUN if [ "$INSTALL_SEMANTIC" = "true" ]; then pip install --no-cache-dir -r requirements-semantic.txt; fi

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
