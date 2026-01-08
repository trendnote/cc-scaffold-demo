import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <Card className="w-[400px]">
        <CardHeader>
          <CardTitle>RAG Platform</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Input placeholder="검색어를 입력하세요" />
          <Button className="w-full">검색</Button>
        </CardContent>
      </Card>
    </main>
  );
}
