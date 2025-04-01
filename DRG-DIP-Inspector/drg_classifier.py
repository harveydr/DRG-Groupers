import json
import datetime
import requests
import pandas as pd
from tqdm import tqdm
import sys
from sqlalchemy import create_engine
from concurrent.futures import ThreadPoolExecutor, as_completed

class DRG_Classifier:
    def __init__(self, engine):
        self.engine = engine

    def build_request_body(self, setl_id: str):
        """用于按照接口文档要求的格式，构造请求的JSON数据"""
        try:
            data = pd.read_sql(f"select * from 分组器数据池 where 病案号 = '{setl_id}'", con=self.engine).to_dict(orient='records')[0]
        except Exception as e:
            return None

        return {
            "akb020": data['医疗机构编码'],
            "log": "",
            "lyfs": data['离院方式'],
            "jbdm1_15": data.get('病案诊断编码1_15', []),
            "xb": data['性别'],
            "zfy": data['实际总费用'],
            "bzyzsnl": data['不足一周岁年龄天'],
            "hxjsysj": data['呼吸机使用时间'],
            "jbdm0_15": data.get('病案诊断编码0_15', []),
            "jbdm": data['病案主诊断编码'],
            "sjzyts": data['住院天数'],
            "xserytz": data['新生儿出生体重'],
            "ssbm": data.get('手术操作编码1', ''),
            "nl": data['年龄'],
            "ssbm2_7": [data.get(f'手术操作编码{i}', '') for i in range(2, 8)],
            "ssbm1_7": [data.get(f'手术操作编码{i}', '') for i in range(1, 8)]
        }

    @staticmethod
    def default_encoder(obj):
        if isinstance(obj, pd.Timestamp):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, datetime.date):
            return obj.strftime('%Y-%m-%d')
        elif isinstance(obj, pd.Series):
            return obj.to_dict()
        raise TypeError(f'Object of type {obj.__class__.__name__} is not JSON serializable')

    def call_drg_classifier(self, setl_id: str) -> dict:
        """传入setl_id，调用分组器进行分组"""
        url = "http://172.20.22.237:3001/comp_drg"
        headers = {'Content-type': 'application/json'}
        data = self.build_request_body(setl_id)
        if data:
            try:
                response = requests.post(url, data=json.dumps(data, default=self.default_encoder), headers=headers)
                result = response.json()
                result['setl_id'] = setl_id
                return result
            except Exception as e:
                print(f"调用分组器发生异常：{e}")
        else:
            print(f"[call_drg_classifier] 获取到的分组器入参为空，setl_id为：{type(setl_id)}")
            sys.exit(1)


    def batch_drg_classifier(self, task_generator) -> list:
        """批量跑完任务表里的数据（带进度条）"""
        results = []
        # 将任务迭代器包装在tqdm中以创建进度条
        print("正在读取数据...")
        task_list = list(task_generator)
        with tqdm(total=len(task_list), desc="正在分组...") as pbar:
            with ThreadPoolExecutor() as executor:
                futures = [executor.submit(self.call_drg_classifier, case.iloc[0,0]) for case in task_list]
                for future in as_completed(futures):
                    results.append(future.result())
                    # 每完成一个任务，更新进度条
                    pbar.update(1)

        return results

    def run(self, dbtable: str) -> list:
        tasks = pd.read_sql(f"select 病案号 from {dbtable}",con=self.engine, chunksize=1)
        results = self.batch_drg_classifier(tasks)
        return results

    def export_requests_data(self):
        results = []
        tasks = pd.read_sql(f"select 病案号 from 分组器数据池",con=self.engine, chunksize=1)
        for case in tasks:
            setl_id = case.iloc[0,0]
            data = self.build_request_body(setl_id)
            data["setl_id"] = setl_id
            results.append(data)
        return results


if __name__ == '__main__':
    engine = create_engine('mysql+pymysql://root:mysql123@localhost/飞检工具')
    drg_classifier = DRG_Classifier(engine)
    results = drg_classifier.run('分组器数据池')
    pd.DataFrame(results).to_excel('result/DRG分组结果.xlsx', index=False)
