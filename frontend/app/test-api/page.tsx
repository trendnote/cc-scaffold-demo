'use client';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useHealthCheck } from '@/hooks/use-health-check';
import { useSearch } from '@/hooks/use-search';

export default function TestAPIPage() {
  const { data: healthData, isLoading: healthLoading } = useHealthCheck();
  const searchMutation = useSearch();

  const handleTestSearch = () => {
    searchMutation.mutate({
      query: '연차 사용 방법',
      limit: 5,
    });
  };

  return (
    <main className="container mx-auto p-8">
      <h1 className="text-3xl font-bold mb-6">API 테스트 페이지</h1>

      <div className="space-y-4">
        {/* Health Check */}
        <Card>
          <CardHeader>
            <CardTitle>Health Check</CardTitle>
          </CardHeader>
          <CardContent>
            {healthLoading ? (
              <p>Loading...</p>
            ) : (
              <pre className="bg-gray-100 p-4 rounded">{JSON.stringify(healthData, null, 2)}</pre>
            )}
          </CardContent>
        </Card>

        {/* Search Test */}
        <Card>
          <CardHeader>
            <CardTitle>Search API 테스트</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button onClick={handleTestSearch} disabled={searchMutation.isPending}>
              {searchMutation.isPending ? '검색 중...' : '테스트 검색 실행'}
            </Button>

            {searchMutation.isSuccess && (
              <pre className="bg-gray-100 p-4 rounded overflow-auto">
                {JSON.stringify(searchMutation.data, null, 2)}
              </pre>
            )}

            {searchMutation.isError && (
              <div className="bg-red-100 p-4 rounded text-red-700">
                Error: {searchMutation.error.message}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
