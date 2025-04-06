from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/receive', methods=['POST'])
def receive_data():
    try:
        # 从请求中获取 JSON 数据
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求体为空"}), 400

        # 打印接收到的数据
        print("接收到的数据:")
        return jsonify({"message": "数据已成功接收", "data": data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
