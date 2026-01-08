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
