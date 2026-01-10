/**
 * 인증 API 클라이언트
 */

import { apiClient } from '@/lib/api-client';
import type { LoginRequest, LoginResponse, LogoutResponse } from '@/types/api';

/**
 * 사용자 로그인
 */
export const authAPI = {
  /**
   * 로그인
   */
  login: async (request: LoginRequest): Promise<LoginResponse> => {
    const response = await apiClient.post<LoginResponse>('/api/v1/auth/login', request);
    return response.data;
  },

  /**
   * 로그아웃
   */
  logout: async (): Promise<LogoutResponse> => {
    const response = await apiClient.post<LogoutResponse>('/api/v1/auth/logout');
    return response.data;
  },
};
