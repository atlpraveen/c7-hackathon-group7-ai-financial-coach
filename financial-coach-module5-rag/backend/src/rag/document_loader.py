from pathlib import Path

class DocumentLoader:
    def load(self, file_path:str):
        return Path(file_path).read_text(errors='ignore')
