import apiClient from '../api-client';
import { HealthCheckResponse } from '@/types/api';

export const healthAPI = {
  // Health Check
  check: async (): Promise<HealthCheckResponse> => {
    const response = await apiClient.get<HealthCheckResponse>('/health');
    return response.data;
  },
};
