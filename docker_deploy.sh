#!/bin/bash

# Docker容器化部署脚本
# 用于一键部署文档处理服务

echo "========================================="
echo "文档处理服务Docker容器化部署"
echo "========================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的信息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否在项目根目录
if [ ! -f "app.py" ]; then
    print_error "请在项目根目录运行此脚本"
    exit 1
fi

# 获取当前目录作为项目目录
PROJECT_DIR=$(pwd)

# 显示部署选项
echo ""
echo "请选择部署方式:"
echo "1) 标准部署 (使用默认配置)"
echo "2) 国内网络优化部署 (使用国内镜像源)"
echo "3) 简化版部署 (移除复杂配置，提高成功率)"
echo "4) 生产环境部署 (包含资源限制和性能优化)"
echo "5) 退出"
echo ""

read -p "请输入选项 (1-5): " choice

case $choice in
    1)
        print_info "开始标准部署..."
        DEPLOY_FILE="docker-compose.yml"
        ;;
    2)
        print_info "开始国内网络优化部署..."
        DEPLOY_FILE="docker-compose.cn.yml"
        # 检查Dockerfile.cn是否存在
        if [ ! -f "Dockerfile.cn" ]; then
            print_warning "Dockerfile.cn不存在，将使用标准Dockerfile"
            DEPLOY_FILE="docker-compose.yml"
        fi
        ;;
    3)
        print_info "开始简化版部署..."
        DEPLOY_FILE="docker-compose.simple.yml"
        ;;
    4)
        print_info "开始生产环境部署..."
        DEPLOY_FILE="docker-compose.prod.yml"
        ;;
    5)
        print_info "退出部署"
        exit 0
        ;;
    *)
        print_error "无效选项"
        exit 1
        ;;
esac

# 检查部署文件是否存在
if [ ! -f "$DEPLOY_FILE" ]; then
    print_error "部署文件不存在: $DEPLOY_FILE"
    exit 1
fi

# 创建必要目录
print_info "创建必要目录..."
mkdir -p uploads processed temp
print_success "目录创建完成"

# 构建镜像
print_info "构建Docker镜像..."
if docker compose -f $DEPLOY_FILE build; then
    print_success "Docker镜像构建成功"
else
    print_error "Docker镜像构建失败"
    exit 1
fi

# 启动服务
print_info "启动服务..."
if docker compose -f $DEPLOY_FILE up -d; then
    print_success "服务启动成功"
else
    print_error "服务启动失败"
    exit 1
fi

# 等待服务启动
print_info "等待服务启动..."
sleep 10

# 检查服务状态
print_info "检查服务状态..."
if docker compose -f $DEPLOY_FILE ps | grep -q "Up"; then
    print_success "服务运行正常"
    
    # 显示服务信息
    echo ""
    echo "========================================="
    echo "服务信息"
    echo "========================================="
    echo "服务地址: http://localhost:5000"
    echo "健康检查: curl http://localhost:5000/health"
    echo "查看日志: docker compose -f $DEPLOY_FILE logs -f"
    echo "停止服务: docker compose -f $DEPLOY_FILE down"
    echo "========================================="
    
    print_success "部署完成！"
else
    print_error "服务启动失败，请检查日志"
    docker compose -f $DEPLOY_FILE logs
    exit 1
fi