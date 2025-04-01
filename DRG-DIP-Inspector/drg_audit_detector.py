from sqlalchemy import create_engine
import json
import requests
from tqdm import tqdm
import pandas as pd
import datetime
import sys
import os
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from drg_classifier import DRG_Classifier
from export import export_dict_txt

logging.basicConfig(filename=os.path.join('logs', 'error.log'), level=logging.ERROR)

class DRG_AuditDetector:
    def __init__(self, engine):
        self.engine = engine

    def get_setlinfo(self, setl_id: str) -> dict:
        """获取患者本次就诊的结算信息"""
        try: 
            return pd.read_sql(f'select * from setlinfo where setl_id = "{setl_id}"', con=self.engine).to_dict(orient='records')[0] # 获取结算信息
        except Exception as e:
            return None

    def get_diseinfo(self, setl_id: str) -> dict:
        """获取患者本次就诊的诊断信息"""
        try: 
            return pd.read_sql(f'select * from diseinfo where setl_id = "{setl_id}"', con=self.engine).to_dict(orient='records') # 获取诊断信息
        except Exception as e:
            return None

    def get_oprninfo(self, setl_id: str) -> dict:
        """获取患者本次就诊的手术信息"""
        try: 
            return pd.read_sql(f'select * from oprninfo where setl_id = "{setl_id}"', con=self.engine).to_dict(orient='records') # 获取诊断信息
        except Exception as e:
            return None

    def get_groupinfo(self, setl_id: str) -> dict:
        drg = DRG_Classifier(self.engine)
        drg_result = drg.call_drg_classifier(setl_id)
        if drg_result:
            return {"aaz645": "1", "bke715": "5", "bke716": drg_result['drg'], "bke717": "", "setl_id": setl_id}

    def get_details(self, setl_id):
        """获取患者本次就诊的收费项目明细信息"""
        try: 
            return pd.read_sql(f'select * from details where setl_id = "{setl_id}"', con=self.engine).to_dict(orient='records') # 获取收费项目明细
        except Exception as e:
            return None
        
    def get_vali_types(self):
        """获取本次要判断的疑点类型信息"""
        return ['lower_in', 'cancer_diagnose_up', 'cancer_immunotherapy_up', 'cancer_chemotherapy_up', 'cancer_radiation_up', 'opt_watered_up', 'opt_lost_low', 'diagnosis_surgery_conflict', 'decomposed_hospitalization', 'abnormal_visits']

    def is_readmission_in_range(self, setl_id: str, days: int) -> tuple:
        """
        判断本次就诊是否是某段时间内再次入院（仅与上一次就诊比较）
        入参：
            mdtrt_id: 患者唯一标识
            setl_id: 就诊号
            days: 天数，指患者再入院的时间周期
        返回：
            is_readmission: True/False，表示本次就诊是否再次入院
            prev_setl_id: 上一次就诊的就诊ID，如果没有则为 None
        """
        try:
            mdtrt_id = pd.read_sql(f"select mdtrt_id from setlinfo where setl_id = '{setl_id}'", con=self.engine).iloc[0,0]
            sql = f"select mdtrt_id, setl_id, adm_time, dscg_time from setlinfo where mdtrt_id = '{mdtrt_id}'"
            df = pd.read_sql(sql, con=self.engine, parse_dates=['adm_time', 'dscg_time'])
            
            if len(df) < 2:
                return False, None
            
            df = df.sort_values(by='adm_time')
            df['prev_dscg_time'] = df['dscg_time'].shift(1)
            df['prev_setl_id'] = df['setl_id'].shift(1)
            df['interval_time'] = df['adm_time'] - df['prev_dscg_time']
            
            prev_setl_id = df.loc[df['setl_id'] == setl_id, 'prev_setl_id'].iloc[0]
            is_readmission = df.loc[df['setl_id'] == setl_id, 'interval_time'].iloc[0] <= pd.Timedelta(days, unit='D')
            
            return is_readmission, prev_setl_id
        
        except Exception as e:
            print(f"[is_readmission_in_range] An error occurred: {e}")
            return False, None

    def print_hos_interval(self, mdtrt_id):
        """
        打印患者在整个数据库表中的住院时间间隔
        入参：
            mdtrt_id: 患者唯一标识
        """
        sql = f"select mdtrt_id, setl_id, adm_time, dscg_time from setlinfo where mdtrt_id = {mdtrt_id}"
        df = pd.read_sql(sql, con=self.engine, parse_dates=['adm_time', 'dscg_time'])
        df = df.sort_values(by='adm_time')
        df['last_dscg_time'] = df['dscg_time'].shift(1)
        df['interval_time'] = df['adm_time'] - df['dscg_time'].shift(1)
        print(df)

    def get_main_case(self, setl_id):
        """获取本次就诊的main_case信息"""
        setlinfo = self.get_setlinfo(setl_id)
        diseinfo = self.get_diseinfo(setl_id)
        oprninfo = self.get_oprninfo(setl_id)
        
        group_info = self.get_groupinfo(setl_id)
        result = {"setlinfo": setlinfo, "diseinfo": diseinfo, "oprninfo": oprninfo, "group_info": group_info}

        return result

    # def get_other_cases(self, setl_id):
    #     """如果本次就诊距离上次在30天以内，则返回上次就诊的main_case数据"""
    #     is_readmission, prev_setl_id = self.is_readmission_in_range(setl_id, 30)
    #     if is_readmission:
    #         return self.get_main_case(prev_setl_id)
    #     else:
    #         print("[get_other_cases] 此节点为必传节点，不能为空！")
    #         sys.exit(1)

    def get_other_cases(self, setl_id):
        """返回该患者其他就诊时的main_case数据"""
        other_cases = []
        try:
            mdtrt_id = pd.read_sql(f"select mdtrt_id from setlinfo where setl_id = '{setl_id}'", con=self.engine).iloc[0,0]
            other_setl_ids = pd.read_sql(f"select setl_id from setlinfo where mdtrt_id = '{mdtrt_id}'", con=self.engine)
            for _, other_setl_id in other_setl_ids.iterrows():
                other_cases.append(self.get_main_case(other_setl_id.iloc[0]))
            return other_cases
        except Exception as e:
            print(f"[get_other_cases] 发生异常：{e}")
            sys.exit(1)
        

    def build_request_body(self, setl_id) -> json:
        """按照接口文档要求的格式，构建请求JSON数据"""
        main_case = self.get_main_case(setl_id)
        other_cases = self.get_other_cases(setl_id)
        details = self.get_details(setl_id)
        vali_types = self.get_vali_types()
        
        result = {"main_case": main_case, "other_cases": other_cases, "details": details, "vali_types": vali_types}
        return result

    @staticmethod
    def default_encoder(obj):
        if isinstance(obj, pd.Timestamp):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, datetime.date):
            return obj.strftime('%Y-%m-%d')
        raise TypeError(f'Object of type {obj.__class__.__name__} is not JSON serializable')
    
    def export_json(self, setl_id: str):
        data = self.build_request_body(setl_id)
        with open('re-test.json', 'w') as file:
            json.dump(data, file, ensure_ascii=False, default=self.default_encoder)
    
    def to_json(self, data: dict): 
        with open('re-data.json', 'w') as file:
            json.dump(data, file, ensure_ascii=False, default=self.default_encoder)

    def debug_current_request(self, data, response):
        print(data)
        print(response.text)
        json_data = json.dumps(data, default=self.default_encoder, ensure_ascii=False)
        with open('json/current_requests.json', 'w') as file:
            file.write(json_data)
        print("=======================================")
        input()
    
    def record_error_requests(self, data):
        json_data = json.dumps(data, default=self.default_encoder, ensure_ascii=False)
        with open('json/error_requests.json', 'a+') as file:
            file.write(json_data)

    def call_audit_detector(self, setl_id: str):
        url = "http://172.20.22.237:5555/validator/validator_person"
        # url = "http://localhost:5555/validator/validator_person"
        headers = { 'Content-type': 'application/json' }
        data = self.build_request_body(setl_id)
        if data:
            try:
                response = requests.post(url, data=json.dumps(data, default=self.default_encoder), headers=headers)
                # self.debug_current_request(data, response)
                if response.status_code != 200:
                    return response.status_code, data, response.text

                return response.status_code, data, response.json()
            except Exception as e:
                logging.error(f"Request error occurred: {e}. setl_id: {setl_id}")
                sys.exit(1)
        else:
            print(f"获取到的疑点识别器入参为空，请检查。setl_id: {setl_id}")
        
    def batch_audit_detector(self, task_generator) -> list:
        results = []
        error_requests = []
        right_requests = []

        for setl_id in task_generator:
            response_status_code, requests_data, result = self.call_audit_detector(setl_id.iloc[0,0])
            if response_status_code != 200:
                error_requests.append(requests_data)
            else:
                results.append(result)
                right_requests.append(requests_data)

        return results, error_requests, right_requests

    def test_request(self):
        url = "http://localhost:5555/validator/validator_person"
        headers = { 'Content-type': 'application/json' }
        with open('json/requests_yes.json', 'r') as file:
            data = json.load(file)
        response = requests.post(url, data=json.dumps(data, default=self.default_encoder), headers=headers)
        print(response.text)

    def run(self):
        tasks = pd.read_sql("select setl_id from setlinfo", con=self.engine, chunksize=1)
        results, error_requests, right_requests = self.batch_audit_detector(tasks)
        return results, error_requests, right_requests

    def export_requests_data(self):
        results = []
        tasks = pd.read_sql(f"select setl_id from setlinfo",con=self.engine, chunksize=1)
        for case in tasks:
            setl_id = case.iloc[0,0]
            data = self.build_request_body(setl_id)
            results.append(data)
        return results

if __name__ == '__main__':
    engine = create_engine('mysql+pymysql://root:mysql123@localhost/飞检工具')
    detector = DRG_AuditDetector(engine)
    results, error_requests, right_requests = detector.run()
    pd.DataFrame(results).to_excel('疑点结果.xlsx', index=False)
    export_dict_txt(error_requests, '请求失败数据.txt')
    export_dict_txt(right_requests, '请求成功数据.txt')
