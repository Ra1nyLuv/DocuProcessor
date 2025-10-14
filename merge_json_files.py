#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Merge JSON files from converted_data and sliced_data directories.

This script merges the pic_index.json files from converted_data with the 
chunk_index.json files from sliced_data to create a unified JSON structure
that contains both text chunks and images in document order.
"""

import os
import json
import base64
import argparse
import re
from pathlib import Path


def find_config_file(config_file: str, script_dir: str) -> str:
    """
    动态查找配置文件路径
    
    Args:
        config_file: 配置文件名
        script_dir: 脚本所在目录
        
    Returns:
        配置文件的完整路径
    """
    # 检查几种可能的路径
    possible_paths = [
        os.path.join(script_dir, config_file),  # 当前目录
        os.path.join(script_dir, '..', config_file),  # 上级目录
        os.path.join(script_dir, '..', '..', config_file),  # 上上级目录
        config_file  # 绝对路径或相对于当前工作目录的路径
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return config_file  # 返回原始路径，让系统决定


def load_merge_config(config_file: str = "merge_config.json") -> dict:
    """
    从配置文件加载合并参数
    
    Args:
        config_file: 配置文件路径
        
    Returns:
        包含合并参数的字典
    """
    # 获取当前脚本的目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 动态查找配置文件
    config_path = find_config_file(config_file, script_dir)
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config
        except Exception as e:
            print(f"读取配置文件时出错: {str(e)}，使用默认参数")
    
    # 默认参数
    return {
        "default_input_converted_path": "converted_data",
        "default_input_sliced_path": "sliced_data",
        "default_output_path": "merged_data",
        "enable_base64_processing": True,
        "save_merged_index": False,
        "merged_index_filename": "merged_index.json"
    }


def load_json_file(file_path):
    """Load JSON file and return its content."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None


def save_json_file(data, file_path):
    """Save data to JSON file."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error saving {file_path}: {e}")
        return False


def load_image_as_base64(image_path):
    """Load image file and return its base64 encoding."""
    try:
        with open(image_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    except Exception as e:
        print(f"Error loading image {image_path}: {e}")
        return None


def extract_base64_from_text(text):
    """Extract base64 data from markdown image syntax in text."""
    pattern = r'!\[.*?\]\(data:image/.*?;base64,([^)]+)\)'
    matches = re.findall(pattern, text)
    return matches


def process_text_with_base64_images(items):
    """
    Process items to handle text entries with base64 image placeholders.
    Convert text entries with base64 placeholders to image entries.
    """
    processed_items = []
    id_counter = 1
    
    for item in items:
        if item['type'] == 'text' and item.get('content'):
            # Check if text contains base64 image placeholders
            base64_matches = extract_base64_from_text(item['content'])
            
            if base64_matches:
                # Split text by base64 placeholders
                parts = re.split(r'!\[.*?\]\(data:image/.*?;base64,[^)]+\)', item['content'])
                
                # Process each part and insert images where placeholders were
                for i, part in enumerate(parts):
                    # Add text part if it's not empty
                    if part.strip():
                        text_item = {
                            'id': id_counter,
                            'type': 'text',
                            'title': item.get('title', ''),
                            'content': part.strip(),
                            'length': len(part.strip())
                        }
                        processed_items.append(text_item)
                        id_counter += 1
                    
                    # Add image item if there's a corresponding base64 match
                    if i < len(base64_matches):
                        image_item = {
                            'id': id_counter,
                            'type': 'image',
                            'base64': base64_matches[i],
                            'original_name': f"embedded_image_{id_counter}.png",
                            'path': f"embedded_images/embedded_image_{id_counter}.png",
                            'size': len(base64_matches[i])
                        }
                        processed_items.append(image_item)
                        id_counter += 1
            else:
                # No base64 placeholders, keep the item as is
                item['id'] = id_counter
                processed_items.append(item)
                id_counter += 1
        else:
            # Not a text item or no content, keep as is
            item['id'] = id_counter
            processed_items.append(item)
            id_counter += 1
    
    return processed_items


def find_document_files(converted_dir, sliced_dir):
    """
    Find all document-related files in the new directory structure.
    
    Args:
        converted_dir (str): Path to converted_data directory
        sliced_dir (str): Path to sliced_data directory
        
    Returns:
        dict: Dictionary mapping document names to their file paths
    """
    document_files = {}
    
    # 遍历sliced_data目录中的所有子目录，因为这是处理流程的最后一步
    # 即使没有图片，也应该处理这些文档
    for root, dirs, files in os.walk(sliced_dir):
        for dir_name in dirs:
            # 检查是否存在chunk_index.json文件
            chunk_index_path = os.path.join(root, dir_name, 'chunk_index.json')
            if os.path.exists(chunk_index_path):
                doc_name = dir_name
                if doc_name not in document_files:
                    document_files[doc_name] = {}
                document_files[doc_name]['chunk_index'] = chunk_index_path
                
                # 检查是否存在images_index.json文件
                images_index_path = os.path.join(converted_dir, doc_name, 'images_index.json')
                if os.path.exists(images_index_path):
                    document_files[doc_name]['images_index'] = images_index_path
    
    return document_files


def merge_document_data(converted_dir, sliced_dir, output_dir, enable_base64_processing=True, save_merged_index=False):
    """
    Merge converted_data and sliced_data JSON files for all documents.
    
    Args:
        converted_dir (str): Path to converted_data directory
        sliced_dir (str): Path to sliced_data directory
        output_dir (str): Path to output directory
        enable_base64_processing (bool): Whether to process base64 image placeholders
        save_merged_index (bool): Whether to save the merged index file
    """
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Find all document files in the new directory structure
    document_files = find_document_files(converted_dir, sliced_dir)
    
    print(f"Found {len(document_files)} documents to process")
    
    # 用于保存所有合并文件的索引
    merged_index = {}
    
    for doc_name, files in document_files.items():
        print(f"Processing: {doc_name}")
        
        # Load images_index.json (contains base64 data) if it exists
        image_index_data = {}
        if 'images_index' in files:
            image_index_data = load_json_file(files['images_index']) or {}
            
        # Load chunk_index.json
        chunk_index_path = files['chunk_index']
        chunk_index_data = load_json_file(chunk_index_path)
        if chunk_index_data is None:
            print(f"  Warning: chunk_index.json not found for {doc_name}")
            continue
            
        # Create a mapping from image_id to base64 data
        image_id_to_base64 = {}
        for image_filename, image_info in image_index_data.items():
            image_id = image_info.get('image_id')
            base64_data = image_info.get('base64')
            if image_id is not None and base64_data is not None:
                image_id_to_base64[image_id] = base64_data
                
        # Process chunk_index_data to add base64 data where image_id matches
        merged_data = []
        for chunk in chunk_index_data:
            # Copy the original chunk data
            new_chunk = chunk.copy()
            
            # If this chunk has an image_id, check if we have base64 data for it
            if 'image_id' in chunk:
                image_id = chunk['image_id']
                if image_id in image_id_to_base64:
                    # Add the base64 data to this chunk
                    new_chunk['base64'] = image_id_to_base64[image_id]
                    
            merged_data.append(new_chunk)
            
        # 修改保存逻辑：为每个文档创建单独的文件夹，并在其中保存result.json
        # 创建文档对应的文件夹
        doc_output_dir = os.path.join(output_dir, doc_name)
        Path(doc_output_dir).mkdir(parents=True, exist_ok=True)
        
        # 在文档文件夹中保存result.json
        output_file = os.path.join(doc_output_dir, "result.json")
        if save_json_file(merged_data, output_file):
            print(f"  Saved: {output_file}")
            # 添加到合并索引
            if save_merged_index:
                merged_index[doc_name] = {
                    "file": f"{doc_name}/result.json",
                    "items_count": len(merged_data)
                }
        else:
            print(f"  Failed to save: {output_file}")
    
    # 保存合并索引文件
    if save_merged_index and merged_index:
        index_file = os.path.join(output_dir, "merged_index.json")
        if save_json_file(merged_index, index_file):
            print(f"  Saved merged index: {index_file}")


def main():
    """Main function."""
    print("🙌 JSON文件合并工具")
    print("=" * 40)
    
    # 获取当前脚本的目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 尝试从配置文件加载参数
    config = load_merge_config()
    print(f"⚙️  已加载配置参数")
    
    # 从配置文件获取默认输入输出路径
    default_converted_path = config.get("default_input_converted_path", "converted_data")
    default_sliced_path = config.get("default_input_sliced_path", "sliced_data")
    default_output_path = config.get("default_output_path", "merged_data")
    default_enable_base64_processing = config.get("enable_base64_processing", True)
    default_save_merged_index = config.get("save_merged_index", False)
    default_merged_index_filename = config.get("merged_index_filename", "merged_index.json")
    
    parser = argparse.ArgumentParser(description='Merge converted_data and sliced_data JSON files')
    parser.add_argument('--converted-dir', default=default_converted_path,
                        help=f'Path to converted_data directory (default: {default_converted_path})')
    parser.add_argument('--sliced-dir', default=default_sliced_path,
                        help=f'Path to sliced_data directory (default: {default_sliced_path})')
    parser.add_argument('--output-dir', default=default_output_path,
                        help=f'Path to output directory (default: {default_output_path})')
    parser.add_argument('--enable-base64-processing', action='store_true', 
                        default=default_enable_base64_processing,
                        help=f'Enable base64 image processing (default: {default_enable_base64_processing})')
    parser.add_argument('--disable-base64-processing', action='store_false', 
                        dest='enable_base64_processing',
                        help='Disable base64 image processing')
    parser.add_argument('--save-merged-index', action='store_true',
                        default=None,
                        help='Save merged index file')
    parser.add_argument('--no-save-merged-index', action='store_false',
                        dest='save_merged_index',
                        help='Do not save merged index file')
    parser.add_argument('--config', help='Configuration file path')
    
    args = parser.parse_args()
    
    # 处理save_merged_index参数
    if args.save_merged_index is not None:
        # 如果命令行参数指定了save_merged_index，则使用命令行参数
        save_merged_index = args.save_merged_index
    else:
        # 否则从配置文件获取参数
        if args.config:
            print(f"📄 使用指定配置文件: {args.config}")
            config = load_merge_config(args.config)
            # 如果命令行参数没有指定，则使用配置文件中的参数
            if args.converted_dir == default_converted_path:  # 默认值
                args.converted_dir = config.get("default_input_converted_path", "converted_data")
            if args.sliced_dir == default_sliced_path:  # 默认值
                args.sliced_dir = config.get("default_input_sliced_path", "sliced_data")
            if args.output_dir == default_output_path:  # 默认值
                args.output_dir = config.get("default_output_path", "merged_data")
            if args.enable_base64_processing == default_enable_base64_processing:  # 默认值
                args.enable_base64_processing = config.get("enable_base64_processing", True)
            # 从配置文件获取save_merged_index参数
            save_merged_index = config.get("save_merged_index", False)
        else:
            # 如果没有指定配置文件，则直接从主配置获取参数
            save_merged_index = config.get("save_merged_index", False)
    
    # 显示当前使用的参数
    print(f"📊 当前参数设置:")
    print(f"   转换数据目录: {args.converted_dir}")
    print(f"   切片数据目录: {args.sliced_dir}")
    print(f"   输出目录: {args.output_dir}")
    print(f"   Base64处理: {'启用' if args.enable_base64_processing else '禁用'}")
    print(f"   保存合并索引: {'启用' if save_merged_index else '禁用'}")
    
    # Check if directories exist
    if not os.path.exists(args.converted_dir):
        print(f"Error: Converted data directory '{args.converted_dir}' does not exist")
        return
        
    if not os.path.exists(args.sliced_dir):
        print(f"Error: Sliced data directory '{args.sliced_dir}' does not exist")
        return
    
    print("Starting merge process...")
    merge_document_data(args.converted_dir, args.sliced_dir, args.output_dir, args.enable_base64_processing, save_merged_index)
    print("Merge process completed.")


if __name__ == '__main__':
    main()