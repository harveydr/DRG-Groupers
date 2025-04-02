import requests
import json

# 服务器的接口地址
url = 'http://127.0.0.1:5000/receive'

try:
    # 从 JSON 文件中读取测试数据
    with open('../data/test_data.json', 'r') as f:
        test_data = json.load(f)

    # 每次最多发起 10 条请求
    batch_size = 10
    for i in range(0, len(test_data), batch_size):
        batch = test_data[i:i + batch_size]
        for data in batch:
            try:
                # 发送 POST 请求
                response = requests.post(url, json=[data])
                if response.status_code == 200:
                    print(f"请求成功，响应内容: {response.text}")
                else:
                    print(f"请求失败，状态码: {response.status_code}，响应内容: {response.text}")
                    break  # 若请求失败，停止当前批次的请求
            except requests.RequestException as e:
                print(f"请求发生错误: {e}")
                break  # 若发生请求异常，停止当前批次的请求

except FileNotFoundError:
    print("未找到测试数据文件 '../data/test_data.json'。")
except json.JSONDecodeError:
    print("测试数据文件格式不是有效的 JSON。")
    