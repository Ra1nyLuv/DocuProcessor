```
curl -X POST http://localhost:12995/api/create -F "files=@docuprocessor/raw_data/自然语言处理课设答辩稿.md" -F 'json_data={"user_id":"test_user","kb_name":"test_kb","description":"测试知识库","fileconfigs":{"自然语言处理课设答辩稿.md":{"filename":"自然语言处理课设答辩稿.md","description":"测试文件","chunk_size":500,"index_size":200,"overlap":0.1,"split_flag":[],"filters":[],"default":true,"re_flags":false,"re_mode":0,"summary_enhancement":true,"qa_enhancement":true,"image_enhancement":false,"keyword_enhancement":true}}}'
```

此命令成功运行, MySQL和Milvus数据库数据一切正常.
docuprocessor服务运行成功. 数据自动清除.
数据增强部分除图像增强之外也一切正常.