import json
import random
from datetime import datetime, timedelta

# 诊断信息列表
diagnoses = [
    {"diag_id": 1, "diag_code": "A00.0", "diag_name": "Hypertension"},
    {"diag_id": 2, "diag_code": "B01.1", "diag_name": "Diabetes"},
    {"diag_id": 3, "diag_code": "C02.2", "diag_name": "Cancer"},
    {"diag_id": 4, "diag_code": "D03.3", "diag_name": "Asthma"},
    {"diag_id": 5, "diag_code": "E04.4", "diag_name": "Arthritis"}
]

# 手术信息列表
surgeries = [
    {"oper_id": 1, "oper_code": "OP001", "oper_name": "Heart Surgery"},
    {"oper_id": 2, "oper_code": "OP002", "oper_name": "Lung Surgery"},
    {"oper_id": 3, "oper_code": "OP003", "oper_name": "Brain Surgery"},
    {"oper_id": 4, "oper_code": "OP004", "oper_name": "Knee Surgery"},
    {"oper_id": 5, "oper_code": "OP005", "oper_name": "Eye Surgery"}
]

# 生成随机日期
def random_date(start_date, end_date):
    days = (end_date - start_date).days
    random_days = random.randint(0, days)
    return (start_date + timedelta(days=random_days)).strftime("%Y-%m-%d")

# 生成 30 条测试数据
test_data = []
for vid in range(1, 31):
    gender = random.choice(["Male", "Female"])
    age = random.randint(18, 80)
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)
    admit_date = random_date(start_date, end_date)
    dis_date = random_date(datetime.strptime(admit_date, "%Y-%m-%d"), end_date)
    total_cost = round(random.uniform(500, 5000), 2)
    birth_weight = round(random.uniform(2, 4), 1)

    # 随机选择诊断信息
    num_diagnoses = random.randint(1, 3)
    selected_diagnoses = random.sample(diagnoses, num_diagnoses)

    # 随机选择手术信息
    num_surgeries = random.randint(0, 2)
    selected_surgeries = random.sample(surgeries, num_surgeries)

    patient_data = {
        "vid": vid,
        "gender": gender,
        "age": age,
        "admit_date": admit_date,
        "dis_date": dis_date,
        "total_cost": total_cost,
        "birth_weight": birth_weight,
        "diagnosis": selected_diagnoses,
        "surgery": selected_surgeries
    }
    test_data.append(patient_data)

# 将测试数据保存到 JSON 文件
with open('../data/test_data.json', 'w') as f:
    json.dump(test_data, f, indent=4)

print("测试数据已生成并保存到 test_data.json 文件中。")
    