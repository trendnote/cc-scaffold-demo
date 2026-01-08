import apiClient from '../api-client';
import { SearchHistoryResponse } from '@/types/api';

export const historyAPI = {
  // 검색 히스토리 조회
  getHistory: async (page = 1, pageSize = 10): Promise<SearchHistoryResponse> => {
    const response = await apiClient.get<SearchHistoryResponse>('/api/v1/users/me/history', {
      params: { page, page_size: pageSize },
    });
    return response.data;
  },
};
