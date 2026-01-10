'use client';

import { SearchHistoryItem } from '@/types/api';
import { Card, CardContent } from '@/components/ui/card';
import { Star, Clock } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { ko } from 'date-fns/locale';

interface HistoryListProps {
  items: SearchHistoryItem[];
  onItemClick: (item: SearchHistoryItem) => void;
}

export function HistoryList({ items, onItemClick }: HistoryListProps) {
  if (items.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <p className="text-lg">검색 기록이 없습니다</p>
        <p className="text-sm mt-2">첫 검색을 시작해보세요!</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {items.map((item) => (
        <Card
          key={item.query_id}
          className="cursor-pointer hover:bg-gray-50 transition-colors"
          onClick={() => onItemClick(item)}
        >
          <CardContent className="p-4">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 space-y-1">
                {/* 검색어 */}
                <h3 className="font-semibold text-lg">{item.query}</h3>

                {/* 답변 미리보기 */}
                <p className="text-sm text-muted-foreground line-clamp-2">
                  {item.answer}
                </p>

                {/* 타임스탬프 */}
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <Clock className="h-3 w-3" />
                  <span>
                    {formatDistanceToNow(new Date(item.created_at), {
                      addSuffix: true,
                      locale: ko,
                    })}
                  </span>
                </div>
              </div>

              {/* 평점 */}
              {item.rating && (
                <div className="flex items-center gap-1">
                  {[...Array(5)].map((_, i) => (
                    <Star
                      key={i}
                      className={`h-4 w-4 ${
                        i < item.rating!
                          ? 'fill-yellow-400 text-yellow-400'
                          : 'text-gray-300'
                      }`}
                    />
                  ))}
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
