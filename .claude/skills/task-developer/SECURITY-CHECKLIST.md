# Security Checklist

모든 Task 구현 시 이 체크리스트를 확인하세요.
**[HARD RULE] 항목은 절대 위반 불가합니다.**

---

## Pre-Implementation (구현 전)

### 데이터 & 개인정보 분석

- [ ] **[HARD] 민감 데이터 처리 여부 확인**
  - 고객 정보 (이름, 주민번호, 전화번호, 주소 등)
  - 결제 정보 (카드번호, 계좌번호, 거래내역 등)
  - 인증 정보 (비밀번호, 토큰, API 키 등)
  - 개인 식별 정보 (이메일, 디바이스 ID 등)

- [ ] **[HARD] 민감 데이터 생성/가정 금지**
  - ❌ 실제 고객처럼 보이는 테스트 데이터
  - ❌ "010-1234-5678" 같은 실제 전화번호 형식
  - ❌ "홍길동", "김철수" 같은 실제 이름
  - ✅ "user-{id}", "test-account-1" 같은 명백히 테스트용 데이터만

- [ ] **데이터 분류 확인**
  - Public (공개 가능)
  - Internal (내부 전용)
  - Confidential (기밀)
  - Restricted (제한, 민감 정보)

### 인증/인가 영향 분석

- [ ] **[HARD] Auth/Authz 로직 변경 여부**
  - 인증 메커니즘 수정
  - 권한 체크 로직 변경
  - 역할(Role) 정의 변경
  - 접근 제어 정책 수정

- [ ] **[HARD] 보안 설정 변경 여부**
  - CORS 설정
  - 세션 관리
  - 토큰 만료 시간
  - 암호화 알고리즘

**⚠️ 위 항목에 해당하면 명시적 승인 없이 진행 금지**

### 프로덕션 영향 평가

- [ ] **[HARD] 프로덕션 환경 변경 여부**
  - 환경 변수 수정
  - 설정 파일 변경
  - 인프라 설정 변경
  - 데이터베이스 스키마 변경

- [ ] **실험 vs 프로덕션 분류**
  - 실험적 코드인 경우 명확히 표시
  - Feature flag로 분리 가능한지 검토
  - 롤백 전략 수립

---

## During Implementation (구현 중)

### 코드 레벨 보안

#### 1. 입력 검증 (Input Validation)

- [ ] **외부 입력 검증**
  - 사용자 입력 (폼, API 파라미터)
  - 외부 API 응답
  - 파일 업로드
  - URL 파라미터

- [ ] **검증 항목**
  - 타입 검증 (string, number, boolean 등)
  - 길이 제한
  - 형식 검증 (이메일, URL, 전화번호 등)
  - 허용 목록 (Whitelist) 사용

**⚠️ 내부 코드 간 통신은 과도한 검증 불필요 (프레임워크 보장 신뢰)**

#### 2. 주입 공격 방지 (Injection Prevention)

- [ ] **SQL Injection**
  - ✅ Parameterized queries 또는 ORM 사용
  - ❌ 문자열 연결로 SQL 쿼리 생성 금지
  ```javascript
  // ❌ BAD
  const query = `SELECT * FROM users WHERE id = ${userId}`;

  // ✅ GOOD
  const query = 'SELECT * FROM users WHERE id = ?';
  db.query(query, [userId]);
  ```

- [ ] **Command Injection**
  - ❌ 사용자 입력을 직접 shell 명령에 전달 금지
  - ✅ 허용 목록 기반 명령만 실행
  ```javascript
  // ❌ BAD
  exec(`convert ${userFilename}`);

  // ✅ GOOD
  const allowedCommands = ['convert', 'resize'];
  if (allowedCommands.includes(command)) { /* ... */ }
  ```

- [ ] **XSS (Cross-Site Scripting)**
  - ✅ 출력 시 HTML 이스케이프
  - ✅ Content Security Policy (CSP) 설정
  - ❌ innerHTML에 사용자 입력 직접 삽입 금지
  ```javascript
  // ❌ BAD
  element.innerHTML = userInput;

  // ✅ GOOD
  element.textContent = userInput;
  // or use sanitization library
  ```

#### 3. 인증 & 세션

- [ ] **[HARD] 기존 인증 로직 무결성**
  - 인증 체크 우회 가능성 없음
  - 세션 하이재킹 방지
  - CSRF 토큰 검증

- [ ] **비밀번호 처리**
  - ❌ 평문 저장 금지
  - ✅ bcrypt, argon2 등 안전한 해싱
  - ✅ Salt 사용

- [ ] **토큰 관리**
  - JWT 만료 시간 설정
  - Refresh token 보안 저장
  - 토큰 무효화 메커니즘

#### 4. 민감 데이터 처리

- [ ] **[HARD] 로깅**
  - ❌ 비밀번호, 토큰, API 키 로그 출력 금지
  - ❌ 신용카드 정보, 개인정보 로그 금지
  - ✅ 민감 필드 마스킹 (`***`, `[REDACTED]`)
  ```javascript
  // ❌ BAD
  console.log('User login:', { email, password });

  // ✅ GOOD
  console.log('User login:', { email, password: '[REDACTED]' });
  ```

- [ ] **[HARD] 하드코딩 금지**
  - ❌ API 키, 비밀번호 코드에 직접 작성 금지
  - ✅ 환경 변수 사용
  - ✅ Secret management 시스템 사용
  ```javascript
  // ❌ BAD
  const apiKey = 'sk-1234567890abcdef';

  // ✅ GOOD
  const apiKey = process.env.API_KEY;
  ```

- [ ] **전송 중 보안**
  - HTTPS 사용 (민감 데이터 전송 시)
  - TLS 1.2 이상
  - 암호화되지 않은 채널로 민감 데이터 전송 금지

- [ ] **저장 시 보안**
  - 민감 데이터 암호화 저장
  - 암호화 키 안전한 장소 보관
  - 불필요한 민감 데이터 보관 금지

#### 5. 에러 처리

- [ ] **에러 메시지 노출**
  - ❌ 스택 트레이스 클라이언트에 노출 금지
  - ❌ 데이터베이스 에러 상세 정보 노출 금지
  - ✅ 일반적인 에러 메시지만 반환
  ```javascript
  // ❌ BAD
  res.status(500).json({ error: error.stack });

  // ✅ GOOD
  res.status(500).json({ error: 'Internal server error' });
  logger.error(error.stack); // 서버 로그에만
  ```

- [ ] **실패 처리**
  - 인증 실패 시 구체적 이유 노출 금지
  - "ID 또는 비밀번호가 잘못되었습니다" (ID 존재 여부 노출 방지)

#### 6. 권한 제어

- [ ] **수평적 권한 확인**
  - 사용자가 자신의 리소스만 접근하는지 확인
  ```javascript
  // ✅ GOOD
  const resource = await db.query(
    'SELECT * FROM resources WHERE id = ? AND user_id = ?',
    [resourceId, currentUserId]
  );
  ```

- [ ] **수직적 권한 확인**
  - 관리자 기능은 관리자만 접근 가능
  - 역할 기반 접근 제어 (RBAC)

- [ ] **API 엔드포인트 보호**
  - 모든 보호된 엔드포인트에 인증 미들웨어
  - 권한 체크 누락 없음

---

## Post-Implementation (구현 후)

### 코드 리뷰 체크

- [ ] **보안 취약점 스캔**
  - Dependency 취약점 확인 (`npm audit`, `pip-audit` 등)
  - SAST (Static Application Security Testing) 도구 실행

- [ ] **시크릿 스캔**
  - Git history에 시크릿 노출 확인
  - `.env` 파일 `.gitignore`에 포함 확인

- [ ] **테스트에 보안 시나리오 포함**
  - 인증 실패 케이스
  - 권한 부족 케이스
  - 잘못된 입력 케이스

### 문서화

- [ ] **보안 관련 결정 문서화**
  - 왜 이 암호화 방식을 선택했는지
  - 왜 이 권한 모델을 사용하는지

- [ ] **위험 요소 명시**
  - 알려진 제약사항
  - 보안 가정 (assumptions)

---

## OWASP Top 10 Quick Check

모든 구현은 OWASP Top 10을 고려해야 합니다:

- [ ] **A01:2021 – Broken Access Control**
  - 권한 체크 누락 없음

- [ ] **A02:2021 – Cryptographic Failures**
  - 민감 데이터 암호화됨

- [ ] **A03:2021 – Injection**
  - SQL, Command, XSS 방지됨

- [ ] **A04:2021 – Insecure Design**
  - 보안을 고려한 설계

- [ ] **A05:2021 – Security Misconfiguration**
  - 기본 설정 검토됨

- [ ] **A06:2021 – Vulnerable and Outdated Components**
  - Dependency 최신 버전

- [ ] **A07:2021 – Identification and Authentication Failures**
  - 인증 메커니즘 안전함

- [ ] **A08:2021 – Software and Data Integrity Failures**
  - 코드/데이터 무결성 보장

- [ ] **A09:2021 – Security Logging and Monitoring Failures**
  - 보안 이벤트 로깅됨

- [ ] **A10:2021 – Server-Side Request Forgery (SSRF)**
  - 서버 측 요청 검증됨

---

## 기술 스택별 추가 체크

### Java/Spring

- [ ] Spring Security 올바르게 설정
- [ ] CSRF 보호 활성화
- [ ] SQL Injection: JPA/Hibernate 사용
- [ ] 직렬화 취약점 확인

### Node.js/Express

- [ ] helmet.js 미들웨어 사용
- [ ] express-rate-limit 적용
- [ ] NoSQL Injection 방지 (MongoDB 사용 시)
- [ ] prototype pollution 방지

### Python/FastAPI

- [ ] Pydantic 모델로 입력 검증
- [ ] SQL Injection: SQLAlchemy ORM 사용
- [ ] CORS 설정 확인
- [ ] Rate limiting 적용

### Frontend (Next.js/React)

- [ ] XSS 방지: React 자동 이스케이프 활용
- [ ] CSP 헤더 설정
- [ ] 민감 데이터 localStorage 저장 금지
- [ ] API 키 클라이언트 노출 금지

---

## Red Flags (즉시 중단 신호)

다음을 발견하면 **즉시 구현 중단**하고 사용자에게 보고:

- 🚨 실제 고객 데이터 사용
- 🚨 비밀번호 평문 저장
- 🚨 하드코딩된 API 키/시크릿
- 🚨 인증 체크 우회 코드
- 🚨 SQL 쿼리 문자열 연결
- 🚨 민감 정보 로그 출력
- 🚨 프로덕션 설정 무단 변경
- 🚨 권한 체크 없는 관리자 기능

---

## 완료 확인

모든 Task 완료 시 최종 확인:

- [ ] 모든 [HARD RULE] 항목 준수
- [ ] 보안 관련 테스트 포함
- [ ] 민감 데이터 처리 안전
- [ ] 인증/인가 무결성 유지
- [ ] 로그에 민감 정보 없음
- [ ] 시크릿 하드코딩 없음
- [ ] 입력 검증 적절함
- [ ] 에러 메시지 안전함

**체크리스트 완료 전까지 Task를 "완료"로 표시하지 마세요.**

---

## 참고 자료

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)
- CLAUDE.md Section 3: Security, Financial, and Production Safety
- 회사 보안 정책 문서 (별도)

---

> **Remember**:
> 보안은 "나중에" 추가할 수 있는 것이 아닙니다.
> 처음부터 안전하게 만드는 것이 유일한 방법입니다.
