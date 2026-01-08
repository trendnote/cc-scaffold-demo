# Task 3.7: 검색 히스토리 페이지 - 실행 계획

---

## 📋 Meta

- **Task ID**: 3.7
- **Task명**: 검색 히스토리 페이지
- **예상 시간**: 4시간
- **담당**: Frontend
- **작성일**: 2026-01-04
- **상태**: Ready for Implementation
- **버전**: 1.0.0

---

## 1. Executive Summary

### 1.1 목표
사용자 검색 히스토리를 조회하고 페이지네이션을 구현합니다.

### 1.2 핵심 요구사항
- **히스토리 리스트**: 검색어, 타임스탬프, 평점
- **클릭 동작**: 히스토리 클릭 → 검색 결과 표시
- **페이지네이션**: 10개씩
- **빈 상태**: "검색 기록이 없습니다"

### 1.3 성공 기준
- [ ] 히스토리 리스트 렌더링
- [ ] 페이지네이션 동작 확인
- [ ] 히스토리 클릭 → 검색 결과 표시
- [ ] 빈 상태 UI 확인

---

## 2. 구현 단계

### Step 1: 히스토리 리스트 컴포넌트 (120분)

**`components/history/HistoryList.tsx` 생성**:
```typescript
'use client';

import { SearchHistoryItem } from '@/types/api';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Star, Clock } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { ko } from 'date-fns/locale';

interface HistoryListProps {
  items: SearchHistoryItem[];
  onItemClick: (item: SearchHistoryItem) => void;
}

export function HistoryList({ items, onItemClick }: HistoryListProps) {
  if (items.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <p className="text-lg">검색 기록이 없습니다</p>
        <p className="text-sm mt-2">첫 검색을 시작해보세요!</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {items.map((item) => (
        <Card
          key={item.query_id}
          className="cursor-pointer hover:bg-gray-50 transition-colors"
          onClick={() => onItemClick(item)}
        >
          <CardContent className="p-4">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 space-y-1">
                {/* 검색어 */}
                <h3 className="font-semibold text-lg">{item.query}</h3>

                {/* 답변 미리보기 */}
                <p className="text-sm text-muted-foreground line-clamp-2">
                  {item.answer}
                </p>

                {/* 타임스탬프 */}
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <Clock className="h-3 w-3" />
                  <span>
                    {formatDistanceToNow(new Date(item.created_at), {
                      addSuffix: true,
                      locale: ko,
                    })}
                  </span>
                </div>
              </div>

              {/* 평점 */}
              {item.rating && (
                <div className="flex items-center gap-1">
                  {[...Array(5)].map((_, i) => (
                    <Star
                      key={i}
                      className={`h-4 w-4 ${
                        i < item.rating!
                          ? 'fill-yellow-400 text-yellow-400'
                          : 'text-gray-300'
                      }`}
                    />
                  ))}
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
```

---

### Step 2: 페이지네이션 컴포넌트 (60분)

**필요한 패키지 설치**:
```bash
npm install date-fns
```

**`components/history/Pagination.tsx` 생성**:
```typescript
import { Button } from '@/components/ui/button';
import { ChevronLeft, ChevronRight } from 'lucide-react';

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

export function Pagination({
  currentPage,
  totalPages,
  onPageChange,
}: PaginationProps) {
  if (totalPages <= 1) return null;

  return (
    <div className="flex items-center justify-center gap-2 mt-6">
      <Button
        variant="outline"
        size="sm"
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
      >
        <ChevronLeft className="h-4 w-4" />
        이전
      </Button>

      <div className="flex items-center gap-1">
        {[...Array(totalPages)].map((_, i) => {
          const page = i + 1;
          // 페이지가 너무 많으면 일부만 표시
          if (
            totalPages > 7 &&
            page !== 1 &&
            page !== totalPages &&
            Math.abs(page - currentPage) > 2
          ) {
            if (page === 2 || page === totalPages - 1) {
              return <span key={page}>...</span>;
            }
            return null;
          }

          return (
            <Button
              key={page}
              variant={currentPage === page ? 'default' : 'outline'}
              size="sm"
              onClick={() => onPageChange(page)}
            >
              {page}
            </Button>
          );
        })}
      </div>

      <Button
        variant="outline"
        size="sm"
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
      >
        다음
        <ChevronRight className="h-4 w-4" />
      </Button>
    </div>
  );
}
```

---

### Step 3: 히스토리 페이지 (90min)

**`app/history/page.tsx` 생성**:
```typescript
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useHistory } from '@/hooks/use-history';
import { HistoryList } from '@/components/history/HistoryList';
import { Pagination } from '@/components/history/Pagination';
import { SearchHistoryItem } from '@/types/api';
import { Loader2 } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';

export default function HistoryPage() {
  const router = useRouter();
  const [page, setPage] = useState(1);
  const pageSize = 10;

  const { data, isLoading, error } = useHistory(page, pageSize);

  const handleItemClick = (item: SearchHistoryItem) => {
    // 검색 페이지로 이동하면서 쿼리 전달
    router.push(`/search?query=${encodeURIComponent(item.query)}`);
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive" className="max-w-2xl mx-auto mt-8">
        <AlertDescription>
          히스토리를 불러오는 중 오류가 발생했습니다.
        </AlertDescription>
      </Alert>
    );
  }

  const totalPages = data ? Math.ceil(data.total / pageSize) : 1;

  return (
    <main className="container mx-auto p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">검색 히스토리</h1>

        {data && (
          <>
            <HistoryList items={data.items} onItemClick={handleItemClick} />
            <Pagination
              currentPage={page}
              totalPages={totalPages}
              onPageChange={setPage}
            />
          </>
        )}
      </div>
    </main>
  );
}
```

---

### Step 4: 검색 페이지 쿼리 파라미터 처리 (30min)

**`app/search/page.tsx` 수정**:
```typescript
'use client';

import { useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { SearchBar } from '@/components/search/SearchBar';
import { SearchResults } from '@/components/search/SearchResults';
import { SearchSkeleton } from '@/components/search/SearchSkeleton';
import { SearchError } from '@/components/search/SearchError';
import { useSearch } from '@/hooks/use-search';

export default function SearchPage() {
  const searchParams = useSearchParams();
  const searchMutation = useSearch();

  // URL 쿼리 파라미터에서 검색어 가져오기
  const queryParam = searchParams.get('query');

  useEffect(() => {
    if (queryParam) {
      searchMutation.mutate({ query: queryParam, limit: 5 });
    }
  }, [queryParam]);

  const handleSearch = (query: string) => {
    searchMutation.mutate({ query, limit: 5 });
  };

  return (
    <main className="container mx-auto p-8">
      <div className="flex flex-col items-center gap-8">
        <h1 className="text-4xl font-bold">사내 정보 검색</h1>

        <SearchBar
          onSearch={handleSearch}
          isLoading={searchMutation.isPending}
        />

        {searchMutation.isPending && <SearchSkeleton />}

        {searchMutation.isSuccess && (
          <SearchResults data={searchMutation.data} />
        )}

        {searchMutation.isError && (
          <SearchError
            error={searchMutation.error}
            onRetry={() => searchMutation.reset()}
          />
        )}
      </div>
    </main>
  );
}
```

---

## 3. 검증 기준

- [ ] 히스토리 페이지 접속 (http://localhost:3000/history)
- [ ] 히스토리 리스트 렌더링 (검색어, 답변 미리보기, 타임스탬프, 평점)
- [ ] 페이지네이션 버튼 동작 (이전/다음, 페이지 번호)
- [ ] 히스토리 항목 클릭 → /search?query=... 리다이렉트
- [ ] 검색 페이지에서 쿼리 파라미터로 자동 검색
- [ ] 빈 상태 UI 표시 (검색 기록 없음)

---

## 4. 출력물

1. `components/history/HistoryList.tsx`
2. `components/history/Pagination.tsx`
3. `app/history/page.tsx`
4. `app/search/page.tsx` (수정)

---

**작성자**: Claude Code (Sonnet 4.5)
**작성일**: 2026-01-04
