import pandas as pd
import json
import os 
def process_json(json_table: dict) -> dict:
    try:
        
        if not isinstance(json_table, dict):
            raise TypeError("Wrong type of input. Must be json")
        
        df = pd.DataFrame(json_table)

        if df.empty:
            raise ValueError("Your JSON is empty.")

        correlation  = df.corr(numeric_only=True).to_dict()
        print("corelation: ", correlation, "\n")

        numeric_stat = df.describe(include=[float, int])
        object_stat = df.describe(include=[object])
        combined_stat = pd.concat([numeric_stat, object_stat], axis=1)
        
        unique_counts = {col: df[col].nunique() for col in df.columns}
        
        missing_counts = df.isnull().sum().to_dict()
        
        skew = df.skew(numeric_only=True).to_dict()
        
        kurt = df.kurt(numeric_only=True).to_dict()
        # Сохранение результата
        result = combined_stat.to_dict()

        for key in unique_counts.keys():
            result[key]['unique'] = unique_counts[key]
            result[key]['missing'] = missing_counts[key]
        for key in skew.keys():
            result[key]['skewness'] = skew[key]
            result[key]['kurtosis'] = kurt[key]
            for subkey in  correlation[key].keys():
                if subkey != key:
                    print(correlation[key][subkey])
                    result['corellation'] = correlation[key][subkey]
        
        return {
            "success":True,
            "result" :result
        }
    except Exception as e:
        return {
                "success":False,
                "error" :str(e)
            }