# Task 3.2: API 클라이언트 및 React Query 설정 - 실행 계획

---

## 📋 Meta

- **Task ID**: 3.2
- **Task명**: API 클라이언트 및 React Query 설정
- **예상 시간**: 4시간
- **담당**: Frontend
- **작성일**: 2026-01-04
- **상태**: Ready for Implementation
- **버전**: 1.0.0

---

## 1. Executive Summary

### 1.1 목표
Axios 기반 API 클라이언트를 구성하고 React Query로 서버 상태 관리를 설정합니다.

### 1.2 핵심 요구사항
- **Axios**: HTTP 클라이언트 설정
- **Interceptors**: 토큰 자동 추가, 에러 처리
- **React Query**: 캐싱, 리프레시, 자동 재시도
- **TypeScript**: API 엔드포인트 타입 정의

### 1.3 성공 기준
- [ ] Health check API 호출 성공
- [ ] 토큰 자동 추가 확인
- [ ] React Query 캐싱 확인
- [ ] 에러 처리 확인 (401, 500)

---

## 2. 구현 단계별 상세 계획

### Step 1: 필수 패키지 설치 (15분)

```bash
cd frontend
npm install axios @tanstack/react-query @tanstack/react-query-devtools
npm install --save-dev @types/node
```

---

### Step 2: Axios API 클라이언트 구성 (60분)

**`lib/api-client.ts` 생성**:
```typescript
import axios, { AxiosError, AxiosRequestConfig, AxiosResponse } from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Axios 인스턴스 생성
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30초 타임아웃
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request Interceptor: 토큰 자동 추가
apiClient.interceptors.request.use(
  (config) => {
    // httpOnly Cookie에서 토큰을 가져오는 대신, 세션에서 가져옴
    // Task 3.5에서 인증 구현 후 수정 예정
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response Interceptor: 에러 처리
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  (error: AxiosError) => {
    if (error.response) {
      // 서버 응답 에러
      switch (error.response.status) {
        case 401:
          // 인증 실패 → 로그인 페이지로 리다이렉트
          console.error('Unauthorized: 로그인이 필요합니다.');
          if (typeof window !== 'undefined') {
            window.location.href = '/login';
          }
          break;
        case 403:
          console.error('Forbidden: 권한이 없습니다.');
          break;
        case 500:
          console.error('Internal Server Error: 서버 오류가 발생했습니다.');
          break;
        default:
          console.error(`Error ${error.response.status}: ${error.message}`);
      }
    } else if (error.request) {
      // 요청은 보냈지만 응답이 없음
      console.error('No response from server:', error.message);
    } else {
      // 요청 설정 중 에러
      console.error('Request setup error:', error.message);
    }
    return Promise.reject(error);
  }
);

export default apiClient;
```

---

### Step 3: API 엔드포인트 타입 정의 (45분)

**`types/api.ts` 생성**:
```typescript
// Search API Types
export interface SearchQueryRequest {
  query: string;
  user_id?: string;
  limit?: number;
  session_id?: string;
}

export interface DocumentSource {
  document_id: string;
  document_title: string;
  document_source: string;
  chunk_content: string;
  page_number: number | null;
  relevance_score: number;
}

export interface PerformanceMetrics {
  embedding_time_ms: number;
  search_time_ms: number;
  llm_time_ms: number;
  total_time_ms: number;
}

export interface ResponseMetadata {
  is_fallback: boolean;
  fallback_reason: string | null;
  model_used: string;
  search_result_count: number;
}

export interface SearchQueryResponse {
  query: string;
  answer: string;
  sources: DocumentSource[];
  performance: PerformanceMetrics;
  metadata: ResponseMetadata;
}

// Health Check API
export interface HealthCheckResponse {
  status: string;
  timestamp: string;
  version: string;
}

// User History API
export interface SearchHistoryItem {
  query_id: string;
  query: string;
  answer: string;
  created_at: string;
  rating: number | null;
}

export interface SearchHistoryResponse {
  items: SearchHistoryItem[];
  total: number;
  page: number;
  page_size: number;
}

// Feedback API
export interface FeedbackRequest {
  query_id: string;
  rating: number; // 1-5
  comment?: string;
}

export interface FeedbackResponse {
  feedback_id: string;
  message: string;
}

// Auth API (Task 3.5)
export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: {
    user_id: string;
    email: string;
    access_level: number;
    department: string;
  };
}

// Error Response
export interface ErrorResponse {
  error: string;
  message: string;
  details?: any;
  request_id?: string;
  timestamp?: string;
}
```

---

### Step 4: React Query 설정 (60min)

**`lib/query-client.ts` 생성**:
```typescript
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // 5분간 캐시 유지
      staleTime: 5 * 60 * 1000,
      // 캐시 유효 기간: 10분
      gcTime: 10 * 60 * 1000,
      // 재시도 설정
      retry: 1,
      // 윈도우 포커스 시 자동 리프레시
      refetchOnWindowFocus: false,
    },
    mutations: {
      // 뮤테이션 재시도 없음
      retry: 0,
    },
  },
});
```

**`app/layout.tsx` 수정 (Provider 추가)**:
```typescript
'use client';

import './globals.css';
import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { queryClient } from '@/lib/query-client';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <body>
        <QueryClientProvider client={queryClient}>
          {children}
          <ReactQueryDevtools initialIsOpen={false} />
        </QueryClientProvider>
      </body>
    </html>
  );
}
```

---

### Step 5: API 서비스 함수 작성 (60분)

**`lib/api/search.ts` 생성**:
```typescript
import apiClient from '../api-client';
import { SearchQueryRequest, SearchQueryResponse } from '@/types/api';

export const searchAPI = {
  // 검색 API
  search: async (request: SearchQueryRequest): Promise<SearchQueryResponse> => {
    const response = await apiClient.post<SearchQueryResponse>(
      '/api/v1/search',
      request
    );
    return response.data;
  },
};
```

**`lib/api/health.ts` 생성**:
```typescript
import apiClient from '../api-client';
import { HealthCheckResponse } from '@/types/api';

export const healthAPI = {
  // Health Check
  check: async (): Promise<HealthCheckResponse> => {
    const response = await apiClient.get<HealthCheckResponse>('/health');
    return response.data;
  },
};
```

**`lib/api/history.ts` 생성**:
```typescript
import apiClient from '../api-client';
import { SearchHistoryResponse } from '@/types/api';

export const historyAPI = {
  // 검색 히스토리 조회
  getHistory: async (page = 1, pageSize = 10): Promise<SearchHistoryResponse> => {
    const response = await apiClient.get<SearchHistoryResponse>(
      '/api/v1/users/me/history',
      {
        params: { page, page_size: pageSize },
      }
    );
    return response.data;
  },
};
```

**`lib/api/feedback.ts` 생성**:
```typescript
import apiClient from '../api-client';
import { FeedbackRequest, FeedbackResponse } from '@/types/api';

export const feedbackAPI = {
  // 피드백 제출
  submitFeedback: async (request: FeedbackRequest): Promise<FeedbackResponse> => {
    const response = await apiClient.post<FeedbackResponse>(
      '/api/v1/feedback',
      request
    );
    return response.data;
  },
};
```

---

### Step 6: 커스텀 훅 작성 (60분)

**`hooks/use-search.ts` 생성**:
```typescript
import { useMutation } from '@tanstack/react-query';
import { searchAPI } from '@/lib/api/search';
import { SearchQueryRequest, SearchQueryResponse } from '@/types/api';

export const useSearch = () => {
  return useMutation<SearchQueryResponse, Error, SearchQueryRequest>({
    mutationFn: (request) => searchAPI.search(request),
    onSuccess: (data) => {
      console.log('Search successful:', data);
    },
    onError: (error) => {
      console.error('Search failed:', error);
    },
  });
};
```

**`hooks/use-health-check.ts` 생성**:
```typescript
import { useQuery } from '@tanstack/react-query';
import { healthAPI } from '@/lib/api/health';

export const useHealthCheck = () => {
  return useQuery({
    queryKey: ['health'],
    queryFn: () => healthAPI.check(),
    // 10초마다 자동 리프레시
    refetchInterval: 10000,
  });
};
```

**`hooks/use-history.ts` 생성**:
```typescript
import { useQuery } from '@tanstack/react-query';
import { historyAPI } from '@/lib/api/history';

export const useHistory = (page = 1, pageSize = 10) => {
  return useQuery({
    queryKey: ['history', page, pageSize],
    queryFn: () => historyAPI.getHistory(page, pageSize),
  });
};
```

**`hooks/use-feedback.ts` 생성**:
```typescript
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { feedbackAPI } from '@/lib/api/feedback';
import { FeedbackRequest, FeedbackResponse } from '@/types/api';

export const useFeedback = () => {
  const queryClient = useQueryClient();

  return useMutation<FeedbackResponse, Error, FeedbackRequest>({
    mutationFn: (request) => feedbackAPI.submitFeedback(request),
    onSuccess: () => {
      // 피드백 제출 성공 시 히스토리 무효화 (새로고침)
      queryClient.invalidateQueries({ queryKey: ['history'] });
    },
  });
};
```

---

### Step 7: 테스트 페이지 작성 (30분)

**`app/test-api/page.tsx` 생성**:
```typescript
'use client';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useHealthCheck } from '@/hooks/use-health-check';
import { useSearch } from '@/hooks/use-search';

export default function TestAPIPage() {
  const { data: healthData, isLoading: healthLoading } = useHealthCheck();
  const searchMutation = useSearch();

  const handleTestSearch = () => {
    searchMutation.mutate({
      query: '연차 사용 방법',
      limit: 5,
    });
  };

  return (
    <main className="container mx-auto p-8">
      <h1 className="text-3xl font-bold mb-6">API 테스트 페이지</h1>

      <div className="space-y-4">
        {/* Health Check */}
        <Card>
          <CardHeader>
            <CardTitle>Health Check</CardTitle>
          </CardHeader>
          <CardContent>
            {healthLoading ? (
              <p>Loading...</p>
            ) : (
              <pre className="bg-gray-100 p-4 rounded">
                {JSON.stringify(healthData, null, 2)}
              </pre>
            )}
          </CardContent>
        </Card>

        {/* Search Test */}
        <Card>
          <CardHeader>
            <CardTitle>Search API 테스트</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button onClick={handleTestSearch} disabled={searchMutation.isPending}>
              {searchMutation.isPending ? '검색 중...' : '테스트 검색 실행'}
            </Button>

            {searchMutation.isSuccess && (
              <pre className="bg-gray-100 p-4 rounded overflow-auto">
                {JSON.stringify(searchMutation.data, null, 2)}
              </pre>
            )}

            {searchMutation.isError && (
              <div className="bg-red-100 p-4 rounded text-red-700">
                Error: {searchMutation.error.message}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
```

---

## 3. 검증 기준

### 필수 체크리스트

- [ ] **Health check API 호출 성공**
  ```bash
  # 백엔드 서버 실행 후
  # http://localhost:3000/test-api 접속
  # Health Check 응답 확인
  ```

- [ ] **토큰 자동 추가 확인**
  ```typescript
  // 개발자 도구 > Network > Request Headers
  // Authorization: Bearer {token} 확인
  ```

- [ ] **React Query 캐싱 확인**
  ```bash
  # React Query Devtools 열기 (F12)
  # 캐시 상태 확인
  ```

- [ ] **에러 처리 확인**
  ```bash
  # 401 에러 → 로그인 페이지 리다이렉트
  # 500 에러 → 콘솔 에러 로그
  ```

---

## 4. 출력물

### 생성될 파일
1. `lib/api-client.ts` - Axios 클라이언트
2. `lib/query-client.ts` - React Query 설정
3. `types/api.ts` - API 타입 정의
4. `lib/api/search.ts` - 검색 API 함수
5. `lib/api/health.ts` - Health Check API
6. `lib/api/history.ts` - 히스토리 API
7. `lib/api/feedback.ts` - 피드백 API
8. `hooks/use-search.ts` - 검색 훅
9. `hooks/use-health-check.ts` - Health Check 훅
10. `hooks/use-history.ts` - 히스토리 훅
11. `hooks/use-feedback.ts` - 피드백 훅
12. `app/test-api/page.tsx` - API 테스트 페이지

### 수정될 파일
1. `app/layout.tsx` - QueryClientProvider 추가

---

**작성자**: Claude Code (Sonnet 4.5)
**작성일**: 2026-01-04
