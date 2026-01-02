"""
PDF 문서 파서

pypdf를 사용하여 PDF 파일에서 텍스트를 추출하고
페이지 번호 및 메타데이터를 포함한 구조화된 데이터를 생성합니다.
"""

import logging
from pathlib import Path
from typing import Dict, Any
import pypdf
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.services.document_parser.base_parser import (
    BaseDocumentParser,
    ParsedDocument,
    ParsedPage,
    ParserConfig,
    FileSizeLimitExceededError,
    CorruptedFileError,
    EncryptedFileError,
    MaliciousFileError,
)

logger = logging.getLogger(__name__)


class PDFParser(BaseDocumentParser):
    """PDF 문서 파서"""

    # 지원하는 파일 확장자
    SUPPORTED_EXTENSIONS = [".pdf"]

    # 지원하는 MIME 타입
    SUPPORTED_MIME_TYPES = ["application/pdf"]

    def parse(self, file_path: str) -> ParsedDocument:
        """
        PDF 파일을 파싱하여 구조화된 데이터 반환

        Args:
            file_path: PDF 파일 경로

        Returns:
            ParsedDocument: 파싱된 문서 데이터

        Raises:
            FileSizeLimitExceededError: 파일 크기 제한 초과
            CorruptedFileError: 손상된 파일
            EncryptedFileError: 암호화된 파일
            MaliciousFileError: 악성 파일
        """
        logger.info(f"PDF 파싱 시작: {file_path}")

        # Step 1: 파일 존재 여부 확인
        self._validate_file_exists(file_path)

        # Step 2: 파일 타입 검증 [HARD RULE]
        self._validate_file_type(file_path)

        # Step 3: 파일 크기 검증 [HARD RULE]
        self._validate_file_size(file_path)

        # Step 4: PDF 읽기
        try:
            reader = PdfReader(file_path)
        except PdfReadError as e:
            logger.error(f"PDF 읽기 실패: {e}")
            raise CorruptedFileError(f"손상된 PDF 파일입니다: {e}")
        except Exception as e:
            logger.error(f"예상치 못한 에러: {e}")
            raise CorruptedFileError(f"PDF 파일을 읽을 수 없습니다: {e}")

        # Step 5: 암호화 확인
        if reader.is_encrypted:
            logger.warning(f"암호화된 PDF 파일: {file_path}")
            raise EncryptedFileError("암호화된 PDF 파일은 지원하지 않습니다.")

        # Step 6: 악성 코드 검사 (JavaScript 확인)
        self._check_malicious_content(reader)

        # Step 7: 페이지별 텍스트 추출
        pages = []
        total_pages = len(reader.pages)
        total_characters = 0

        for page_num, page in enumerate(reader.pages, start=1):
            try:
                text = page.extract_text()

                # 빈 페이지 처리
                if self.config.skip_empty_pages and not text.strip():
                    logger.debug(f"빈 페이지 건너뛰기: {page_num}")
                    continue

                # 페이지 데이터 생성
                parsed_page = ParsedPage(
                    page_number=page_num,
                    content=text,
                    metadata={
                        "rotation": page.get("/Rotate", 0),
                        "mediabox": str(page.mediabox) if hasattr(page, 'mediabox') else None,
                    }
                )
                pages.append(parsed_page)
                total_characters += len(text)

            except Exception as e:
                logger.error(f"페이지 {page_num} 추출 실패: {e}")
                # 페이지 추출 실패해도 계속 진행 (best effort)
                continue

        # Step 8: 문서 메타데이터 추출
        metadata = self._extract_metadata(reader)

        # Step 9: 결과 반환
        result = ParsedDocument(
            pages=pages,
            total_pages=total_pages,
            total_characters=total_characters,
            metadata=metadata,
        )

        logger.info(
            f"PDF 파싱 완료: {file_path}, "
            f"페이지 {total_pages}개, 문자 {total_characters}개"
        )

        return result

    def _check_malicious_content(self, reader: PdfReader) -> None:
        """
        악성 콘텐츠 검사 [HARD RULE]

        Args:
            reader: PDF 리더 객체

        Raises:
            MaliciousFileError: 악성 콘텐츠 발견 시
        """
        # JavaScript 검사
        if hasattr(reader, "get_fields") and reader.get_fields():
            for field_name, field_value in reader.get_fields().items():
                if "JavaScript" in str(field_value) or "/JS" in str(field_value):
                    logger.error(f"악성 JavaScript 발견: {field_name}")
                    raise MaliciousFileError(
                        "JavaScript가 포함된 PDF는 보안상 지원하지 않습니다."
                    )

        # 추가 보안 검사 (필요 시 확장)
        # - 외부 링크 검사
        # - 임베디드 파일 검사
        # - 매크로 검사

    def _extract_metadata(self, reader: PdfReader) -> Dict[str, Any]:
        """
        PDF 메타데이터 추출

        Args:
            reader: PDF 리더 객체

        Returns:
            메타데이터 딕셔너리
        """
        metadata = {}

        try:
            if reader.metadata:
                metadata = {
                    "title": reader.metadata.get("/Title"),
                    "author": reader.metadata.get("/Author"),
                    "subject": reader.metadata.get("/Subject"),
                    "creator": reader.metadata.get("/Creator"),
                    "producer": reader.metadata.get("/Producer"),
                    "creation_date": reader.metadata.get("/CreationDate"),
                    "modification_date": reader.metadata.get("/ModDate"),
                }
                # None 값 제거
                metadata = {k: v for k, v in metadata.items() if v is not None}
        except Exception as e:
            logger.warning(f"메타데이터 추출 실패: {e}")

        return metadata
