FROM --platform=linux/amd64 python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
ENV PYTHONUNBUFFERED=1

# Use python directly to run the application
CMD ["python", "wsgi.py"]