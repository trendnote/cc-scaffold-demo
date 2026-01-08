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
