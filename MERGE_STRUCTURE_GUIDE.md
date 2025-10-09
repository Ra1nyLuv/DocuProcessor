# 合并文件目录结构指南

本文档说明了修改后的文档处理服务中合并文件的目录结构。

## 目录结构变更

### 旧的目录结构
```
merged_data/
├── document1_merged.json
├── document2_merged.json
└── merged_index.json
```

### 新的目录结构
```
merged_data/
├── document1/
│   └── result.json
├── document2/
│   └── result.json
└── merged_index.json
```

## 变更说明

1. **为每个文档创建独立文件夹**：每个处理的文档现在都有自己的文件夹
2. **统一的结果文件名**：所有文档的结果文件都命名为`result.json`
3. **保持索引文件**：`merged_index.json`仍然在根目录下

## 优势

1. **更好的组织性**：每个文档的结果文件都在其专属目录中
2. **一致的命名**：所有结果文件都使用相同的文件名`result.json`
3. **易于扩展**：可以轻松地为每个文档添加更多相关文件

## API接口变更

### 单文档处理响应
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "result_file": "document1/result.json",
  "download_url": "/api/v1/download/550e8400-e29b-41d4-a716-446655440000/document1%2Fresult.json"
}
```

### 批量处理响应
```json
{
  "task_id": "660e8400-e29b-41d4-a716-446655440001",
  "status": "completed",
  "result_files": [
    "document1/result.json",
    "document2/result.json"
  ],
  "download_urls": [
    "/api/v1/download/660e8400-e29b-41d4-a716-446655440001/document1%2Fresult.json",
    "/api/v1/download/660e8400-e29b-41d4-a716-446655440001/document2%2Fresult.json"
  ]
}
```

## 使用示例

### 下载结果文件
```bash
# 下载单个结果文件
curl -o result.json "http://localhost:5000/api/v1/download/{task_id}/document1%2Fresult.json"

# 或者直接访问URL（浏览器中）
http://localhost:5000/api/v1/download/{task_id}/document1/result.json
```

### Python客户端示例
```python
import requests
from urllib.parse import quote

def download_result(task_id, filename):
    """下载处理结果"""
    # URL编码文件路径
    encoded_filename = quote(filename)
    response = requests.get(f"http://localhost:5000/api/v1/download/{task_id}/{encoded_filename}")
    
    if response.status_code == 200:
        # 保存文件
        with open("result.json", "wb") as f:
            f.write(response.content)
        print("文件下载成功")
    else:
        print(f"下载失败: {response.status_code}")

# 使用示例
download_result("task_id", "document1/result.json")
```

## 注意事项

1. **URL编码**：在API调用中，路径分隔符`/`需要编码为`%2F`
2. **文件访问**：在服务器端，可以通过`document1/result.json`直接访问文件
3. **向后兼容**：此变更不会影响现有的API接口，只是改变了内部文件组织结构

通过这种新的目录结构，文档处理服务能够更好地组织和管理处理结果文件。