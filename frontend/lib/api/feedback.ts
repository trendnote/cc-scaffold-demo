import apiClient from '../api-client';
import { FeedbackRequest, FeedbackResponse } from '@/types/api';

export const feedbackAPI = {
  // 피드백 제출
  submitFeedback: async (request: FeedbackRequest): Promise<FeedbackResponse> => {
    const response = await apiClient.post<FeedbackResponse>('/api/v1/feedback', request);
    return response.data;
  },
};
