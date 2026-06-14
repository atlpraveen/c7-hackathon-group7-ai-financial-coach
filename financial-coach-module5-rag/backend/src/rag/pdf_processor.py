from pypdf import PdfReader

class PDFProcessor:
    def extract_text(self, pdf_path:str):
        reader = PdfReader(pdf_path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
