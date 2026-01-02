"""
문서 파서 팩토리

파일 확장자에 따라 적절한 파서를 자동으로 선택합니다.
"""

import logging
from pathlib import Path
from typing import Type

from app.services.document_parser.base_parser import (
    BaseDocumentParser,
    ParserConfig,
    UnsupportedFileTypeError,
)
from app.services.document_parser.pdf_parser import PDFParser
from app.services.document_parser.docx_parser import DOCXParser
from app.services.document_parser.text_parser import TextParser
from app.services.document_parser.markdown_parser import MarkdownParser

logger = logging.getLogger(__name__)


class DocumentParserFactory:
    """문서 파서 팩토리"""

    # 확장자별 파서 매핑
    _PARSER_MAP = {
        ".pdf": PDFParser,
        ".docx": DOCXParser,
        ".txt": TextParser,
        ".md": MarkdownParser,
        ".markdown": MarkdownParser,
    }

    @classmethod
    def get_parser(
        cls,
        file_path: str,
        config: ParserConfig = None
    ) -> BaseDocumentParser:
        """
        파일 확장자에 따라 적절한 파서 반환

        Args:
            file_path: 파싱할 파일 경로
            config: 파서 설정 (선택 사항)

        Returns:
            BaseDocumentParser: 적절한 파서 인스턴스

        Raises:
            UnsupportedFileTypeError: 지원하지 않는 파일 타입
            FileNotFoundError: 파일을 찾을 수 없음
        """
        # 파일 존재 확인
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

        # 확장자 추출
        extension = path.suffix.lower()

        # 파서 클래스 찾기
        parser_class = cls._PARSER_MAP.get(extension)

        if parser_class is None:
            supported_extensions = ", ".join(cls._PARSER_MAP.keys())
            raise UnsupportedFileTypeError(
                f"지원하지 않는 파일 확장자: {extension}. "
                f"지원하는 확장자: {supported_extensions}"
            )

        # 파서 인스턴스 생성
        parser = parser_class(config=config)

        logger.info(f"파서 선택: {parser_class.__name__} for {extension}")

        return parser

    @classmethod
    def get_supported_extensions(cls) -> list[str]:
        """
        지원하는 모든 파일 확장자 반환

        Returns:
            지원하는 확장자 리스트
        """
        return list(cls._PARSER_MAP.keys())

    @classmethod
    def is_supported(cls, file_path: str) -> bool:
        """
        파일이 지원되는지 확인

        Args:
            file_path: 확인할 파일 경로

        Returns:
            지원 여부 (True/False)
        """
        extension = Path(file_path).suffix.lower()
        return extension in cls._PARSER_MAP

    @classmethod
    def register_parser(
        cls,
        extension: str,
        parser_class: Type[BaseDocumentParser]
    ) -> None:
        """
        새로운 파서 등록 (확장성을 위한 메서드)

        Args:
            extension: 파일 확장자 (예: ".xml")
            parser_class: 파서 클래스
        """
        if not extension.startswith("."):
            extension = f".{extension}"

        extension = extension.lower()

        if extension in cls._PARSER_MAP:
            logger.warning(f"기존 파서를 덮어씁니다: {extension}")

        cls._PARSER_MAP[extension] = parser_class
        logger.info(f"파서 등록 완료: {extension} -> {parser_class.__name__}")
