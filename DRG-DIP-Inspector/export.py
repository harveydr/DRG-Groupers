import json
import pandas as pd
import datetime

def default_encoder(obj):
        if isinstance(obj, pd.Timestamp):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, datetime.date):
            return obj.strftime('%Y-%m-%d')
        raise TypeError(f'Object of type {obj.__class__.__name__} is not JSON serializable')

def export_dict_txt(data: list, file_path):
    with open(file_path, 'w') as file:
        for item in data:
            file.write(json.dumps(item, default=default_encoder, ensure_ascii=False) + '\n')

def export_list_json(data: list, file_path):
     with open(file_path, 'w') as file:
          json.dump(data, file, default=default_encoder, ensure_ascii=False)
