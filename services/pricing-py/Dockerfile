FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY pricing ./pricing

EXPOSE 8002 9002

CMD ["python", "-m", "pricing.main"]
