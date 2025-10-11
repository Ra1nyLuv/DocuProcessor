#!/bin/bash

# Docker容器化部署服务调用测试脚本
# 使用File/temp/test_user下的文档进行测试

echo "========================================="
echo "文档处理服务Docker容器化部署测试"
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

# 检查Docker是否安装
check_docker() {
    print_info "检查Docker是否已安装..."
    if command -v docker &> /dev/null; then
        print_success "Docker已安装"
        docker --version
        return 0
    else
        print_error "Docker未安装"
        return 1
    fi
}

# 检查Docker服务是否运行
check_docker_service() {
    print_info "检查Docker服务是否运行..."
    if docker info &> /dev/null; then
        print_success "Docker服务正在运行"
        return 0
    else
        print_error "Docker服务未运行"
        return 1
    fi
}

# 检查docker-compose命令
check_docker_compose() {
    print_info "检查docker-compose命令..."
    # 检查docker compose（不带连字符）命令，优先使用（根据经验教训）
    if command -v docker &> /dev/null && docker compose version &> /dev/null; then
        print_success "docker compose命令可用"
        echo "使用命令: docker compose"
        export COMPOSE_CMD="docker compose"
        return 0
    # 检查docker-compose（带连字符）命令
    elif command -v docker-compose &> /dev/null; then
        print_success "docker-compose命令可用"
        echo "使用命令: docker-compose"
        export COMPOSE_CMD="docker-compose"
        return 0
    else
        print_error "docker-compose命令不可用"
        return 1
    fi
}

# 构建并启动服务
start_service() {
    print_info "构建并启动文档处理服务..."
    
    # 创建必要目录
    print_info "创建必要目录..."
    mkdir -p ../uploads ../processed ../temp
    
    # 构建镜像
    print_info "构建Docker镜像..."
    if $COMPOSE_CMD build; then
        print_success "Docker镜像构建成功"
    else
        print_error "Docker镜像构建失败"
        return 1
    fi
    
    # 启动服务
    print_info "启动服务..."
    if $COMPOSE_CMD up -d; then
        print_success "服务启动成功"
        return 0
    else
        print_error "服务启动失败"
        return 1
    fi
}

# 等待服务启动
wait_for_service() {
    print_info "等待服务启动..."
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f http://localhost:5000/health > /dev/null; then
            print_success "服务已启动并运行"
            return 0
        fi
        print_info "等待服务启动... ($attempt/$max_attempts)"
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_error "服务启动超时"
    return 1
}

# 检查测试文件
check_test_files() {
    local test_dir="../../File/temp/test_user/test_knowledge_base"
    print_info "检查测试文件目录: $test_dir"
    
    if [ ! -d "$test_dir" ]; then
        print_error "测试文件目录不存在: $test_dir"
        return 1
    fi
    
    # 查找支持的文件类型
    local supported_files=()
    while IFS= read -r -d '' file; do
        supported_files+=("$file")
    done < <(find "$test_dir" -type f \( -name "*.txt" -o -name "*.pdf" -o -name "*.docx" -o -name "*.doc" -o -name "*.html" -o -name "*.htm" -o -name "*.pptx" -o -name "*.xlsx" \) -print0 2>/dev/null | head -n 3)
    
    if [ ${#supported_files[@]} -eq 0 ]; then
        print_error "未找到支持的测试文件"
        return 1
    fi
    
    print_success "找到 ${#supported_files[@]} 个测试文件:"
    for file in "${supported_files[@]}"; do
        echo "  - $(basename "$file") ($(stat -c%s "$file" 2>/dev/null || stat -f%z "$file" 2>/dev/null) bytes)"
    done
    
    # 导出文件列表供后续使用
    export TEST_FILES=("${supported_files[@]}")
    return 0
}

# 测试单文档处理
test_single_document() {
    local test_file="${TEST_FILES[0]}"
    local file_name=$(basename "$test_file")
    
    print_info "测试单文档处理: $file_name"
    
    # 复制文件到uploads目录
    cp "$test_file" "../uploads/"
    
    # 发送处理请求
    local response
    response=$(curl -s -w "%{http_code}" \
        -F "file=@../uploads/$file_name" \
        http://localhost:5000/api/v1/process-document)
    
    local http_code="${response: -3}"
    local response_body="${response%???}"
    
    if [ "$http_code" = "200" ]; then
        print_success "单文档处理成功"
        echo "响应内容:"
        echo "$response_body" | jq '.' 2>/dev/null || echo "$response_body"
        
        # 提取任务ID和结果文件名
        local task_id
        local result_file
        task_id=$(echo "$response_body" | jq -r '.task_id' 2>/dev/null)
        result_file=$(echo "$response_body" | jq -r '.result_file' 2>/dev/null)
        
        if [ "$task_id" != "null" ] && [ "$result_file" != "null" ]; then
            echo "task_id=$task_id" > .test_result_docker
            echo "result_file=$result_file" >> .test_result_docker
            print_success "处理结果信息已保存"
        fi
        return 0
    else
        print_error "单文档处理失败 (HTTP $http_code)"
        echo "响应内容:"
        echo "$response_body"
        return 1
    fi
}

# 测试批量文档处理
test_batch_documents() {
    print_info "测试批量文档处理 (${#TEST_FILES[@]}个文件)"
    
    # 准备文件参数
    local curl_params=()
    for file in "${TEST_FILES[@]}"; do
        local file_name=$(basename "$file")
        # 复制文件到uploads目录
        cp "$file" "../uploads/"
        curl_params+=("-F" "files=@../uploads/$file_name")
    done
    
    # 发送批量处理请求
    local response
    response=$(curl -s -w "%{http_code}" \
        "${curl_params[@]}" \
        http://localhost:5000/api/v1/batch-process)
    
    local http_code="${response: -3}"
    local response_body="${response%???}"
    
    if [ "$http_code" = "200" ]; then
        print_success "批量文档处理成功"
        echo "响应内容:"
        echo "$response_body" | jq '.' 2>/dev/null || echo "$response_body"
        return 0
    else
        print_error "批量文档处理失败 (HTTP $http_code)"
        echo "响应内容:"
        echo "$response_body"
        return 1
    fi
}

# 测试下载结果
test_download_result() {
    if [ ! -f ".test_result_docker" ]; then
        print_warning "没有找到处理结果信息，请先运行单文档处理测试"
        return 1
    fi
    
    # 读取处理结果信息
    source .test_result_docker
    if [ -z "$task_id" ] || [ -z "$result_file" ]; then
        print_error "处理结果信息不完整"
        return 1
    fi
    
    print_info "测试结果下载..."
    # URL编码文件名
    local encoded_filename
    encoded_filename=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$result_file', safe=''))" 2>/dev/null)
    
    if [ -z "$encoded_filename" ]; then
        # 如果python命令失败，使用原始文件名并进行基本的URL编码
        encoded_filename=$(echo "$result_file" | sed 's|/|%2F|g')
    fi
    
    local response
    response=$(curl -s -w "%{http_code}" \
        -o "test_results/docker_downloaded_result.json" \
        "http://localhost:5000/api/v1/download/$task_id/$encoded_filename")
    
    local http_code="${response: -3}"
    
    if [ "$http_code" = "200" ]; then
        print_success "结果下载成功"
        print_info "结果文件已保存为 test_results/docker_downloaded_result.json"
        
        # 显示结果文件大小
        local file_size
        file_size=$(stat -c%s "test_results/docker_downloaded_result.json" 2>/dev/null || stat -f%z "test_results/docker_downloaded_result.json" 2>/dev/null)
        print_info "文件大小: $file_size 字节"
        return 0
    else
        print_error "结果下载失败 (HTTP $http_code)"
        echo "响应内容:"
        echo "${response%???}"
        return 1
    fi
}

# 停止服务
stop_service() {
    print_info "停止服务..."
    if $COMPOSE_CMD down; then
        print_success "服务已停止"
        return 0
    else
        print_error "停止服务失败"
        return 1
    fi
}

# 显示测试结果
show_test_results() {
    print_info "测试结果预览:"
    if [ -d "test_results" ]; then
        echo "测试结果目录结构:"
        find test_results/ -type f | head -10
        echo ""
        
        # 显示单个结果文件的内容预览
        if [ -f "test_results/docker_downloaded_result.json" ]; then
            echo "结果文件预览 (test_results/docker_downloaded_result.json):"
            head -20 "test_results/docker_downloaded_result.json"
        fi
    else
        print_warning "未找到测试结果目录"
    fi
}

# 清理临时文件
cleanup() {
    print_info "清理临时文件..."
    # 清理uploads目录中的测试文件
    if [ -d "../uploads" ]; then
        for file in "${TEST_FILES[@]}"; do
            local file_name=$(basename "$file")
            rm -f "../uploads/$file_name"
        done
    fi
    
    # 清理临时结果文件
    rm -f .test_result_docker
    
    print_success "临时文件清理完成"
}

# 主程序
main() {
    # 创建测试结果目录
    mkdir -p test_results
    
    # 检查依赖
    if ! check_docker; then
        exit 1
    fi
    
    echo ""
    
    if ! check_docker_service; then
        exit 1
    fi
    
    echo ""
    
    if ! check_docker_compose; then
        exit 1
    fi
    
    echo ""
    
    # 启动服务
    if ! start_service; then
        exit 1
    fi
    
    echo ""
    
    # 等待服务启动
    if ! wait_for_service; then
        stop_service
        exit 1
    fi
    
    echo ""
    
    # 检查测试文件
    if ! check_test_files; then
        stop_service
        exit 1
    fi
    
    echo ""
    
    # 运行测试
    print_info "开始运行测试..."
    
    # 测试单文档处理
    if test_single_document; then
        echo ""
        # 测试下载结果
        test_download_result
    fi
    
    echo ""
    
    # 测试批量文档处理
    test_batch_documents
    
    echo ""
    
    # 显示测试结果
    show_test_results
    
    echo ""
    
    # 清理临时文件
    cleanup
    
    echo ""
    
    # 停止服务
    if stop_service; then
        print_success "Docker容器化部署测试完成！"
        echo "测试结果已保存在 test/test_results/ 目录下"
    else
        print_error "Docker容器化部署测试完成，但服务停止失败！"
        echo "测试结果已保存在 test/test_results/ 目录下"
    fi
}

# 执行主程序
main "$@"