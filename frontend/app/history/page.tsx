'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useHistory } from '@/hooks/use-history';
import { HistoryList } from '@/components/history/HistoryList';
import { Pagination } from '@/components/history/Pagination';
import { SearchHistoryItem } from '@/types/api';
import { Loader2 } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';

export default function HistoryPage() {
  const router = useRouter();
  const [page, setPage] = useState(1);
  const pageSize = 10;

  const { data, isLoading, error } = useHistory(page, pageSize);

  const handleItemClick = (item: SearchHistoryItem) => {
    // 검색 페이지로 이동하면서 쿼리 전달
    router.push(`/search?query=${encodeURIComponent(item.query)}`);
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive" className="max-w-2xl mx-auto mt-8">
        <AlertDescription>
          히스토리를 불러오는 중 오류가 발생했습니다.
        </AlertDescription>
      </Alert>
    );
  }

  const totalPages = data ? Math.ceil(data.total / pageSize) : 1;

  return (
    <main className="container mx-auto p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">검색 히스토리</h1>

        {data && (
          <>
            <HistoryList items={data.items} onItemClick={handleItemClick} />
            <Pagination
              currentPage={page}
              totalPages={totalPages}
              onPageChange={setPage}
            />
          </>
        )}
      </div>
    </main>
  );
}
