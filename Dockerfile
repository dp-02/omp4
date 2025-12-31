# 1. 指定 Base Image (基底映像檔)
# 使用官方 Python 3.9 的輕量版本 (slim 版本體積較小)
FROM python:3.9-slim

# 2. 設定工作目錄
# 這是在容器(Container)內部的路徑，所有後續指令都會在這裡執行
WORKDIR /app

# 3. 複製 requirements.txt 到容器中
COPY requirements.txt .

# 4. 安裝依賴套件
# --no-cache-dir 可以減少 Image 的體積
RUN pip install --no-cache-dir -r requirements.txt

# 5. 複製目前目錄下的所有程式碼到容器中
COPY . .

# 6. 設定容器啟動時執行的指令
# 這裡假設你的主程式是 main.py
CMD ["python", "main.py"]