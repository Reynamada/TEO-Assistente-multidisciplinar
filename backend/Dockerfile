FROM python:3.12-slim

WORKDIR /app

# Install dependencies (requirements.txt is at repo root)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy templates used by the backend
COPY templates/ ./templates/

EXPOSE 8000
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
