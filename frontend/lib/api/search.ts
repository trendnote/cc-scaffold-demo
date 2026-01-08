import apiClient from '../api-client';
import { SearchQueryRequest, SearchQueryResponse } from '@/types/api';

export const searchAPI = {
  // 검색 API
  search: async (request: SearchQueryRequest): Promise<SearchQueryResponse> => {
    const response = await apiClient.post<SearchQueryResponse>('/api/v1/search', request);
    return response.data;
  },
};
