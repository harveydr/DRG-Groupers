import requests
import json
import os

# 服务器的接口地址
api_drg_grouper_url = 'http://127.0.0.1:5000/receive'

try:
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # 构建测试数据文件的绝对路径
    file_path = os.path.join(script_dir, '../../data/test_data.json')
    # 从 JSON 文件中读取测试数据
    with open(file_path, 'r') as f:
        test_data = json.load(f)

    # 遍历 JSON 数组，每次请求发送单条数据
    for data in test_data:
        response = requests.post(api_drg_grouper_url, json=data)
        # 设置响应的编码为 UTF-8
        response.encoding = 'utf-8'
        print(f"响应状态码: {response.status_code}，响应内容: {response.text}")

except FileNotFoundError:
    print("未找到测试数据文件。")
except json.JSONDecodeError:
    print("测试数据文件格式不是有效的 JSON。")
