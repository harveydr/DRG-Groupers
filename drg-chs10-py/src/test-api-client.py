import requests

# 替换为实际的服务器 IP 地址和端口
server_url = 'http://127.0.0.1:5000/bmi'

# 示例数据
test_data = [
    {"weight": 50, "height": 1.6},
    {"weight": 70, "height": 1.75},
    {"weight": 90, "height": 1.8},
    {"weight": -10, "height": 1.7},  # 测试无效数据
    {"weight": 80, "height": 0}      # 测试无效数据
]

for data in test_data:
    try:
        response = requests.post(server_url, json=data)
        if response.status_code == 200:
            result = response.json()
            print(f"输入数据: {data}")
            print(f"计算结果: BMI = {result['bmi']}, 解读: {result['interpretation']}")
        else:
            error = response.json()
            print(f"输入数据: {data}")
            print(f"请求失败，状态码: {response.status_code}, 错误信息: {error['error']}")
    except requests.RequestException as e:
        print(f"请求发生错误: {e}")
    print("-" * 50)
    