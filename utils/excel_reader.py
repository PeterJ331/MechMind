import pandas as pd

class ExcelReader:
    def __init__(self, filepath):
        self.filepath = filepath

    def extract_data(self, max_rows=5):
        try:
            df = pd.read_excel(self.filepath)
            headers = df.columns.tolist()
            sample_rows = df.head(max_rows).to_dict(orient="records")
            return headers, sample_rows
        except Exception as e:
            print(f"❌ Excel读取失败: {e}")
            return [], []
