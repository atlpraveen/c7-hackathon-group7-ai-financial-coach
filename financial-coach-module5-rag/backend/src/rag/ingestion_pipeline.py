from .chunking import chunk_text

class IngestionPipeline:
    def run(self, text:str):
        return chunk_text(text)
