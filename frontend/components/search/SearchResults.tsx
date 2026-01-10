'use client';

import ReactMarkdown from 'react-markdown';
import rehypeSanitize from 'rehype-sanitize';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Clock, FileText } from 'lucide-react';
import { SearchQueryResponse } from '@/types/api';
import { SourceList } from './SourceList';
import { FeedbackForm } from './FeedbackForm';

interface SearchResultsProps {
  data: SearchQueryResponse;
}

export function SearchResults({ data }: SearchResultsProps) {
  const { query_id, answer, sources, performance, metadata } = data;

  return (
    <div className="w-full max-w-4xl space-y-6">
      {/* 답변 섹션 */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>답변</CardTitle>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Clock className="h-4 w-4" />
              <span>{(performance.total_time_ms / 1000).toFixed(2)}초</span>
              {metadata.is_fallback && <Badge variant="secondary">Fallback</Badge>}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="prose prose-slate max-w-none">
            <ReactMarkdown rehypePlugins={[rehypeSanitize]}>{answer}</ReactMarkdown>
          </div>
        </CardContent>
      </Card>

      {/* 출처 섹션 */}
      {sources.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              <CardTitle>참고 문서 ({sources.length}개)</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <SourceList sources={sources} />
          </CardContent>
        </Card>
      )}

      {/* 성능 메트릭 (개발 환경에만 표시) */}
      {process.env.NODE_ENV === 'development' && (
        <Card className="bg-gray-50">
          <CardHeader>
            <CardTitle className="text-sm">성능 메트릭</CardTitle>
          </CardHeader>
          <CardContent className="text-sm space-y-1">
            <div>임베딩: {performance.embedding_time_ms}ms</div>
            <div>벡터 검색: {performance.search_time_ms}ms</div>
            <div>LLM: {performance.llm_time_ms}ms</div>
            <div>전체: {performance.total_time_ms}ms</div>
          </CardContent>
        </Card>
      )}

      {/* 피드백 폼 */}
      <FeedbackForm queryId={query_id} />
    </div>
  );
}
