'use client';

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Star } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { feedbackAPI } from '@/lib/api/feedback';
import { cn } from '@/lib/utils';

interface FeedbackFormProps {
  queryId: string;
}

export function FeedbackForm({ queryId }: FeedbackFormProps) {
  const [rating, setRating] = useState<number>(0);
  const [hoveredRating, setHoveredRating] = useState<number>(0);
  const [comment, setComment] = useState<string>('');
  const [submitted, setSubmitted] = useState<boolean>(false);

  const feedbackMutation = useMutation({
    mutationFn: feedbackAPI.submitFeedback,
    onSuccess: () => {
      toast.success('피드백이 저장되었습니다. 감사합니다!');
      setSubmitted(true);
    },
    onError: (error: Error) => {
      toast.error(`피드백 제출에 실패했습니다: ${error.message}`);
    },
  });

  const handleSubmit = () => {
    if (rating === 0) {
      toast.warning('별점을 선택해주세요');
      return;
    }

    feedbackMutation.mutate({
      query_id: queryId,
      rating,
      comment: comment.trim() || undefined,
    });
  };

  if (submitted) {
    return (
      <Card className="bg-green-50 border-green-200">
        <CardContent className="pt-6">
          <p className="text-sm text-green-800 text-center">
            피드백을 제출해주셔서 감사합니다! 더 나은 서비스를 제공하는 데 활용하겠습니다.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">이 답변이 도움이 되셨나요?</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* 별점 선택 */}
        <div className="space-y-2">
          <Label htmlFor="rating">별점</Label>
          <div className="flex items-center gap-1">
            {[1, 2, 3, 4, 5].map((star) => (
              <button
                key={star}
                type="button"
                onClick={() => setRating(star)}
                onMouseEnter={() => setHoveredRating(star)}
                onMouseLeave={() => setHoveredRating(0)}
                className="transition-transform hover:scale-110 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 rounded"
                aria-label={`${star}점`}
              >
                <Star
                  className={cn(
                    'h-8 w-8 transition-colors',
                    (hoveredRating >= star || rating >= star)
                      ? 'fill-yellow-400 text-yellow-400'
                      : 'text-gray-300'
                  )}
                />
              </button>
            ))}
            {rating > 0 && (
              <span className="ml-2 text-sm text-muted-foreground">
                {rating}점
              </span>
            )}
          </div>
        </div>

        {/* 댓글 입력 (선택적) */}
        <div className="space-y-2">
          <Label htmlFor="comment">
            의견 <span className="text-muted-foreground text-sm">(선택사항)</span>
          </Label>
          <Textarea
            id="comment"
            placeholder="개선이 필요한 부분이나 좋았던 점을 알려주세요 (최대 500자)"
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            maxLength={500}
            rows={3}
            className="resize-none"
          />
          <p className="text-xs text-muted-foreground text-right">
            {comment.length} / 500
          </p>
        </div>

        {/* 제출 버튼 */}
        <Button
          onClick={handleSubmit}
          disabled={rating === 0 || feedbackMutation.isPending}
          className="w-full"
        >
          {feedbackMutation.isPending ? '제출 중...' : '피드백 제출'}
        </Button>
      </CardContent>
    </Card>
  );
}
