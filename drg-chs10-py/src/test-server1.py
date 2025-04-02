from flask import Flask, request

app = Flask(__name__)


@app.route('/receive', methods=['POST'])
def receive_data():
    try:
        data = request.get_json()
        if not data:
            return "请求数据为空", 400
        for patient in data:
            vid = patient.get('vid')
            gender = patient.get('gender')
            age = patient.get('age')
            if vid is None or gender is None or age is None:
                return "请求数据格式错误，缺少必要字段", 400
            result = f"{vid}的性别为{gender}，年龄为{age}"
            return result, 200
    except Exception as e:
        return f"发生错误: {str(e)}", 500


if __name__ == '__main__':
    app.run(debug=True)
