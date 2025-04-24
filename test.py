import csv
import json

# CSVファイルを読み込んで辞書リストに変換
def csv_to_json():

    for csv_link in ["csv/1-1:team","csv/1-2:ground"]:
        data = []
        with open(csv_link+".csv", 'r', encoding='utf-8') as f:
            csv_reader = csv.DictReader(f)
            for row in csv_reader:
                data.append(row)
        
        # JSONファイルとして保存
        with open(csv_link+".json", 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    
    return data

# 使用例
data = csv_to_json()