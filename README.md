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
- [许可证](#许可证)

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
原始文档 → 文档转换 → 文本分块 → 数据合并 → JSON结果
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

## 直接使用

- 根据*_config.json*文件修改配置参数例如输入路径输出路径等等, 把需要处理的数据放在conversion_config.json中的default_input_path路径下, 运行convert_doc_to_md.py, 即可在default_output_path路径下生成结果文件
- 一般*_config.json的输入路径和逻辑上的上一个config.json的输出路径一致
- 默认输入路径为`raw_data`, 将数据放在`raw_data`目录下, 依次运行convert_doc_to_md.py, text_chunker.py, merge_json_files.py后, 即可得到result.json文件

### 使用Docker部署（推荐）

```bash
# 克隆项目代码
git clone <repository-url>
cd document-processor

# 创建必要目录
mkdir -p uploads processed temp

# 使用一键部署脚本
chmod +x docker_deploy.sh
./docker_deploy.sh
```

### 直接运行api服务

```bash
# 安装依赖
pip install -r requirements.txt
pip install markitdown[docx,pdf]

# 创建必要目录
mkdir -p uploads processed temp

# 启动服务
python app.py
```

## 安装部署

### Docker容器化部署

项目支持多种Docker部署方式：

1. **标准部署** - 使用默认配置
2. **国内网络优化部署** - 针对中国网络环境优化
3. **简化版部署** - 移除复杂配置，提高构建成功率
4. **生产环境部署** - 包含资源限制和性能优化

详细部署说明请参考[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)。

### 直接运行

```bash
# 1. 安装Python依赖
pip install -r requirements.txt

# 2. 安装文档处理额外依赖
pip install markitdown[docx,pdf]

# 3. 创建必要目录
mkdir -p uploads processed temp

# 4. 启动服务
python app.py
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

## 配置说明

### 环境变量
- `FLASK_APP`：Flask应用入口文件（默认：app.py）
- `FLASK_ENV`：运行环境（默认：production）

### 配置文件
- [conversion_config.json](file:///home/lynn/projects/filesfromWork/new_project/readFile/demo/conversion_config.json)：文档转换配置
- [chunk_config.json](file:///home/lynn/projects/filesfromWork/new_project/readFile/demo/chunk_config.json)：文本分块配置
- [merge_config.json](file:///home/lynn/projects/filesfromWork/new_project/readFile/demo/merge_config.json)：数据合并配置

### 目录说明
- `uploads/`：上传文件目录
- `processed/`：处理结果目录
- `temp/`：临时文件目录
- `raw_data/`：原始文档目录（示例）

## 目录结构

```
document-processor/
├── app.py                 # 主服务应用
├── convert_doc_to_md.py   # 文档转换模块
├── text_chunker.py        # 文本分块模块
├── merge_json_files.py    # 数据合并模块
├── requirements.txt       # Python依赖
├── Dockerfile            # Docker配置
├── docker-compose.yml    # Docker编排配置
├── docker_deploy.sh      # 部署脚本
├── conversion_config.json # 转换配置
├── chunk_config.json     # 分块配置
├── merge_config.json     # 合并配置
├── raw_data/             # 原始文档目录
├── uploads/              # 上传文件目录
├── processed/            # 处理结果目录
├── temp/                 # 临时文件目录
└── README.md             # 项目说明文档
```

## 开发指南

### 本地开发

```bash
# 1. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 2. 安装开发依赖
pip install -r requirements.txt
pip install markitdown[docx,pdf]

# 3. 运行开发服务器
python app.py
```

### 代码规范
- 遵循PEP 8代码规范
- 使用类型注解
- 编写单元测试

### 测试

```bash
# 运行单元测试
python -m pytest tests/

# 运行API测试
python test/test_api.py
```

## 故障排除

### 常见问题

1. **Docker构建失败**：
   - 检查网络连接
   - 配置Docker镜像加速器
   - 使用简化版部署配置

2. **依赖安装失败**：
   ```bash
   pip install --upgrade pip
   pip install markitdown[docx,pdf]
   ```

3. **服务无法启动**：
   - 检查端口是否被占用
   - 确认配置文件是否存在
   - 查看服务日志

### 查看日志

```bash
# Docker部署
docker compose logs -f

# 直接运行
tail -f app.log
```

## 许可证

本项目采用MIT许可证，详情请见[LICENSE](LICENSE)文件。