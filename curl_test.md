## 验证docuprocessor服务的curl命令示例
``` shell
cd /home/lynn/projects/filesfromWork/new_project/docuprocessor && curl -s -X POST -F "file=@raw_data/数据可视化实验报告.docx" http://localhost:5000/api/v1/process-document | jq

```


## 验证项目完整数据流向的curl命令示例
### 无图片文档测试.
``` shell
curl -X POST http://localhost:12995/api/create -F "files=@docuprocessor/raw_data/自然语言处理课设答辩稿.md" -F 'json_data={"user_id":"test_user","kb_name":"test_kb","description":"测试知识库","fileconfigs":{"自然语言处理课设答辩稿.md":{"filename":"自然语言处理课设答辩稿.md","description":"测试文件","chunk_size":500,"index_size":200,"overlap":0.1,"split_flag":[],"filters":[],"default":true,"re_flags":false,"re_mode":0,"summary_enhancement":true,"qa_enhancement":true,"image_enhancement":false,"keyword_enhancement":true}}}' | jq .
```
##### 此命令成功运行, MySQL和Milvus数据库数据一切正常.
##### docuprocessor服务运行成功. 数据自动清理.
##### 数据增强部分除图像增强之外(无图片文档, 未启动图像增强)一切正常.

### 带图片文档测试.
``` shell
curl -X POST http://localhost:12995/api/create -F "files=@docuprocessor/raw_data/数据可视化实验报告.docx" -F 'json_data={"user_id":"test_user","kb_name":"test_kb_with_images","description":"测试知识库","fileconfigs":{"数据可视化实验报告.docx":{"filename":"数据可视化实验报告.docx","description":"带图片测试文件","chunk_size":500,"index_size":200,"overlap":0.1,"split_flag":[],"filters":[],"default":true,"re_flags":false,"re_mode":0,"summary_enhancement":true,"qa_enhancement":true,"image_enhancement":true,"keyword_enhancement":true}}}' | jq .
```

``` shell
curl -X POST http://localhost:12995/api/create -F "files=@docuprocessor/raw_data/大数据综合项目课程设计计划书-22级.docx" -F 'json_data={"user_id":"test_user","kb_name":"test_kb_with_images_2","description":"测试知识库","fileconfigs":{"大数据综合项目课程设计计划书-22级.docx":{"filename":"大数据综合项目课程设计计划书-22级.docx","description":"带图片测试文件2","chunk_size":500,"index_size":200,"overlap":0.1,"split_flag":[],"filters":[],"default":true,"re_flags":false,"re_mode":0,"summary_enhancement":true,"qa_enhancement":true,"image_enhancement":true,"keyword_enhancement":true}}}' | jq .
```