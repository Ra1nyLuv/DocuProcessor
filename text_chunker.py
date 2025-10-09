#!/usr/bin/env python3
"""
基于文本分析的文本分割切块工具
该工具将Markdown文档按照文本单元进行分割，确保每个分割块的文本完整性
"""

import os
import re
import json
from typing import List, Tuple
import argparse


class SemanticChunker:
    """文本文本分割器"""
    
    def __init__(self, chunk_min_length: int = 20, chunk_max_length: int = 200, 
                 overlap_min_length: int = 10, overlap_max_length: int = 50,
                 semantic_patterns: List[str] = None, enable_overlap: bool = True,
                 chunking_method: str = "semantic", chunk_by_length_config: dict = None,
                 chunk_by_paragraph_config: dict = None):
        """
        初始化文本分割器
        
        Args:
            chunk_min_length: 分割块最小字符长度
            chunk_max_length: 分割块最大字符长度
            overlap_min_length: 重叠文本最小长度
            overlap_max_length: 重叠文本最大长度
            semantic_patterns: 文本分割点的正则表达式模式列表
            enable_overlap: 是否启用重叠文本功能
            chunking_method: 分块方式 ("semantic", "length", "paragraph")
            chunk_by_length_config: 按长度分块的配置
            chunk_by_paragraph_config: 按段落分块的配置
        """
        self.chunk_min_length = chunk_min_length
        self.chunk_max_length = chunk_max_length
        self.overlap_min_length = overlap_min_length
        self.overlap_max_length = overlap_max_length
        self.enable_overlap = enable_overlap
        self.chunking_method = chunking_method
        self.chunk_by_length_config = chunk_by_length_config or {}
        self.chunk_by_paragraph_config = chunk_by_paragraph_config or {}
        
        # 定义文本分割点的正则表达式模式
        self.semantic_patterns = semantic_patterns if semantic_patterns else [
            r'\n#{1,6} ',           # 标题
            r'\n###+',              # 分隔线
            r'\n\n\*\*[^\n]+\*\*\n', # 加粗的段落标题
            r'\n\n[A-Z][^\n]*\n\n', # 可能的章节标题（大写字母开头的独立段落）
        ]
        # 标题识别模式
        self.title_patterns = [
            r'^#{1,6}\s.*$',           # Markdown标题
            r'^\*\*[^\n]+\*\*$',       # 加粗标题
        ]
    
    def read_markdown(self, file_path: str) -> str:
        """
        读取Markdown文件内容
        
        Args:
            file_path: Markdown文件路径
            
        Returns:
            文件内容字符串
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def detect_semantic_breaks(self, content: str) -> List[int]:
        """
        检测文本分割点位置
        
        Args:
            content: 文本内容
            
        Returns:
            分割点位置列表
        """
        breaks = [0]  # 开始位置总是分割点
        
        # 查找所有可能的文本分割点
        for pattern in self.semantic_patterns:
            for match in re.finditer(pattern, content):
                pos = match.start() + 1  # +1 是为了跳过前面的\n
                if pos not in breaks:
                    breaks.append(pos)
        
        # 添加段落边界作为分割点（两个换行符）
        paragraph_pattern = r'\n\s*\n'
        for match in re.finditer(paragraph_pattern, content):
            pos = match.end()
            if pos not in breaks:
                breaks.append(pos)
        
        # 添加结束位置
        breaks.append(len(content))
        
        # 按位置排序
        breaks.sort()
        return breaks
    
    def chunk_text(self, content: str) -> List[str]:
        """
        根据配置的分块方式对文本进行分块
        
        Args:
            content: 待分割的文本内容
            
        Returns:
            分割后的文本块列表
        """
        if self.chunking_method == "length":
            return self.chunk_by_length(content)
        elif self.chunking_method == "paragraph":
            return self.chunk_by_paragraph(content)
        else:  # 默认使用语义分块
            return self.chunk_by_semantic(content)
    
    def chunk_by_length(self, content: str) -> List[str]:
        """
        按固定长度进行文本分割，同时正确处理标题
        
        Args:
            content: 待分割的文本内容
            
        Returns:
            分割后的文本块列表
        """
        chunk_size = self.chunk_by_length_config.get("chunk_size", 100)
        chunk_overlap = self.chunk_by_length_config.get("chunk_overlap", 20)
        
        # 首先按段落分割内容
        paragraphs = re.split(r'\n\s*\n', content)
        
        chunks = []
        
        for paragraph in paragraphs:
            if not paragraph.strip():
                continue
                
            cleaned_paragraph = paragraph.strip()
            
            # 检查当前段落是否为标题
            is_title = self._is_title_paragraph(cleaned_paragraph)
            
            if is_title:
                # 标题作为独立的空块处理
                chunks.append("")
            else:
                # 非标题段落按长度分块
                start = 0
                para_length = len(cleaned_paragraph)
                
                while start < para_length:
                    end = min(start + chunk_size, para_length)
                    chunk = cleaned_paragraph[start:end]
                    chunks.append(chunk)
                    
                    # 如果不是最后一个块，移动起始位置以创建重叠
                    if end < para_length:
                        start = end - min(chunk_overlap, chunk_size // 2)
                    else:
                        break
        
        return chunks
    
    def chunk_by_paragraph(self, content: str) -> List[str]:
        """
        按段落进行文本分割，同时正确处理标题
        
        Args:
            content: 待分割的文本内容
            
        Returns:
            分割后的文本块列表
        """
        max_chunk_size = self.chunk_by_paragraph_config.get("max_chunk_size", 500)
        
        # 按段落分割内容（两个换行符）
        paragraphs = re.split(r'\n\s*\n', content)
        
        chunks = []
        
        for paragraph in paragraphs:
            if not paragraph.strip():
                continue
            
            cleaned_paragraph = paragraph.strip()
            
            # 检查当前段落是否为标题
            is_title = self._is_title_paragraph(cleaned_paragraph)
            
            # 如果是标题，则单独作为一个块处理（但内容为空）
            if is_title:
                # 标题单独作为一个块，但内容为空（只在索引中保留标题）
                chunks.append("")
                continue
            
            # 如果单个段落就超过最大块大小，则进行句子分割
            if len(cleaned_paragraph) > max_chunk_size:
                # 按句子分割段落
                sentences = self._split_into_sentences(cleaned_paragraph)
                current_chunk = ""
                
                for sentence in sentences:
                    # 如果加上当前句子会超过最大块大小，且当前块已有内容，则保存当前块
                    if current_chunk and len(current_chunk) + len(sentence) > max_chunk_size:
                        chunks.append(current_chunk.strip())
                        current_chunk = sentence
                    else:
                        # 合并到当前块
                        if current_chunk:
                            current_chunk += sentence
                        else:
                            current_chunk = sentence
                
                # 保存最后一个块
                if current_chunk:
                    chunks.append(current_chunk.strip())
            else:
                # 每个段落作为一个独立的块
                chunks.append(cleaned_paragraph)
        
        return chunks
    
    def chunk_by_semantic(self, content: str) -> List[str]:
        """
        基于文本分析进行文本分割，优先保持段落完整性
        
        Args:
            content: 待分割的文本内容
            
        Returns:
            分割后的文本块列表
        """
        # 按段落分割内容（两个换行符）
        paragraphs = re.split(r'\n\s*\n', content)
        
        chunks = []
        current_chunk = ""
        
        # 按段落进行分组，优先保持段落完整性
        i = 0
        while i < len(paragraphs):
            paragraph = paragraphs[i]
            if not paragraph.strip():
                i += 1
                continue
                
            cleaned_paragraph = paragraph.strip()
            
            # 检查当前段落是否包含base64图片（使用模糊匹配）
            # 使用更宽松的正则表达式来匹配图片，支持多行匹配
            base64_images = re.findall(r'!\[.*?\]\(data:image/.*?;base64.*?\)', cleaned_paragraph, re.DOTALL)
            if base64_images:
                # 如果当前块不为空，先保存当前块
                if current_chunk and current_chunk.strip():
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                
                # 特殊处理：将包含图片的段落按图片分割成独立的块
                # 使用正则表达式分割，保留分隔符
                parts = re.split(r'(!\[.*?\]\(data:image/.*?;base64.*?\))', cleaned_paragraph, flags=re.DOTALL)
                
                # 处理分割后的部分
                for part in parts:
                    if part.strip():
                        # 检查是否为图片（使用模糊匹配）
                        if re.match(r'!\[.*?\]\(data:image/.*?;base64.*?\)', part.strip(), re.DOTALL):
                            # 这是一个base64图片，单独作为一个块
                            chunks.append(part.strip())
                        else:
                            # 这是普通文本部分，需要进一步处理
                            # 如果文本部分不为空，按正常逻辑处理
                            if part.strip():
                                text_chunks = self._process_text_content(part.strip())
                                chunks.extend(text_chunks)
                
                i += 1
                continue
            
            # 检查当前段落是否为标题
            is_title = self._is_title_paragraph(cleaned_paragraph)
            
            # 如果是标题，则单独作为一个块处理（但内容为空）
            if is_title:
                # 如果当前块不为空，先保存当前块
                if current_chunk and current_chunk.strip():
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                # 标题单独作为一个块，但内容为空（只在索引中保留标题）
                chunks.append("")
                i += 1
                continue
            
            # 检查当前段落是否以列表项开始
            is_list_item = bool(re.match(r'^([\*\-\+]\s|\d+\.\s)', cleaned_paragraph))
            
            # 如果当前块加上新段落后超过最大长度
            if len(current_chunk) + len(cleaned_paragraph) > self.chunk_max_length:
                # 如果当前块已达到最小长度，则保存当前块并开始新块
                if len(current_chunk) >= self.chunk_min_length:
                    chunks.append(current_chunk.strip())
                    current_chunk = cleaned_paragraph
                else:
                    # 如果当前块未达到最小长度，尝试合并
                    if current_chunk:
                        current_chunk += "\n\n" + cleaned_paragraph
                    else:
                        current_chunk = cleaned_paragraph
                    
                    # 如果合并后超过最大长度，则强制分割
                    if len(current_chunk) > self.chunk_max_length:
                        # 如果是列表项，尽量保持完整性
                        if is_list_item:
                            chunks.append(current_chunk.strip())
                            current_chunk = ""
                        else:
                            # 否则按句子分割
                            sentences = self._split_into_sentences(current_chunk)
                            temp_chunk = ""
                            for sentence in sentences:
                                if len(temp_chunk) + len(sentence) > self.chunk_max_length or len(temp_chunk) < self.chunk_min_length:
                                    if temp_chunk:
                                        chunks.append(temp_chunk.strip())
                                    temp_chunk = sentence
                            if temp_chunk:
                                current_chunk = temp_chunk
                            else:
                                current_chunk = ""
            else:
                # 合并到当前块
                if current_chunk:
                    current_chunk += "\n\n" + cleaned_paragraph
                else:
                    current_chunk = cleaned_paragraph
            i += 1
        
        # 保存最后一个块
        if current_chunk and current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        # 后处理：处理过长的块
        final_chunks = []
        for chunk in chunks:
            if len(chunk) <= self.chunk_max_length:
                final_chunks.append(chunk)
            else:
                # 对于仍然过长的块，按段落进行分割
                final_chunks.extend(self._split_long_chunk_by_paragraph(chunk))
        
        # 处理重叠文本（如果启用）
        if self.enable_overlap and len(final_chunks) > 1:
            final_chunks = self._add_overlap_to_chunks(final_chunks)
        
        return final_chunks
    
    def _process_text_content(self, text_content: str) -> List[str]:
        """
        处理纯文本内容，按正常分块逻辑进行分割
        
        Args:
            text_content: 纯文本内容
            
        Returns:
            分割后的文本块列表
        """
        if not text_content.strip():
            return []
            
        # 如果文本长度小于等于最大块长度，直接返回
        if len(text_content) <= self.chunk_max_length:
            return [text_content]
            
        # 如果文本长度超过最大块长度，按句子分割
        sentences = self._split_into_sentences(text_content)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if not sentence.strip():
                continue
                
            if len(current_chunk) + len(sentence) > self.chunk_max_length and len(current_chunk) >= self.chunk_min_length:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                if current_chunk:
                    current_chunk += sentence
                else:
                    current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return chunks if chunks else [text_content]
    
    def _add_overlap_to_chunks(self, chunks: List[str]) -> List[str]:
        """
        为文本块添加重叠文本以保证完整性，同时保持内容连续性
        
        Args:
            chunks: 原始文本块列表
            
        Returns:
            添加重叠文本后的文本块列表
        """
        if len(chunks) <= 1:
            return chunks
        
        overlapped_chunks = []
        for i, chunk in enumerate(chunks):
            if i == 0:
                # 第一个块，只向后添加重叠
                next_chunk = chunks[i + 1]
                overlap_text = self._extract_overlap_text(chunk, next_chunk, is_forward=True)
                overlapped_chunks.append(chunk + ("\n\n" + overlap_text if overlap_text else ""))
            elif i == len(chunks) - 1:
                # 最后一个块，只向前添加重叠
                prev_chunk = chunks[i - 1]
                overlap_text = self._extract_overlap_text(prev_chunk, chunk, is_forward=False)
                overlapped_chunks.append((overlap_text + "\n\n" if overlap_text else "") + chunk)
            else:
                # 中间的块，前后都添加重叠
                prev_chunk = chunks[i - 1]
                next_chunk = chunks[i + 1]
                
                # 向前添加重叠（确保不重复已有内容）
                forward_overlap = self._extract_overlap_text(prev_chunk, chunk, is_forward=False)
                # 向后添加重叠（确保不重复已有内容）
                backward_overlap = self._extract_overlap_text(chunk, next_chunk, is_forward=True)
                
                # 避免重复内容，只添加必要的重叠部分
                overlapped_chunk = chunk
                if forward_overlap and not chunk.startswith(forward_overlap.strip()):
                    overlapped_chunk = forward_overlap + "\n\n" + overlapped_chunk
                if backward_overlap and not chunk.endswith(backward_overlap.strip()):
                    overlapped_chunk = overlapped_chunk + "\n\n" + backward_overlap
                
                overlapped_chunks.append(overlapped_chunk)
        
        return overlapped_chunks
    
    def _extract_overlap_text(self, prev_chunk: str, next_chunk: str, is_forward: bool = True) -> str:
        """
        从相邻文本块中提取重叠文本
        
        Args:
            prev_chunk: 前一个文本块
            next_chunk: 后一个文本块
            is_forward: 是否向前添加重叠（False表示向后添加重叠）
            
        Returns:
            提取的重叠文本
        """
        # 确定重叠长度
        overlap_length = min(self.overlap_max_length, len(prev_chunk) if is_forward else len(next_chunk))
        overlap_length = max(overlap_length, self.overlap_min_length)
        
        if is_forward:
            # 从后一个块的开头提取重叠文本
            return next_chunk[:overlap_length] if len(next_chunk) >= overlap_length else next_chunk
        else:
            # 从前一个块的结尾提取重叠文本
            return prev_chunk[-overlap_length:] if len(prev_chunk) >= overlap_length else prev_chunk
    
    def _split_long_chunk_by_paragraph(self, chunk: str) -> List[str]:
        """
        按段落分割过长的文本块
        
        Args:
            chunk: 过长的文本块
            
        Returns:
            分割后的文本块列表
        """
        # 按段落分割（两个换行符）
        paragraphs = re.split(r'\n\s*\n', chunk)
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            if not paragraph.strip():
                continue
                
            # 清理段落
            cleaned_paragraph = paragraph.strip()
            
            if len(current_chunk) + len(cleaned_paragraph) > self.chunk_max_length and len(current_chunk) >= self.chunk_min_length:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = cleaned_paragraph
            else:
                if current_chunk:
                    current_chunk += "\n\n" + cleaned_paragraph
                else:
                    current_chunk = cleaned_paragraph
        
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        # 如果仍然有超过最大长度的块，使用句子分割
        final_chunks = []
        for ch in chunks:
            if len(ch) <= self.chunk_max_length:
                final_chunks.append(ch)
            else:
                final_chunks.extend(self._split_long_chunk(ch))
        
        return final_chunks if final_chunks else [chunk]
    
    def _split_long_chunk(self, chunk: str) -> List[str]:
        """
        分割过长的文本块
        
        Args:
            chunk: 过长的文本块
            
        Returns:
            分割后的文本块列表
        """
        # 按句子分割
        sentences = re.split(r'(?<=[。！？])', chunk)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if not sentence.strip():
                continue
                
            if len(current_chunk) + len(sentence) > self.chunk_max_length and len(current_chunk) >= self.chunk_min_length:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                if current_chunk:
                    current_chunk += sentence
                else:
                    current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return chunks if chunks else [chunk]
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        将文本按句子分割
        
        Args:
            text: 待分割的文本
            
        Returns:
            分割后的句子列表
        """
        # 中英文句子分割的正则表达式
        sentence_endings = r'[.!?。！？]+'
        sentences = re.split(f'({sentence_endings})', text)
        
        # 合并句子和标点符号
        combined_sentences = []
        i = 0
        while i < len(sentences):
            if i + 1 < len(sentences) and re.match(sentence_endings, sentences[i + 1]):
                combined_sentences.append(sentences[i] + sentences[i + 1])
                i += 2
            else:
                if sentences[i].strip():  # 只添加非空句子
                    combined_sentences.append(sentences[i])
                i += 1
        
        return [s.strip() for s in combined_sentences if s.strip()]
    
    def _is_title_paragraph(self, paragraph: str) -> bool:
        """
        判断段落是否为标题
        
        Args:
            paragraph: 段落内容
            
        Returns:
            是否为标题
        """
        for pattern in self.title_patterns:
            if re.match(pattern, paragraph.strip()):
                return True
        return False
    
    def _extract_meaningful_title(self, chunk: str) -> str:
        """
        从文本块中提取有意义的标题
        
        Args:
            chunk: 文本块
            
        Returns:
            提取的标题
        """
        # 如果文本块为空，返回默认标题
        if not chunk or not chunk.strip():
            return "文本段落"
            
        lines = chunk.strip().split('\n')
        
        # 如果第一行是标题格式，使用它作为标题
        if lines and self._is_title_paragraph(lines[0]):
            title = re.sub(r'[#*\[\]]', '', lines[0]).strip()
            # 清理标题中的特殊字符
            title = re.sub(r'[<>:"/\\|?*\x00-\x1f]|data:image/[a-z]+;base64[^\s]*|\![\(][^\)]*[\)]', '', title).strip()
            return title[:30]  # 限制长度
        
        # 否则使用前30个字符作为标题
        first_line = lines[0] if lines else "文本段落"
        # 移除可能导致文件名问题的字符
        safe_title = re.sub(r'[<>:"/\\|?*\x00-\x1f]|data:image/[a-z]+;base64[^\s]*|\![\(][^\)]*[\)]', '', first_line).strip()
        return safe_title[:30] or "文本段落"
    
    def process_file(self, input_file: str, output_dir: str = None, save_chunk_index: bool = False, chunk_index_filename: str = "chunk_index.json") -> List[str]:
        """
        处理单个Markdown文件
        
        Args:
            input_file: 输入的Markdown文件路径
            output_dir: 输出目录，如果为None则不保存到文件
            save_chunk_index: 是否保存分块索引
            chunk_index_filename: 分块索引文件名
            
        Returns:
            分割后的文本块列表
        """
        print(f"正在处理文件: {os.path.basename(input_file)}")
        
        # 读取文件内容
        try:
            content = self.read_markdown(input_file)
            print(f"  已读取文件内容，共 {len(content)} 个字符")
        except Exception as e:
            print(f"  读取文件时出错: {str(e)}")
            return []
        
        # 进行文本分割
        print(f"  正在进行{self.chunking_method}文本分割...")
        chunks = self.chunk_text(content)
        print(f"  分割完成，共生成 {len(chunks)} 个文本块")
        
        # 保存到文件（如果指定了输出目录）
        if output_dir:
            base_filename = os.path.splitext(os.path.basename(input_file))[0]
            specific_output_dir = os.path.join(output_dir, base_filename)
            print(f"  正在保存文本块到目录: {specific_output_dir}")
            self.save_chunks(chunks, specific_output_dir, base_filename, save_chunk_index, chunk_index_filename, content)
            print(f"  ✓ 文件处理完成，共保存 {len(chunks)} 个文本块")
        
        return chunks
    
    def save_chunks(self, chunks: List[str], output_dir: str, base_filename: str, save_chunk_index: bool = False, chunk_index_filename: str = "chunk_index.json", original_content: str = ""):
        """
        保存分割后的文本块到文件
        
        Args:
            chunks: 文本块列表
            output_dir: 输出目录
            base_filename: 基础文件名
            save_chunk_index: 是否保存分块索引
            chunk_index_filename: 分块索引文件名
            original_content: 原始内容，用于提取标题
        """
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 清空已存在的分割结果
        if os.path.exists(output_dir):
            existing_files = [f for f in os.listdir(output_dir) if os.path.isfile(os.path.join(output_dir, f))]
            if existing_files:
                print(f"  清理输出目录，删除 {len(existing_files)} 个已存在的文件")
                for file in existing_files:
                    file_path = os.path.join(output_dir, file)
                    os.remove(file_path)
        
        # 用于存储分块索引信息
        chunk_index = []
        
        # 如果有原始内容，预先提取所有标题
        titles = []
        is_title_list = []
        if original_content:
            titles, is_title_list = self._extract_titles_and_flags_from_content(original_content)
        
        # 保存每个文本块到索引文件中，而不是单独的文件
        print(f"  正在保存 {len(chunks)} 个文本块到索引文件...")
        
        # 图片ID计数器，从1开始
        image_id_counter = 1
        
        for i, chunk in enumerate(chunks, 1):
            # 生成有意义的标题
            if i <= len(titles):
                title = titles[i-1]
            else:
                title = self._extract_meaningful_title(chunk)
            
            # 生成文件名（仅用于标识）
            filename = f"{i:03d}_{title}.md"
            
            # 记录索引信息，直接包含文本内容
            if save_chunk_index:
                # 确定是否为标题块
                is_title_block = i <= len(is_title_list) and is_title_list[i-1]
                
                # 对于标题块，我们存储标题信息
                index_title = title if is_title_block else ""
                
                # 对于空内容的块，添加特殊标记
                content = chunk if chunk.strip() else ""
                
                # 检查是否为图片块（使用模糊匹配）
                is_image_block = False
                image_content = ""
                
                # 检查整个块是否就是一张图片
                if re.match(r'^!\[.*?\]\(data:image/.*?;base64.*?\)$', chunk.strip(), re.DOTALL):
                    is_image_block = True
                    image_content = chunk.strip()
                
                # 准备索引条目
                index_entry = {
                    "id": len(chunk_index) + 1,
                    "title": index_title,
                    "content": image_content if is_image_block else content,  # 图片块存储图片内容，其他块存储文本内容
                    "is_title": is_title_block  # 添加标题标记字段
                }
                
                # 如果是图片块，添加image_id属性和type属性
                if is_image_block:
                    index_entry["image_id"] = image_id_counter
                    index_entry["type"] = "image"
                    image_id_counter += 1
                else:
                    index_entry["type"] = "text"
                
                chunk_index.append(index_entry)
        
        # 保存分块索引文件
        if save_chunk_index and chunk_index:
            index_filepath = os.path.join(output_dir, chunk_index_filename)
            try:
                with open(index_filepath, 'w', encoding='utf-8') as f:
                    json.dump(chunk_index, f, ensure_ascii=False, indent=2)
                print(f"  ✓ 已保存分块索引文件: {chunk_index_filename} (包含 {len(chunk_index)} 个条目)")
            except Exception as e:
                print(f"  保存索引文件时出错: {str(e)}")
        elif save_chunk_index:
            print("  ⚠️ 未生成索引信息，跳过索引文件保存")
    
    def _extract_titles_and_flags_from_content(self, content: str) -> Tuple[List[str], List[bool]]:
        """
        从原始内容中提取所有标题和标题标记
        
        Args:
            content: 原始内容
            
        Returns:
            标题列表和是否为标题的标记列表
        """
        titles = []
        is_title_list = []
        # 按段落分割内容
        paragraphs = re.split(r'\n\s*\n', content)
        
        for paragraph in paragraphs:
            if not paragraph.strip():
                continue
                
            cleaned_paragraph = paragraph.strip()
            
            # 检查当前段落是否为标题
            is_title = self._is_title_paragraph(cleaned_paragraph)
            is_title_list.append(is_title)
            
            if is_title:
                # 提取标题文本（去除Markdown标记）
                title = re.sub(r'[#*\[\]]', '', cleaned_paragraph).strip()
                # 清理标题中的特殊字符
                title = re.sub(r'[<>:"/\\|?*\x00-\x1f]|data:image/[a-z]+;base64[^\s]*|\![\(][^\)]*[\)]', '', title).strip()
                titles.append(title[:30])  # 限制长度
            else:
                # 对于非标题段落，使用前30个字符作为文件名
                first_line = cleaned_paragraph.split('\n')[0] if '\n' in cleaned_paragraph else cleaned_paragraph
                # 移除可能导致文件名问题的字符
                safe_title = re.sub(r'[<>:"/\\|?*\x00-\x1f]|data:image/[a-z]+;base64[^\s]*|\![\(][^\)]*[\)]', '', first_line).strip()
                titles.append(safe_title[:30] or "文本段落")
        
        return titles, is_title_list
    
    def process_directory(self, input_dir: str, output_dir: str, save_chunk_index: bool = False, chunk_index_filename: str = "chunk_index.json"):
        """
        处理目录中的所有Markdown文件
        
        Args:
            input_dir: 输入目录
            output_dir: 输出目录
            save_chunk_index: 是否保存分块索引
            chunk_index_filename: 分块索引文件名
        """
        if not os.path.exists(input_dir):
            print(f"❌ 错误: 输入目录 '{input_dir}' 不存在")
            return
        
        # 递归获取所有Markdown文件（适应新的目录结构）
        md_files = []
        for root, dirs, files in os.walk(input_dir):
            for file in files:
                if file.lower().endswith('.md'):
                    # 构建相对于输入目录的路径
                    full_path = os.path.join(root, file)
                    relative_path = os.path.relpath(full_path, input_dir)
                    md_files.append((relative_path, full_path))
        
        if not md_files:
            print(f"⚠️  提示: 在目录 '{input_dir}' 中未找到Markdown文件")
            return
        
        print(f"📁 找到 {len(md_files)} 个Markdown文件，开始批量处理...")
        print("-" * 50)
        
        success_count = 0
        failed_count = 0
        
        # 处理每个文件
        for i, (relative_path, full_path) in enumerate(md_files, 1):
            print(f"[{i}/{len(md_files)}] 处理文件: {relative_path}")
            try:
                self.process_file(full_path, output_dir, save_chunk_index, chunk_index_filename)
                success_count += 1
            except Exception as e:
                print(f"  ❌ 处理文件 '{relative_path}' 时出错: {str(e)}")
                failed_count += 1
        
        print("-" * 50)
        print(f"📊 批量处理完成统计:")
        print(f"  ✅ 成功处理: {success_count} 个文件")
        if failed_count > 0:
            print(f"  ❌ 处理失败: {failed_count} 个文件")
        print(f"  📦 输出目录: {output_dir}")

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

def load_config(config_file: str = "chunk_config.json") -> dict:
    """
    从配置文件加载分块参数
    
    Args:
        config_file: 配置文件路径
        
    Returns:
        包含分块参数的字典
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
        "chunk_min_length": 50,
        "chunk_max_length": 200,
        "overlap_min_length": 10,
        "overlap_max_length": 50,
        "semantic_patterns": [
            "\\n#{1,6} ",           
            "\\n###+",              
            "\\n\\n\\*\\*[^\\n]+\\*\\*\\n", 
            "\\n\\n[A-Z][^\\n]*\\n\\n" 
        ],
        "enable_overlap": True,
        "save_chunk_index": True,
        "chunk_index_filename": "chunk_index.json"
    }


def main():
    print("🔤 基于语义分析的文本分割工具")
    print("=" * 40)
    
    # 获取当前脚本的目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 尝试从配置文件加载参数
    config = load_config()
    print(f"⚙️  已加载配置参数")
    
    # 从配置文件获取默认输入输出路径
    default_input_path = config.get("default_input_path", "md_ConvertResult")
    default_output_path = config.get("default_output_path", "md_SemanticSliced")
    
    # 从配置文件获取分块方式配置
    chunking_method = config.get("chunking_method", "semantic")
    chunk_by_length_config = config.get("chunk_by_length", {})
    chunk_by_paragraph_config = config.get("chunk_by_paragraph", {})
    
    parser = argparse.ArgumentParser(description='基于文本分析的文本分割工具')
    parser.add_argument('-i', '--input', default=default_input_path, help=f'输入目录路径或单个文件路径（默认: {default_input_path}）')
    parser.add_argument('-o', '--output', default=default_output_path, help=f'输出目录路径（默认: {default_output_path}）')
    parser.add_argument('--min-length', type=int, default=config["chunk_min_length"], help='分割块最小字符长度（默认: 50）')
    parser.add_argument('--max-length', type=int, default=config["chunk_max_length"], help='分割块最大字符长度（默认: 200）')
    parser.add_argument('--overlap-min', type=int, default=config.get("overlap_min_length", 10), help='重叠文本最小长度（默认: 10）')
    parser.add_argument('--overlap-max', type=int, default=config.get("overlap_max_length", 50), help='重叠文本最大长度（默认: 50）')
    parser.add_argument('--enable-overlap', action='store_true', default=config.get("enable_overlap", True), help='启用重叠文本功能（默认: 启用）')
    parser.add_argument('--save-index', action='store_true', default=config.get("save_chunk_index", True), help='保存分块索引文件（默认: 保存）')
    parser.add_argument('--index-filename', default=config.get("chunk_index_filename", "chunk_index.json"), help='分块索引文件名（默认: chunk_index.json）')
    parser.add_argument('--chunking-method', default=chunking_method, choices=['semantic', 'length', 'paragraph'], help=f'分块方式（默认: {chunking_method}）')
    parser.add_argument('--config', help='配置文件路径')
    
    args = parser.parse_args()
    
    # 如果指定了配置文件，则从配置文件加载参数
    if args.config:
        print(f"📄 使用指定配置文件: {args.config}")
        config = load_config(args.config)
        # 如果命令行参数没有指定，则使用配置文件中的参数
        if args.min_length == 50:  # 默认值
            args.min_length = config.get("chunk_min_length", 50)
        if args.max_length == 200:  # 默认值
            args.max_length = config.get("chunk_max_length", 200)
        if args.overlap_min == 10:  # 默认值
            args.overlap_min = config.get("overlap_min_length", 10)
        if args.overlap_max == 50:  # 默认值
            args.overlap_max = config.get("overlap_max_length", 50)
        if not args.enable_overlap:  # 如果未在命令行指定，则使用配置文件
            args.enable_overlap = config.get("enable_overlap", True)
        if not args.save_index:  # 如果未在命令行指定，则使用配置文件
            args.save_index = config.get("save_chunk_index", True)
        if args.index_filename == "chunk_index.json":  # 默认值
            args.index_filename = config.get("chunk_index_filename", "chunk_index.json")
        if args.chunking_method == chunking_method:  # 如果使用默认值
            args.chunking_method = config.get("chunking_method", "semantic")
    
    # 显示当前使用的参数
    print(f"📊 当前参数设置:")
    print(f"   最小块长度: {args.min_length}")
    print(f"   最大块长度: {args.max_length}")
    print(f"   重叠文本: {'启用' if args.enable_overlap else '禁用'}")
    if args.enable_overlap:
        print(f"   重叠范围: {args.overlap_min}-{args.overlap_max} 字符")
    print(f"   索引文件: {'保存' if args.save_index else '不保存'}")
    if args.save_index:
        print(f"   索引文件名: {args.index_filename}")
    print(f"   分块方式: {args.chunking_method}")
    
    # 创建文本分割器
    chunker = SemanticChunker(
        chunk_min_length=args.min_length,
        chunk_max_length=args.max_length,
        overlap_min_length=args.overlap_min,
        overlap_max_length=args.overlap_max,
        semantic_patterns=config.get("semantic_patterns"),
        enable_overlap=args.enable_overlap,
        chunking_method=args.chunking_method,
        chunk_by_length_config=chunk_by_length_config,
        chunk_by_paragraph_config=chunk_by_paragraph_config
    )
    
    # 构建完整的输入路径（优先使用相对于脚本的路径）
    input_path = os.path.join(script_dir, args.input)
    
    # 检查是否为单个文件
    if os.path.isfile(input_path) and input_path.lower().endswith('.md'):
        # 处理单个文件
        print("📄 检测到单个文件，开始处理...")
        chunks = chunker.process_file(input_path, args.output, args.save_index, args.index_filename)
        if chunks:
            print(f"✅ 处理完成，共生成 {len(chunks)} 个文本块")
        else:
            print("❌ 文件处理失败")
    elif os.path.isfile(args.input) and args.input.lower().endswith('.md'):
        # 如果提供了绝对路径或相对路径的文件
        print("📄 检测到单个文件，开始处理...")
        chunks = chunker.process_file(args.input, args.output, args.save_index, args.index_filename)
        if chunks:
            print(f"✅ 处理完成，共生成 {len(chunks)} 个文本块")
        else:
            print("❌ 文件处理失败")
    else:
        # 处理目录
        print("📁 检测到目录，开始批量处理...")
        # 对于输出目录也使用相对于脚本的路径
        output_path = args.output
        if not os.path.isabs(output_path):
            output_path = os.path.join(script_dir, output_path)
        chunker.process_directory(args.input, output_path, args.save_index, args.index_filename)


    print("=" * 40)
    print("🎉 文本分割工具执行完毕")

def process_all_documents(input_dir: str, output_dir: str, config_file: str = None):
    """
    处理目录中的所有文档
    
    Args:
        input_dir (str): 输入目录路径
        output_dir (str): 输出目录路径
        config_file (str): 配置文件路径
    """
    # 加载配置
    config = load_chunk_config(config_file) if config_file else {}
    
    # 应用配置
    chunk_min_length = config.get("chunk_min_length", 10)
    chunk_max_length = config.get("chunk_max_length", 150)
    overlap_min_length = config.get("overlap_min_length", 10)
    overlap_max_length = config.get("overlap_max_length", 50)
    semantic_patterns = config.get("semantic_patterns", None)
    enable_overlap = config.get("enable_overlap", False)
    save_chunk_index = config.get("save_chunk_index", True)
    chunk_index_filename = config.get("chunk_index_filename", "chunk_index.json")
    chunking_method = config.get("chunking_method", "semantic")
    chunk_by_length_config = config.get("chunk_by_length", {})
    chunk_by_paragraph_config = config.get("chunk_by_paragraph", {})
    
    # 创建文本分割器
    chunker = SemanticChunker(
        chunk_min_length=chunk_min_length,
        chunk_max_length=chunk_max_length,
        overlap_min_length=overlap_min_length,
        overlap_max_length=overlap_max_length,
        semantic_patterns=semantic_patterns,
        enable_overlap=enable_overlap,
        chunking_method=chunking_method,
        chunk_by_length_config=chunk_by_length_config,
        chunk_by_paragraph_config=chunk_by_paragraph_config
    )
    
    # 处理目录中的所有文档
    chunker.process_directory(input_dir, output_dir, save_chunk_index, chunk_index_filename)


if __name__ == "__main__":
    main()