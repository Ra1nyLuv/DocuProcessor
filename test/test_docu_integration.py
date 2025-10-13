#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档处理服务集成测试脚本
使用File/temp/test_user下的实际文档进行测试
"""

import requests
import json
import os
import time
from pathlib import Path
from urllib.parse import quote

# 服务配置
BASE_URL = "http://localhost:5000"
# TEST_DATA_DIR = "../../File/temp/test_user/test_knowledge_base"  # 相对于test目录的路径
TEST_DATA_DIR = "/home/lynn/projects/filesfromWork/new_project/File/temp/test_user/test_knowledge_base"  # 测试用的路径

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

def get_test_files():
    """获取测试文件列表"""
    test_data_path = Path(TEST_DATA_DIR)
    if not test_data_path.exists():
        print(f"✗ 测试数据目录不存在: {TEST_DATA_DIR}")
        return []
    
    # 支持的文件类型
    supported_extensions = {'.txt', '.pdf', '.docx', '.doc', '.html', '.htm', '.pptx', '.xlsx'}
    
    test_files = []
    for file_path in test_data_path.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
            test_files.append(file_path)
    
    return test_files

def test_single_document(file_path):
    """测试单个文档处理"""
    print(f"\n=== 测试单文档处理: {file_path.name} ===")
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f)}
            print(f"正在处理文件: {file_path.name}")
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

def test_batch_documents(file_paths):
    """测试批量文档处理"""
    print(f"\n=== 测试批量文档处理 ({len(file_paths)}个文件) ===")
    
    try:
        # 准备文件列表
        files = []
        for file_path in file_paths:
            files.append(('files', (file_path.name, open(file_path, 'rb'))))
        
        print(f"正在批量处理 {len(file_paths)} 个文件...")
        response = requests.post(f"{BASE_URL}/api/v1/batch-process", files=files)
        
        # 关闭所有文件
        for _, (_, file_obj) in files:
            file_obj.close()
        
        if response.status_code == 200:
            result = response.json()
            print("✓ 批量文档处理成功")
            print(f"  批量任务ID: {result['task_id']}")
            print(f"  结果文件数量: {len(result['result_files'])}")
            for i, (result_file, download_url) in enumerate(zip(result['result_files'], result['download_urls'])):
                print(f"  文件{i+1}: {result_file}")
            return result
        else:
            print(f"✗ 批量文档处理失败: {response.status_code}")
            print(f"  错误信息: {response.text}")
            # 确保文件被关闭
            for _, (_, file_obj) in files:
                file_obj.close()
            return None
    except Exception as e:
        print(f"✗ 批量处理文档时发生错误: {str(e)}")
        # 确保文件被关闭
        for _, (_, file_obj) in files:
            try:
                file_obj.close()
            except:
                pass
        return None

def download_result(task_id, filename, save_path):
    """下载处理结果"""
    print(f"\n=== 下载处理结果: {filename} ===")
    
    try:
        # URL编码文件名（处理路径分隔符和中文字符）
        encoded_filename = quote(filename, safe='')
        download_url = f"{BASE_URL}/api/v1/download/{task_id}/{encoded_filename}"
        
        print(f"正在下载结果文件: {filename}")
        print(f"下载URL: {download_url}")
        response = requests.get(download_url)
        
        if response.status_code == 200:
            # 确保保存目录存在
            save_path = Path(save_path)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(save_path, 'wb') as f:
                f.write(response.content)
            print(f"✓ 结果文件已保存为: {save_path}")
            return str(save_path)
        else:
            print(f"✗ 下载失败: {response.status_code}")
            print(f"  错误信息: {response.text}")
            return None
    except Exception as e:
        print(f"✗ 下载结果时发生错误: {str(e)}")
        return None

def show_result_preview(filename):
    """显示结果文件内容预览"""
    print(f"\n=== 结果文件内容预览: {filename} ===")
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
            # 只显示前1000个字符
            preview = content[:1000] + "..." if len(content) > 1000 else content
            print(preview)
            
            if len(content) > 1000:
                print(f"\n... (文件内容已截断，完整内容请查看 {filename})")
                
        # 显示文件大小
        file_size = os.path.getsize(filename)
        print(f"\n文件大小: {file_size} 字节")
    except Exception as e:
        print(f"✗ 读取结果文件时发生错误: {str(e)}")

def main():
    """主函数"""
    print("文档处理服务集成测试")
    print("=" * 50)
    
    # 1. 检查服务健康状态
    if not check_service_health():
        print("\n请先启动文档处理服务再运行此测试。")
        print("启动命令:")
        print("  cd .. && docker-compose up -d")
        return
    
    # 2. 获取测试文件
    test_files = get_test_files()
    if not test_files:
        print("✗ 未找到可用的测试文件")
        return
    
    print(f"\n找到 {len(test_files)} 个测试文件:")
    for i, file_path in enumerate(test_files):
        print(f"  {i+1}. {file_path.name} ({file_path.stat().st_size} bytes)")
    
    # 3. 测试单个文档处理
    single_result = test_single_document(test_files[0])
    
    if single_result:
        # 4. 下载单个文档处理结果
        download_path = f"test_results/integration_single_{test_files[0].stem}_result.json"
        downloaded_file = download_result(
            single_result['task_id'], 
            single_result['result_file'], 
            download_path
        )
        
        if downloaded_file:
            # 5. 显示结果预览
            show_result_preview(downloaded_file)
    
    # 6. 测试批量文档处理
    batch_result = test_batch_documents(test_files)
    
    if batch_result:
        # 7. 下载批量处理结果
        print(f"\n=== 下载批量处理结果 ===")
        batch_dir = Path("test_results/integration_batch_results")
        batch_dir.mkdir(parents=True, exist_ok=True)
        
        for i, (result_file, download_url) in enumerate(
            zip(batch_result['result_files'], batch_result['download_urls'])
        ):
            download_path = batch_dir / f"integration_batch_result_{i+1}.json"
            download_result(
                batch_result['task_id'],
                result_file,
                download_path
            )
    
    print("\n" + "=" * 50)
    print("文档处理服务集成测试完成！")
    print("测试结果已保存在 test/test_results/ 目录下")

if __name__ == "__main__":
    main()