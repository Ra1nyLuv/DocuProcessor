#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档处理服务API使用示例脚本
提供简单的API调用示例，方便快速测试服务功能
"""

import requests
import json
import os
import sys
from urllib.parse import quote

# 服务配置
BASE_URL = "http://localhost:5000"
TEST_FILE = "test_sample.docx"  # 测试文件名

def check_service_health():
    """检查服务健康状态"""
    print("正在检查服务健康状态...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✓ 服务运行正常")
            return True
        else:
            print(f"✗ 服务异常: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ 无法连接到服务，请确保服务已启动")
        return False
    except Exception as e:
        print(f"✗ 检查服务时发生错误: {str(e)}")
        return False

def create_test_file():
    """创建测试文件（如果不存在）"""
    if not os.path.exists(TEST_FILE):
        print(f"创建测试文件: {TEST_FILE}")
        # 创建一个简单的测试文件内容
        with open(TEST_FILE, 'w', encoding='utf-8') as f:
            f.write("# 测试文档\n\n这是一个用于测试文档处理服务的示例文档。\n\n## 章节一\n\n测试内容...\n")
        print("✓ 测试文件创建完成")

def process_single_document():
    """处理单个文档示例"""
    print("\n=== 单文档处理示例 ===")
    
    # 检查测试文件是否存在
    if not os.path.exists(TEST_FILE):
        print(f"测试文件 {TEST_FILE} 不存在")
        return None
    
    try:
        with open(TEST_FILE, 'rb') as f:
            files = {'file': f}
            print(f"正在处理文件: {TEST_FILE}")
            response = requests.post(f"{BASE_URL}/api/v1/process-document", files=files)
        
        if response.status_code == 200:
            result = response.json()
            print("✓ 文档处理成功")
            print(f"  任务ID: {result['task_id']}")
            print(f"  结果文件: {result['result_file']}")
            print(f"  下载URL: {result['download_url']}")
            return result
        else:
            print(f"✗ 文档处理失败: {response.status_code}")
            print(f"  错误信息: {response.text}")
            return None
    except Exception as e:
        print(f"✗ 处理文档时发生错误: {str(e)}")
        return None

def download_result(task_id, filename):
    """下载处理结果示例"""
    print("\n=== 下载处理结果示例 ===")
    
    try:
        # URL编码文件名（处理中文字符）
        encoded_filename = quote(filename)
        download_url = f"{BASE_URL}/api/v1/download/{task_id}/{encoded_filename}"
        
        print(f"正在下载结果文件: {filename}")
        response = requests.get(download_url)
        
        if response.status_code == 200:
            # 保存结果文件
            result_filename = f"result_{filename}"
            with open(result_filename, 'wb') as f:
                f.write(response.content)
            print(f"✓ 结果文件已保存为: {result_filename}")
            return result_filename
        else:
            print(f"✗ 下载失败: {response.status_code}")
            print(f"  错误信息: {response.text}")
            return None
    except Exception as e:
        print(f"✗ 下载结果时发生错误: {str(e)}")
        return None

def show_result_content(filename):
    """显示结果文件内容"""
    print("\n=== 结果文件内容预览 ===")
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
            # 只显示前500个字符
            preview = content[:500] + "..." if len(content) > 500 else content
            print(preview)
            
            if len(content) > 500:
                print(f"\n... (文件内容已截断，完整内容请查看 {filename})")
    except Exception as e:
        print(f"✗ 读取结果文件时发生错误: {str(e)}")

def main():
    """主函数"""
    print("文档处理服务API使用示例")
    print("=" * 40)
    
    # 1. 检查服务健康状态
    if not check_service_health():
        print("\n请先启动文档处理服务再运行此示例。")
        print("启动命令:")
        print("  docker-compose up -d")
        print("或")
        print("  python app.py")
        return
    
    # 2. 创建测试文件
    create_test_file()
    
    # 3. 处理单个文档
    result = process_single_document()
    if not result:
        return
    
    # 4. 下载处理结果
    downloaded_file = download_result(result['task_id'], result['result_file'])
    if not downloaded_file:
        return
    
    # 5. 显示结果内容
    show_result_content(downloaded_file)
    
    print("\n" + "=" * 40)
    print("API使用示例完成！")
    print(f"处理结果已保存为: {downloaded_file}")

if __name__ == "__main__":
    main()