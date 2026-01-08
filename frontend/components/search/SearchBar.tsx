'use client';

import { useState, useEffect, useCallback } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Search, Loader2 } from 'lucide-react';
import { useDebounce } from '@/hooks/use-debounce';

interface SearchBarProps {
  onSearch: (query: string) => void;
  isLoading?: boolean;
}

export function SearchBar({ onSearch, isLoading = false }: SearchBarProps) {
  const [query, setQuery] = useState('');
  const [error, setError] = useState<string | null>(null);
  const debouncedQuery = useDebounce(query, 500);

  const validateQuery = useCallback((value: string): boolean => {
    if (value.length < 5) {
      setError('검색어는 5자 이상이어야 합니다.');
      return false;
    }
    if (value.length > 200) {
      setError('검색어는 200자 이하여야 합니다.');
      return false;
    }
    setError(null);
    return true;
  }, []);

  useEffect(() => {
    if (debouncedQuery.length > 0) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      validateQuery(debouncedQuery);
    }
  }, [debouncedQuery, validateQuery]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setQuery(value);
    if (value.length === 0) {
      setError(null);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validateQuery(query)) {
      onSearch(query);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-3xl">
      <div className="flex gap-2">
        <div className="flex-1">
          <Input
            type="text"
            placeholder="무엇이든 물어보세요... (예: 연차 사용 방법)"
            value={query}
            onChange={handleInputChange}
            className={error ? 'border-red-500' : ''}
            disabled={isLoading}
          />
          {error && <p className="text-sm text-red-500 mt-1">{error}</p>}
        </div>
        <Button
          type="submit"
          disabled={isLoading || !!error || query.length === 0}
          className="px-6"
        >
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              검색 중...
            </>
          ) : (
            <>
              <Search className="mr-2 h-4 w-4" />
              검색
            </>
          )}
        </Button>
      </div>
    </form>
  );
}
