from flask import Flask, request

app = Flask(__name__)

@app.route('/receive', methods=['POST'])
def receive_data():
    try:
        data = request.get_json()
        if not data:
            return "请求数据为空", 400
        for patient in data:
            if not is_data_valid(patient):
                return "请求数据格式错误，缺少必要字段", 400
            result = process_patient_data(patient)
            return result, 200
    except Exception as e:
        return f"发生错误: {str(e)}", 500

def is_data_valid(patient):
    """
    检查单个患者数据是否包含必要字段
    :param patient: 单个患者的信息字典
    :return: 若数据有效返回 True，否则返回 False
    """
    required_fields = [
        "vid", "gender", "age", "admit_date", "dis_date",
        "total_cost", "birth_weight", "diagnosis", "surgery"
    ]
    for field in required_fields:
        if field not in patient:
            return False

    if not isinstance(patient["vid"], int):
        return False
    if patient["gender"] not in ["Male", "Female"]:
        return False
    if not isinstance(patient["age"], int):
        return False
    try:
        datetime.strptime(patient["admit_date"], '%Y-%m-%d')
        datetime.strptime(patient["dis_date"], '%Y-%m-%d')
    except ValueError:
        return False
    if not isinstance(patient["total_cost"], (int, float)):
        return False
    if not isinstance(patient["birth_weight"], (int, float)):
        return False

    if not isinstance(patient["diagnosis"], list) or len(patient["diagnosis"]) == 0:
        return False
    diagnosis_required_fields = ["diag_id", "diag_code", "diag_name"]
    for diagnosis in patient["diagnosis"]:
        for field in diagnosis_required_fields:
            if field not in diagnosis:
                return False
        if not isinstance(diagnosis["diag_id"], int):
            return False
        if not isinstance(diagnosis["diag_code"], str):
            return False
        if not isinstance(diagnosis["diag_name"], str):
            return False

    if not isinstance(patient["surgery"], list) or len(patient["surgery"]) == 0:
        return False
    surgery_required_fields = ["oper_id", "oper_code", "oper_name"]
    for surgery in patient["surgery"]:
        for field in surgery_required_fields:
            if field not in surgery:
                return False
        if not isinstance(surgery["oper_id"], int):
            return False
        if not isinstance(surgery["oper_code"], str):
            return False
        if not isinstance(surgery["oper_name"], str):
            return False

    return True

def drg_grouper(data):
    ...


if __name__ == '__main__':
    app.run(debug=True)
