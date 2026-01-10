'use client';

import { DocumentSource } from '@/types/api';
import { Progress } from '@/components/ui/progress';
import { ExternalLink } from 'lucide-react';

interface SourceListProps {
  sources: DocumentSource[];
}

export function SourceList({ sources }: SourceListProps) {
  return (
    <div className="space-y-4">
      {sources.map((source, index) => (
        <div
          key={`${source.document_id}-${index}`}
          className="border rounded-lg p-4 hover:bg-gray-50 transition-colors"
        >
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 space-y-2">
              {/* 문서 제목 */}
              <div className="flex items-center gap-2">
                <h3 className="font-semibold text-lg">{source.document_title}</h3>
                {source.page_number && (
                  <span className="text-sm text-muted-foreground">(p.{source.page_number})</span>
                )}
              </div>

              {/* 문서 출처 */}
              <p className="text-sm text-muted-foreground">{source.document_source}</p>

              {/* 청크 내용 미리보기 */}
              <p className="text-sm line-clamp-3">{source.chunk_content}</p>

              {/* 관련도 점수 */}
              <div className="space-y-1">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">관련도</span>
                  <span className="font-medium">{(source.relevance_score * 100).toFixed(0)}%</span>
                </div>
                <Progress value={source.relevance_score * 100} className="h-2" />
              </div>
            </div>

            {/* 문서 링크 */}
            <a
              href={`/documents/${source.document_id}`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:text-blue-800"
              aria-label={`${source.document_title} 문서 열기`}
            >
              <ExternalLink className="h-5 w-5" />
            </a>
          </div>
        </div>
      ))}
    </div>
  );
}
