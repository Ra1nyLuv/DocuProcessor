#!/bin/bash

# 文档处理服务API测试脚本
# 提供简单的curl命令示例来测试API功能

echo "========================================="
echo "文档处理服务API测试"
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

# 检查服务是否运行
check_service() {
    print_info "检查服务是否运行..."
    if curl -s -f http://localhost:5000/health > /dev/null; then
        print_success "服务运行正常"
        return 0
    else
        print_error "服务未运行或无法访问"
        return 1
    fi
}

# 健康检查
health_check() {
    print_info "执行健康检查..."
    response=$(curl -s -w "%{http_code}" http://localhost:5000/health)
    http_code="${response: -3}"
    
    if [ "$http_code" = "200" ]; then
        print_success "健康检查通过"
        echo "响应内容:"
        echo "${response%???}" | jq '.' 2>/dev/null || echo "${response%???}"
    else
        print_error "健康检查失败 (HTTP $http_code)"
    fi
}

# 创建测试文件
create_test_file() {
    if [ ! -f "test_sample.txt" ]; then
        print_info "创建测试文件..."
        cat > test_sample.txt << EOF
# 测试文档

这是一个用于测试文档处理服务的示例文档。

## 章节一

测试内容...

## 章节二

更多测试内容...
EOF
        print_success "测试文件 test_sample.txt 创建完成"
    else
        print_info "测试文件 test_sample.txt 已存在"
    fi
}

# 单文档处理测试
test_single_document() {
    if [ ! -f "test_sample.txt" ]; then
        print_error "测试文件不存在"
        return 1
    fi
    
    print_info "测试单文档处理..."
    response=$(curl -s -w "%{http_code}" \
        -F "file=@test_sample.txt" \
        http://localhost:5000/api/v1/process-document)
    
    http_code="${response: -3}"
    
    if [ "$http_code" = "200" ]; then
        print_success "单文档处理成功"
        echo "响应内容:"
        echo "${response%???}" | jq '.' 2>/dev/null || echo "${response%???}"
        
        # 提取任务ID和结果文件名用于后续测试
        task_id=$(echo "${response%???}" | jq -r '.task_id' 2>/dev/null)
        result_file=$(echo "${response%???}" | jq -r '.result_file' 2>/dev/null)
        
        if [ "$task_id" != "null" ] && [ "$result_file" != "null" ]; then
            echo "task_id=$task_id" > .test_result
            echo "result_file=$result_file" >> .test_result
        fi
    else
        print_error "单文档处理失败 (HTTP $http_code)"
        echo "响应内容:"
        echo "${response%???}"
    fi
}

# 下载结果测试
test_download_result() {
    if [ ! -f ".test_result" ]; then
        print_warning "没有找到处理结果信息，请先运行单文档处理测试"
        return 1
    fi
    
    # 读取处理结果信息
    source .test_result
    if [ -z "$task_id" ] || [ -z "$result_file" ]; then
        print_error "处理结果信息不完整"
        return 1
    fi
    
    print_info "测试结果下载..."
    # URL编码文件名
    encoded_filename=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$result_file'))" 2>/dev/null)
    
    if [ -z "$encoded_filename" ]; then
        # 如果python命令失败，使用原始文件名
        encoded_filename="$result_file"
    fi
    
    response=$(curl -s -w "%{http_code}" \
        -o "downloaded_result.json" \
        "http://localhost:5000/api/v1/download/$task_id/$encoded_filename")
    
    http_code="${response: -3}"
    
    if [ "$http_code" = "200" ]; then
        print_success "结果下载成功"
        print_info "结果文件已保存为 downloaded_result.json"
        
        # 显示结果文件大小
        file_size=$(stat -c%s "downloaded_result.json" 2>/dev/null || stat -f%z "downloaded_result.json" 2>/dev/null)
        print_info "文件大小: $file_size 字节"
    else
        print_error "结果下载失败 (HTTP $http_code)"
    fi
}

# 显示使用说明
show_usage() {
    echo ""
    echo "使用方法:"
    echo "  $0 [选项]"
    echo ""
    echo "选项:"
    echo "  health     执行健康检查"
    echo "  single     测试单文档处理"
    echo "  download   测试结果下载"
    echo "  all        执行所有测试"
    echo "  help       显示此帮助信息"
    echo ""
}

# 主程序
main() {
    if [ $# -eq 0 ]; then
        show_usage
        exit 0
    fi
    
    # 检查服务
    if ! check_service; then
        print_error "请先启动文档处理服务"
        exit 1
    fi
    
    case "$1" in
        health)
            health_check
            ;;
        single)
            create_test_file
            test_single_document
            ;;
        download)
            test_download_result
            ;;
        all)
            health_check
            echo ""
            create_test_file
            test_single_document
            echo ""
            test_download_result
            ;;
        help)
            show_usage
            ;;
        *)
            print_error "未知选项: $1"
            show_usage
            exit 1
            ;;
    esac
}

# 执行主程序
main "$@"