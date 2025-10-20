# 文档处理服务API使用示例

本文档提供了文档处理服务的详细API使用示例，结合实际操作经验，帮助您快速上手使用该服务。

## 目录

- [服务启动](#服务启动)
- [健康检查](#健康检查)
- [单文档处理示例](#单文档处理示例)
- [批量文档处理示例](#批量文档处理示例)
- [处理结果下载示例](#处理结果下载示例)
- [错误处理示例](#错误处理示例)
- [Python客户端示例](#python客户端示例)

## 服务启动

### Docker方式启动
```bash
# 创建必要目录
mkdir -p uploads processed temp

# 启动服务
docker-compose up -d
```

### 直接运行方式启动
```bash
# 安装依赖
pip install -r requirements.txt
pip install markitdown[docx,pdf]

# 创建必要目录
mkdir -p uploads processed temp

# 启动服务
python app.py
```

## 健康检查

在使用API之前，建议先检查服务是否正常运行：

```bash
curl http://localhost:5000/health
```

**成功响应**：
```json
{
  "status": "healthy",
  "timestamp": "2023-07-19T10:30:00.123456"
}
```

## 单文档处理示例

### 1. 处理包含中文文件名的文档
```bash
curl -X POST -F "file=@大数据获取与预处理项目实践任务书.md" http://localhost:5000/api/v1/process-document
```

**成功响应**：
```json
{
  "task_id": "c6952912-6437-4cf5-874d-74811d1dfe18",
  "status": "completed",
  "result_file": "大数据获取与预处理项目实践任务书/result.json",
  "download_url": "/api/v1/download/c6952912-6437-4cf5-874d-74811d1dfe18/大数据获取与预处理项目实践任务书/result.json"
}
```

### 2. 处理TXT文档
```bash
curl -X POST -F "file=@自然语言处理课设答辩稿.txt" http://localhost:5000/api/v1/process-document
```

### 3. 处理DOCX文档
```bash
curl -X POST -F "file=@example.docx" http://localhost:5000/api/v1/process-document
```

## 批量文档处理示例

### 1. 批量处理多个文档
```bash
curl -X POST \
  -F "files=@大数据获取与预处理项目实践任务书.md" \
  -F "files=@自然语言处理课设答辩稿.txt" \
  -F "files=@example.docx" \
  http://localhost:5000/api/v1/batch-process
```

**成功响应**：
```json
{
  "task_id": "660e8400-e29b-41d4-a716-446655440001",
  "status": "completed",
  "result_files": [
    "大数据获取与预处理项目实践任务书/result.json", 
    "自然语言处理课设答辩稿/result.json", 
    "example/result.json"
  ],
  "download_urls": [
    "/api/v1/download/660e8400-e29b-41d4-a716-446655440001/大数据获取与预处理项目实践任务书/result.json",
    "/api/v1/download/660e8400-e29b-41d4-a716-446655440001/自然语言处理课设答辩稿/result.json",
    "/api/v1/download/660e8400-e29b-41d4-a716-446655440001/example/result.json"
  ]
}
```

## 处理结果下载示例

### 1. 下载单个处理结果
```bash
# 使用返回的download_url直接下载（支持中文URL）
curl -o result.json "http://localhost:5000/api/v1/download/c6952912-6437-4cf5-874d-74811d1dfe18/大数据获取与预处理项目实践任务书/result.json"
```

### 2. 下载批量处理结果
```bash
# 直接使用包含中文的URL下载
curl -o 大数据获取与预处理项目实践任务书_result.json "http://localhost:5000/api/v1/download/660e8400-e29b-41d4-a716-446655440001/大数据获取与预处理项目实践任务书/result.json"
```

### 3. 使用wget下载
```bash
wget -O result.json "http://localhost:5000/api/v1/download/c6952912-6437-4cf5-874d-74811d1dfe18/大数据获取与预处理项目实践任务书/result.json"
```

## 错误处理示例

### 1. 文件大小超限
```bash
curl -X POST -F "file=@large_file.pdf" http://localhost:5000/api/v1/process-document
```

**错误响应**：
```json
{
  "error": "文件大小超过限制（最大50MB）"
}
```

### 2. 不支持的文件类型
```bash
curl -X POST -F "file=@image.jpg" http://localhost:5000/api/v1/process-document
```

**错误响应**：
```json
{
  "error": "不支持的文件类型"
}
```

### 3. 未上传文件
```bash
curl -X POST http://localhost:5000/api/v1/process-document
```

**错误响应**：
```json
{
  "error": "没有上传文件"
}
```

## Python客户端示例

### 1. 单文档处理客户端
```python
import requests
import json

# 服务地址
BASE_URL = "http://localhost:5000"

def process_single_document(file_path):
    """处理单个文档"""
    with open(file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(f"{BASE_URL}/api/v1/process-document", files=files)
    
    if response.status_code == 200:
        result = response.json()
        print(f"任务ID: {result['task_id']}")
        print(f"结果文件: {result['result_file']}")
        print(f"下载URL: {result['download_url']}")
        return result
    else:
        print(f"处理失败: {response.text}")
        return None

def download_result(download_url, save_path):
    """下载处理结果"""
    response = requests.get(f"{BASE_URL}{download_url}")
    
    if response.status_code == 200:
        with open(save_path, 'wb') as f:
            f.write(response.content)
        print(f"文件已保存到: {save_path}")
    else:
        print(f"下载失败: {response.text}")

# 使用示例
if __name__ == "__main__":
    # 处理单个文档
    result = process_single_document("大数据获取与预处理项目实践任务书.md")
    if result:
        # 直接使用返回的下载URL
        download_result(result['download_url'], "大数据获取与预处理项目实践任务书_result.json")
```

### 2. 批量文档处理客户端
```python
import requests
import json
import os

# 服务地址
BASE_URL = "http://localhost:5000"

def process_batch_documents(file_paths):
    """批量处理文档"""
    files = [('files', (os.path.basename(path), open(path, 'rb'))) for path in file_paths]
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/batch-process", files=files)
        
        # 关闭所有文件
        for _, (_, file_obj) in files:
            file_obj.close()
        
        if response.status_code == 200:
            result = response.json()
            print(f"批量任务ID: {result['task_id']}")
            print(f"结果文件数量: {len(result['result_files'])}")
            return result
        else:
            print(f"批量处理失败: {response.text}")
            return None
    except Exception as e:
        # 确保文件被关闭
        for _, (_, file_obj) in files:
            file_obj.close()
        print(f"发生错误: {str(e)}")
        return None

def download_batch_results(task_id, download_urls, save_dir):
    """下载批量处理结果"""
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    for i, download_url in enumerate(download_urls):
        response = requests.get(f"{BASE_URL}{download_url}")
        
        if response.status_code == 200:
            # 从URL中提取文件名
            filename = download_url.split('/')[-2] + "_result.json"
            save_path = os.path.join(save_dir, filename)
            with open(save_path, 'wb') as f:
                f.write(response.content)
            print(f"文件已保存到: {save_path}")
        else:
            print(f"下载失败: {response.text}")

# 使用示例
if __name__ == "__main__":
    # 批量处理文档
    file_paths = [
        "大数据获取与预处理项目实践任务书.md", 
        "自然语言处理课设答辩稿.txt"
    ]
    result = process_batch_documents(file_paths)
    
    if result:
        # 直接使用返回的下载URL列表
        download_batch_results(
            result['task_id'], 
            result['download_urls'], 
            "batch_results"
        )
```

## 实际使用经验总结

### 1. 文件大小限制
- 默认限制：50MB
- 超过限制会返回413错误
- 如需处理更大文件，可修改app.py中的`MAX_CONTENT_LENGTH`参数

### 2. 中文文件名处理
- 现在API支持直接使用包含中文字符的URL，无需额外编码
- 返回的下载URL中直接显示中文字符，更加直观易读
- 下载时可直接使用返回的URL，系统会自动处理

### 3. 支持的文件类型
- 文本文件：txt
- 办公文档：docx, doc
- PDF文档：pdf
- 网页文件：html, htm
- 演示文稿：pptx
- 电子表格：xlsx
- Markdown文件：md

### 4. 处理时间
- 小文件（<1MB）：通常在几秒内完成
- 中等文件（1-10MB）：可能需要几十秒
- 大文件（>10MB）：可能需要几分钟

### 5. 最新改进
- API返回的URL中直接显示中文字符，提高可读性
- 下载时支持直接使用包含中文的URL
- 简化了客户端处理逻辑，无需手动进行URL编码

在实际使用中，请根据具体需求调整参数和处理逻辑.