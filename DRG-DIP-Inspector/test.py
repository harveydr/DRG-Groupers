import json
import pandas as pd
from sqlalchemy import create_engine
from drg_classifier import DRG_Classifier 
from drg_audit_detector import DRG_AuditDetector
from export import export_list_json

engine = create_engine('mysql+pymysql://root:mysql123@localhost/飞检工具')

detector = DRG_AuditDetector(engine)
drg = DRG_Classifier(engine)

data_drg = drg.call_drg_classifier('IP0004269019')
data_detector = detector.call_audit_detector('IP0004269019')

print(data_drg)
print(data_detector)

# export_list_json(data_drg, 'DRG分组器入参.json')
# export_list_json(data_detector, '疑点识别器入参.json')
