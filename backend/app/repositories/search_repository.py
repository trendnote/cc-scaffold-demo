"""
검색 히스토리 Repository

Task 2.7: 검색 쿼리 및 응답 저장, 히스토리 조회
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
import uuid
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from app.models.search import SearchQuery, SearchResponse
from app.schemas.search import SearchQueryResponse

logger = logging.getLogger(__name__)


class SearchRepository:
    """검색 히스토리 저장 및 조회 Repository"""

    def __init__(self, db: AsyncSession):
        """
        Repository 초기화

        Args:
            db: AsyncSession 인스턴스
        """
        self.db = db

    async def save_query(
        self,
        user_id: Optional[UUID],
        query: str,
        session_id: Optional[str] = None
    ) -> UUID:
        """
        검색 쿼리 저장

        Args:
            user_id: 사용자 ID (UUID, nullable for now until Task 3.x JWT auth)
            query: 검색어
            session_id: 세션 ID (선택적)

        Returns:
            UUID: 생성된 query_id

        Raises:
            Exception: DB 저장 실패 시
        """
        try:
            # user_id가 None이면 임시 사용자 ID 사용 (Task 3.x에서 해결)
            if user_id is None:
                # 임시로 고정된 UUID 사용 (실제로는 JWT에서 추출)
                user_id = UUID("00000000-0000-0000-0000-000000000001")

            search_query = SearchQuery(
                user_id=user_id,
                query=query,
                session_id=session_id
            )

            self.db.add(search_query)
            await self.db.commit()
            await self.db.refresh(search_query)

            logger.info(
                f"검색 쿼리 저장 완료: query_id={search_query.id}, "
                f"user_id={user_id}, query='{query[:50]}...'"
            )

            return search_query.id

        except Exception as e:
            await self.db.rollback()
            logger.error(f"검색 쿼리 저장 실패: {e}")
            raise

    async def save_response(
        self,
        query_id: UUID,
        response: SearchQueryResponse
    ) -> None:
        """
        검색 응답 저장

        Args:
            query_id: 쿼리 ID
            response: 검색 응답 스키마 (SearchQueryResponse)

        Raises:
            Exception: DB 저장 실패 시 (단, 이 경우에도 검색은 성공으로 처리)
        """
        try:
            search_response = SearchResponse(
                query_id=query_id,
                answer=response.answer,
                sources=[s.model_dump() for s in response.sources],
                performance=response.performance.model_dump(),
                response_metadata=response.metadata.model_dump(),
                response_time_ms=response.performance.total_time_ms
            )

            self.db.add(search_response)
            await self.db.commit()

            logger.info(
                f"검색 응답 저장 완료: query_id={query_id}, "
                f"response_time={response.performance.total_time_ms}ms, "
                f"sources={len(response.sources)}"
            )

        except Exception as e:
            await self.db.rollback()
            logger.error(f"검색 응답 저장 실패: {e}")
            # [중요] 응답 저장 실패해도 검색은 성공으로 처리
            logger.warning("응답 저장 실패했지만 검색은 계속 진행합니다")
            # Exception을 다시 raise하지 않음

    async def get_user_history(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        사용자 검색 히스토리 조회 (페이지네이션)

        Args:
            user_id: 사용자 ID
            page: 페이지 번호 (1부터 시작)
            page_size: 페이지 크기

        Returns:
            dict: {
                "items": List[dict],
                "total": int,
                "page": int,
                "page_size": int,
                "total_pages": int
            }

        Raises:
            Exception: DB 조회 실패 시
        """
        try:
            # 전체 개수 조회
            count_stmt = select(func.count()).select_from(SearchQuery).where(
                SearchQuery.user_id == user_id
            )
            count_result = await self.db.execute(count_stmt)
            total = count_result.scalar()

            # 페이지네이션 쿼리
            offset = (page - 1) * page_size

            # 검색 쿼리 조회 (최신순 정렬)
            query_stmt = (
                select(SearchQuery)
                .where(SearchQuery.user_id == user_id)
                .order_by(desc(SearchQuery.timestamp))
                .offset(offset)
                .limit(page_size)
            )
            query_result = await self.db.execute(query_stmt)
            queries = query_result.scalars().all()

            # 응답 데이터 구성
            items = []
            for query in queries:
                # 관련 응답 조회
                response_stmt = select(SearchResponse).where(
                    SearchResponse.query_id == query.id
                )
                response_result = await self.db.execute(response_stmt)
                response = response_result.scalar_one_or_none()

                item = {
                    "query_id": str(query.id),
                    "query": query.query,
                    "answer": response.answer if response else None,
                    "sources_count": len(response.sources) if response else 0,
                    "response_time_ms": response.response_time_ms if response else None,
                    "created_at": query.timestamp.isoformat()
                }

                items.append(item)

            total_pages = (total + page_size - 1) // page_size if total > 0 else 0

            logger.info(
                f"히스토리 조회 완료: user_id={user_id}, "
                f"page={page}, total={total}, items={len(items)}"
            )

            return {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            }

        except Exception as e:
            logger.error(f"히스토리 조회 실패: {e}")
            raise
