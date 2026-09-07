# A small, production-friendly base image with Python pre-installed.
FROM python:3.12-slim

# Prevents Python from writing .pyc files and buffers stdout/stderr less,
# so logs show up immediately in `docker logs`.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first, separately from the app code. Docker caches
# each instruction as a layer -- as long as requirements.txt doesn't
# change, this layer is reused on rebuilds, making them much faster.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the rest of the application code.
COPY . .

EXPOSE 8000

# Runs the same app used in local development, just without --reload
# (auto-reload is a dev-only feature and shouldn't run in a container
# meant to represent production).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
