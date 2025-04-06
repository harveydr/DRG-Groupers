import pandas as pd
import re
import json
from collections import defaultdict
import pandas as pd


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
    对于诊断+手术入组的情况，从ADRG[ICD]中分离入组逻辑中的诊断和手术操作。
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


def get_check_keys(group_rules: list):
    """
    获取分组规则中需要检查的键。
    Args:
        group_rules (list): 包含MDC主诊表规则和ADRG规则的列表。
    Returns:
        set: 包含所有键的集合。
    """
    check_keys = []
    for mdc in group_rules:
        for adrg in mdc["包含的ADRG"]:
            for key in adrg:
                if key not in check_keys and key not in ['ADRG编码', 'ADRG名称', '入组逻辑']:
                    check_keys.append(key)
    return check_keys

def check_error_icd(group_rules: list):
    """
    检查分组规则中的ICD编码是否存在错误。
    Args:
        group_rules (list): 包含MDC主诊表规则和ADRG规则的列表。
    """
    error_icds = []
    
    # 检查是否存在ICD编码或名称为空的情况
    check_keys = get_check_keys(group_rules)
    for mdc in group_rules:
        for icd in mdc["主诊表"]:
            if not icd["ICD编码"] or not icd["ICD名称"]:
                error_icds.append(icd)
        for adrg in mdc["包含的ADRG"]:
            for key in check_keys:
                if key in adrg:
                    for icd in adrg[key]:
                        if not icd["ICD编码"] or not icd["ICD名称"]:
                            error_icds.append(icd)
    return error_icds

def get_icd_name(df: pd.DataFrame, icd_codes: list):
    """
    从DataFrame中获取ICD编码对应的名称。
    Args:
        df (pd.DataFrame): 原始的数据文件
        icd_codes (list): 要查询的ICD编码列表，每个元素是一个包含ICD编码和名称的字典。
    Returns:
        list: 包含ICD编码和名称的字典列表。
    """
    result = []
    for icd_item in icd_codes:
        icd_code = icd_item["ICD编码"]
        # 查找包含ICD编码的行
        for _, row in df.iterrows():
            content = str(row["内容"])  # 强制转换为字符串
            if content.startswith(icd_code):
                # 提取ICD名称
                icd_name = ""
                start_index = df.index.get_loc(row.name)
                # 从当前行开始，遍历后续行，直到遇到下一个ICD编码
                for i in range(start_index, len(df)):
                    next_content = str(df.iloc[i]["内容"])  # 强制转换为字符串
                    # 如果遇到下一个ICD编码，则停止
                    if i != start_index and re.match(r'^[A-Z]?[0-9]{2}\.[A-Za-z0-9.+*]+', next_content):
                        break
                    # 拼接名称内容
                    if i == start_index:
                        icd_name += next_content[len(icd_code):].strip()  # 去掉ICD编码部分
                    else:
                        icd_name += " " + next_content.strip()
                # 去掉换行符和多余空格
                icd_name = " ".join(icd_name.split())
                # 更新ICD名称
                icd_item["ICD名称"] = icd_name
                result.append(icd_item)
                break
    return result

def update_icd_name(group_rules: list, icd_names: list):
    """
    更新分组规则中的ICD名称。
    Args:
        group_rules (list): 包含MDC主诊表规则和ADRG规则的列表。
        icd_names (list): 包含ICD编码和名称的字典列表。
    """
    # 将icd_names转换为字典，方便快速查找
    icd_name_dict = {item["ICD编码"]: item["ICD名称"] for item in icd_names}
    check_keys = get_check_keys(group_rules)
    for mdc in group_rules:
        for icd in mdc["主诊表"]:
            icd_code = icd["ICD编码"]
            if icd_code in icd_name_dict:
                icd["ICD名称"] = icd_name_dict[icd_code]
        
        for adrg in mdc["包含的ADRG"]:
            for key in check_keys:
                if key in adrg:
                    for icd in adrg[key]:
                        icd_code = icd["ICD编码"]
                        if icd_code in icd_name_dict:
                            icd["ICD名称"] = icd_name_dict[icd_code]

    # 保存更新后的规则
    export_to_json(group_rules, "../rules/group_rules.json")
    print(f"结果已保存到 rules/group_rules.json")

def remove_space(group_rules: list):
    """
    去除分组规则中的空格。
    Args:
        group_rules (list): 包含MDC主诊表规则和ADRG规则的列表。
    """
    check_keys = get_check_keys(group_rules)
    for mdc in group_rules:
        for icd in mdc["主诊表"]:
            icd["ICD名称"] = icd["ICD名称"].replace(" ", "")
        for adrg in mdc["包含的ADRG"]:
            for key in check_keys:
                if key in adrg:
                    for icd in adrg[key]:
                        icd["ICD名称"] = icd["ICD名称"].replace(" ", "")
    
    export_to_json(group_rules, "../rules/group_rules.json")

def merge_grouping_logic(group_rules: list):
    """
    将group_rules中每个DRG的入组逻辑变成字符串，即拼接列表中的每一项。
    Args:
        group_rules (list): 包含MDC主诊表规则和ADRG规则的列表。
    Returns:
        list: 修改后的规则列表。
    """
    for mdc in group_rules:
        for adrg in mdc["包含的ADRG"]:
            adrg["入组逻辑"] = ' + '.join(adrg["入组逻辑"])
    export_to_json(group_rules, "../rules/group_rules.json")

if __name__ == "__main__":

    # # 读取CSV文件
    # file_path = "../doc/ADRG列表（65-1156）.xlsx"
    # df = pd.read_excel(file_path)
    
    # # 1.移除数字
    # df = remove_number(df)
    # # 2.处理异常换行，即把异常换行的内容合并到上一行
    # df = handle_abnormal_linebreak(df)
    # # 3.解析文本
    # origin_result = parse_text(df)
    # # export_to_json(origin_result, "../rules/ADRG_rules_origin.json")
    # # 4.检查分组规则
    # doctor_rules(result)
    # # 5.分离入组逻辑中的诊断和手术操作
    # result = separate_grouping_logic(origin_result)
    # export_to_json(result, "../rules/ADRG_rules.json")
    # # 6.人工整理分组规则后读取结果
    result = read_json("../rules/group_rules.json")
    # # 7. 检查ICD编码或名称是否为空，结果是ICD编码不为空，但是ICD名称存在空值；获取ICD名称
    # error_icds = check_error_icd(result)
    # # pd.DataFrame(error_icds).to_excel("error_icds.xlsx", index=False)
    # icd_names = get_icd_name(df, error_icds)
    # # pd.DataFrame(icd_names).to_excel("icd_names.xlsx", index=False)
    # # check_keys = get_check_keys(result)
    # # print(check_keys)
    # # 8.更新ICD名称
    # icd_names = pd.read_excel("icd_names.xlsx")
    # update_icd_name(result, icd_names.to_dict(orient="records"))
    # 9.去除空格
    # remove_space(result)
    # 10.合并入组逻辑
    merge_grouping_logic(result)
