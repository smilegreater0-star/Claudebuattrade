FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bott_v4.py .

CMD ["python", "bott_v4.py"]
