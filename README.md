# 文档处理服务

[![Python](https://img.shields.io/badge/python-3.10-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-supported-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 目录

- [项目简介](#项目简介)
- [功能特性](#功能特性)
- [技术架构](#技术架构)
- [系统要求](#系统要求)
- [快速开始](#快速开始)
- [安装部署](#安装部署)
- [API接口](#api接口)
- [配置说明](#配置说明)
- [目录结构](#目录结构)
- [开发指南](#开发指南)
- [故障排除](#故障排除)

## 项目简介

文档处理服务是一个完整的文档处理解决方案，能够将多种格式的文档（如.docx、.pdf等）转换为结构化的JSON格式。该服务整合了文档转换、文本分块和数据合并三个核心处理模块，提供RESTful API接口，支持单文档和批量文档处理。

## 功能特性

- **多格式支持**：支持TXT、PDF、DOCX、DOC、HTML、HTM、PPTX、XLSX等多种文档格式
- **文档转换**：将各种格式文档转换为Markdown格式
- **智能分块**：基于语义的文本分块算法，支持重叠分块
- **数据合并**：将文本块与图片信息合并为最终的JSON结构
- **RESTful API**：提供完整的API接口，支持单文档和批量处理
- **容器化部署**：支持Docker容器化部署，提供多种部署方案
- **健康检查**：内置健康检查接口，便于监控服务状态
- **错误处理**：完善的错误处理机制，提供详细的错误信息

## 技术架构

### 核心组件
- **Web框架**：Flask
- **文档处理库**：markitdown
- **PDF处理库**：PyMuPDF
- **容器化**：Docker & Docker Compose

### 处理流程
```
原始文档 → 文档转换(convert_doc_to_md.py) → 文本分块(text_chunker.py) → 数据合并(merge_json_files.py) → JSON结果
```

## 系统要求

### 最低配置
- Python 3.10或以上版本
- 至少4GB内存
- 至少2GB磁盘空间

### 推荐配置
- Python 3.10+
- 8GB内存
- 10GB磁盘空间
- Docker 18.06.0+（用于容器化部署）

## 快速开始

### 手动使用独立功能
### 可独立使用格式转换, 分块, 整理合并功能
- 根据`*_config.json`文件修改配置参数例如输入路径输出路径等等, 把需要处理的数据放在`conversion_config.json`的`default_input_path`路径下 
- 运行`convert_doc_to_md.py`, 即可在`default_output_path`路径下生成结果文件
- 一般`*_config.json`的输入路径应该与逻辑上的上一个`*_config.json`的输出路径一致, 例如`conversion_config.json`的`default_output_path`路径应该与`chunk_config.json`的`default_input_path`路径一致
- 默认输入路径为`raw_data`, 将数据放在`raw_data`目录下, 依次运行`convert_doc_to_md.py`, `text_chunker.py`, `merge_json_files.py`后, 即可得到最终的`result.json`文件


### Docker容器化部署运行
**标准部署** 
- 使用docker运行
`docker build -t document-processor .` 
- 或者使用docker-compose启动服务 
`docker-compose up -d`

**启动服务**:
- docker: 
`docker run -d -p 5000:5000 document-processor`
- docker-compose:
`docker-compose up -d`

### 本地部署运行
```bash
# 1. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows
# 或
conda activate myenv
# 2. 安装开发依赖
pip install -r requirements.txt
pip install markitdown[docx,pdf]

# 3. 运行开发服务器
python app.py
# 或
flask run
```


## API接口

### 健康检查
```
GET /health
```

### 单文档处理
```
POST /api/v1/process-document
参数：file（要处理的文档文件）
```

### 批量文档处理
```
POST /api/v1/batch-process
参数：files（要处理的文档文件列表）
```

### 下载处理结果
```
GET /api/v1/download/<task_id>/<filename>
参数：
- task_id：任务ID
- filename：结果文件名
```

## API使用

服务提供以下RESTful API接口：

### 健康检查

```bash
curl http://localhost:5000/health
```

### 单文档处理

```bash
curl -X POST -F "file=@document.docx" http://localhost:5000/api/v1/process-document
```

### 批量文档处理

```bash
curl -X POST \
  -F "files=@doc1.docx" \
  -F "files=@doc2.pdf" \
  http://localhost:5000/api/v1/batch-process
```

### 下载处理结果

```bash
# 注意：文件路径需要进行URL编码
curl -o result.json "http://localhost:5000/api/v1/download/{task_id}/{url_encoded_file_path}"
```

详细使用示例请参考 [API_USAGE_EXAMPLES.md](API_USAGE_EXAMPLES.md)。

## 配置说明

### 环境变量
- `FLASK_APP`：Flask应用入口文件（默认：app.py）
- `FLASK_ENV`：运行环境（默认：production）

###
l 配置文件
- [conversion_config.json](file:///home/lynn/projects/filesfromWork/new_project/readFile/demo/conversion_config.json)：文档转换配置
- [chunk_config.json](file:///home/lynn/projects/filesfromWork/new_project/readFile/demo/chunk_config.json)：文本分块配置
- [merge_config.json](file:///home/lynn/projects/filesfromWork/new_project/readFile/demo/merge_config.json)：数据合并配置

### 目录说明
- `uploads/`：上传文件目录
- `processed/`：处理结果目录
- `temp/`：临时文件目录
- `raw_data/`：原始文档目录（示例）