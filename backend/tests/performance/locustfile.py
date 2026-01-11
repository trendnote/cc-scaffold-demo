"""
Performance Test Scenarios

Task 4.3c: 성능 테스트

목표:
- P95 응답 시간 < 30초
- 동시 사용자 100명 처리
- 에러율 < 1%
"""
from locust import HttpUser, task, between
import random


class RAGPlatformUser(HttpUser):
    """RAG 플랫폼 사용자 시뮬레이션"""

    wait_time = between(1, 3)  # 1-3초 대기
    host = "http://localhost:8000"

    def on_start(self):
        """테스트 시작 시 로그인"""
        # 로그인하여 토큰 얻기
        response = self.client.post(
            "/api/v1/auth/login",
            json={
                "email": "user@example.com",
                "password": "password123"
            }
        )

        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
        else:
            raise Exception("Login failed")

    @task(10)
    def search_query(self):
        """검색 쿼리 (가장 빈번한 작업)"""
        queries = [
            "연차 사용 방법",
            "휴가 신청 절차",
            "급여 지급일",
            "출퇴근 시간",
            "회의실 예약 방법",
            "복지 제도",
            "재택 근무 정책",
            "교육 지원 제도",
        ]

        query = random.choice(queries)

        self.client.post(
            "/api/v1/search/",
            json={"query": query, "limit": 5},
            headers={"Authorization": f"Bearer {self.token}"},
            name="/api/v1/search/ (검색)"
        )

    @task(3)
    def view_history(self):
        """히스토리 조회"""
        self.client.get(
            "/api/v1/users/me/history?page=1&page_size=10",
            headers={"Authorization": f"Bearer {self.token}"},
            name="/api/v1/users/me/history (히스토리)"
        )

    @task(1)
    def submit_feedback(self):
        """피드백 제출"""
        self.client.post(
            "/api/v1/feedback/",
            json={
                "query_id": "test_query_123",
                "rating": random.randint(1, 5),
                "comment": "테스트 피드백"
            },
            headers={"Authorization": f"Bearer {self.token}"},
            name="/api/v1/feedback/ (피드백)"
        )
