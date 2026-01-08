# RAG Platform Frontend

Next.js 14 기반 사내 정보 검색 플랫폼 프론트엔드

## 기술 스택

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Library**: shadcn/ui
- **Code Quality**: ESLint, Prettier

## 개발 환경 실행

```bash
npm install
npm run dev
```

http://localhost:3000 접속

## 빌드

```bash
npm run build
npm start
```

## 코드 포맷팅

```bash
npm run format
npm run lint
```

## 디렉토리 구조

- `app/`: Next.js App Router 페이지
- `components/`: React 컴포넌트
- `lib/`: 유틸리티 함수, API 클라이언트
- `types/`: TypeScript 타입 정의
- `store/`: 상태 관리
- `hooks/`: 커스텀 훅
