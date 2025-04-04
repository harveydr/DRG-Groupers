from datetime import timedelta
import json
import ijson
import receive_api_data
from flask import Flask, request, jsonify

# 本地导入
from data_classes import Diagnosis, Surgery, Patient
from drg_grouper import DrgGrouper
from get_patient import get_patient

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

@app.route('/receive', methods=['POST'])
def receive_data():
    try:
        # 从请求中获取 JSON 数据
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求体为空"}), 400

        # 检查接收到的数据是否有效
        if not is_data_valid(data):
            return jsonify({"error": "接收到的数据无效"}), 400

        # 封装成Patients对象列表
        patient = get_patient(data)
        # 处理数据并返回结果
        result = process_batch(patient)
        # 明确指定响应的字符编码为 utf-8
        resp = jsonify(result)
        resp.headers['Content-Type'] = 'application/json; charset=utf-8'
        return resp, 200
    except Exception as e:
        # 返回详细的错误信息
        return jsonify({"error": f"处理请求时发生错误: {str(e)}"}), 500

def is_data_valid(patient):
    """
    检查单个患者数据是否包含必要字段
    :param patient: 单个患者的信息字典
    :return: 若数据有效返回 True，否则返回 False
    """
    return True

def process_batch(patient: Patient):
    """
    处理一批数据
    :param batch: 包含多条患者数据的列表
    :return: 处理结果
    """
    drg = DrgGrouper(patient)
    result = drg.classify_into_mdc()
    return result


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000, debug=True)