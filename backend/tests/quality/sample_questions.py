"""
LLM 품질 평가용 샘플 질문

Task 2.5a: LLM 기본 답변 생성
"""

SAMPLE_QUESTIONS = [
    {
        "id": "Q1",
        "question": "연차 사용 방법은 어떻게 되나요?",
        "expected_source": "휴가 규정 문서",
        "category": "휴가"
    },
    {
        "id": "Q2",
        "question": "급여 지급일은 언제인가요?",
        "expected_source": "급여 규정 문서",
        "category": "급여"
    },
    {
        "id": "Q3",
        "question": "회의실 예약은 어떻게 하나요?",
        "expected_source": "시설 이용 안내",
        "category": "시설"
    },
    {
        "id": "Q4",
        "question": "재택근무 정책이 궁금합니다.",
        "expected_source": "근무 규정 문서",
        "category": "근무"
    },
    {
        "id": "Q5",
        "question": "경조사 휴가는 며칠인가요?",
        "expected_source": "휴가 규정 문서",
        "category": "휴가"
    }
]
