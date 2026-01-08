# Task 3.5: Mock 인증 시스템 구현 - 실행 계획

---

## 📋 Meta

- **Task ID**: 3.5
- **Task명**: Mock 인증 시스템 구현
- **예상 시간**: 6시간
- **담당**: Backend + Frontend
- **작성일**: 2026-01-04
- **상태**: Ready for Implementation
- **버전**: 1.0.0

---

## 1. Executive Summary

### 1.1 목표
JWT 기반 인증 시스템을 Backend와 Frontend에 구현합니다.

### 1.2 핵심 요구사항
- **Backend**: JWT 토큰 생성, 검증 Middleware, 로그아웃 API
- **Frontend**: 로그인 API 호출, httpOnly Cookie 저장, 토큰 자동 갱신
- **[HARD RULE]**: JWT Secret 환경 변수 관리

### 1.3 성공 기준
- [ ] 로그인 → 토큰 발급 성공
- [ ] 보호된 API 호출 성공 (토큰 포함)
- [ ] 토큰 만료 → 401 에러
- [ ] 로그아웃 → 토큰 삭제

---

## 2. 구현 단계

### Backend Implementation

#### Step 1: JWT 라이브러리 설치 (10분)

```bash
cd backend
pip install python-jose[cryptography] passlib[bcrypt]
```

**requirements.txt 업데이트**:
```
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
```

---

#### Step 2: JWT 설정 (30분)

**`backend/app/core/security.py` 생성**:
```python
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

# 비밀번호 해싱
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT 설정
SECRET_KEY = settings.JWT_SECRET
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1시간


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    JWT Access Token 생성

    Args:
        data: 토큰에 포함할 데이터 (예: user_id, email)
        expires_delta: 만료 시간 (기본 1시간)

    Returns:
        str: JWT 토큰
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """
    JWT 토큰 검증

    Args:
        token: JWT 토큰

    Returns:
        dict: 토큰에 포함된 데이터 (성공 시)
        None: 검증 실패 시
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호 검증"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """비밀번호 해싱"""
    return pwd_context.hash(password)
```

---

#### Step 3: 인증 API 구현 (90분)

**`backend/app/routers/auth.py` 생성**:
```python
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from app.core.security import create_access_token, verify_token, verify_password
from app.core.config import settings

router = APIRouter()
security = HTTPBearer()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class LogoutResponse(BaseModel):
    message: str


# Mock 사용자 데이터 (실제로는 DB에서 조회)
MOCK_USERS = {
    "user@example.com": {
        "user_id": "user_001",
        "email": "user@example.com",
        "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aeGVYCH/TbTy",  # "password123"
        "access_level": 2,
        "department": "Engineering",
    },
    "admin@example.com": {
        "user_id": "admin_001",
        "email": "admin@example.com",
        "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aeGVYCH/TbTy",  # "password123"
        "access_level": 3,
        "department": "Management",
    },
}


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    로그인 API

    Mock 사용자:
    - user@example.com / password123 (L2, Engineering)
    - admin@example.com / password123 (L3, Management)
    """
    # 사용자 조회
    user = MOCK_USERS.get(request.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다.",
        )

    # 비밀번호 검증
    if not verify_password(request.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다.",
        )

    # JWT 토큰 생성
    access_token = create_access_token(
        data={
            "user_id": user["user_id"],
            "email": user["email"],
            "access_level": user["access_level"],
            "department": user["department"],
        }
    )

    return LoginResponse(
        access_token=access_token,
        user={
            "user_id": user["user_id"],
            "email": user["email"],
            "access_level": user["access_level"],
            "department": user["department"],
        },
    )


@router.post("/logout", response_model=LogoutResponse)
async def logout():
    """
    로그아웃 API

    클라이언트에서 토큰 삭제 처리
    """
    return LogoutResponse(message="로그아웃 되었습니다.")


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    현재 사용자 가져오기 (Dependency)

    Usage:
        @router.get("/protected")
        async def protected_route(user = Depends(get_current_user)):
            return {"user": user}
    """
    token = credentials.credentials
    payload = verify_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="토큰이 유효하지 않습니다.",
        )

    return payload
```

**`backend/app/main.py`에 라우터 추가**:
```python
from app.routers import auth

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
```

---

#### Step 4: 환경 변수 설정 (15분)

**`backend/.env` 업데이트**:
```bash
# JWT Secret (절대 하드코딩 금지!)
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
```

**`backend/app/core/config.py` 업데이트**:
```python
class Settings(BaseSettings):
    # ... 기존 설정
    JWT_SECRET: str

    class Config:
        env_file = ".env"
```

---

### Frontend Implementation

#### Step 5: 인증 API 클라이언트 (60min)

**`lib/api/auth.ts` 생성**:
```typescript
import apiClient from '../api-client';
import { LoginRequest, LoginResponse } from '@/types/api';

export const authAPI = {
  // 로그인
  login: async (request: LoginRequest): Promise<LoginResponse> => {
    const response = await apiClient.post<LoginResponse>(
      '/api/v1/auth/login',
      request
    );
    return response.data;
  },

  // 로그아웃
  logout: async (): Promise<void> => {
    await apiClient.post('/api/v1/auth/logout');
  },
};
```

#### Step 6: 인증 Context (90min)

**`lib/auth-context.tsx` 생성**:
```typescript
'use client';

import { createContext, useContext, useEffect, useState } from 'react';
import { authAPI } from '@/lib/api/auth';
import { LoginRequest } from '@/types/api';

interface User {
  user_id: string;
  email: string;
  access_level: number;
  department: string;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (request: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // 페이지 로드 시 로컬 스토리지에서 토큰 확인
    const token = localStorage.getItem('access_token');
    const userStr = localStorage.getItem('user');

    if (token && userStr) {
      setUser(JSON.parse(userStr));
    }
    setIsLoading(false);
  }, []);

  const login = async (request: LoginRequest) => {
    try {
      const response = await authAPI.login(request);

      // 토큰 및 사용자 정보 저장
      localStorage.setItem('access_token', response.access_token);
      localStorage.setItem('user', JSON.stringify(response.user));

      setUser(response.user);
    } catch (error) {
      throw error;
    }
  };

  const logout = async () => {
    try {
      await authAPI.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // 로컬 스토리지에서 삭제
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      setUser(null);
    }
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
```

**`app/layout.tsx` 수정**:
```typescript
import { AuthProvider } from '@/lib/auth-context';

// ... QueryClientProvider 내부에 AuthProvider 추가
<QueryClientProvider client={queryClient}>
  <AuthProvider>
    {children}
  </AuthProvider>
  <ReactQueryDevtools initialIsOpen={false} />
</QueryClientProvider>
```

---

## 3. 검증 기준

- [ ] 로그인 API 호출 성공 (user@example.com / password123)
- [ ] 토큰 로컬 스토리지 저장 확인
- [ ] Authorization Header에 토큰 포함 확인
- [ ] 잘못된 비밀번호 → 401 에러
- [ ] 토큰 만료 → 401 에러 (1시간 후)
- [ ] 로그아웃 → 토큰 삭제 확인

---

## 4. 출력물

### Backend
1. `backend/app/core/security.py`
2. `backend/app/routers/auth.py`
3. `backend/requirements.txt` (업데이트)
4. `backend/.env` (JWT_SECRET 추가)

### Frontend
1. `lib/api/auth.ts`
2. `lib/auth-context.tsx`
3. `app/layout.tsx` (수정)

---

**작성자**: Claude Code (Sonnet 4.5)
**작성일**: 2026-01-04
