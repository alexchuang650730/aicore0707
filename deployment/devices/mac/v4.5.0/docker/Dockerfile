# ClaudeEditor 4.5 + PowerAutomation Core 4.5 Docker镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV CLAUDEDITOR_ENV=production
ENV CLAUDEDITOR_VERSION=4.5.0

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    tesseract-ocr-chi-tra \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# 创建非root用户
RUN useradd -m -u 1000 claudeditor && \
    chown -R claudeditor:claudeditor /app

# 复制requirements文件
COPY requirements.txt /app/

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY core/ /app/core/
COPY adapters/ /app/adapters/
COPY ui/ /app/ui/
COPY tests/ /app/tests/
COPY scripts/ /app/scripts/
COPY main.py /app/
COPY pytest.ini /app/
COPY run_tests.py /app/

# 创建必要的目录
RUN mkdir -p /app/data /app/logs /app/cache /app/temp && \
    chown -R claudeditor:claudeditor /app

# 切换到非root用户
USER claudeditor

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# 暴露端口
EXPOSE 8000 8001 8002

# 启动命令
CMD ["python", "main.py"]

