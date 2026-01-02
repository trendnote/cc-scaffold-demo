"""
TXT 문서 파서

일반 텍스트 파일을 읽어 구조화된 데이터를 생성합니다.
"""

import logging
from pathlib import Path
from typing import Dict, Any

from app.services.document_parser.base_parser import (
    BaseDocumentParser,
    ParsedDocument,
    ParsedPage,
    ParserConfig,
    FileSizeLimitExceededError,
    CorruptedFileError,
)

logger = logging.getLogger(__name__)


class TextParser(BaseDocumentParser):
    """TXT 문서 파서"""

    # 지원하는 파일 확장자
    SUPPORTED_EXTENSIONS = [".txt"]

    # 지원하는 MIME 타입
    SUPPORTED_MIME_TYPES = ["text/plain"]

    def parse(self, file_path: str) -> ParsedDocument:
        """
        TXT 파일을 파싱하여 구조화된 데이터 반환

        Args:
            file_path: TXT 파일 경로

        Returns:
            ParsedDocument: 파싱된 문서 데이터

        Raises:
            FileSizeLimitExceededError: 파일 크기 제한 초과
            CorruptedFileError: 파일 읽기 실패 (인코딩 오류 등)
        """
        logger.info(f"TXT 파싱 시작: {file_path}")

        # Step 1: 파일 존재 여부 확인
        self._validate_file_exists(file_path)

        # Step 2: 파일 타입 검증 [HARD RULE]
        self._validate_file_type(file_path)

        # Step 3: 파일 크기 검증 [HARD RULE]
        self._validate_file_size(file_path)

        # Step 4: 텍스트 파일 읽기
        try:
            with open(file_path, "r", encoding=self.config.encoding) as f:
                content = f.read()
        except UnicodeDecodeError as e:
            logger.error(f"인코딩 오류 ({self.config.encoding}): {e}")
            # 다른 인코딩으로 재시도
            try:
                logger.info("UTF-8 인코딩으로 재시도")
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except UnicodeDecodeError:
                logger.error("UTF-8 인코딩 실패, latin-1로 재시도")
                try:
                    with open(file_path, "r", encoding="latin-1") as f:
                        content = f.read()
                except Exception as e2:
                    raise CorruptedFileError(f"텍스트 파일 읽기 실패: {e2}")
        except Exception as e:
            logger.error(f"예상치 못한 에러: {e}")
            raise CorruptedFileError(f"텍스트 파일을 읽을 수 없습니다: {e}")

        # Step 5: 빈 파일 처리
        if self.config.skip_empty_pages and not content.strip():
            logger.warning(f"빈 텍스트 파일: {file_path}")
            content = ""

        total_characters = len(content)

        # Step 6: 메타데이터 추출
        metadata = self._extract_metadata(file_path, content)

        # Step 7: ParsedDocument 생성 (전체 텍스트를 1페이지로 처리)
        pages = [
            ParsedPage(
                page_number=1,
                content=content,
                metadata={
                    "line_count": len(content.splitlines()),
                    "encoding": self.config.encoding,
                }
            )
        ]

        result = ParsedDocument(
            pages=pages,
            total_pages=1,
            total_characters=total_characters,
            metadata=metadata,
        )

        logger.info(
            f"TXT 파싱 완료: {file_path}, "
            f"라인 {len(content.splitlines())}개, 문자 {total_characters}개"
        )

        return result

    def _extract_metadata(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        TXT 메타데이터 추출

        Args:
            file_path: 파일 경로
            content: 파일 내용

        Returns:
            메타데이터 딕셔너리
        """
        metadata = {}

        try:
            path = Path(file_path)
            stat = path.stat()

            metadata = {
                "file_name": path.name,
                "file_size_bytes": stat.st_size,
                "created": str(stat.st_ctime),
                "modified": str(stat.st_mtime),
                "line_count": len(content.splitlines()),
                "word_count": len(content.split()),
            }
        except Exception as e:
            logger.warning(f"메타데이터 추출 실패: {e}")

        return metadata
