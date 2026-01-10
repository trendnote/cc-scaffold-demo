'use client';

import { useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { SearchBar } from '@/components/search/SearchBar';
import { SearchResults } from '@/components/search/SearchResults';
import { SearchSkeleton } from '@/components/search/SearchSkeleton';
import { SearchError } from '@/components/search/SearchError';
import { useSearch } from '@/hooks/use-search';

export default function SearchPage() {
  const searchParams = useSearchParams();
  const searchMutation = useSearch();

  // URL 쿼리 파라미터에서 검색어 가져오기
  const queryParam = searchParams.get('query');

  useEffect(() => {
    if (queryParam) {
      searchMutation.mutate({ query: queryParam, limit: 5 });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [queryParam]);

  const handleSearch = (query: string) => {
    searchMutation.mutate({ query, limit: 5 });
  };

  return (
    <main className="container mx-auto p-8">
      <div className="flex flex-col items-center gap-8">
        <h1 className="text-4xl font-bold">사내 정보 검색</h1>

        <SearchBar onSearch={handleSearch} isLoading={searchMutation.isPending} />

        {searchMutation.isPending && <SearchSkeleton />}

        {searchMutation.isSuccess && <SearchResults data={searchMutation.data} />}

        {searchMutation.isError && (
          <SearchError error={searchMutation.error} onRetry={() => searchMutation.reset()} />
        )}
      </div>
    </main>
  );
}
