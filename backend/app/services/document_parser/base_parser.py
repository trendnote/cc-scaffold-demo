"""
문서 파서 추상 클래스 및 공통 데이터 모델

이 모듈은 모든 문서 파서가 구현해야 하는 인터페이스와
공통 데이터 구조를 정의합니다.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


class ParsedPage(BaseModel):
    """파싱된 페이지 정보"""
    page_number: int = Field(..., ge=1, description="페이지 번호 (1부터 시작)")
    content: str = Field(..., min_length=0, description="페이지 텍스트 내용")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="추가 메타데이터")


class ParsedDocument(BaseModel):
    """파싱된 문서 전체 정보"""
    pages: List[ParsedPage] = Field(..., min_length=0, description="페이지 리스트")
    total_pages: int = Field(..., ge=0, description="전체 페이지 수")
    total_characters: int = Field(..., ge=0, description="전체 문자 수")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="문서 메타데이터")


class ParserConfig(BaseModel):
    """파서 설정"""
    max_file_size_mb: int = Field(default=100, ge=1, le=500, description="최대 파일 크기 (MB)")
    skip_empty_pages: bool = Field(default=True, description="빈 페이지 건너뛰기 여부")
    encoding: str = Field(default="utf-8", description="텍스트 인코딩")


class DocumentParserError(Exception):
    """문서 파서 기본 에러"""
    pass


class FileSizeLimitExceededError(DocumentParserError):
    """파일 크기 제한 초과 에러"""
    pass


class CorruptedFileError(DocumentParserError):
    """손상된 파일 에러"""
    pass


class EncryptedFileError(DocumentParserError):
    """암호화된 파일 에러"""
    pass


class MaliciousFileError(DocumentParserError):
    """악성 파일 에러"""
    pass


class UnsupportedFileTypeError(DocumentParserError):
    """지원하지 않는 파일 타입 에러"""
    pass


class BaseDocumentParser(ABC):
    """문서 파서 추상 클래스"""

    # 지원하는 파일 확장자 (하위 클래스에서 오버라이드)
    SUPPORTED_EXTENSIONS: List[str] = []

    # 지원하는 MIME 타입 (하위 클래스에서 오버라이드)
    SUPPORTED_MIME_TYPES: List[str] = []

    def __init__(self, config: ParserConfig = None):
        self.config = config or ParserConfig()

    @abstractmethod
    def parse(self, file_path: str) -> ParsedDocument:
        """
        문서를 파싱하여 구조화된 데이터 반환

        Args:
            file_path: 파싱할 파일 경로

        Returns:
            ParsedDocument: 파싱된 문서 데이터

        Raises:
            FileSizeLimitExceededError: 파일 크기 제한 초과
            CorruptedFileError: 손상된 파일
            EncryptedFileError: 암호화된 파일
            MaliciousFileError: 악성 파일
        """
        pass

    def _validate_file_exists(self, file_path: str) -> None:
        """
        파일 존재 여부 확인

        Args:
            file_path: 확인할 파일 경로

        Raises:
            FileNotFoundError: 파일이 없을 때
        """
        if not Path(file_path).exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

    def _validate_file_type(self, file_path: str) -> None:
        """
        파일 타입 검증 [HARD RULE]

        Args:
            file_path: 검증할 파일 경로

        Raises:
            UnsupportedFileTypeError: 지원하지 않는 파일 타입
        """
        path = Path(file_path)

        # Step 1: 확장자 검증
        extension = path.suffix.lower()
        if extension not in self.SUPPORTED_EXTENSIONS:
            raise UnsupportedFileTypeError(
                f"지원하지 않는 파일 확장자: {extension}. "
                f"지원하는 확장자: {', '.join(self.SUPPORTED_EXTENSIONS)}"
            )

        # Step 2: MIME 타입 검증 (optional - python-magic 설치된 경우만)
        # python-magic이 없어도 동작하도록 optional 처리
        try:
            import magic
            mime_type = magic.from_file(file_path, mime=True)

            if mime_type not in self.SUPPORTED_MIME_TYPES:
                logger.warning(
                    f"MIME 타입 불일치: {mime_type}. "
                    f"지원하는 타입: {', '.join(self.SUPPORTED_MIME_TYPES)}. "
                    f"확장자 검증은 통과했으므로 계속 진행합니다."
                )
        except ImportError:
            # python-magic이 설치되지 않은 경우 - 확장자 검증만으로 충분
            logger.debug("python-magic이 설치되지 않음. 확장자 검증만 수행합니다.")
        except Exception as e:
            # MIME 타입 검증 실패 - 확장자 검증으로 fallback
            logger.warning(f"MIME 타입 검증 실패 (확장자 검증으로 대체): {e}")

    def _validate_file_size(self, file_path: str) -> None:
        """
        파일 크기 검증 [HARD RULE]

        Args:
            file_path: 검증할 파일 경로

        Raises:
            FileSizeLimitExceededError: 파일 크기 제한 초과
        """
        import os
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb > self.config.max_file_size_mb:
            raise FileSizeLimitExceededError(
                f"파일 크기 {file_size_mb:.2f}MB가 "
                f"제한 {self.config.max_file_size_mb}MB를 초과했습니다."
            )
