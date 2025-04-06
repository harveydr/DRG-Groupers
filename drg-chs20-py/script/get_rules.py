import pandas as pd
import re
import json
from collections import defaultdict


def remove_number(df: pd.DataFrame):
    """去除从PDF复制过来的文本中的页码，页码的分布特征是只在某些行的行尾。"""
    # 存储提取的页码
    extracted_page_nums = []
    # 存储清理后的数据
    cleaned_data = []

    try:
        for _, row in df.iterrows():
            line = str(row.iloc[0])  # 强制转换为字符串
            # 提取行尾的页码
            page_nums = re.findall(r'(?<![\d.*+xX])([4-9]\d|[1-9]\d{2}|10\d{2}|11[0-3]\d)(?!\d)$', line)
            extracted_page_nums.extend(page_nums)
            # 去除行尾的页码
            cleaned_line = re.sub(r'(?<![\d.*+xX])([4-9]\d|[1-9]\d{2}|10\d{2}|11[0-3]\d)(?!\d)$', '', line)
            cleaned_data.append([cleaned_line])

        # 打印提取的页码
        print("提取到的页码：", extracted_page_nums, "\n>>>请检查是否有误，若无误请按下回车继续。")
        input()

        # 返回清理后的数据，并保留列名
        cleaned_df = pd.DataFrame(cleaned_data, columns=["内容"])
        return cleaned_df

    except Exception as e:
        print(f"去除文本中的页码时发生未知错误：{e}")
        return df  # 发生错误时返回原始 DataFrame


def handle_abnormal_linebreak(df: pd.DataFrame):
    """处理PDF中粘贴过来的异常换行的字符串"""
    # 检查DataFrame是否包含'内容'列
    if "内容" not in df.columns:
        raise ValueError("输入的DataFrame必须包含'内容'列")
    
    # 定义需要排除的关键字
    exclude_keywords = ["包含", "同时", "手术或操作", "诊断", "主诊表", "入组条件", "内容"]
    # 初始化变量
    corrected_rows = []
    previous_row = None
    
    # 遍历每一行
    for _, row in df.iterrows():
        content = row["内容"]
        # 检查当前行是否为异常行
        is_invalid = (
            not re.match(r'^[A-Za-z0-9]', str(content)) and 
            not (content == "和" or any(keyword in str(content) for keyword in exclude_keywords))
        )
        
        if previous_row is None:
            previous_row = row
            continue
        
        if not is_invalid:
            # 如果不是异常行，则直接添加到结果中
            corrected_rows.append(previous_row)
            previous_row = row
        else:
            # 如果是异常行且上一行存在，则将其附加到上一行的末尾
            previous_row += content
    
    # 处理最后一行
    if previous_row is not None:
        corrected_rows.append(previous_row)
    
    # 创建新的DataFrame
    corrected_df = pd.DataFrame(corrected_rows)
    return corrected_df

def parse_text(df: pd.DataFrame):
    """
    从PDF中复制的文本中解析出MDC主诊表规则和ADRG规则。
    Args:
        df (pd.DataFrame): 包含文本内容的DataFrame，必须包含'内容'列。
    Returns:
        list: 包含MDC主诊表规则和ADRG规则的列表。
    """
    # 初始化变量
    group_rules = []
    is_mdc_main_diagnosis = False  # 用于判断当前行是否是MDC的主诊表规则
    current_mdc = None
    current_adrg = None

    # 遍历每一行
    for _, row in df.iterrows():
        content = row["内容"]
        # 如果当前行以MDC开头，则说明遇到了一个新的MDC，此时需要新增一个MDC，并且将主诊表的判断状态设为True。
        if content.startswith("MDC"):
            mdc_code_match = re.match(r'MDC[A-Z]', content)
            current_mdc = {
                "MDC编码": mdc_code_match.group() if mdc_code_match else None,  # 转换为字符串
                "MDC名称": re.sub(r'MDC[A-Z]', '', content).strip(),
                "主诊表": [],
                "包含的ADRG": []
            }
            group_rules.append(current_mdc)
            current_adrg = None
            is_mdc_main_diagnosis = True
        # 如果当前行以ADRG开头
        elif re.match(r'^[A-Z]{2}[0-9]', content):
            adrg_code_match = re.match(r'[A-Z]{2}[0-9]', content)
            current_adrg = {
                "ADRG编码": adrg_code_match.group() if adrg_code_match else None,  # 转换为字符串
                "ADRG名称": re.sub(r'[A-Z]{2}[0-9]', '', content).strip(),
                "入组逻辑": [],
                "ICD": []
            }
            group_rules[-1]["包含的ADRG"].append(current_adrg)
            is_mdc_main_diagnosis = False
        elif re.match(r'^[A-Z]?[0-9]{2}\.', content):
            icd_code_match = re.match(r'^[A-Z]?[0-9]{2}\.[A-Za-z0-9.+*]+', content)
            icd_code = icd_code_match.group() if icd_code_match else None
            icd_name = re.sub(r'^[A-Z]?[0-9]{2}\.[A-Za-z0-9.+*]+', '', content).strip()
            if is_mdc_main_diagnosis:
                group_rules[-1]["主诊表"].append({"ICD编码": icd_code, "ICD名称": icd_name})
            else:
                group_rules[-1]["包含的ADRG"][-1]["ICD"].append({"ICD编码": icd_code, "ICD名称": icd_name})
        elif re.match(r'^[\u4e00-\u9fa5]', content) and current_adrg:
            group_rules[-1]["包含的ADRG"][-1]["入组逻辑"].append(content)
    return group_rules

def separate_grouping_logic(group_rules: list):
    """
    分离入组逻辑中的诊断和手术操作。
    Args:
        group_rules (list): 包含MDC主诊表规则和ADRG规则的列表。
    Returns:
        list: 分离后的规则列表。
    """
    # 遍历每个MDC规则
    for mdc in group_rules:
        # 遍历每个ADRG规则
        for adrg in mdc["包含的ADRG"]:
            # 拼接入组逻辑元素
            grouping_logic_str = ' + '.join(adrg["入组逻辑"])
            # 检查是否符合特定格式
            if grouping_logic_str == "包含以下主要诊断： + 包含以下主要手术或操作：": 
                # 初始化主要诊断和主要手术操作列表
                main_diagnoses = []
                main_operations = []
                # 遍历ICD列表
                for icd in adrg["ICD"]:
                    icd_code = icd["ICD编码"]
                    # 判断ICD编码是诊断还是手术
                    if re.match(r'[A-Z][0-9]{2}\.', icd_code):
                        main_diagnoses.append(icd)
                    else:
                        main_operations.append(icd)
                # 更新ADRG规则
                adrg["主要诊断"] = main_diagnoses
                adrg["主要手术操作"] = main_operations
                # 删除原有的ICD列表
                del adrg["ICD"]
                # 将入组逻辑列表转换为字符串
                # adrg["入组逻辑"] = grouping_logic_str

    return group_rules

def doctor_rules(group_rules: list):
    """
    1. 统计分组规则的类型；
    2. 判断分组规则有没有重复入组的情况
    """
    statistics = defaultdict(list)
    for mdc in group_rules:
        for adrg in mdc["包含的ADRG"]:
            logic_str = " + ".join(adrg["入组逻辑"])
            statistics[logic_str].append(adrg["ADRG编码"])

    with open("../rules/statistics.json", 'w', encoding='utf-8') as json_file:
        json.dump(statistics, json_file, ensure_ascii=False, indent=4)

    print("统计完成，分析结果已写入到statistics.json。")

def export_to_json(group_rules: list, file_path: str):
    """
    将分组规则导出为JSON文件。
    Args:
        group_rules (list): 包含MDC主诊表规则和ADRG规则的列表。
        file_path (str): 导出的JSON文件路径。
    """
    with open(file_path, 'w', encoding='utf-8') as json_file:
        json.dump(group_rules, json_file, ensure_ascii=False, indent=4)

def read_json(file_path: str):
    """
    读取JSON文件。
    Args:
        file_path (str): JSON文件路径。
    Returns:
        list: 包含MDC主诊表规则和ADRG规则的列表。
    """
    with open(file_path, 'r', encoding='utf-8') as json_file:
        return json.load(json_file)

if __name__ == "__main__":

    # 读取CSV文件
    # file_path = "../doc/ADRG列表（65-1156）.xlsx"
    # df = pd.read_excel(file_path)
    # # 移除数字
    # df = remove_number(df)
    # # 处理异常换行
    # df = handle_abnormal_linebreak(df)
    # # 解析文本
    # origin_result = parse_text(df)
    # export_to_json(origin_result, "../rules/ADRG_rules_origin.json")
    result = read_json("../rules/group_rules.json")
    # # 分离入组逻辑中的诊断和手术操作
    # result = separate_grouping_logic(origin_result)
    # # 保存结果
    # export_to_json(result, "../rules/ADRG_rules.json")
    # print(f"结果已保存到 rules/ADRG_rules.json")

    doctor_rules(result)

