# Task 3.1: Next.js 14 프로젝트 초기화 - 실행 계획

---

## 📋 Meta

- **Task ID**: 3.1
- **Task명**: Next.js 14 프로젝트 초기화
- **예상 시간**: 3시간
- **담당**: Frontend
- **작성일**: 2026-01-04
- **상태**: Ready for Implementation
- **버전**: 1.0.0

---

## 1. Executive Summary

### 1.1 목표
Next.js 14 App Router 기반 프론트엔드 프로젝트를 초기화하고 개발 환경을 설정합니다.

### 1.2 핵심 요구사항
- **Next.js 14**: App Router 사용
- **TypeScript**: strict mode 활성화
- **Tailwind CSS**: 스타일링
- **shadcn/ui**: UI 컴포넌트 라이브러리
- **ESLint & Prettier**: 코드 품질 및 포맷팅

### 1.3 성공 기준
- [ ] 개발 서버 실행 성공 (`npm run dev`)
- [ ] TypeScript strict mode 활성화
- [ ] Tailwind CSS 작동 확인
- [ ] shadcn/ui 설치 및 테스트 컴포넌트 렌더링
- [ ] 빌드 성공 (`npm run build`)

### 1.4 Why This Task Matters
**프론트엔드 기반 구축**:
- **개발 생산성**: 타입 안전성과 자동 완성으로 개발 속도 향상
- **일관성**: Prettier와 ESLint로 코드 스타일 통일
- **확장성**: App Router로 페이지 기반 라우팅 및 서버 컴포넌트 활용

---

## 2. 선행 조건 검증

### 2.1 환경 검증
```bash
# Node.js 버전 확인 (18.17 이상 필요)
node -v

# npm 버전 확인
npm -v

# 프로젝트 루트 확인
ls -la /Users/young/Dev/workspace/cc-scaffold-demo/
```

### 2.2 의존성 확인
- [x] **Node.js**: 18.17 이상
- [ ] **frontend 디렉토리**: 아직 생성되지 않음

---

## 3. 구현 단계별 상세 계획

### Step 1: Next.js 14 프로젝트 생성 (30분)

#### 작업 내용
**프로젝트 생성**:
```bash
cd /Users/young/Dev/workspace/cc-scaffold-demo
npx create-next-app@latest frontend
```

**설정 옵션**:
- ✅ TypeScript
- ✅ ESLint
- ✅ Tailwind CSS
- ✅ `src/` directory: No (App Router는 app/ 사용)
- ✅ App Router
- ✅ Import alias: `@/*`

**디렉토리 구조 검증**:
```
frontend/
├── app/
│   ├── layout.tsx
│   ├── page.tsx
│   └── globals.css
├── public/
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── next.config.js
└── .eslintrc.json
```

---

### Step 2: TypeScript 설정 강화 (20분)

#### 작업 내용
**`tsconfig.json` 수정**:
```json
{
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "paths": {
      "@/*": ["./*"]
    },
    "strictNullChecks": true,
    "strictFunctionTypes": true,
    "noImplicitAny": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

**검증**:
```bash
cd frontend
npm run build
# 타입 에러 없이 빌드 성공 확인
```

---

### Step 3: Prettier 설정 (15분)

#### 작업 내용
**Prettier 설치**:
```bash
cd frontend
npm install --save-dev prettier eslint-config-prettier
```

**`.prettierrc` 생성**:
```json
{
  "semi": true,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 100,
  "arrowParens": "always"
}
```

**`.prettierignore` 생성**:
```
node_modules
.next
out
build
dist
```

**ESLint 설정 업데이트** (`.eslintrc.json`):
```json
{
  "extends": [
    "next/core-web-vitals",
    "prettier"
  ]
}
```

**package.json scripts 추가**:
```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "format": "prettier --write \"**/*.{ts,tsx,js,jsx,json,css,md}\""
  }
}
```

**검증**:
```bash
npm run format
npm run lint
```

---

### Step 4: shadcn/ui 설치 및 설정 (45분)

#### 작업 내용
**shadcn/ui 초기화**:
```bash
cd frontend
npx shadcn-ui@latest init
```

**설정 옵션**:
- Style: Default
- Base color: Slate
- CSS variables: Yes

**`components.json` 생성 확인**:
```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "default",
  "rsc": true,
  "tsx": true,
  "tailwind": {
    "config": "tailwind.config.ts",
    "css": "app/globals.css",
    "baseColor": "slate",
    "cssVariables": true
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils"
  }
}
```

**기본 컴포넌트 설치**:
```bash
# Button 컴포넌트
npx shadcn-ui@latest add button

# Input 컴포넌트
npx shadcn-ui@latest add input

# Card 컴포넌트
npx shadcn-ui@latest add card
```

**테스트 페이지 작성** (`app/page.tsx`):
```tsx
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
```

**검증**:
```bash
npm run dev
# http://localhost:3000 접속
# Card, Input, Button 렌더링 확인
```

---

### Step 5: 디렉토리 구조 생성 (30분)

#### 작업 내용
**필수 디렉토리 생성**:
```bash
cd frontend

# 컴포넌트 디렉토리
mkdir -p components/ui
mkdir -p components/search
mkdir -p components/history
mkdir -p components/feedback

# 라이브러리 디렉토리
mkdir -p lib

# 타입 디렉토리
mkdir -p types

# 스토어 디렉토리 (상태 관리)
mkdir -p store

# 훅 디렉토리
mkdir -p hooks

# App 라우팅 디렉토리
mkdir -p app/search
mkdir -p app/history
mkdir -p app/login
mkdir -p app/api
```

**최종 디렉토리 구조**:
```
frontend/
├── app/
│   ├── layout.tsx
│   ├── page.tsx
│   ├── globals.css
│   ├── search/
│   ├── history/
│   ├── login/
│   └── api/
├── components/
│   ├── ui/           (shadcn/ui 컴포넌트)
│   ├── search/       (검색 관련 컴포넌트)
│   ├── history/      (히스토리 관련 컴포넌트)
│   └── feedback/     (피드백 관련 컴포넌트)
├── lib/              (유틸리티, API 클라이언트)
├── types/            (TypeScript 타입 정의)
├── store/            (상태 관리)
├── hooks/            (커스텀 훅)
└── public/           (정적 파일)
```

**README.md 작성**:
```markdown
# RAG Platform Frontend

Next.js 14 기반 사내 정보 검색 플랫폼 프론트엔드

## 기술 스택
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Library**: shadcn/ui
- **Code Quality**: ESLint, Prettier

## 개발 환경 실행
\`\`\`bash
npm install
npm run dev
\`\`\`

http://localhost:3000 접속

## 빌드
\`\`\`bash
npm run build
npm start
\`\`\`

## 코드 포맷팅
\`\`\`bash
npm run format
npm run lint
\`\`\`

## 디렉토리 구조
- `app/`: Next.js App Router 페이지
- `components/`: React 컴포넌트
- `lib/`: 유틸리티 함수, API 클라이언트
- `types/`: TypeScript 타입 정의
- `store/`: 상태 관리
- `hooks/`: 커스텀 훅
```

---

### Step 6: 환경 변수 설정 (20분)

#### 작업 내용
**`.env.local` 생성**:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**`.env.example` 생성**:
```bash
# API 엔드포인트
NEXT_PUBLIC_API_URL=http://localhost:8000

# 기타 환경 변수 (필요 시 추가)
# NEXT_PUBLIC_GOOGLE_ANALYTICS_ID=
```

**`.gitignore` 업데이트 확인**:
```
# dependencies
/node_modules

# next.js
/.next/
/out/

# production
/build

# misc
.DS_Store
*.pem

# debug
npm-debug.log*

# local env files
.env*.local

# vercel
.vercel
```

---

## 4. 검증 기준

### 4.1 필수 체크리스트

- [ ] **개발 서버 실행 성공**
  ```bash
  cd frontend
  npm run dev
  # http://localhost:3000 접속 가능
  ```

- [ ] **TypeScript strict mode 동작**
  ```bash
  # tsconfig.json에서 strict: true 확인
  # 타입 에러 발생 시 빌드 실패 확인
  ```

- [ ] **Tailwind CSS 작동**
  ```bash
  # 브라우저에서 스타일 적용 확인
  # 개발자 도구에서 Tailwind 클래스 확인
  ```

- [ ] **shadcn/ui 컴포넌트 렌더링**
  ```bash
  # http://localhost:3000에서 Card, Input, Button 렌더링 확인
  ```

- [ ] **빌드 성공**
  ```bash
  npm run build
  # 빌드 성공 및 .next/ 디렉토리 생성 확인
  ```

- [ ] **Lint 및 Format 동작**
  ```bash
  npm run lint
  npm run format
  # 에러 없이 완료
  ```

### 4.2 품질 기준

- [ ] **디렉토리 구조 완성**
  - app/, components/, lib/, types/, store/, hooks/ 디렉토리 생성
  - 각 디렉토리에 README.md 또는 .gitkeep 파일 생성

- [ ] **TypeScript 설정 엄격성**
  - strict: true
  - noImplicitAny: true
  - strictNullChecks: true

- [ ] **문서화**
  - README.md 작성
  - 환경 변수 설명 (.env.example)

---

## 5. 출력물

### 5.1 생성될 파일

1. **프로젝트 설정**:
   - `frontend/package.json`
   - `frontend/tsconfig.json`
   - `frontend/next.config.js`
   - `frontend/tailwind.config.ts`
   - `frontend/.eslintrc.json`
   - `frontend/.prettierrc`
   - `frontend/components.json` (shadcn/ui)

2. **환경 변수**:
   - `frontend/.env.local`
   - `frontend/.env.example`

3. **문서**:
   - `frontend/README.md`

4. **테스트 페이지**:
   - `frontend/app/page.tsx` (shadcn/ui 컴포넌트 테스트)
   - `frontend/app/layout.tsx`

5. **디렉토리**:
   - `frontend/components/` (ui, search, history, feedback)
   - `frontend/lib/`
   - `frontend/types/`
   - `frontend/store/`
   - `frontend/hooks/`

### 5.2 수정될 파일
- 없음 (신규 프로젝트)

---

## 6. 실행 명령어 요약

```bash
# Step 1: Next.js 프로젝트 생성
cd /Users/young/Dev/workspace/cc-scaffold-demo
npx create-next-app@latest frontend

# Step 2: Prettier 설치
cd frontend
npm install --save-dev prettier eslint-config-prettier

# Step 3: shadcn/ui 초기화
npx shadcn-ui@latest init
npx shadcn-ui@latest add button input card

# Step 4: 디렉토리 생성
mkdir -p components/{ui,search,history,feedback} lib types store hooks
mkdir -p app/{search,history,login,api}

# Step 5: 환경 변수 생성
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
cp .env.local .env.example

# Step 6: 개발 서버 실행
npm run dev

# Step 7: 빌드 테스트
npm run build

# Step 8: Lint 및 Format
npm run lint
npm run format
```

---

## 7. 참고 문서

- **Next.js 14 공식 문서**: https://nextjs.org/docs
- **shadcn/ui 공식 문서**: https://ui.shadcn.com/
- **Tailwind CSS 공식 문서**: https://tailwindcss.com/docs
- **TypeScript 공식 문서**: https://www.typescriptlang.org/docs/

---

## 8. 트러블슈팅

### 문제 1: shadcn/ui 설치 실패
**증상**: `npx shadcn-ui@latest init` 실패

**해결**:
```bash
# Node.js 버전 확인 (18.17 이상 필요)
node -v

# npm 캐시 정리
npm cache clean --force

# 재시도
npx shadcn-ui@latest init
```

### 문제 2: Tailwind CSS 스타일 적용 안됨
**증상**: 브라우저에서 Tailwind 클래스 스타일 미적용

**해결**:
1. `tailwind.config.ts` content 경로 확인:
   ```ts
   content: [
     './app/**/*.{js,ts,jsx,tsx,mdx}',
     './components/**/*.{js,ts,jsx,tsx,mdx}',
   ]
   ```

2. `app/globals.css` Tailwind directives 확인:
   ```css
   @tailwind base;
   @tailwind components;
   @tailwind utilities;
   ```

3. 개발 서버 재시작:
   ```bash
   npm run dev
   ```

---

**작성자**: Claude Code (Sonnet 4.5)
**작성일**: 2026-01-04
