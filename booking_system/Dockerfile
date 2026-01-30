# 1. 使用官方 Python 轻量级镜像
FROM python:3.9-slim

# 2. 设置工作目录
WORKDIR /app

# 3. 复制依赖文件到容器
COPY requirements.txt .

# 4. 安装依赖 (使用清华源加速)
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 5. 复制当前目录下的所有文件到容器
COPY . .

# 6. 暴露端口 (Zeabur 会自动分配，但写上也无妨)
EXPOSE 5000

# 7. 启动命令 (直接运行你的 main.py)
CMD ["python", "main.py"]