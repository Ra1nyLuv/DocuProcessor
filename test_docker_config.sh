#!/bin/bash

# Docker配置测试脚本

echo "========================================="
echo "Docker配置测试"
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

# 检查Docker是否已安装
check_docker_installed() {
    print_info "检查Docker是否已安装..."
    if command -v docker &> /dev/null; then
        print_success "Docker已安装"
        docker --version
    else
        print_error "Docker未安装"
        return 1
    fi
}

# 检查Docker服务是否运行
check_docker_running() {
    print_info "检查Docker服务是否运行..."
    if docker info &> /dev/null; then
        print_success "Docker服务正在运行"
    else
        print_error "Docker服务未运行"
        return 1
    fi
}

# 检查镜像加速器配置
check_registry_mirrors() {
    print_info "检查镜像加速器配置..."
    if docker info | grep -q "Registry Mirrors"; then
        print_success "检测到镜像加速器配置"
        echo "配置的镜像源:"
        docker info | grep -A 10 "Registry Mirrors" | sed 's/^/  /'
    else
        print_warning "未检测到镜像加速器配置"
        echo "  建议配置镜像加速器以提高镜像拉取速度"
    fi
}

# 测试拉取基础镜像
test_pull_base_image() {
    print_info "测试拉取基础镜像..."
    echo "  正在拉取python:3.10-slim镜像..."
    if timeout 60s docker pull python:3.10-slim &> /dev/null; then
        print_success "基础镜像拉取成功"
        docker image ls python:3.10-slim
    else
        print_error "基础镜像拉取失败或超时"
        echo "  可能的原因:"
        echo "  1. 网络连接问题"
        echo "  2. 未配置镜像加速器"
        echo "  3. 防火墙限制"
        return 1
    fi
}

# 主程序
main() {
    echo ""
    
    if ! check_docker_installed; then
        exit 1
    fi
    
    echo ""
    
    if ! check_docker_running; then
        exit 1
    fi
    
    echo ""
    
    check_registry_mirrors
    
    echo ""
    
    test_pull_base_image
    
    echo ""
    print_success "Docker配置测试完成"
}

# 执行主程序
main