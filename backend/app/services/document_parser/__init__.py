"""
문서 파서 모듈

다양한 문서 형식(PDF, DOCX, TXT, Markdown)을 파싱하여
구조화된 데이터로 변환합니다.

Usage:
    from app.services.document_parser import DocumentParserFactory, ParserConfig

    # 기본 사용법
    parser = DocumentParserFactory.get_parser("document.pdf")
    result = parser.parse("document.pdf")

    # 커스텀 설정 사용
    config = ParserConfig(max_file_size_mb=50, skip_empty_pages=True)
    parser = DocumentParserFactory.get_parser("document.docx", config=config)
    result = parser.parse("document.docx")
"""

from app.services.document_parser.base_parser import (
    BaseDocumentParser,
    ParsedDocument,
    ParsedPage,
    ParserConfig,
    DocumentParserError,
    FileSizeLimitExceededError,
    CorruptedFileError,
    EncryptedFileError,
    MaliciousFileError,
    UnsupportedFileTypeError,
)
from app.services.document_parser.pdf_parser import PDFParser
from app.services.document_parser.docx_parser import DOCXParser
from app.services.document_parser.text_parser import TextParser
from app.services.document_parser.markdown_parser import MarkdownParser
from app.services.document_parser.factory import DocumentParserFactory

__all__ = [
    # Base classes and models
    "BaseDocumentParser",
    "ParsedDocument",
    "ParsedPage",
    "ParserConfig",
    # Exceptions
    "DocumentParserError",
    "FileSizeLimitExceededError",
    "CorruptedFileError",
    "EncryptedFileError",
    "MaliciousFileError",
    "UnsupportedFileTypeError",
    # Parsers
    "PDFParser",
    "DOCXParser",
    "TextParser",
    "MarkdownParser",
    # Factory
    "DocumentParserFactory",
]
