"""
문서 저장소 스캔 및 신규 문서 감지
"""
from pathlib import Path
from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.document import Document
import logging

logger = logging.getLogger(__name__)


class FileScanner:
    """문서 저장소 스캐너"""

    SUPPORTED_EXTENSIONS = {'.pdf', '.docx', '.txt', '.md'}

    def __init__(self, watch_dir: str):
        """
        Args:
            watch_dir: 모니터링할 디렉토리 경로
        """
        self.watch_dir = Path(watch_dir)
        if not self.watch_dir.exists():
            logger.warning(f"Directory not found: {watch_dir}, creating it...")
            self.watch_dir.mkdir(parents=True, exist_ok=True)

    async def scan_for_new_documents(
        self,
        db: AsyncSession
    ) -> List[Dict[str, str]]:
        """
        신규 문서 스캔

        Args:
            db: DB 세션

        Returns:
            List[Dict]: 신규 문서 리스트
                - file_path: 파일 경로
                - file_name: 파일명
                - file_type: 파일 타입
        """
        new_docs = []

        # 저장소 전체 스캔
        for file_path in self.watch_dir.rglob('*'):
            if not file_path.is_file():
                continue

            # 심볼릭 링크 차단 (보안)
            if file_path.is_symlink():
                logger.warning(f"Skipping symlink: {file_path}")
                continue

            if file_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
                continue

            # DB에 이미 존재하는지 확인
            exists = await self._check_document_exists(
                db,
                str(file_path.absolute())
            )

            if not exists:
                new_docs.append({
                    'file_path': str(file_path.absolute()),
                    'file_name': file_path.name,
                    'file_type': file_path.suffix.lower()[1:]  # .pdf -> pdf
                })

        logger.info(f"Found {len(new_docs)} new documents")
        return new_docs

    async def _check_document_exists(
        self,
        db: AsyncSession,
        file_path: str
    ) -> bool:
        """
        문서가 DB에 존재하는지 확인

        Args:
            db: DB 세션
            file_path: 파일 경로

        Returns:
            bool: 존재 여부
        """
        from sqlalchemy import select

        stmt = select(Document).where(
            Document.source == file_path
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none() is not None
