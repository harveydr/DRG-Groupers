import redis

# 连接到本地 Redis 服务
r = redis.Redis(host='localhost', port=6379, db=0)
try:
    # 执行一个简单的 PING 命令来测试连接
    response = r.ping()
    if response:
        print("成功连接到 Redis 服务")
    else:
        print("无法连接到 Redis 服务")
except redis.exceptions.ConnectionError as e:
    print(f"连接错误: {e}")