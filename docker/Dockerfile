FROM python:3.12-alpine

LABEL maintainer="cbodden" \
      org.opencontainers.image.source="https://github.com/cbodden/cleaner"

# Keeps Python from buffering stdout/stderr
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .
COPY templates/ templates/

EXPOSE 5000

CMD ["python", "app.py"]
