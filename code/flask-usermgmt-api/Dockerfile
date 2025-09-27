FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .

RUN apt-get update && apt-get install -y gcc libffi-dev libssl-dev && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get remove -y gcc libffi-dev libssl-dev && apt-get autoremove -y

COPY . .

EXPOSE 8080
CMD ["python", "app.py"]

