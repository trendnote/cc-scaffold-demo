'use client';

import { SearchBar } from '@/components/search/SearchBar';
import { useSearch } from '@/hooks/use-search';
import { Card, CardContent } from '@/components/ui/card';

export default function SearchPage() {
  const searchMutation = useSearch();

  const handleSearch = (query: string) => {
    searchMutation.mutate({ query, limit: 5 });
  };

  return (
    <main className="container mx-auto p-8">
      <div className="flex flex-col items-center gap-8">
        <h1 className="text-4xl font-bold">사내 정보 검색</h1>

        <SearchBar onSearch={handleSearch} isLoading={searchMutation.isPending} />

        {searchMutation.isSuccess && (
          <Card className="w-full max-w-3xl">
            <CardContent className="pt-6">
              <pre className="whitespace-pre-wrap">
                {JSON.stringify(searchMutation.data, null, 2)}
              </pre>
            </CardContent>
          </Card>
        )}

        {searchMutation.isError && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            검색 중 오류가 발생했습니다.
          </div>
        )}
      </div>
    </main>
  );
}
