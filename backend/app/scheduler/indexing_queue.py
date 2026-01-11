"""
인덱싱 작업 큐 관리
"""
from typing import List, Dict
import asyncio
from sqlalchemy.orm import Session
from app.services.document_indexer import DocumentIndexer
from app.db.base import SessionLocal
import logging

logger = logging.getLogger(__name__)


class IndexingQueue:
    """인덱싱 작업 큐"""

    def __init__(self, max_concurrent: int = 5):
        """
        Args:
            max_concurrent: 최대 동시 처리 수
        """
        self.max_concurrent = max_concurrent

    async def process_documents(
        self,
        documents: List[Dict[str, str]]
    ) -> Dict[str, int]:
        """
        문서 배치 인덱싱

        Args:
            documents: 문서 리스트

        Returns:
            Dict: 처리 결과
                - success: 성공 개수
                - failed: 실패 개수
                - total: 전체 개수
        """
        if not documents:
            return {'success': 0, 'failed': 0, 'total': 0}

        results = {
            'success': 0,
            'failed': 0,
            'total': len(documents)
        }

        # 세마포어로 동시 처리 수 제한
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def process_with_semaphore(doc: Dict[str, str]):
            async with semaphore:
                return await self._process_single_document(doc)

        # 병렬 처리
        tasks = [
            process_with_semaphore(doc)
            for doc in documents
        ]

        completed = await asyncio.gather(*tasks, return_exceptions=True)

        # 결과 집계
        for result in completed:
            if isinstance(result, Exception):
                results['failed'] += 1
                logger.error(f"Indexing failed: {result}")
            elif result:
                results['success'] += 1
            else:
                results['failed'] += 1

        logger.info(
            f"Indexing completed: {results['success']}/{results['total']} succeeded"
        )

        return results

    async def _process_single_document(
        self,
        doc: Dict[str, str]
    ) -> bool:
        """
        단일 문서 인덱싱 (재시도 포함)

        Args:
            doc: 문서 정보

        Returns:
            bool: 성공 여부
        """
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                # 동기 작업을 비동기로 래핑
                result = await asyncio.to_thread(
                    self._index_document_sync,
                    doc['file_path']
                )
                return result

            except Exception as e:
                retry_count += 1
                logger.warning(
                    f"Indexing retry {retry_count}/{max_retries}: {e}"
                )

                if retry_count >= max_retries:
                    logger.error(
                        f"Indexing failed after {max_retries} retries: "
                        f"{doc['file_path']}"
                    )
                    return False

                # Exponential backoff
                await asyncio.sleep(2 ** retry_count)

        return False

    def _index_document_sync(self, file_path: str) -> bool:
        """
        동기 방식으로 문서 인덱싱 (실제 처리)

        Args:
            file_path: 파일 경로

        Returns:
            bool: 성공 여부
        """
        db: Session = SessionLocal()
        try:
            indexer = DocumentIndexer(db_session=db)
            result = indexer.index_document(file_path)
            return result.success
        finally:
            db.close()
