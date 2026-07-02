FROM python:3.12-slim

WORKDIR /app

# Copy only backend requirements (from repo root context)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only the backend application code
COPY backend/app ./app
COPY backend/main.py .
COPY backend/scripts ./scripts
COPY backend/sql ./sql
COPY backend/templates ./templates

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
