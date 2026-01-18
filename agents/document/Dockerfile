FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt langgraph-cli[inmem]

COPY . /app

EXPOSE 2027
CMD ["langgraph", "dev", "--host", "0.0.0.0", "--port", "2027"]
