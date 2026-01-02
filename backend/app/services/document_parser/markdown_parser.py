"""
Markdown 문서 파서

Markdown 파일을 읽어 구조화된 데이터를 생성합니다.
"""

import logging
import re
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


class MarkdownParser(BaseDocumentParser):
    """Markdown 문서 파서"""

    # 지원하는 파일 확장자
    SUPPORTED_EXTENSIONS = [".md", ".markdown"]

    # 지원하는 MIME 타입
    SUPPORTED_MIME_TYPES = ["text/markdown", "text/x-markdown"]

    def parse(self, file_path: str) -> ParsedDocument:
        """
        Markdown 파일을 파싱하여 구조화된 데이터 반환

        Args:
            file_path: Markdown 파일 경로

        Returns:
            ParsedDocument: 파싱된 문서 데이터

        Raises:
            FileSizeLimitExceededError: 파일 크기 제한 초과
            CorruptedFileError: 파일 읽기 실패 (인코딩 오류 등)
        """
        logger.info(f"Markdown 파싱 시작: {file_path}")

        # Step 1: 파일 존재 여부 확인
        self._validate_file_exists(file_path)

        # Step 2: 파일 타입 검증 [HARD RULE]
        self._validate_file_type(file_path)

        # Step 3: 파일 크기 검증 [HARD RULE]
        self._validate_file_size(file_path)

        # Step 4: Markdown 파일 읽기
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
                    raise CorruptedFileError(f"Markdown 파일 읽기 실패: {e2}")
        except Exception as e:
            logger.error(f"예상치 못한 에러: {e}")
            raise CorruptedFileError(f"Markdown 파일을 읽을 수 없습니다: {e}")

        # Step 5: 빈 파일 처리
        if self.config.skip_empty_pages and not content.strip():
            logger.warning(f"빈 Markdown 파일: {file_path}")
            content = ""

        total_characters = len(content)

        # Step 6: Markdown 메타데이터 추출
        markdown_metadata = self._extract_markdown_metadata(content)

        # Step 7: 파일 메타데이터 추출
        file_metadata = self._extract_file_metadata(file_path, content)

        # 메타데이터 병합
        metadata = {**file_metadata, **markdown_metadata}

        # Step 8: ParsedDocument 생성 (전체 텍스트를 1페이지로 처리)
        pages = [
            ParsedPage(
                page_number=1,
                content=content,
                metadata={
                    "line_count": len(content.splitlines()),
                    "encoding": self.config.encoding,
                    "heading_count": markdown_metadata.get("heading_count", 0),
                    "code_block_count": markdown_metadata.get("code_block_count", 0),
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
            f"Markdown 파싱 완료: {file_path}, "
            f"라인 {len(content.splitlines())}개, 문자 {total_characters}개"
        )

        return result

    def _extract_markdown_metadata(self, content: str) -> Dict[str, Any]:
        """
        Markdown 특화 메타데이터 추출

        Args:
            content: Markdown 내용

        Returns:
            메타데이터 딕셔너리
        """
        metadata = {}

        try:
            # 헤딩 카운트 (# 으로 시작하는 라인)
            heading_pattern = r"^#{1,6}\s+.+"
            headings = re.findall(heading_pattern, content, re.MULTILINE)
            metadata["heading_count"] = len(headings)

            # 코드 블록 카운트 (``` 또는 ~~~로 감싸진 블록)
            code_block_pattern = r"```[\s\S]*?```|~~~[\s\S]*?~~~"
            code_blocks = re.findall(code_block_pattern, content)
            metadata["code_block_count"] = len(code_blocks)

            # 링크 카운트 ([text](url) 형태)
            link_pattern = r"\[([^\]]+)\]\(([^\)]+)\)"
            links = re.findall(link_pattern, content)
            metadata["link_count"] = len(links)

            # 이미지 카운트 (![alt](url) 형태)
            image_pattern = r"!\[([^\]]*)\]\(([^\)]+)\)"
            images = re.findall(image_pattern, content)
            metadata["image_count"] = len(images)

            # 리스트 아이템 카운트 (- 또는 * 또는 1. 으로 시작)
            list_pattern = r"^[\*\-\+]\s+.+|^\d+\.\s+.+"
            list_items = re.findall(list_pattern, content, re.MULTILINE)
            metadata["list_item_count"] = len(list_items)

        except Exception as e:
            logger.warning(f"Markdown 메타데이터 추출 실패: {e}")

        return metadata

    def _extract_file_metadata(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        파일 메타데이터 추출

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
            logger.warning(f"파일 메타데이터 추출 실패: {e}")

        return metadata
