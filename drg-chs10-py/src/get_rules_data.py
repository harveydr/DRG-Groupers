import pandas as pd
import json

def get_mdc_json(file_path):
    df = pd.read_excel(file_path)
    result_list = []
    for mdc_code in df["MDC编码"].unique():
        sub_df = df[df["MDC编码"] == mdc_code]
        icd_list = []
        for _, row in sub_df.iterrows():
            icd_item = {
                "ICD编码": row["icd_code"],
                "ICD名称": row["icd_name"]
            }
            icd_list.append(icd_item)
        # 获取唯一的性别、年龄和部位值
        gender = [val for val in sub_df["性别节点"].unique() if val != '-']
        age = [val for val in sub_df["年龄节点"].unique() if val!= '-']
        location = [val for val in sub_df["部位"].unique() if val!= '-']
        # 如果只有一个值，则直接取该值，否则保持列表形式
        if len(gender) == 1:
            gender = gender[0]
        if len(age) == 1:
            age = age[0]
        if len(location) == 1:
            location = location[0]
        # 构建结果字典
        result = {
            "MDC编码": mdc_code,
            "MDC名称": sub_df["MDC名称"].iloc[0],
            "入组条件": {
                "ICD-10": icd_list,
                "性别": gender,
                "年龄": age,
                "部位": location
            }
        }
        result_list.append(result)
    return result_list

def get_unique_values(file_path, column_name):
    df = pd.read_excel(file_path)
    return df[column_name].unique()

def export_to_json(data, file_path):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_adrg_json(file_path):
    df = pd.read_excel(file_path)
    result_list = []
    for adrg_code in df["ADRG编码"].unique():
        sub_df = df[df["ADRG编码"] == adrg_code]
        adrg_name = sub_df["ADRG名称"].iloc[0]
        entry_type = ""
        entry_conditions = {
            "性别": None,
            "年龄": None,
        }
        op1_list = []
        op2_list = []
        main_diagnosis_list = []
        main_surgery_list = []

        for _, row in sub_df.iterrows():
            if row["病组属性"] == "1-联合手术":
                entry_type = "联合手术"
                if row["编码操作类别"] == 1:
                    icd_item = {
                        "ICD编码": row["icd_code"],
                        "ICD名称": row["icd_name"]
                    }
                    op1_list.append(icd_item)
                elif row["编码操作类别"] == 2:
                    icd_item = {
                        "ICD编码": row["icd_code"],
                        "ICD名称": row["icd_name"]
                    }
                    op2_list.append(icd_item)
            elif row["病组属性"] == "3-诊断+手术":
                entry_type = "诊断+手术"
                if row["编码操作类别"] == 0:
                    icd_item = {
                        "ICD编码": row["icd_code"],
                        "ICD名称": row["icd_name"]
                    }
                    main_diagnosis_list.append(icd_item)
                elif row["编码操作类别"] == 1:
                    icd_item = {
                        "ICD编码": row["icd_code"],
                        "ICD名称": row["icd_name"]
                    }
                    main_surgery_list.append(icd_item)
            elif row["病组属性"] == "2-手术":
                entry_type = "手术"
                if row["编码操作类别"] == 1:
                    icd_item = {
                        "ICD编码": row["icd_code"],
                        "ICD名称": row["icd_name"]
                    }
                    main_surgery_list.append(icd_item)
            elif row["病组属性"] == "4-诊断":
                entry_type = "诊断"
                if row["编码操作类别"] == 0:
                    icd_item = {
                        "ICD编码": row["icd_code"],
                        "ICD名称": row["icd_name"]
                    }
                    main_diagnosis_list.append(icd_item)

        age = [val for val in sub_df["年龄节点"].unique() if val!= '-']
        gender = [val for val in sub_df["性别节点"].unique() if val!= '-']
        if len(age) == 1:
            entry_conditions["年龄"] = age[0]
        if len(gender) == 1:
            entry_conditions["性别"] = gender[0]

        if entry_type == "联合手术":
            entry_conditions["手术操作1"] = op1_list
            entry_conditions["手术操作2"] = op2_list
        elif entry_type == "诊断+手术":
            entry_conditions["主要诊断"] = main_diagnosis_list
            entry_conditions["主要手术"] = main_surgery_list
        elif entry_type == "手术":
            entry_conditions["主要手术"] = main_surgery_list
        elif entry_type == "诊断":
            entry_conditions["主要诊断"] = main_diagnosis_list

        result = {
            "ADRG编码": adrg_code,
            "ADRG名称": adrg_name,
            "入组类型": entry_type,
            "入组条件": entry_conditions
        }
        result_list.append(result)
    return result_list

def get_mcc_cc_json(file_path):
    df = pd.read_excel(file_path)
    result_dict = {}
    for _, row in df.iterrows():
        icd_code = row["icd_code"]
        result_dict[icd_code] = {
            "icd_name": row["icd_name"],
            "type": row["type"],
            "exclude_icd": row["exclude_icd"]
        }
    return result_dict

def get_exclude_json(file_path):
    df = pd.read_excel(file_path)
    result_dict = df.groupby('exclude_icd')['icd_code'].apply(list).to_dict()
    return result_dict

if __name__ == "__main__":
    # json_data = get_adrg_json("../doc/ADRG列表.xlsx")
    # export_to_json(json_data, "../config/adrg.json")

    # json_data = get_mcc_cc_json("../doc/MCC_CC表.xlsx")
    # export_to_json(json_data, "../config/mcc_cc.json")

    json_data = get_exclude_json("../doc/排除表.xlsx")
    export_to_json(json_data, "../config/exclude.json")