FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY grant_scout_production_v2.1.py .
COPY .env .

ENV PORT=8080
EXPOSE 8080

CMD ["python", "-u", "grant_scout_production_v2.1.py"]
