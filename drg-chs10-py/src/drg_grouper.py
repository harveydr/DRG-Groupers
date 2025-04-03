import json
from data_classes import Patient, DrgResult

class DrgGrouper:
    """DRG分组器类，负责根据传入的数据进行DRG分组"""
    def __init__(self, patient: Patient) -> None:
        self.patient = patient
        
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
            print(f"加载规则文件时出现错误: {e}")

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
            print(f"错误: 文件 {json_file} 未找到。")
            return {}
        except json.JSONDecodeError:
            print(f"错误: 无法解析 {json_file} 为有效的JSON。")
            return {}
    

    def to_mdc(self):
        result = ()
        for diag in self.patient.diagnosis:
            # 假设diag是一个自定义类的实例，需要通过属性访问而不是字典的get方法
            if diag.diag_id == 1:
                result




    def group(self) -> DrgResult:
        ...
        # return {"drg_code": "BB19", "drg_name": "DRG名称测试"}
