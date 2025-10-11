#!/bin/bash

# 文档处理服务运行脚本（conda环境版本）

set -e  # 遇到错误时退出

echo "🚀 启动文档处理服务..."

# 检查conda是否安装
if ! command -v conda &> /dev/null
then
    echo "❌ 未找到conda，请先安装conda"
    exit 1
fi

# 激活conda环境
echo "🔧 激活conda环境 'main'..."
if conda env list | grep -q "main"; then
    conda activate main
else
    echo "❌ 未找到conda环境 'main'，请先创建该环境"
    exit 1
fi

# 检查并安装依赖
echo "📦 检查并安装依赖..."
if [ ! -f "requirements.txt" ]; then
    echo "❌ 未找到 requirements.txt 文件"
    exit 1
fi

pip install -r requirements.txt
pip install markitdown[docx,pdf]

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p uploads processed temp

# 启动服务
echo "🚀 启动服务..."
echo "🌐 服务地址: http://localhost:5000"
echo "📋 可用接口:"
echo "   - 健康检查: GET /health"
echo "   - 处理文档: POST /api/v1/process-document"
echo "   - 批量处理: POST /api/v1/batch-process"
echo "   - 下载结果: GET /api/v1/download/<task_id>/<filename>"
echo "🛑 按 Ctrl+C 停止服务"

python app.py