# Task 3.8: 사용자 피드백 수집 UI - 실행 계획

---

## 📋 Meta

- **Task ID**: 3.8
- **Task명**: 사용자 피드백 수집 UI
- **예상 시간**: 4시간
- **담당**: Frontend + Backend
- **작성일**: 2026-01-04
- **상태**: Ready for Implementation
- **버전**: 1.0.0

---

## 1. Executive Summary

### 1.1 목표
검색 결과에 대한 만족도 평가 UI를 구현하고 피드백 저장 API를 연동합니다.

### 1.2 핵심 요구사항
- **별점 평가**: 1-5점 (Star Rating)
- **댓글 입력**: 선택적
- **피드백 저장**: API 연동
- **Toast 알림**: 저장 성공 메시지

### 1.3 성공 기준
- [ ] 별점 UI 렌더링
- [ ] 평가 저장 → DB 확인
- [ ] 댓글 저장 확인
- [ ] Toast 알림 표시

---

## 2. 구현 단계

### Backend Implementation

#### Step 1: 피드백 API 구현 (60분)

**`backend/app/routers/feedback.py` 생성**:
```python
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid
from app.routers.auth import get_current_user

router = APIRouter()


class FeedbackRequest(BaseModel):
    query_id: str
    rating: int = Field(..., ge=1, le=5, description="1-5점 평가")
    comment: Optional[str] = Field(None, max_length=500, description="댓글 (선택적)")


class FeedbackResponse(BaseModel):
    feedback_id: str
    message: str


@router.post("/", response_model=FeedbackResponse)
async def submit_feedback(
    request: FeedbackRequest,
    user: dict = Depends(get_current_user)
):
    """
    피드백 제출 API

    사용자가 검색 결과에 대해 별점(1-5) 및 댓글을 남깁니다.
    """
    feedback_id = f"feedback_{uuid.uuid4().hex[:8]}"

    # TODO: DB에 저장 (Task 3.8에서 구현)
    # 현재는 로그만 출력
    print(f"Feedback received: query_id={request.query_id}, rating={request.rating}, user={user['user_id']}")

    return FeedbackResponse(
        feedback_id=feedback_id,
        message="피드백이 저장되었습니다. 감사합니다!"
    )
```

**`backend/app/main.py`에 라우터 추가**:
```python
from app.routers import feedback

app.include_router(feedback.router, prefix="/api/v1/feedback", tags=["Feedback"])
```

---

### Frontend Implementation

#### Step 2: Toast UI 라이브러리 설치 (15분)

```bash
cd frontend
npx shadcn-ui@latest add toast
```

**`app/layout.tsx`에 Toaster 추가**:
```typescript
import { Toaster } from '@/components/ui/toaster';

// ... layout 내부
<QueryClientProvider client={queryClient}>
  <AuthProvider>
    {children}
    <Toaster />
  </AuthProvider>
  <ReactQueryDevtools initialIsOpen={false} />
</QueryClientProvider>
```

---

#### Step 3: FeedbackForm 컴포넌트 (120분)

**`components/feedback/FeedbackForm.tsx` 생성**:
```typescript
'use client';

import { useState } from 'react';
import { Star } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useFeedback } from '@/hooks/use-feedback';
import { useToast } from '@/components/ui/use-toast';

interface FeedbackFormProps {
  queryId: string;
}

export function FeedbackForm({ queryId }: FeedbackFormProps) {
  const [rating, setRating] = useState<number>(0);
  const [hoveredRating, setHoveredRating] = useState<number>(0);
  const [comment, setComment] = useState('');
  const [isSubmitted, setIsSubmitted] = useState(false);

  const feedbackMutation = useFeedback();
  const { toast } = useToast();

  const handleSubmit = () => {
    if (rating === 0) {
      toast({
        title: '평가를 선택해주세요',
        description: '별점을 1-5점 중 선택해주세요.',
        variant: 'destructive',
      });
      return;
    }

    feedbackMutation.mutate(
      {
        query_id: queryId,
        rating,
        comment: comment.trim() || undefined,
      },
      {
        onSuccess: () => {
          toast({
            title: '피드백이 저장되었습니다',
            description: '소중한 의견 감사합니다!',
          });
          setIsSubmitted(true);
        },
        onError: (error) => {
          toast({
            title: '피드백 저장 실패',
            description: error.message,
            variant: 'destructive',
          });
        },
      }
    );
  };

  if (isSubmitted) {
    return (
      <Card>
        <CardContent className="pt-6">
          <p className="text-center text-green-600 font-medium">
            ✓ 피드백이 저장되었습니다. 감사합니다!
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">이 답변이 도움이 되었나요?</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* 별점 평가 */}
        <div className="flex items-center justify-center gap-2">
          {[1, 2, 3, 4, 5].map((star) => (
            <button
              key={star}
              type="button"
              onClick={() => setRating(star)}
              onMouseEnter={() => setHoveredRating(star)}
              onMouseLeave={() => setHoveredRating(0)}
              className="transition-transform hover:scale-110"
            >
              <Star
                className={`h-8 w-8 ${
                  star <= (hoveredRating || rating)
                    ? 'fill-yellow-400 text-yellow-400'
                    : 'text-gray-300'
                }`}
              />
            </button>
          ))}
        </div>

        {rating > 0 && (
          <p className="text-center text-sm text-muted-foreground">
            {rating}점 선택됨
          </p>
        )}

        {/* 댓글 입력 (선택적) */}
        <div className="space-y-2">
          <label htmlFor="comment" className="text-sm font-medium">
            추가 의견 (선택사항)
          </label>
          <Textarea
            id="comment"
            placeholder="개선이 필요한 부분이나 추가 의견을 남겨주세요 (최대 500자)"
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            maxLength={500}
            rows={3}
          />
          <p className="text-xs text-muted-foreground text-right">
            {comment.length}/500
          </p>
        </div>

        {/* 제출 버튼 */}
        <Button
          onClick={handleSubmit}
          disabled={rating === 0 || feedbackMutation.isPending}
          className="w-full"
        >
          {feedbackMutation.isPending ? '저장 중...' : '피드백 제출'}
        </Button>
      </CardContent>
    </Card>
  );
}
```

---

#### Step 4: SearchResults에 FeedbackForm 추가 (30min)

**`components/search/SearchResults.tsx` 수정**:
```typescript
import { FeedbackForm } from '@/components/feedback/FeedbackForm';

// ... SearchResults 컴포넌트 내부에 추가
return (
  <div className="w-full max-w-4xl space-y-6">
    {/* 답변 섹션 */}
    <Card>
      {/* ... 기존 코드 */}
    </Card>

    {/* 출처 섹션 */}
    {sources.length > 0 && (
      <Card>
        {/* ... 기존 코드 */}
      </Card>
    )}

    {/* 피드백 폼 추가 */}
    <FeedbackForm queryId={data.query} />

    {/* 성능 메트릭 (개발 환경) */}
    {/* ... 기존 코드 */}
  </div>
);
```

---

#### Step 5: Textarea 컴포넌트 추가 (15min)

```bash
npx shadcn-ui@latest add textarea
```

---

## 3. 검증 기준

### Backend
- [ ] `POST /api/v1/feedback` API 동작 확인
- [ ] 1-5점 외의 값 → 422 에러
- [ ] 500자 초과 댓글 → 422 에러

### Frontend
- [ ] 별점 UI 렌더링 (http://localhost:3000/search)
- [ ] 별 클릭 → 선택 상태 변경
- [ ] 별에 마우스 오버 → hover 효과
- [ ] 평가 미선택 상태에서 제출 → 에러 Toast
- [ ] 평가 제출 성공 → 성공 Toast
- [ ] 제출 후 → "피드백이 저장되었습니다" 메시지
- [ ] 댓글 500자 제한 (실시간 카운터)

---

## 4. 출력물

### Backend
1. `backend/app/routers/feedback.py`
2. `backend/app/main.py` (수정)

### Frontend
1. `components/feedback/FeedbackForm.tsx`
2. `components/search/SearchResults.tsx` (수정)
3. `app/layout.tsx` (Toaster 추가)

---

**작성자**: Claude Code (Sonnet 4.5)
**작성일**: 2026-01-04
