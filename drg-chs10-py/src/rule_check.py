import json
from collections import defaultdict
import pandas as pd
import pandas as pd
# 加载adrg.json文件
with open('../config/adrg.json', 'r', encoding='utf-8') as f:
    adrg_data = json.load(f)

# 对于主手术入组的ICD编码，找到对应的ADRG编码
main_oper_to_adrg = defaultdict(list)
# 对于主诊断入组的ICD编码，找到对应的ADRG编码
main_diag_to_adrg = defaultdict(list)
# 对于联合手术入组的ICD编码，找到对应的ADRG编码
joint_oper_to_adrg = defaultdict(list)
# 对于诊断+手术入组的ICD编码，找到对应的ADRG编码
diag_oper_to_adrg = defaultdict(list)


# 遍历每个ADRG
for adrg in adrg_data:
    adrg_code = adrg["ADRG编码"]
    adrg_name = adrg["ADRG名称"]

    if adrg["入组类型"] == "手术":
        for operation in adrg["入组条件"]["主要手术"]:
            main_oper_to_adrg[operation["ICD编码"]].append((adrg_code, adrg_name))
    elif adrg["入组类型"] == "诊断":
        for diagnosis in adrg["入组条件"]["主要诊断"]:
            main_diag_to_adrg[diagnosis["ICD编码"]].append((adrg_code, adrg_name))
    elif adrg["入组类型"] == "联合手术":
        for operation1 in adrg["入组条件"]["手术操作1"]:
            for operation2 in adrg["入组条件"]["手术操作2"]:
                operation1_code = operation1["ICD编码"]
                operation2_code = operation2["ICD编码"]
                joint_key = (operation1_code, operation2_code)
                joint_oper_to_adrg[joint_key].append((adrg_code, adrg_name))
    elif adrg["入组类型"] == "诊断+手术":
        for diagnosis in adrg["入组条件"]["主要诊断"]:
            for operation in adrg["入组条件"]["主要手术"]:
                diag_code = diagnosis["ICD编码"]
                oper_code = operation["ICD编码"]
                diag_oper_key = (diag_code, oper_code)
                diag_oper_to_adrg[diag_oper_key].append((adrg_code, adrg_name))

# 找出重复入组的ICD或ICD组合
def find_duplicate_mappings(mapping_dict):
    duplicate_mappings = {}
    for key, values in mapping_dict.items():
        if len(values) > 1:
            duplicate_mappings[key] = values
    return duplicate_mappings

# 找出主手术重复入组的ICD编码
duplicate_main_oper = find_duplicate_mappings(main_oper_to_adrg)
# 找出主诊断重复入组的ICD编码
duplicate_main_diag = find_duplicate_mappings(main_diag_to_adrg)
# 找出联合手术重复入组的ICD编码组合
duplicate_joint_oper = find_duplicate_mappings(joint_oper_to_adrg)
# 找出诊断+手术重复入组的ICD编码组合
duplicate_diag_oper = find_duplicate_mappings(diag_oper_to_adrg)
# 创建一个空的DataFrame来存储结果
results = []

# 主手术重复入组的ICD编码
for icd, adrgs in duplicate_main_oper.items():
    for adrg in adrgs:
        results.append({
            '入组类型': '主手术',
            'ICD编码/组合': icd,
            '重复入组的ADRG编码': adrg[0],
            '重复入组的ADRG名称': adrg[1]
        })

# 主诊断重复入组的ICD编码
for icd, adrgs in duplicate_main_diag.items():
    for adrg in adrgs:
        results.append({
            '入组类型': '主诊断',
            'ICD编码/组合': icd,
            '重复入组的ADRG编码': adrg[0],
            '重复入组的ADRG名称': adrg[1]
        })

# 联合手术重复入组的ICD编码组合
for icd_pair, adrgs in duplicate_joint_oper.items():
    for adrg in adrgs:
        results.append({
            '入组类型': '联合手术',
            'ICD编码/组合': icd_pair,
            '重复入组的ADRG编码': adrg[0],
            '重复入组的ADRG名称': adrg[1]
        })

# 诊断+手术重复入组的ICD编码组合
for icd_pair, adrgs in duplicate_diag_oper.items():
    for adrg in adrgs:
        results.append({
            '入组类型': '诊断+手术',
            'ICD编码/组合': icd_pair,
            '重复入组的ADRG编码': adrg[0],
            '重复入组的ADRG名称': adrg[1]
        })

# 将结果转换为DataFrame
df = pd.DataFrame(results)

# 保存为XLSX文件
df.to_excel('../results/duplicate_mappings.xlsx', index=False)

