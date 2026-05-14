from pathlib import Path
from html.parser import HTMLParser
import xml.etree.ElementTree as ET
import zipfile


class _TextHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if text:
            self.parts.append(text)


def _parse_html(file_path: str) -> str:
    parser = _TextHTMLParser()
    parser.feed(Path(file_path).read_text(encoding="utf-8"))
    return "\n\n".join(parser.parts).strip()


def _parse_docx(file_path: str) -> str:
    with zipfile.ZipFile(file_path) as archive:
        document_xml = archive.read("word/document.xml")
    root = ET.fromstring(document_xml)
    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs = []
    for paragraph in root.findall('.//w:p', namespace):
        texts = [node.text or "" for node in paragraph.findall('.//w:t', namespace)]
        joined = ''.join(texts).strip()
        if joined:
            paragraphs.append(joined)
    return "\n\n".join(paragraphs).strip()


def parse_document(file_path: str, source_type: str) -> str:
    suffix = Path(file_path).suffix.lower()
    if source_type == "file" and suffix in {".txt", ".md", ".csv", ".json"}:
        return Path(file_path).read_text(encoding="utf-8")
    if source_type == "file" and suffix in {".html", ".htm"}:
        return _parse_html(file_path)
    if source_type == "file" and suffix == ".docx":
        return _parse_docx(file_path)
    if source_type == "file" and suffix == ".pdf":
        try:
            from langchain_mineru import MinerULoader  # type: ignore
        except Exception as exc:  # pragma: no cover - depends on environment
            raise RuntimeError("解析 PDF 需要安装 langchain_mineru") from exc

        loader = MinerULoader(source=file_path)
        docs = loader.load()
        return "\n\n".join((doc.page_content or "").strip() for doc in docs if (doc.page_content or "").strip()).strip()

    raise RuntimeError(f"暂不支持的文档类型: {suffix or source_type}")
