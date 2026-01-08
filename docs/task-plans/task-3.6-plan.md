# Task 3.6: 인증 Provider 및 UI - 실행 계획

---

## 📋 Meta

- **Task ID**: 3.6
- **Task명**: 인증 Provider 및 UI
- **예상 시간**: 4시간
- **담당**: Frontend
- **작성일**: 2026-01-04
- **상태**: Ready for Implementation
- **버전**: 1.0.0

---

## 1. Executive Summary

### 1.1 목표
로그인 페이지 UI, 로그아웃 버튼, 보호된 라우트를 구현합니다.

### 1.2 핵심 요구사항
- **로그인 페이지**: 이메일/비밀번호 입력 폼
- **로그아웃 버튼**: 헤더에 배치
- **보호된 라우트**: 미인증 시 로그인 페이지 리다이렉트

### 1.3 성공 기준
- [ ] 로그인 페이지 렌더링
- [ ] 로그인 성공 → 홈으로 리다이렉트
- [ ] 로그아웃 → 로그인 페이지로 리다이렉트
- [ ] 보호된 라우트 접근 차단

---

## 2. 구현 단계

### Step 1: 로그인 페이지 (120분)

**`app/login/page.tsx` 생성**:
```typescript
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2 } from 'lucide-react';

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      await login({ email, password });
      router.push('/search');
    } catch (err: any) {
      setError(err.response?.data?.message || '로그인에 실패했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center p-8">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>로그인</CardTitle>
          <CardDescription>
            사내 정보 검색 플랫폼에 로그인하세요
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">이메일</Label>
              <Input
                id="email"
                type="email"
                placeholder="user@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                disabled={isLoading}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">비밀번호</Label>
              <Input
                id="password"
                type="password"
                placeholder="비밀번호"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={isLoading}
              />
            </div>

            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  로그인 중...
                </>
              ) : (
                '로그인'
              )}
            </Button>

            <div className="text-sm text-muted-foreground mt-4">
              <p>테스트 계정:</p>
              <ul className="list-disc list-inside mt-1">
                <li>user@example.com / password123</li>
                <li>admin@example.com / password123</li>
              </ul>
            </div>
          </form>
        </CardContent>
      </Card>
    </main>
  );
}
```

---

### Step 2: 헤더 및 로그아웃 버튼 (60분)

**`components/layout/Header.tsx` 생성**:
```typescript
'use client';

import { useAuth } from '@/lib/auth-context';
import { Button } from '@/components/ui/button';
import { LogOut, User } from 'lucide-react';
import { useRouter } from 'next/navigation';

export function Header() {
  const { user, logout } = useAuth();
  const router = useRouter();

  const handleLogout = async () => {
    await logout();
    router.push('/login');
  };

  if (!user) return null;

  return (
    <header className="border-b">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h1 className="text-xl font-bold">RAG Platform</h1>
            <nav className="flex gap-4">
              <a href="/search" className="text-sm hover:underline">
                검색
              </a>
              <a href="/history" className="text-sm hover:underline">
                히스토리
              </a>
            </nav>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-sm">
              <User className="h-4 w-4" />
              <span>{user.email}</span>
              <span className="text-muted-foreground">
                (L{user.access_level})
              </span>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={handleLogout}
            >
              <LogOut className="mr-2 h-4 w-4" />
              로그아웃
            </Button>
          </div>
        </div>
      </div>
    </header>
  );
}
```

---

### Step 3: 보호된 라우트 (60분)

**`components/layout/ProtectedRoute.tsx` 생성**:
```typescript
'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import { Loader2 } from 'lucide-react';

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !user) {
      router.push('/login');
    }
  }, [user, isLoading, router]);

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return <>{children}</>;
}
```

**`app/search/layout.tsx` 생성**:
```typescript
import { ProtectedRoute } from '@/components/layout/ProtectedRoute';
import { Header } from '@/components/layout/Header';

export default function SearchLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ProtectedRoute>
      <Header />
      {children}
    </ProtectedRoute>
  );
}
```

**`app/history/layout.tsx` 생성**:
```typescript
import { ProtectedRoute } from '@/components/layout/ProtectedRoute';
import { Header } from '@/components/layout/Header';

export default function HistoryLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ProtectedRoute>
      <Header />
      {children}
    </ProtectedRoute>
  );
}
```

---

### Step 4: 홈 페이지 리다이렉트 (20min)

**`app/page.tsx` 수정**:
```typescript
'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import { Loader2 } from 'lucide-react';

export default function Home() {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading) {
      if (user) {
        router.push('/search');
      } else {
        router.push('/login');
      }
    }
  }, [user, isLoading, router]);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <Loader2 className="h-8 w-8 animate-spin" />
    </div>
  );
}
```

---

## 3. 검증 기준

- [ ] 로그인 페이지 렌더링 (http://localhost:3000/login)
- [ ] 로그인 성공 → /search로 리다이렉트
- [ ] 잘못된 비밀번호 → 에러 메시지 표시
- [ ] 로그아웃 버튼 클릭 → /login으로 리다이렉트
- [ ] 미인증 상태에서 /search 접근 → /login으로 리다이렉트
- [ ] 헤더에 사용자 정보 표시 (이메일, Access Level)

---

## 4. 출력물

1. `app/login/page.tsx`
2. `components/layout/Header.tsx`
3. `components/layout/ProtectedRoute.tsx`
4. `app/search/layout.tsx`
5. `app/history/layout.tsx`
6. `app/page.tsx` (수정)

---

**작성자**: Claude Code (Sonnet 4.5)
**작성일**: 2026-01-04
