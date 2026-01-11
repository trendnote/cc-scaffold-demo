# API Reference

## 목차

1. [개요](#개요)
2. [인증](#인증)
3. [엔드포인트](#엔드포인트)
4. [Error Codes](#error-codes)
5. [Rate Limiting](#rate-limiting)

---

## 개요

### Base URL

```
Development:  http://localhost:8000
Production:   https://api.example.com
```

### API 버전

현재 버전: `v1`

모든 API 엔드포인트는 `/api/v1` 접두사를 사용합니다.

### Content Type

```
Content-Type: application/json
Accept: application/json
```

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 인증

### JWT Bearer Token

모든 API 요청은 JWT 토큰을 사용하여 인증합니다.

**요청 헤더**:

```http
Authorization: Bearer <access_token>
```

### 로그인

**Endpoint**: `POST /api/v1/auth/login`

**Request**:

```json
{
  "username": "user@example.com",
  "password": "password123"
}
```

**Response (200 OK)**:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Example**:

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"user@example.com","password":"password123"}'
```

### Token Refresh

**Endpoint**: `POST /api/v1/auth/refresh`

**Request**:

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK)**:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

---

## 엔드포인트

### Health Check

#### GET /health

시스템 상태 확인

**인증**: 불필요

**Response (200 OK)**:

```json
{
  "status": "healthy",
  "database": "connected",
  "milvus": "connected",
  "llm": "available",
  "timestamp": "2026-01-11T14:30:45.123456Z"
}
```

**Example**:

```bash
curl http://localhost:8000/health
```

---

### Authentication

#### POST /api/v1/auth/register

사용자 등록

**인증**: 불필요

**Request**:

```json
{
  "email": "user@example.com",
  "password": "password123",
  "full_name": "John Doe",
  "department": "Engineering"
}
```

**Response (201 Created)**:

```json
{
  "id": "user123",
  "email": "user@example.com",
  "full_name": "John Doe",
  "department": "Engineering",
  "access_level": "L1",
  "created_at": "2026-01-11T14:30:45.123456Z"
}
```

**Errors**:

- `400 Bad Request`: 이메일 중복
- `422 Unprocessable Entity`: 유효하지 않은 입력

**Example**:

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123",
    "full_name": "John Doe",
    "department": "Engineering"
  }'
```

#### POST /api/v1/auth/login

사용자 로그인

**인증**: 불필요

**Request**:

```json
{
  "username": "user@example.com",
  "password": "password123"
}
```

**Response (200 OK)**:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Errors**:

- `401 Unauthorized`: 잘못된 인증 정보

#### GET /api/v1/auth/me

현재 사용자 정보 조회

**인증**: 필요

**Response (200 OK)**:

```json
{
  "id": "user123",
  "email": "user@example.com",
  "full_name": "John Doe",
  "department": "Engineering",
  "access_level": "L1"
}
```

**Example**:

```bash
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

---

### Search

#### POST /api/v1/search/query

RAG 기반 검색 쿼리 실행

**인증**: 필요

**Request**:

```json
{
  "query": "How to deploy FastAPI application?",
  "filters": {
    "department": "Engineering",
    "access_level": "L1"
  }
}
```

**Response (200 OK)**:

```json
{
  "search_id": "search123",
  "query": "How to deploy FastAPI application?",
  "answer": "To deploy a FastAPI application, you can use...",
  "sources": [
    {
      "id": "doc1",
      "title": "FastAPI Deployment Guide",
      "content": "FastAPI can be deployed using...",
      "score": 0.95,
      "metadata": {
        "department": "Engineering",
        "access_level": "L1"
      }
    },
    {
      "id": "doc2",
      "title": "Docker Deployment",
      "content": "Using Docker to deploy...",
      "score": 0.87,
      "metadata": {
        "department": "Engineering",
        "access_level": "L1"
      }
    }
  ],
  "duration_ms": 2345,
  "timestamp": "2026-01-11T14:30:45.123456Z"
}
```

**Parameters**:

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `query` | string | ✓ | 검색 쿼리 (1-500자) |
| `filters` | object | × | 필터 조건 |
| `filters.department` | string | × | 부서 필터 (Engineering, HR, Management) |
| `filters.access_level` | string | × | 접근 레벨 (L1, L2, L3) |

**Errors**:

- `400 Bad Request`: 잘못된 필터 값
- `422 Unprocessable Entity`: 유효하지 않은 쿼리

**Performance**:

- P95 응답 시간: < 30초
- P99 응답 시간: < 45초

**Example**:

```bash
curl -X POST http://localhost:8000/api/v1/search/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How to deploy FastAPI?",
    "filters": {
      "department": "Engineering"
    }
  }'
```

#### GET /api/v1/search/history

검색 히스토리 조회

**인증**: 필요

**Query Parameters**:

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|----------|------|------|--------|------|
| `page` | integer | × | 1 | 페이지 번호 |
| `size` | integer | × | 20 | 페이지 크기 (1-100) |
| `sort` | string | × | desc | 정렬 순서 (asc, desc) |

**Response (200 OK)**:

```json
{
  "items": [
    {
      "search_id": "search123",
      "query": "How to deploy FastAPI?",
      "answer_preview": "To deploy a FastAPI application...",
      "source_count": 3,
      "timestamp": "2026-01-11T14:30:45.123456Z"
    },
    {
      "search_id": "search122",
      "query": "Docker best practices",
      "answer_preview": "Docker best practices include...",
      "source_count": 5,
      "timestamp": "2026-01-11T14:25:30.123456Z"
    }
  ],
  "total": 42,
  "page": 1,
  "size": 20,
  "pages": 3
}
```

**Example**:

```bash
curl "http://localhost:8000/api/v1/search/history?page=1&size=20" \
  -H "Authorization: Bearer $TOKEN"
```

#### GET /api/v1/search/{search_id}

특정 검색 결과 조회

**인증**: 필요

**Path Parameters**:

| 파라미터 | 타입 | 설명 |
|----------|------|------|
| `search_id` | string | 검색 ID |

**Response (200 OK)**:

```json
{
  "search_id": "search123",
  "query": "How to deploy FastAPI?",
  "answer": "To deploy a FastAPI application, you can use...",
  "sources": [...],
  "duration_ms": 2345,
  "timestamp": "2026-01-11T14:30:45.123456Z"
}
```

**Errors**:

- `404 Not Found`: 검색 결과 없음
- `403 Forbidden`: 접근 권한 없음

**Example**:

```bash
curl http://localhost:8000/api/v1/search/search123 \
  -H "Authorization: Bearer $TOKEN"
```

---

### Documents

#### POST /api/v1/documents

문서 업로드

**인증**: 필요

**Request**:

```json
{
  "title": "FastAPI Deployment Guide",
  "content": "This guide covers how to deploy FastAPI...",
  "metadata": {
    "department": "Engineering",
    "access_level": "L1",
    "tags": ["fastapi", "deployment", "docker"]
  }
}
```

**Response (201 Created)**:

```json
{
  "id": "doc123",
  "title": "FastAPI Deployment Guide",
  "content_preview": "This guide covers how to deploy FastAPI...",
  "metadata": {
    "department": "Engineering",
    "access_level": "L1",
    "tags": ["fastapi", "deployment", "docker"]
  },
  "created_at": "2026-01-11T14:30:45.123456Z",
  "updated_at": "2026-01-11T14:30:45.123456Z"
}
```

**Example**:

```bash
curl -X POST http://localhost:8000/api/v1/documents \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "FastAPI Deployment Guide",
    "content": "This guide covers...",
    "metadata": {
      "department": "Engineering",
      "access_level": "L1"
    }
  }'
```

#### GET /api/v1/documents

문서 목록 조회

**인증**: 필요

**Query Parameters**:

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|----------|------|------|--------|------|
| `page` | integer | × | 1 | 페이지 번호 |
| `size` | integer | × | 20 | 페이지 크기 (1-100) |
| `department` | string | × | - | 부서 필터 |
| `access_level` | string | × | - | 접근 레벨 필터 |

**Response (200 OK)**:

```json
{
  "items": [
    {
      "id": "doc123",
      "title": "FastAPI Deployment Guide",
      "content_preview": "This guide covers how to deploy...",
      "metadata": {
        "department": "Engineering",
        "access_level": "L1"
      },
      "created_at": "2026-01-11T14:30:45.123456Z"
    }
  ],
  "total": 150,
  "page": 1,
  "size": 20,
  "pages": 8
}
```

#### GET /api/v1/documents/{document_id}

문서 상세 조회

**인증**: 필요

**Response (200 OK)**:

```json
{
  "id": "doc123",
  "title": "FastAPI Deployment Guide",
  "content": "Full content of the document...",
  "metadata": {
    "department": "Engineering",
    "access_level": "L1",
    "tags": ["fastapi", "deployment"]
  },
  "created_at": "2026-01-11T14:30:45.123456Z",
  "updated_at": "2026-01-11T14:30:45.123456Z"
}
```

**Errors**:

- `404 Not Found`: 문서 없음
- `403 Forbidden`: 접근 권한 없음

#### PUT /api/v1/documents/{document_id}

문서 수정

**인증**: 필요

**Request**:

```json
{
  "title": "Updated Title",
  "content": "Updated content...",
  "metadata": {
    "department": "Engineering",
    "access_level": "L2"
  }
}
```

**Response (200 OK)**:

```json
{
  "id": "doc123",
  "title": "Updated Title",
  "content": "Updated content...",
  "metadata": {
    "department": "Engineering",
    "access_level": "L2"
  },
  "created_at": "2026-01-11T14:30:45.123456Z",
  "updated_at": "2026-01-11T15:00:00.123456Z"
}
```

#### DELETE /api/v1/documents/{document_id}

문서 삭제

**인증**: 필요

**Response (204 No Content)**

**Errors**:

- `404 Not Found`: 문서 없음
- `403 Forbidden`: 삭제 권한 없음

---

## Error Codes

### HTTP Status Codes

| 코드 | 의미 | 설명 |
|------|------|------|
| 200 | OK | 요청 성공 |
| 201 | Created | 리소스 생성 성공 |
| 204 | No Content | 요청 성공 (응답 본문 없음) |
| 400 | Bad Request | 잘못된 요청 |
| 401 | Unauthorized | 인증 실패 |
| 403 | Forbidden | 권한 없음 |
| 404 | Not Found | 리소스 없음 |
| 422 | Unprocessable Entity | 유효성 검증 실패 |
| 500 | Internal Server Error | 서버 오류 |
| 503 | Service Unavailable | 서비스 일시 중단 |

### Error Response Format

```json
{
  "detail": "Error message",
  "error_code": "INVALID_INPUT",
  "timestamp": "2026-01-11T14:30:45.123456Z"
}
```

### Error Codes

| 코드 | 설명 |
|------|------|
| `INVALID_INPUT` | 유효하지 않은 입력 |
| `AUTHENTICATION_FAILED` | 인증 실패 |
| `INSUFFICIENT_PERMISSIONS` | 권한 부족 |
| `RESOURCE_NOT_FOUND` | 리소스 없음 |
| `DUPLICATE_RESOURCE` | 중복 리소스 |
| `RATE_LIMIT_EXCEEDED` | 요청 한도 초과 |
| `INTERNAL_ERROR` | 내부 서버 오류 |

**Example**:

```json
{
  "detail": "Email already exists",
  "error_code": "DUPLICATE_RESOURCE",
  "timestamp": "2026-01-11T14:30:45.123456Z"
}
```

---

## Rate Limiting

### 제한

| 엔드포인트 | 제한 | 기간 |
|------------|------|------|
| `/api/v1/search/query` | 60 requests | 1분 |
| `/api/v1/auth/login` | 10 requests | 5분 |
| 기타 | 100 requests | 1분 |

### Headers

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1641920445
```

### 429 Too Many Requests

```json
{
  "detail": "Rate limit exceeded. Try again in 45 seconds.",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "retry_after": 45
}
```

---

## SDK Examples

### Python

```python
import requests

# 설정
BASE_URL = "http://localhost:8000"
token = None

# 로그인
response = requests.post(
    f"{BASE_URL}/api/v1/auth/login",
    json={"username": "user@example.com", "password": "password123"}
)
token = response.json()["access_token"]

# 검색
headers = {"Authorization": f"Bearer {token}"}
response = requests.post(
    f"{BASE_URL}/api/v1/search/query",
    json={"query": "How to deploy FastAPI?"},
    headers=headers
)
result = response.json()
print(result["answer"])
```

### JavaScript (Node.js)

```javascript
const axios = require('axios');

const BASE_URL = 'http://localhost:8000';
let token;

// 로그인
async function login() {
  const response = await axios.post(`${BASE_URL}/api/v1/auth/login`, {
    username: 'user@example.com',
    password: 'password123',
  });
  token = response.data.access_token;
}

// 검색
async function search(query) {
  const response = await axios.post(
    `${BASE_URL}/api/v1/search/query`,
    { query },
    { headers: { Authorization: `Bearer ${token}` } }
  );
  return response.data;
}

// 사용
(async () => {
  await login();
  const result = await search('How to deploy FastAPI?');
  console.log(result.answer);
})();
```

### TypeScript (React)

```typescript
const API_URL = process.env.NEXT_PUBLIC_API_URL;

interface SearchResult {
  answer: string;
  sources: Source[];
  search_id: string;
}

async function searchQuery(query: string, token: string): Promise<SearchResult> {
  const response = await fetch(`${API_URL}/api/v1/search/query`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({ query }),
  });

  if (!response.ok) {
    throw new Error('Search failed');
  }

  return response.json();
}

// 사용 (React Component)
function SearchComponent() {
  const [result, setResult] = useState<SearchResult | null>(null);

  const handleSearch = async (query: string) => {
    const token = localStorage.getItem('token');
    const data = await searchQuery(query, token!);
    setResult(data);
  };

  return (
    <div>
      {result && <div>{result.answer}</div>}
    </div>
  );
}
```

---

## Changelog

### v1.0.0 (2026-01-11)

- Initial API release
- Authentication endpoints
- Search endpoints
- Document management endpoints

---

## 관련 문서

- [Deployment Guide](../operations/deployment-guide.md) - 배포 가이드
- [Development Setup](../development/setup.md) - 개발 환경 설정
- [Testing Guide](../development/testing-guide.md) - API 테스트 가이드

---

**API 문서는 항상 최신 상태로 유지하세요!** 📚
