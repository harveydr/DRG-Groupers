import json
from collections import defaultdict
from pandas import read_json

def doctor_rules(group_rules: list[dict]):
    """
    1. 统计分组规则的入组逻辑类型；
    """
    statistics = defaultdict(list)
    for mdc in group_rules:
        for adrg in mdc["包含的ADRG"]:
            logic_str = adrg["入组逻辑"]
            statistics[logic_str].append(adrg["ADRG编码"])

    with open("../rules/statistics.json", 'w', encoding='utf-8') as json_file:
        json.dump(statistics, json_file, ensure_ascii=False, indent=4)

    print("统计完成，分析结果已写入到 rules/statistics.json。")

if __name__ == "__main__":
    with open("../rules/group_rules.json", 'r', encoding='utf-8') as f:
        group_rules = json.load(f)
    
    doctor_rules(group_rules)