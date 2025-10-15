"""
使用 markitdown 将多种格式的文件转换为 .md 文件
支持格式包括: .docx, .pdf, .txt, .html, .pptx, .xlsx 等
"""

import os
import sys
import json
import argparse
import base64
import re
from typing import Dict, List, Tuple
from zipfile import ZipFile
import xml.etree.ElementTree as ET

# 尝试导入PDF处理库
try:
    import fitz  # PyMuPDF
    PDF_SUPPORTED = True
except ImportError:
    PDF_SUPPORTED = False

# 直接导入markitdown包（已通过pip安装）
try:
    from markitdown import MarkItDown
    MARKITDOWN_AVAILABLE = True
except ImportError as e:
    print(f"警告: 无法导入 markitdown 包: {e}")
    MarkItDown = None
    MARKITDOWN_AVAILABLE = False

# 获取当前脚本的目录
script_dir = os.path.dirname(os.path.abspath(__file__))

# 动态查找配置文件路径
def find_config_file(config_file: str) -> str:
    """动态查找配置文件路径"""
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

# 从配置文件加载参数
def load_conversion_config(config_file: str = "conversion_config.json") -> dict:
    """从配置文件加载转换参数"""
    # 动态查找配置文件
    config_path = find_config_file(config_file)
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config
        except Exception as e:
            print(f"读取配置文件时出错: {str(e)}，使用默认参数")
    
    # 默认参数
    return {
        "default_input_path": "raw_data",
        "default_output_path": "converted_data"
    }

def is_supported_file(filepath: str) -> bool:
    """检查文件是否为支持的格式"""
    # 添加.md到支持的格式列表中
    supported_extensions = ['.docx', '.pdf', '.txt', '.html', '.htm', '.pptx', '.xlsx', '.md']
    return any(filepath.lower().endswith(ext) for ext in supported_extensions)

def get_file_extension(filepath: str) -> str:
    """获取文件扩展名"""
    return os.path.splitext(filepath)[1].lower()

def convert_file_to_md(input_path, output_dir="converted_data"):
    """
    将支持的文件格式转换为同名的 .md 文件
    修改文件生成路径结构为: converted_data/<文件名>/<文件名>.md 和 converted_data/<文件名>/images_index.json
    对于.md文件，直接复制到目标位置而不进行转换
    
    Args:
        input_path (str): 输入文件路径
        output_dir (str): 输出目录路径
    """
    if not MARKITDOWN_AVAILABLE or MarkItDown is None:
        print("错误: markitdown 包不可用，请检查依赖安装")
        return False
    
    # 检查文件是否存在
    if not os.path.exists(input_path):
        print(f"错误: 文件 {input_path} 不存在")
        return False
    
    # 检查文件格式是否支持
    if not is_supported_file(input_path):
        print(f"错误: 文件 {input_path} 格式不支持")
        print("支持的格式包括: .docx, .pdf, .txt, .html, .htm, .pptx, .xlsx, .md")
        return False
    
    # 获取文件名（不含扩展名）
    filename = os.path.basename(input_path)
    base_filename = os.path.splitext(filename)[0]
    
    # 创建特定于该文件的输出目录: converted_data/<文件名>/
    file_output_dir = os.path.join(script_dir, output_dir, base_filename)
    os.makedirs(file_output_dir, exist_ok=True)
    
    # 生成输出文件路径: converted_data/<文件名>/<文件名>.md
    md_filename = base_filename + '.md'
    md_path = os.path.join(file_output_dir, md_filename)
    
    # 检查是否为.md文件，如果是则直接复制，否则进行转换
    if input_path.lower().endswith('.md'):
        print(f"检测到.md文件，直接复制到目标位置: {md_path}")
        try:
            # 直接复制.md文件
            import shutil
            shutil.copy2(input_path, md_path)
            print(f"成功将 {input_path} 复制到 {md_path}")
            
            # 对于.md文件，我们不处理图片索引，直接返回成功
            print("  未检测到图片")
            return True
        except Exception as e:
            print(f"复制.md文件过程中出现错误: {str(e)}")
            return False
    else:
        try:
            # 创建 MarkItDown 实例
            md = MarkItDown()
            
            # 转换文件
            result = md.convert(input_path)
            
            # 将结果写入 .md 文件
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(result.text_content)
            
            # 处理图片索引
            image_index = {}
            # 首先尝试从result.images获取图片信息
            if hasattr(result, 'images') and result.images:
                print(f"  从result.images检测到 {len(result.images)} 张图片")
                for i, image in enumerate(result.images):
                    # 生成图片文件名
                    image_filename = f"{base_filename}_image_{i+1:03d}.png"
                    
                    # 生成base64编码
                    image_base64 = base64.b64encode(image.data).decode('utf-8')
                    
                    # 记录图片索引信息（只保存base64编码，不保存原始图片文件）
                    image_index[image_filename] = {
                        "image_id": i+1,
                        "base64": image_base64,
                        "size": len(image.data)
                    }
            else:
                print("  未从result.images检测到图片，尝试从Markdown内容中提取")
                # 如果没有从result.images获取到图片信息，则从Markdown内容中提取base64图片
                image_index, _ = extract_images_from_markdown(result.text_content, base_filename)
                
                # 如果仍然没有提取到图片，尝试直接从docx或pdf文件中提取
                if not image_index:
                    if input_path.lower().endswith('.docx'):
                        print("  未从Markdown内容中检测到图片，尝试直接从docx文件中提取")
                        image_index, _ = extract_images_from_docx(input_path, base_filename)
                    elif input_path.lower().endswith('.pdf') and PDF_SUPPORTED:
                        print("  未从Markdown内容中检测到图片，尝试直接从pdf文件中提取")
                        image_index, _ = extract_images_from_pdf(input_path, base_filename)
            
            # 保存图片索引文件为 images_index.json（而不是原来的 <文件名>_image_index.json）
            if image_index:
                # 生成图片索引文件路径: converted_data/<文件名>/images_index.json
                image_index_path = os.path.join(file_output_dir, "images_index.json")
                with open(image_index_path, 'w', encoding='utf-8') as f:
                    json.dump(image_index, f, ensure_ascii=False, indent=2)
                
                print(f"  ✓ 已保存 {len(image_index)} 张图片的base64编码及索引文件")
            else:
                print("  未检测到图片")
            
            print(f"成功将 {input_path} 转换为 {md_path}")
            return True
            
        except Exception as e:
            print(f"转换过程中出现错误: {str(e)}")
            return False

def extract_images_from_markdown(markdown_content: str, base_filename: str) -> Tuple[Dict, Dict]:
    """
    从Markdown内容中提取base64编码的图片（不保存原始图片文件）
    
    Args:
        markdown_content (str): Markdown内容
        base_filename (str): 基础文件名
        
    Returns:
        Tuple[Dict, Dict]: 图片索引信息和pics索引信息
    """
    image_index = {}
    # 匹配Markdown中的base64图片（更宽松的匹配）
    pattern = r'data:image/[^;]+;base64,([a-zA-Z0-9+/=]+)'
    matches = re.findall(pattern, markdown_content)
    
    # 如果上面的模式没有匹配到，尝试更宽松的匹配
    if not matches:
        pattern = r'data:image/[a-zA-Z]+;base64,([a-zA-Z0-9+/=]+)'
        matches = re.findall(pattern, markdown_content)
    
    for i, base64_data in enumerate(matches):
        try:
            # 解码base64数据
            image_data = base64.b64decode(base64_data)
            
            # 生成图片文件名
            image_filename = f"{base_filename}_image_{i+1:03d}.png"
            
            # 记录图片索引信息（只保存base64编码，不保存原始图片文件）
            image_index[image_filename] = {
                "image_id": i+1,
                "base64": base64_data,
                "size": len(image_data)
            }
        except Exception as e:
            print(f"  警告: 提取第{i+1}张图片时出错: {str(e)}")
    
    return image_index, {}

def extract_images_from_docx(docx_path: str, base_filename: str) -> Tuple[Dict, Dict]:
    """
    从docx文件中直接提取图片（不保存原始图片文件）
    
    Args:
        docx_path (str): docx文件路径
        base_filename (str): 基础文件名
        
    Returns:
        Tuple[Dict, Dict]: 图片索引信息和pics索引信息
    """
    image_index = {}
    
    try:
        # 打开docx文件（docx本质上是一个zip文件）
        with ZipFile(docx_path, 'r') as docx_zip:
            # 获取所有图片文件
            image_files = [f for f in docx_zip.namelist() if f.startswith('word/media/')]
            
            print(f"  从docx文件中检测到 {len(image_files)} 张图片")
            
            # 提取每张图片
            for i, image_file in enumerate(image_files):
                # 读取图片数据
                image_data = docx_zip.read(image_file)
                
                # 获取图片扩展名
                ext = os.path.splitext(image_file)[1]
                if not ext:
                    ext = '.png'  # 默认使用png格式
                
                # 生成图片文件名
                image_filename = f"{base_filename}_image_{i+1:03d}{ext}"
                
                # 生成base64编码
                image_base64 = base64.b64encode(image_data).decode('utf-8')
                
                # 记录图片索引信息（只保存base64编码，不保存原始图片文件）
                image_index[image_filename] = {
                    "image_id": i+1,
                    "base64": image_base64,
                    "size": len(image_data)
                }
    except Exception as e:
        print(f"  警告: 从docx文件提取图片时出错: {str(e)}")
    
    return image_index, {}

def extract_images_from_pdf(pdf_path: str, base_filename: str) -> Tuple[Dict, Dict]:
    """
    从PDF文件中直接提取图片（不保存原始图片文件）
    
    Args:
        pdf_path (str): PDF文件路径
        base_filename (str): 基础文件名
        
    Returns:
        Tuple[Dict, Dict]: 图片索引信息和pics索引信息
    """
    image_index = {}
    
    if not PDF_SUPPORTED:
        print("  警告: 未安装PyMuPDF库，无法从PDF文件中提取图片")
        return image_index, {}
    
    try:
        # 打开PDF文件
        doc = fitz.open(pdf_path)
        
        image_count = 0
        
        # 遍历每一页
        for page_num in range(len(doc)):
            # 获取页面中的图片列表
            image_list = doc.get_page_images(page_num)
            
            for image_index_in_page, img in enumerate(image_list, start=1):
                # 提取图片数据
                xref = img[0]
                pix = fitz.Pixmap(doc, xref)
                
                # 生成图片文件名
                image_count += 1
                image_filename = f"{base_filename}_image_{image_count:03d}.png"
                
                # 获取图片数据
                if pix.n < 5:  # 如果不是CMYK格式，直接获取数据
                    image_data = pix.tobytes()
                else:  # 如果是CMYK格式，转换为RGB再获取数据
                    pix = fitz.Pixmap(fitz.csRGB, pix)
                    image_data = pix.tobytes()
                
                # 生成base64编码
                image_base64 = base64.b64encode(image_data).decode('utf-8')
                
                # 记录图片索引信息（只保存base64编码，不保存原始图片文件）
                image_index[image_filename] = {
                    "image_id": image_count,
                    "base64": image_base64,
                    "size": len(image_data)
                }
                
                # 释放资源
                pix = None
        
        doc.close()
        
        print(f"  从PDF文件中检测到 {image_count} 张图片")
        
    except Exception as e:
        print(f"  警告: 从PDF文件提取图片时出错: {str(e)}")
    
    return image_index, {}

def convert_all_files_in_directory(input_dir="doc_Data", output_dir="md_ConvertResult"):
    """
    转换指定目录中的所有支持的文件
    
    Args:
        input_dir (str): 输入目录路径
        output_dir (str): 输出目录路径
    """
    # 构建完整的输入目录路径（使用相对于脚本的路径）
    input_dir = os.path.join(script_dir, input_dir)
    
    if not os.path.exists(input_dir):
        print(f"错误: 输入目录 {input_dir} 不存在")
        return
    
    # 获取目录中所有支持的文件
    supported_files = [f for f in os.listdir(input_dir) if is_supported_file(f)]
    
    if not supported_files:
        print(f"在目录 {input_dir} 中未找到支持的文件")
        return
    
    print(f"找到 {len(supported_files)} 个支持的文件，开始转换...")
    
    # 转换每个文件
    for filename in supported_files:
        file_path = os.path.join(input_dir, filename)
        convert_file_to_md(file_path, output_dir)

if __name__ == "__main__":
    # 尝试从配置文件加载参数
    config = load_conversion_config()
    
    # 从配置文件获取默认输入输出路径
    default_input_path = config.get("default_input_path", "raw_data")
    default_output_path = config.get("default_output_path", "converted_data")
    
    parser = argparse.ArgumentParser(description='将多种格式的文件转换为 .md 文件\n支持格式包括: .docx, .pdf, .txt, .html, .htm, .pptx, .xlsx')
    parser.add_argument('-i', '--input', default=default_input_path, help=f'输入目录路径或单个文件路径（默认: {default_input_path}）')
    parser.add_argument('-o', '--output', default=default_output_path, help=f'输出目录路径（默认: {default_output_path}）')
    parser.add_argument('--config', help='配置文件路径')
    
    args = parser.parse_args()
    
    # 如果指定了配置文件，则从配置文件加载参数
    if args.config:
        print(f"📄 使用指定配置文件: {args.config}")
        config = load_conversion_config(args.config)
        # 如果命令行参数没有指定，则使用配置文件中的参数
        if args.input == default_input_path:  # 如果使用默认值
            args.input = config.get("default_input_path", default_input_path)
        if args.output == default_output_path:  # 如果使用默认值
            args.output = config.get("default_output_path", default_output_path)
    
    # 构建完整的输入路径（优先使用相对于脚本的路径）
    input_path = os.path.join(script_dir, args.input)
    
    # 检查是否为单个文件
    if os.path.isfile(input_path) and is_supported_file(input_path):
        # 处理单个文件
        convert_file_to_md(input_path, args.output)
    elif os.path.isfile(args.input) and is_supported_file(args.input):
        # 如果提供了绝对路径或相对路径的文件
        convert_file_to_md(args.input, args.output)
    else:
        # 处理目录
        convert_all_files_in_directory(args.input, args.output)
