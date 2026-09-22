FROM mcr.microsoft.com/playwright/python:v1.58.0-noble
WORKDIR /app
COPY requirements-browser.txt .
RUN pip install --no-cache-dir -r requirements-browser.txt
COPY . .
RUN mkdir -p /app/data
CMD ["python3", "server.py"]
