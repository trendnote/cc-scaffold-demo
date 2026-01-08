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
