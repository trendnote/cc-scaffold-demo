# Task 3.3: SearchBar 컴포넌트 구현 - 실행 계획

---

## 📋 Meta

- **Task ID**: 3.3
- **Task명**: SearchBar 컴포넌트 구현
- **예상 시간**: 4시간
- **담당**: Frontend
- **작성일**: 2026-01-04
- **상태**: Ready for Implementation
- **버전**: 1.0.0

---

## 1. Executive Summary

### 1.1 목표
검색 입력 UI를 구현하고 입력 검증, 검색 버튼 클릭, 로딩 상태 처리를 완성합니다.

### 1.2 핵심 요구사항
- **입력 검증**: 5-200자 제한, 실시간 검증
- **검색 버튼**: 클릭 시 API 호출
- **로딩 상태**: 스피너 표시
- **디바운싱**: 사용자 경험 최적화 ([SOFT RULE])

### 1.3 성공 기준
- [ ] UI 렌더링 확인
- [ ] 입력 검증 (4자 → 빨간색 테두리)
- [ ] 검색 버튼 클릭 → API 호출
- [ ] 로딩 상태 표시

---

## 2. 구현 단계

### Step 1: SearchBar 컴포넌트 기본 구조 (60분)

**`components/search/SearchBar.tsx` 생성**:
```typescript
'use client';

import { useState } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Search, Loader2 } from 'lucide-react';

interface SearchBarProps {
  onSearch: (query: string) => void;
  isLoading?: boolean;
}

export function SearchBar({ onSearch, isLoading = false }: SearchBarProps) {
  const [query, setQuery] = useState('');
  const [error, setError] = useState<string | null>(null);

  const validateQuery = (value: string): boolean => {
    if (value.length < 5) {
      setError('검색어는 5자 이상이어야 합니다.');
      return false;
    }
    if (value.length > 200) {
      setError('검색어는 200자 이하여야 합니다.');
      return false;
    }
    setError(null);
    return true;
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setQuery(value);
    if (value.length > 0) {
      validateQuery(value);
    } else {
      setError(null);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validateQuery(query)) {
      onSearch(query);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-3xl">
      <div className="flex gap-2">
        <div className="flex-1">
          <Input
            type="text"
            placeholder="무엇이든 물어보세요... (예: 연차 사용 방법)"
            value={query}
            onChange={handleInputChange}
            className={error ? 'border-red-500' : ''}
            disabled={isLoading}
          />
          {error && (
            <p className="text-sm text-red-500 mt-1">{error}</p>
          )}
        </div>
        <Button
          type="submit"
          disabled={isLoading || !!error || query.length === 0}
          className="px-6"
        >
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              검색 중...
            </>
          ) : (
            <>
              <Search className="mr-2 h-4 w-4" />
              검색
            </>
          )}
        </Button>
      </div>
    </form>
  );
}
```

### Step 2: 디바운싱 추가 ([SOFT RULE]) (45분)

**`hooks/use-debounce.ts` 생성**:
```typescript
import { useEffect, useState } from 'react';

export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}
```

**SearchBar에 디바운싱 적용**:
```typescript
import { useDebounce } from '@/hooks/use-debounce';

// ... 컴포넌트 내부
const debouncedQuery = useDebounce(query, 500);

useEffect(() => {
  if (debouncedQuery.length > 0) {
    validateQuery(debouncedQuery);
  }
}, [debouncedQuery]);
```

### Step 3: 테스트 페이지 작성 (30분)

**`app/search/page.tsx` 생성**:
```typescript
'use client';

import { SearchBar } from '@/components/search/SearchBar';
import { useSearch } from '@/hooks/use-search';
import { Card, CardContent } from '@/components/ui/card';

export default function SearchPage() {
  const searchMutation = useSearch();

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

        {searchMutation.isSuccess && (
          <Card className="w-full max-w-3xl">
            <CardContent className="pt-6">
              <pre className="whitespace-pre-wrap">
                {JSON.stringify(searchMutation.data, null, 2)}
              </pre>
            </CardContent>
          </Card>
        )}

        {searchMutation.isError && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            검색 중 오류가 발생했습니다.
          </div>
        )}
      </div>
    </main>
  );
}
```

---

## 3. 검증 기준

- [ ] UI 렌더링 확인 (http://localhost:3000/search)
- [ ] 4자 입력 → 빨간색 테두리 및 에러 메시지
- [ ] 201자 입력 → 에러 메시지
- [ ] 유효한 검색어 입력 → 검색 버튼 활성화
- [ ] 검색 버튼 클릭 → API 호출 및 로딩 상태
- [ ] 디바운싱 동작 (500ms 지연)

---

## 4. 출력물

1. `components/search/SearchBar.tsx`
2. `hooks/use-debounce.ts`
3. `app/search/page.tsx`

---

**작성자**: Claude Code (Sonnet 4.5)
**작성일**: 2026-01-04
