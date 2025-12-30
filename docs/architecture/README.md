# 아키텍처 설계 가이드

이 문서는 PRD와 기술 스택을 기반으로
**시스템 아키텍처를 설계하기 위한 가이드**이다.

---

## 1. 아키텍처 설계의 목적

아키텍처 설계는 다음을 명확히 하기 위해 수행한다.

- 시스템을 어떻게 구성할 것인가
- 컴포넌트들이 어떻게 상호작용하는가
- 데이터가 어떻게 흐르는가
- 시스템을 어떻게 배포할 것인가

아키텍처는 **기술 스택을 활용한 구체적인 설계**이다.
구현 코드와는 다르지만, 구현의 청사진이 된다.

---

## 2. 아키텍처 설계 시점

다음 상황에서 아키텍처를 설계한다.

- 기술 스택이 결정된 직후
- 구현 시작 전
- 시스템 구조 변경이 필요할 때
- 성능/확장성 문제 해결 시

---

## 3. 아키텍처 설계 원칙

### 3.1 요구사항 충족
- PRD의 모든 기능 요구사항 구현 가능
- 성능, 보안, 확장성 목표 달성 가능
- 기술 스택과 일관성

### 3.2 단순성 우선
- 복잡한 패턴보다 단순한 패턴
- 필요한 만큼만 설계
- Over-engineering 지양

### 3.3 확장 가능성
- 미래 변경을 고려한 설계
- 모듈화, 느슨한 결합
- 단계적 확장 가능

### 3.4 운영 가능성
- 모니터링 가능
- 디버깅 가능
- 장애 대응 가능

---

## 4. 아키텍처 구성 요소

아키텍처 문서는 다음을 포함한다.

### 4.1 System Architecture
- 전체 시스템 구조
- 주요 컴포넌트
- 컴포넌트 간 관계

### 4.2 Component Design
- 각 컴포넌트 상세 설계
- 책임과 역할
- 인터페이스

### 4.3 Data Flow
- 데이터가 흐르는 경로
- 데이터 변환 과정
- 상태 관리

### 4.4 API Design
- 엔드포인트 정의
- Request/Response 스키마
- 에러 처리

### 4.5 Database Design
- 스키마 설계
- 인덱스 전략
- 마이그레이션 계획

### 4.6 Security Architecture
- 인증/인가 흐름
- 데이터 암호화
- 보안 경계

### 4.7 Deployment Architecture
- 배포 구조
- 스케일링 전략
- 고가용성 설계

---

## 5. 아키텍처 패턴

프로젝트 특성에 맞는 패턴을 선택한다.

### 5.1 Backend Patterns
- Monolithic
- Microservices
- Serverless
- Layered Architecture
- Clean Architecture

### 5.2 Frontend Patterns
- MVC
- MVVM
- Component-based
- Micro-frontends

### 5.3 Data Patterns
- CQRS
- Event Sourcing
- Database per Service
- Shared Database

---

## 6. 아키텍처와 다른 문서의 관계

```
PRD (요구사항)
  ↓
Tech Stack (도구)
  ↓
Architecture (구조) ← 이 문서
  ↓
Implementation (코드)
```

- PRD 변경 → Architecture 재검토
- Tech Stack 변경 → Architecture 재설계
- Architecture 변경 → 구현 코드 영향

---

## 7. 템플릿 사용

아키텍처 설계 시 `TEMPLATE.md`를 기준으로 작성한다.

- 다이어그램은 필수
- 텍스트만으로는 부족
- Mermaid, PlantUML, 또는 이미지 사용

---

## 8. 최종 원칙

아키텍처는 "멋진 설계를 만드는 것"이 아니라
**요구사항을 충족하면서 구현 가능하고 운영 가능한 시스템을 설계하는 것**이다.