from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/bmi', methods=['POST'])
def calculate_bmi():
    try:
        data = request.get_json()
        if not data or 'weight' not in data or 'height' not in data:
            return jsonify({"error": "请求数据必须包含 'weight' 和 'height' 字段"}), 400

        weight = float(data['weight'])
        height = float(data['height'])

        if weight <= 0 or height <= 0:
            return jsonify({"error": "体重和身高必须是正数"}), 400

        bmi = weight / (height ** 2)
        result = {
            "bmi": bmi,
            "interpretation": interpret_bmi(bmi)
        }
        return jsonify(result), 200
    except ValueError:
        return jsonify({"error": "体重和身高必须是有效的数字"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def interpret_bmi(bmi):
    if bmi < 18.5:
        return "体重过轻"
    elif 18.5 <= bmi < 24:
        return "正常范围"
    elif 24 <= bmi < 28:
        return "超重"
    else:
        return "肥胖"


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)