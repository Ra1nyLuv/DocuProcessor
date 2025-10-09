#!/bin/bash

# 使用实际数据测试API服务的bash脚本

echo "========================================="
echo "文档处理服务实际数据测试"
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

# 显示可用的测试文件
show_sample_files() {
    print_info "可用的测试文件:"
    if [ -d "../raw_data" ]; then
        ls -lh ../raw_data/ | head -10
    else
        print_error "未找到raw_data目录"
        return 1
    fi
}

# 运行Python测试脚本
run_python_test() {
    print_info "运行Python测试脚本..."
    if python test_real_data_api.py; then
        print_success "Python测试脚本执行完成"
    else
        print_error "Python测试脚本执行失败"
        return 1
    fi
}

# 显示测试结果
show_test_results() {
    print_info "测试结果预览:"
    if [ -d "test_results" ]; then
        echo "测试结果目录结构:"
        find test_results/ -type f | head -20
        echo ""
        
        # 显示单个结果文件的内容预览
        result_file=$(find test_results/ -name "*.json" | head -1)
        if [ -n "$result_file" ]; then
            echo "结果文件预览 ($result_file):"
            head -20 "$result_file"
        fi
    else
        print_warning "未找到测试结果目录"
    fi
}



# 主程序
main() {
    # 检查服务
    if ! check_service; then
        print_error "请先启动文档处理服务"
        echo "启动命令:"
        echo "  cd .. && python app.py"
        exit 1
    fi
    
    # 显示可用的测试文件
    show_sample_files
    
    echo ""
    read -p "是否继续运行测试? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "测试已取消"
        exit 0
    fi
    
    # 运行Python测试
    run_python_test
    
    # 显示测试结果
    show_test_results
    
    # 创建目录结构示例
    create_directory_structure_example
    
    print_success "实际数据测试完成！"
    echo "详细结果请查看 test/test_results/ 目录"
}

# 执行主程序
main