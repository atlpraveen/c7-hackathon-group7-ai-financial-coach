import pandas as pd

class CSVProcessor:
    def load(self, csv_path:str):
        return pd.read_csv(csv_path)
