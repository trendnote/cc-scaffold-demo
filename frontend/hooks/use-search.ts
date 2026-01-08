import { useMutation } from '@tanstack/react-query';
import { searchAPI } from '@/lib/api/search';
import { SearchQueryRequest, SearchQueryResponse } from '@/types/api';

export const useSearch = () => {
  return useMutation<SearchQueryResponse, Error, SearchQueryRequest>({
    mutationFn: (request) => searchAPI.search(request),
    onSuccess: (data) => {
      console.log('Search successful:', data);
    },
    onError: (error) => {
      console.error('Search failed:', error);
    },
  });
};
