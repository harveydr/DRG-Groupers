import json
from collections import defaultdict
import pandas as pd
import pandas as pd


def reverse_mappings(adrg_rules: list) -> dict:
    """
    反向映射ADRG入组规则，将ICD编码映射到对应的ADRG编码和名称。
    :param adrg_rules: ADRG入组规则列表
    :return: 反向映射字典
    """
    mappings = {
        "手术": defaultdict(list),
        "诊断": defaultdict(list),
        "联合手术": defaultdict(list),
        "诊断+手术": defaultdict(list)
    }
    # 遍历每个ADRG规则
    for adrg in adrg_rules:
        adrg_code, adrg_name = adrg["ADRG编码"], adrg["ADRG名称"]
        group_type = adrg["入组类型"]
        conditions = adrg["入组条件"]

        if group_type == "手术":
            for operation in conditions["主要手术"]:
                mappings["手术"][operation["ICD编码"]].append((adrg_code, adrg_name))
        elif group_type == "诊断":
            for diagnosis in conditions["主要诊断"]:
                mappings["诊断"][diagnosis["ICD编码"]].append((adrg_code, adrg_name))
        elif group_type == "联合手术":
            for op1, op2 in zip(conditions["手术操作1"], conditions["手术操作2"]):
                mappings["联合手术"][(op1["ICD编码"], op2["ICD编码"])].append((adrg_code, adrg_name))
        elif group_type == "诊断+手术":
            for diag, op in zip(conditions["主要诊断"], conditions["主要手术"]):
                mappings["诊断+手术"][(diag["ICD编码"], op["ICD编码"])].append((adrg_code, adrg_name))

    return mappings

def find_duplicates(mappings):
    """找出重复的映射"""
    return {k: v for k, v in mappings.items() if len(v) > 1}

def generate_results(duplicates):
    """生成结果数据"""
    results = []
    for group_type, mappings in duplicates.items():
        for key, adrgs in mappings.items():
            for adrg in adrgs:
                results.append({
                    '入组类型': group_type,
                    'ICD编码/组合': key,
                    '重复入组的ADRG编码': adrg[0],
                    '重复入组的ADRG名称': adrg[1]
                })
    return results

def doctor_adrg_rules(adrg_rules: list):
    """判断ADRG入组规则是否有重复入组的问题"""
    mappings = reverse_mappings(adrg_rules)
    duplicates = {k: find_duplicates(v) for k, v in mappings.items()}
    results = generate_results(duplicates)
    return results

def doctor_mdc_rules(mdc_rules: list):
    """判断MDC入组规则是否有重复入组的问题"""
    pass

if __name__ == '__main__':
    # 加载adrg.json文件
    with open('../config/adrg.json', 'r', encoding='utf-8') as f:
        adrg_data = json.load(f)
    result = doctor_adrg_rules(adrg_data)
    pd.DataFrame(result).to_excel('results/ADRG分组规则分析.xlsx', index=False)

