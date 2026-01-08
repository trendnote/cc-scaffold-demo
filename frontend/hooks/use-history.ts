import { useQuery } from '@tanstack/react-query';
import { historyAPI } from '@/lib/api/history';

export const useHistory = (page = 1, pageSize = 10) => {
  return useQuery({
    queryKey: ['history', page, pageSize],
    queryFn: () => historyAPI.getHistory(page, pageSize),
  });
};
