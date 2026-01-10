import { AlertCircle } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';

interface SearchErrorProps {
  error: Error;
  onRetry?: () => void;
}

export function SearchError({ error, onRetry }: SearchErrorProps) {
  return (
    <Alert variant="destructive" className="max-w-2xl">
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>검색 중 오류가 발생했습니다</AlertTitle>
      <AlertDescription className="mt-2 space-y-2">
        <p>{error.message}</p>
        {onRetry && (
          <Button variant="outline" size="sm" onClick={onRetry} className="mt-2">
            다시 시도
          </Button>
        )}
      </AlertDescription>
    </Alert>
  );
}
