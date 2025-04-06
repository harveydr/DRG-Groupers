import json
import pandas as pd
from typing import Optional, List, Dict, Tuple
from data_classes import Patient, MDC, ADRG
from convert_to_patient import get_patient

class DrgGrouper:
    """DRG分组器类，负责根据传入的数据进行DRG分组"""
    def __init__(self, patient: Patient) -> None:
        self.patient = patient
        self.load_rules()

    def load_rules(self):
        """
        加载DRG规则文件
        :param json_file: 规则文件路径
        :return: 规则字典
        """
        try:
            self.mdc_rules = self.read_json('../config/mdc.json')
            self.adrg_rules = self.read_json('../config/adrg.json')
            self.drg_rules = self.read_json('../config/mcc_cc.json')
        except Exception as e:
            raise Exception(f"加载规则文件时出现错误: {e}")

    def read_json(self, json_file) -> dict:
        """
        加载DRG规则文件
        :param json_file: 规则文件路径
        :return: 规则字典
        """
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                rules = json.load(f)
            return rules
        except FileNotFoundError:
            raise FileNotFoundError(f"错误: 文件 {json_file} 未找到。")
        except json.JSONDecodeError:
            raise ValueError(f"错误: 无法解析 {json_file} 为有效的JSON。")

    def has_multiple_severe_trauma(self):
        """
        判断当前患者是否有多发严重创伤
        :return: 如果有多发严重创伤返回True，否则返回False，以及判断依据
        """
        location_icd = pd.read_excel('../doc/部位.xlsx')
        # 获取当前患者的所有诊断信息
        all_diagnoses = self.patient.diagnosis
        # 存储匹配到的部位、ICD编码和ICD名称信息
        matched_locations = []
        # 遍历所有诊断信息
        for diag in all_diagnoses:
            # 在location_icd中查找匹配的部位信息
            for _, row in location_icd.iterrows():
                if diag.diag_code == row['ICD编码']:
                    matched_locations.append({
                        '诊断序号': diag.diag_id,
                        '诊断编码': row['ICD编码'],
                        '诊断名称': row['ICD名称'],
                        '部位': row['部位'],
                    })
        # 检查是否有多个不同的部位
        # 提取部位信息
        unique_locations = set([loc['部位'] for loc in matched_locations])
        # 检查是否有多个不同的部位
        if len(unique_locations) <= 1:
            return False, None
        # 按诊断序号排序
        matched_locations.sort(key=lambda x: x['诊断序号'])
        # 拼接部位信息字符串
        location_str = ', '.join([f"{loc['部位']}（{loc['诊断编码']} {loc['诊断名称']}）" for loc in matched_locations])
        return True, location_str


    def classify_into_mdc(self) -> Optional[MDC]:
        """
        根据性别、主要诊断、次要诊断（MDCZ）入到MDC组。流程：
        1. 判断是否为多发严重创伤，若是并且主诊断在MDCZ中，则进入MDCZ组。
        2. 根据主诊断判断属于哪个MDC组，如果同时进入到了MDCM和MDCN，那么再根据性别判断进入哪个组。
        3. MDCA组先不管，到ADRG分组的时候再判断，如果能进入MDCA的ADRG组，则直接进入MDCA。
        :return: 匹配的MDC编码，如果未找到则返回None
        """
        # 获取主诊断信息
        main_diag = self.get_main_diag()
        if main_diag is None:
            return None

        # 判断主诊断代码在哪个MDC中
        for mdc in self.mdc_rules:
            # 检查主诊断是否在MDC的ICD入组条件中，如果不是，直接pass这个MDC
            if not any(diag['ICD编码'] == main_diag.diag_code for diag in mdc['入组条件']['ICD-10']):
                continue

            # 处理MDCZ特殊情况
            if mdc["MDC编码"] == "MDCZ":
                ism, reason = self.has_multiple_severe_trauma()
                if ism:
                    return MDC(
                        code=mdc["MDC编码"],
                        name=mdc["MDC名称"],
                        based=f"主要诊断在MDCZ中且为多发严重创伤：{reason}"
                    )
            # 处理性别匹配情况
            if self.patient.gender == mdc["入组条件"]["性别"]:
                return MDC(
                    code=mdc["MDC编码"],
                    name=mdc["MDC名称"],
                    based=f"主要诊断在{mdc['MDC编码']}中且性别为{self.patient.gender}"
                )
            # 其他MDC直接根据主诊断判断
            return MDC(
                code=mdc["MDC编码"],
                name=mdc["MDC名称"],
                based=f"主要诊断在{mdc['MDC编码']}中"
            )

        return None

    def classify_into_adrg(self, mdc: Optional[MDC]):
        """
        1. 首先判断能否入到MDCA组，如果能，则直接返回MDCA组。
        2. 如果不能入到MDCA组，则根据MDC编码判断应该选择哪些ADRG组去判断
        3. 最后根据诊断和手术判断应该选择哪个ADRG组
        :param mdc_code: 匹配的MDC编码
        :return: 匹配的ADRG编码，如果未找到则返回None
        """
        # 获取主诊断和主手术信息
        main_diag = self.get_main_diag()
        main_surg = self.get_main_surg()
        if main_diag is None or main_surg is None:
            return None
        
        # 遍历ADRG规则，找到匹配的规则
        for adrg in self.adrg_rules:
            if adrg["入组类型"] == "联合手术":
                # 检查患者的所有手术编码
                patient_surg_codes = [surg.oper_code for surg in self.patient.surgery]
                # 检查手术操作1和手术操作2的编码，并直接返回匹配的编码
                oper1_match = next((code for code in adrg["入组条件"]["手术操作1"] if code['ICD编码'] in patient_surg_codes), None)
                oper2_match = next((code for code in adrg["入组条件"]["手术操作2"] if code['ICD编码'] in patient_surg_codes), None)
                # 判断是否同时存在手术操作1和手术操作2中的手术编码
                if oper1_match and oper2_match:
                    return {
                        "ADRG编码": adrg["ADRG编码"],
                        "ADRG名称": adrg["ADRG名称"],
                        "入组依据": f"同时包含（{oper1_match['ICD编码']} {oper1_match['ICD名称']}）和（{oper2_match['ICD编码']} {oper2_match["ICD名称"]}）"
                    }
            elif adrg["入组类型"] == "诊断+手术":
                # 检查主诊断和主手术的编码，并直接返回匹配的编码
                # 原代码使用生成器表达式，这里改为使用 next 函数获取第一个匹配的诊断代码
                diag_match = next((code for code in adrg["入组条件"]["主要诊断"] if code['ICD编码'] == main_diag.diag_code), None)
                surg_match = next((code for code in adrg["入组条件"]["主要手术"] if code['ICD编码'] == main_surg.oper_code), None)
                # 判断是否同时存在主诊断和主手术中的编码
                if diag_match and surg_match:
                    return {
                        "ADRG编码": adrg["ADRG编码"],
                        "ADRG名称": adrg["ADRG名称"],
                        "入组依据": f"同时包含（{diag_match['ICD编码']} {diag_match['ICD名称']}）和（{surg_match['ICD编码']} {surg_match["ICD名称"]}）"
                    }
            elif adrg["入组类型"] == "手术":
                # 检查手术编码是否在ADRG的入组条件中
                surg_match = next((code for code in adrg["入组条件"]["主要手术"] if code['ICD编码'] == main_surg.oper_code), None)
                if surg_match:
                    return {
                        "ADRG编码": adrg["ADRG编码"],
                        "ADRG名称": adrg["ADRG名称"],   
                        "入组依据": f"包含（{surg_match['ICD编码']} {surg_match["ICD名称"]}）"
                    }
            elif adrg["入组类型"] == "诊断":
                # 检查诊断编码是否在ADRG的入组条件中
                diag_match = next((code for code in adrg["入组条件"]["主要诊断"] if code['ICD编码'] == main_diag.diag_code), None)
                if diag_match:
                    return {
                        "ADRG编码": adrg["ADRG编码"],
                        "ADRG名称": adrg["ADRG名称"],
                        "入组依据": f"包含（{diag_match['ICD编码']} {diag_match['ICD名称']}）"
                    }
            return None

    def get_main_diag(self):
        """
        获取主诊断
        :return: 主诊断信息
        """
        for diag in self.patient.diagnosis:
            if diag.diag_id == 1:
                return diag
        return None

    def get_main_surg(self):
        """
        获取主手术
        :return: 主手术信息
        """
        for surg in self.patient.surgery:
            if surg.oper_id == 1:
                return surg
    
    def run(self):
        mdc = self.classify_into_mdc()
        adrg = self.classify_into_adrg(mdc)



if __name__ == "__main__":
    with open('../data/test_data.json', 'r') as f:
        data = json.load(f)
        for i, item in enumerate(data, start=1):
            patient = get_patient(item)
            drg = DrgGrouper(patient)
            print(f"第 {i} 个患者的测试结果:")
            result = drg.classify_into_mdc()
            print(result)