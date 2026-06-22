from pathlib import Path


class DocumentTextExtractor:
    def extract(self, path: str, file_type: str) -> str:
        file_type = file_type.lower().lstrip(".")
        if file_type == "pdf":
            return self._extract_pdf(path)
        if file_type == "docx":
            return self._extract_docx(path)
        raise ValueError("Unsupported file type")

    @staticmethod
    def _extract_pdf(path: str) -> str:
        import fitz

        text_parts: list[str] = []
        with fitz.open(path) as pdf:
            for page in pdf:
                text_parts.append(page.get_text("text"))
        return "\n".join(text_parts).strip()

    @staticmethod
    def _extract_docx(path: str) -> str:
        from docx import Document

        document = Document(Path(path))
        return "\n".join(paragraph.text for paragraph in document.paragraphs).strip()
