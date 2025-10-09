#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API压力测试脚本
用于测试文档处理服务在高并发情况下的稳定性和健壮性
"""

import os
import sys
import json
import time
import requests
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 服务配置
BASE_URL = "http://localhost:5000"
TEST_FILES_DIR = project_root / "raw_data"
CONCURRENT_REQUESTS = 5  # 并发请求数
TOTAL_REQUESTS = 10  # 总请求数

# 测试结果统计
test_results = {
    'total': 0,
    'success': 0,
    'failed': 0,
    'errors': []
}

def test_single_document_processing_stress(file_path):
    """压力测试单文档处理接口"""
    global test_results
    
    test_results['total'] += 1
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f, 'application/octet-stream')}
            response = requests.post(f"{BASE_URL}/api/v1/process-document", files=files)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'completed':
                test_results['success'] += 1
                print(f"✓ 请求成功: {data['task_id']}")
                return True
            else:
                test_results['failed'] += 1
                error_msg = f"处理失败: {data}"
                test_results['errors'].append(error_msg)
                print(f"✗ {error_msg}")
                return False
        else:
            test_results['failed'] += 1
            error_msg = f"HTTP {response.status_code}: {response.text}"
            test_results['errors'].append(error_msg)
            print(f"✗ {error_msg}")
            return False
    except Exception as e:
        test_results['failed'] += 1
        error_msg = f"异常: {str(e)}"
        test_results['errors'].append(error_msg)
        print(f"✗ {error_msg}")
        return False

def run_stress_test():
    """运行压力测试"""
    print("开始API压力测试...")
    print(f"测试目标: {BASE_URL}")
    print(f"并发请求数: {CONCURRENT_REQUESTS}")
    print(f"总请求数: {TOTAL_REQUESTS}")
    
    # 查找测试文件
    test_files = list(TEST_FILES_DIR.glob("*.docx")) + list(TEST_FILES_DIR.glob("*.pdf"))
    if not test_files:
        print("✗ 未找到测试文件")
        return False
    
    # 使用第一个文件进行所有测试
    test_file = test_files[0]
    print(f"使用测试文件: {test_file.name}")
    
    # 创建任务列表
    tasks = [test_file] * TOTAL_REQUESTS
    
    # 使用线程池执行并发请求
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=CONCURRENT_REQUESTS) as executor:
        # 提交所有任务
        future_to_task = {
            executor.submit(test_single_document_processing_stress, task): i 
            for i, task in enumerate(tasks)
        }
        
        # 等待所有任务完成
        for future in as_completed(future_to_task):
            try:
                future.result()
            except Exception as e:
                print(f"任务执行异常: {str(e)}")
    
    end_time = time.time()
    
    # 输出测试结果
    print(f"\n=== 压力测试结果 ===")
    print(f"总请求数: {test_results['total']}")
    print(f"成功请求数: {test_results['success']}")
    print(f"失败请求数: {test_results['failed']}")
    print(f"成功率: {test_results['success']/test_results['total']*100:.1f}%")
    print(f"总耗时: {end_time - start_time:.2f}秒")
    print(f"平均响应时间: {(end_time - start_time)/test_results['total']:.2f}秒")
    
    # 输出错误信息
    if test_results['errors']:
        print(f"\n错误详情:")
        for i, error in enumerate(test_results['errors'][:5]):  # 只显示前5个错误
            print(f"{i+1}. {error}")
        if len(test_results['errors']) > 5:
            print(f"... 还有{len(test_results['errors'])-5}个错误")
    
    if test_results['success'] == test_results['total']:
        print("\n🎉 所有压力测试通过！API服务在高并发下稳定健壮。")
        return True
    else:
        print("\n⚠ 部分压力测试未通过，请检查上述错误信息。")
        return False

if __name__ == "__main__":
    success = run_stress_test()
    sys.exit(0 if success else 1)