FROM python:3.11-slim

WORKDIR /app

# 先安裝依賴，利用 Docker 快取機制
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 關鍵：這行必須存在，且放在安裝依賴之後，確保 COPY 最新程式碼
COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]