import axios, { AxiosError, AxiosResponse } from 'axios';

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
    // localStorage에서 토큰 가져오기
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
