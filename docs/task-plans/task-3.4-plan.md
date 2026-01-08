# Task 3.4: SearchResults 컴포넌트 구현 - 실행 계획

---

## 📋 Meta

- **Task ID**: 3.4
- **Task명**: SearchResults 컴포넌트 구현
- **예상 시간**: 6시간
- **담당**: Frontend
- **작성일**: 2026-01-04
- **상태**: Ready for Implementation
- **버전**: 1.0.0

---

## 1. Executive Summary

### 1.1 목표
검색 결과 표시 UI를 구현하고 답변, 출처 리스트, 로딩/에러 상태를 처리합니다.

### 1.2 핵심 요구사항
- **답변 표시**: Markdown 렌더링
- **출처 리스트**: 문서 제목, 링크, 페이지 번호, 관련도 점수
- **로딩 상태**: 스켈레톤 UI
- **에러 상태**: 에러 메시지 (빨간색 알림)
- **접근성**: ARIA 레이블 ([SOFT RULE])

### 1.3 성공 기준
- [ ] 실제 검색 결과 렌더링 확인
- [ ] Markdown 렌더링 확인
- [ ] 출처 링크 클릭 가능 확인
- [ ] 로딩/에러 상태 확인

---

## 2. 구현 단계

### Step 1: Markdown 렌더링 설정 (30분)

**패키지 설치**:
```bash
npm install react-markdown rehype-sanitize
```

### Step 2: SearchResults 컴포넌트 (120분)

**`components/search/SearchResults.tsx` 생성**:
```typescript
'use client';

import ReactMarkdown from 'react-markdown';
import rehypeSanitize from 'rehype-sanitize';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Clock, FileText } from 'lucide-react';
import { SearchQueryResponse } from '@/types/api';
import { SourceList } from './SourceList';

interface SearchResultsProps {
  data: SearchQueryResponse;
}

export function SearchResults({ data }: SearchResultsProps) {
  const { answer, sources, performance, metadata } = data;

  return (
    <div className="w-full max-w-4xl space-y-6">
      {/* 답변 섹션 */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>답변</CardTitle>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Clock className="h-4 w-4" />
              <span>{(performance.total_time_ms / 1000).toFixed(2)}초</span>
              {metadata.is_fallback && (
                <Badge variant="secondary">Fallback</Badge>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="prose prose-slate max-w-none">
            <ReactMarkdown rehypePlugins={[rehypeSanitize]}>
              {answer}
            </ReactMarkdown>
          </div>
        </CardContent>
      </Card>

      {/* 출처 섹션 */}
      {sources.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              <CardTitle>참고 문서 ({sources.length}개)</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <SourceList sources={sources} />
          </CardContent>
        </Card>
      )}

      {/* 성능 메트릭 (개발 환경에만 표시) */}
      {process.env.NODE_ENV === 'development' && (
        <Card className="bg-gray-50">
          <CardHeader>
            <CardTitle className="text-sm">성능 메트릭</CardTitle>
          </CardHeader>
          <CardContent className="text-sm space-y-1">
            <div>임베딩: {performance.embedding_time_ms}ms</div>
            <div>벡터 검색: {performance.search_time_ms}ms</div>
            <div>LLM: {performance.llm_time_ms}ms</div>
            <div>전체: {performance.total_time_ms}ms</div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
```

### Step 3: SourceList 컴포넌트 (90분)

**`components/search/SourceList.tsx` 생성**:
```typescript
'use client';

import { DocumentSource } from '@/types/api';
import { Progress } from '@/components/ui/progress';
import { ExternalLink } from 'lucide-react';

interface SourceListProps {
  sources: DocumentSource[];
}

export function SourceList({ sources }: SourceListProps) {
  return (
    <div className="space-y-4">
      {sources.map((source, index) => (
        <div
          key={`${source.document_id}-${index}`}
          className="border rounded-lg p-4 hover:bg-gray-50 transition-colors"
        >
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 space-y-2">
              {/* 문서 제목 */}
              <div className="flex items-center gap-2">
                <h3 className="font-semibold text-lg">
                  {source.document_title}
                </h3>
                {source.page_number && (
                  <span className="text-sm text-muted-foreground">
                    (p.{source.page_number})
                  </span>
                )}
              </div>

              {/* 문서 출처 */}
              <p className="text-sm text-muted-foreground">
                {source.document_source}
              </p>

              {/* 청크 내용 미리보기 */}
              <p className="text-sm line-clamp-3">
                {source.chunk_content}
              </p>

              {/* 관련도 점수 */}
              <div className="space-y-1">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">관련도</span>
                  <span className="font-medium">
                    {(source.relevance_score * 100).toFixed(0)}%
                  </span>
                </div>
                <Progress
                  value={source.relevance_score * 100}
                  className="h-2"
                />
              </div>
            </div>

            {/* 문서 링크 */}
            <a
              href={`/documents/${source.document_id}`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:text-blue-800"
              aria-label={`${source.document_title} 문서 열기`}
            >
              <ExternalLink className="h-5 w-5" />
            </a>
          </div>
        </div>
      ))}
    </div>
  );
}
```

### Step 4: 로딩 스켈레톤 (45분)

**`components/search/SearchSkeleton.tsx` 생성**:
```typescript
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';

export function SearchSkeleton() {
  return (
    <div className="w-full max-w-4xl space-y-6">
      {/* 답변 스켈레톤 */}
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-24" />
        </CardHeader>
        <CardContent className="space-y-2">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
        </CardContent>
      </Card>

      {/* 출처 스켈레톤 */}
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-32" />
        </CardHeader>
        <CardContent className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="border rounded-lg p-4 space-y-2">
              <Skeleton className="h-5 w-1/2" />
              <Skeleton className="h-4 w-1/3" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-2 w-full" />
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
```

### Step 5: 에러 상태 컴포넌트 (30분)

**`components/search/SearchError.tsx` 생성**:
```typescript
import { AlertCircle } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';

interface SearchErrorProps {
  error: Error;
  onRetry?: () => void;
}

export function SearchError({ error, onRetry }: SearchErrorProps) {
  return (
    <Alert variant="destructive" className="max-w-2xl">
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>검색 중 오류가 발생했습니다</AlertTitle>
      <AlertDescription className="mt-2 space-y-2">
        <p>{error.message}</p>
        {onRetry && (
          <Button
            variant="outline"
            size="sm"
            onClick={onRetry}
            className="mt-2"
          >
            다시 시도
          </Button>
        )}
      </AlertDescription>
    </Alert>
  );
}
```

### Step 6: 통합 페이지 업데이트 (45min)

**`app/search/page.tsx` 수정**:
```typescript
'use client';

import { SearchBar } from '@/components/search/SearchBar';
import { SearchResults } from '@/components/search/SearchResults';
import { SearchSkeleton } from '@/components/search/SearchSkeleton';
import { SearchError } from '@/components/search/SearchError';
import { useSearch } from '@/hooks/use-search';

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

- [ ] 실제 검색 결과 렌더링 (http://localhost:3000/search)
- [ ] Markdown 렌더링 (볼드, 리스트 등)
- [ ] 출처 링크 클릭 가능
- [ ] 관련도 점수 프로그레스 바 표시
- [ ] 로딩 상태 → 스켈레톤 UI
- [ ] 에러 상태 → 빨간색 알림 + 재시도 버튼

---

## 4. 출력물

1. `components/search/SearchResults.tsx`
2. `components/search/SourceList.tsx`
3. `components/search/SearchSkeleton.tsx`
4. `components/search/SearchError.tsx`
5. `app/search/page.tsx` (수정)

---

**작성자**: Claude Code (Sonnet 4.5)
**작성일**: 2026-01-04
