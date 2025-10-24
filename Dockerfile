# 使用 Python 3.10-slim 基础镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量（合并减少层数）
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py \
    FLASK_ENV=production

# 配置清华 APT 源
RUN set -eux; \
    CODENAME=$(grep -oP 'VERSION_CODENAME=\K\w+' /etc/os-release); \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ $CODENAME main" > /etc/apt/sources.list; \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian-security/ $CODENAME-security main" >> /etc/apt/sources.list; \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件（利于缓存）
COPY requirements.txt .

# 安装 Python 依赖（使用清华 PyPI 源加速）
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt && \
    pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple "markitdown[docx,pdf]"

# 创建非 root 用户
RUN useradd --create-home --shell /bin/bash appuser

# 创建必要目录并设置权限
RUN mkdir -p uploads processed temp converted_data sliced_data merged_data && \
    chown -R appuser:appuser . && \
    chmod -R 777 uploads processed temp converted_data sliced_data merged_data

# 复制代码并直接指定用户（避免额外 chown 层）
COPY --chown=appuser:appuser . .

# 切换用户
USER appuser

# 暴露端口
EXPOSE 5000

# 启动命令
CMD ["python", "app.py"]