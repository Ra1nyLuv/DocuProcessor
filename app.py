#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档处理服务API
提供文档转换、分块和合并的一站式服务
"""

import os
import sys
import json
import uuid
import shutil
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from flask import Flask, request, jsonify, send_file, abort
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入处理模块
from convert_doc_to_md import convert_file_to_md
from text_chunker import process_all_documents
from merge_json_files import merge_document_data

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask应用配置
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 限制上传文件大小为50MB

# 服务配置
BASE_DIR = Path(__file__).parent
UPLOAD_FOLDER = BASE_DIR / "uploads"
PROCESSED_FOLDER = BASE_DIR / "processed"
TEMP_FOLDER = BASE_DIR / "temp"

# 确保目录存在
for folder in [UPLOAD_FOLDER, PROCESSED_FOLDER, TEMP_FOLDER]:
    folder.mkdir(exist_ok=True)

# 支持的文件类型
ALLOWED_EXTENSIONS = {
    'txt', 'pdf', 'docx', 'doc', 'html', 'htm', 'pptx', 'xlsx'
}

def allowed_file(filename: str) -> bool:
    """检查文件扩展名是否被允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_task_id() -> str:
    """生成唯一任务ID"""
    return str(uuid.uuid4())

def cleanup_temp_files(task_id: str):
    """清理临时文件"""
    task_temp_dir = TEMP_FOLDER / task_id
    if task_temp_dir.exists():
        shutil.rmtree(task_temp_dir)

def secure_filename_chinese(filename: str) -> str:
    """
    处理中文文件名的secure_filename函数
    """
    # 只保留文件名中的基本字符，但允许中文字符
    import re
    # 移除路径部分
    filename = os.path.basename(filename)
    # 保留中文、英文字母、数字、点号、下划线和连字符
    filename = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9._-]', '_', filename)
    # 确保文件名不以点号开头
    if filename.startswith('.'):
        filename = '_' + filename
    return filename or 'unnamed_file'

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/v1/process-document', methods=['POST'])
def process_document():
    """处理单个文档的主接口"""
    task_id = generate_task_id()
    logger.info(f"开始处理任务: {task_id}")
    
    try:
        # 检查是否有文件上传
        if 'file' not in request.files:
            return jsonify({"error": "没有上传文件"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "文件名为空"}), 400
        
        if not allowed_file(file.filename):
            return jsonify({"error": "不支持的文件类型"}), 400
        
        # 保存上传的文件（使用改进的文件名处理）
        filename = secure_filename_chinese(file.filename)
        task_temp_dir = TEMP_FOLDER / task_id
        task_temp_dir.mkdir(exist_ok=True)
        
        input_dir = task_temp_dir / "input"
        input_dir.mkdir(exist_ok=True)
        
        file_path = input_dir / filename
        file.save(file_path)
        logger.info(f"文件已保存: {file_path}")
        
        # 创建处理目录结构
        converted_dir = task_temp_dir / "converted_data"
        sliced_dir = task_temp_dir / "sliced_data"
        merged_dir = task_temp_dir / "merged_data"
        
        for directory in [converted_dir, sliced_dir, merged_dir]:
            directory.mkdir(exist_ok=True)
        
        # 步骤1: 文档转换
        logger.info(f"任务 {task_id}: 开始文档转换")
        if not convert_file_to_md(str(file_path), str(converted_dir)):
            raise Exception("文档转换失败")
        
        # 步骤2: 文本分块
        logger.info(f"任务 {task_id}: 开始文本分块")
        process_all_documents(str(converted_dir), str(sliced_dir))
        
        # 步骤3: 数据合并
        logger.info(f"任务 {task_id}: 开始数据合并")
        merge_document_data(str(converted_dir), str(sliced_dir), str(merged_dir))
        
        # 查找生成的合并文件（现在在各自的文件夹中）
        # 查找merged_dir下所有子目录中的result.json文件
        merged_files = []
        for subdir in merged_dir.iterdir():
            if subdir.is_dir():
                result_file = subdir / "result.json"
                if result_file.exists():
                    merged_files.append((subdir.name, result_file))
        
        if not merged_files:
            raise Exception("未找到合并后的文件")
        
        # 将结果移动到处理目录
        result_dir = PROCESSED_FOLDER / task_id
        result_dir.mkdir(exist_ok=True)
        
        # 为每个文档创建对应的文件夹并复制result.json
        result_filenames = []
        for doc_name, result_file_path in merged_files:
            doc_result_dir = result_dir / doc_name
            doc_result_dir.mkdir(exist_ok=True)
            shutil.copy(result_file_path, doc_result_dir / "result.json")
            result_filenames.append(f"{doc_name}/result.json")
        
        # 清理临时文件
        cleanup_temp_files(task_id)
        
        # 返回结果（只返回第一个文档的结果，保持接口兼容性）
        result_filename = result_filenames[0] if result_filenames else "result.json"
        # URL编码文件路径
        from urllib.parse import quote
        encoded_filename = quote(result_filename, safe='')
        return jsonify({
            "task_id": task_id,
            "status": "completed",
            "result_file": result_filename,
            "download_url": f"/api/v1/download/{task_id}/{encoded_filename}"
        })
        
    except Exception as e:
        logger.error(f"任务 {task_id} 处理失败: {str(e)}")
        cleanup_temp_files(task_id)
        return jsonify({"error": f"处理失败: {str(e)}"}), 500

@app.route('/api/v1/batch-process', methods=['POST'])
def batch_process():
    """批量处理文档接口"""
    task_id = generate_task_id()
    logger.info(f"开始批量处理任务: {task_id}")
    
    try:
        # 检查是否有文件上传
        if 'files' not in request.files:
            return jsonify({"error": "没有上传文件"}), 400
        
        files = request.files.getlist('files')
        if not files or all(f.filename == '' for f in files):
            return jsonify({"error": "文件列表为空"}), 400
        
        # 保存上传的文件
        task_temp_dir = TEMP_FOLDER / task_id
        task_temp_dir.mkdir(exist_ok=True)
        
        input_dir = task_temp_dir / "input"
        input_dir.mkdir(exist_ok=True)
        
        saved_files = []
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename_chinese(file.filename)
                file_path = input_dir / filename
                file.save(file_path)
                saved_files.append(filename)
                logger.info(f"文件已保存: {file_path}")
        
        if not saved_files:
            return jsonify({"error": "没有有效的文件被上传"}), 400
        
        # 创建处理目录结构
        converted_dir = task_temp_dir / "converted_data"
        sliced_dir = task_temp_dir / "sliced_data"
        merged_dir = task_temp_dir / "merged_data"
        
        for directory in [converted_dir, sliced_dir, merged_dir]:
            directory.mkdir(exist_ok=True)
        
        # 步骤1: 文档转换
        logger.info(f"任务 {task_id}: 开始批量文档转换")
        for filename in saved_files:
            file_path = input_dir / filename
            if not convert_file_to_md(str(file_path), str(converted_dir)):
                logger.warning(f"文件 {filename} 转换失败")
        
        # 步骤2: 文本分块
        logger.info(f"任务 {task_id}: 开始批量文本分块")
        process_all_documents(str(converted_dir), str(sliced_dir))
        
        # 步骤3: 数据合并
        logger.info(f"任务 {task_id}: 开始批量数据合并")
        merge_document_data(str(converted_dir), str(sliced_dir), str(merged_dir))
        
        # 将结果移动到处理目录
        result_dir = PROCESSED_FOLDER / task_id
        result_dir.mkdir(exist_ok=True)
        
        # 查找merged_dir下所有子目录中的result.json文件
        merged_files = []
        for subdir in merged_dir.iterdir():
            if subdir.is_dir():
                result_file = subdir / "result.json"
                if result_file.exists():
                    merged_files.append((subdir.name, result_file))
        
        if not merged_files:
            raise Exception("未找到合并后的文件")
        
        # 为每个文档创建对应的文件夹并复制result.json
        result_files = []
        for doc_name, result_file_path in merged_files:
            doc_result_dir = result_dir / doc_name
            doc_result_dir.mkdir(exist_ok=True)
            shutil.copy(result_file_path, doc_result_dir / "result.json")
            result_files.append(f"{doc_name}/result.json")
        
        # 清理临时文件
        cleanup_temp_files(task_id)
        
        # 返回结果
        # URL编码所有文件路径
        from urllib.parse import quote
        download_urls = [f"/api/v1/download/{task_id}/{quote(filename, safe='')}" for filename in result_files]
        return jsonify({
            "task_id": task_id,
            "status": "completed",
            "result_files": result_files,
            "download_urls": download_urls
        })
        
    except Exception as e:
        logger.error(f"批量任务 {task_id} 处理失败: {str(e)}")
        cleanup_temp_files(task_id)
        return jsonify({"error": f"批量处理失败: {str(e)}"}), 500

@app.route('/api/v1/download/<task_id>/<path:filename>', methods=['GET'])
def download_result(task_id: str, filename: str):
    """下载处理结果文件"""
    try:
        # URL解码文件名（处理中文字符）
        from urllib.parse import unquote
        decoded_filename = unquote(filename)
        
        # 处理新的目录结构（filename可能包含路径分隔符）
        result_path = PROCESSED_FOLDER / task_id / decoded_filename
        if not result_path.exists():
            # 如果直接路径不存在，尝试处理可能的URL编码问题
            # 将%2F转换回/
            decoded_filename = decoded_filename.replace('%2F', '/')
            result_path = PROCESSED_FOLDER / task_id / decoded_filename
            if not result_path.exists():
                logger.error(f"文件未找到: {result_path}")
                abort(404)
        
        # 提取实际的文件名用于下载
        actual_filename = os.path.basename(decoded_filename)
        if not actual_filename:
            actual_filename = "result.json"
        
        logger.info(f"下载文件: {result_path}")
        return send_file(
            result_path,
            as_attachment=True,
            download_name=actual_filename
        )
    except Exception as e:
        logger.error(f"下载文件失败: {str(e)}")
        abort(500)

@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(e):
    return jsonify({"error": "文件大小超过限制（最大50MB）"}), 413

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "资源未找到"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "服务器内部错误"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)