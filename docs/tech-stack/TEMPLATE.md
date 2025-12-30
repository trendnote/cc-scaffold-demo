# Tech Stack: [Project Name]

---

## Meta
- PRD Reference: [PRD 파일명 또는 링크]
- Decision Date: [날짜]
- Decision Makers: [참여자들]
- Status: Draft | Approved | Deprecated
- Last Updated: [날짜]

---

## 1. Overview

<!--
한 문단으로 요약:
- 프로젝트 개요
- 핵심 기술 선택 (3-5개)
- 선택 이유 요약
-->

---

## 2. PRD Requirements Summary

<!--
PRD에서 기술 선택에 영향을 주는 요구사항 요약
-->

### 2.1 Functional Requirements
- [핵심 기능 요구사항 1-3개]

### 2.2 Non-Functional Requirements
- Performance: [성능 목표]
- Security: [보안 요구사항]
- Scalability: [확장성 목표]
- Availability: [가용성 목표]

### 2.3 Constraints
- [제약 사항 - 예: 예산, 인력, 시간, 레거시 시스템 등]

---

## 3. Technology Decisions

### 3.1 Backend

#### Programming Language
- **Selected**: [선택된 언어]
- **Version**: [버전]
- **Rationale**: [선택 이유]

#### Web Framework
- **Selected**: [선택된 프레임워크]
- **Version**: [버전]
- **Rationale**: [선택 이유]

#### API Style
- **Selected**: REST | GraphQL | gRPC | [기타]
- **Rationale**: [선택 이유]

---

### 3.2 Frontend

#### Framework
- **Selected**: [React | Vue | Svelte | Next.js | 기타]
- **Version**: [버전]
- **Rationale**: [선택 이유]

#### Language
- **Selected**: TypeScript | JavaScript
- **Rationale**: [선택 이유]

#### Styling
- **Selected**: [CSS-in-JS | Tailwind | SCSS | 기타]
- **Rationale**: [선택 이유]

#### State Management
- **Selected**: [Redux | Zustand | React Query | 기타]
- **Rationale**: [선택 이유]

---

### 3.3 Database

#### Primary Database
- **Type**: [RDBMS | NoSQL | NewSQL]
- **Selected**: [PostgreSQL | MySQL | MongoDB | 기타]
- **Version**: [버전]
- **Rationale**: [선택 이유]

#### Cache Layer
- **Selected**: [Redis | Memcached | 없음]
- **Rationale**: [선택 이유]

#### Special-Purpose Databases
<!--
Vector DB, Graph DB, Time-series DB 등 특수 목적 DB
-->
- **Type**: [Vector | Graph | Time-series | 기타]
- **Selected**: [구체적 제품]
- **Rationale**: [선택 이유]

---

### 3.4 Infrastructure

#### Cloud Provider
- **Selected**: AWS | GCP | Azure | 온프레미스 | Hybrid
- **Rationale**: [선택 이유]

#### Containerization
- **Selected**: Docker | Podman | 없음
- **Orchestration**: Kubernetes | Docker Compose | ECS | 없음
- **Rationale**: [선택 이유]

#### CI/CD
- **Selected**: [GitHub Actions | GitLab CI | Jenkins | 기타]
- **Rationale**: [선택 이유]

---

### 3.5 External Services

#### Authentication
- **Selected**: [자체 구현 | Auth0 | Clerk | AWS Cognito | 기타]
- **Rationale**: [선택 이유]

#### Monitoring & Logging
- **Monitoring**: [Prometheus | Datadog | New Relic | 기타]
- **Logging**: [ELK Stack | CloudWatch | 기타]
- **Rationale**: [선택 이유]

#### Third-party APIs
<!--
프로젝트별로 사용하는 외부 API (LLM, Payment 등)
-->
- **Service 1**: [서비스명]
  - Purpose: [사용 목적]
  - Rationale: [선택 이유]

---

## 4. Technology Comparison

<!--
주요 의사결정에서 비교했던 옵션들
최소 2-3개 옵션 비교
-->

### 4.1 [카테고리 - 예: Backend Language]

| Criteria | Option A: [이름] | Option B: [이름] | Option C: [이름] | Winner |
|----------|------------------|------------------|------------------|--------|
| 성능 | [평가] | [평가] | [평가] | |
| 생태계 | [평가] | [평가] | [평가] | |
| 학습 곡선 | [평가] | [평가] | [평가] | |
| 팀 경험 | [평가] | [평가] | [평가] | |
| 커뮤니티 | [평가] | [평가] | [평가] | |
| **총점** | X/5 | Y/5 | Z/5 | **Option A** |

**Decision**: Option A 선택
**Reason**: [상세 이유]

---

## 5. Development Tools

### 5.1 IDE & Editors
- [VS Code | IntelliJ | 기타]

### 5.2 Version Control
- [Git + GitHub | GitLab | Bitbucket]

### 5.3 Project Management
- [Jira | Linear | GitHub Projects | 기타]

### 5.4 Communication
- [Slack | Teams | Discord | 기타]

---

## 6. Dependencies Summary

### 6.1 Backend Dependencies
```
[주요 라이브러리 3-5개]
- library-1: version
- library-2: version
```

### 6.2 Frontend Dependencies
```
[주요 라이브러리 3-5개]
- library-1: version
- library-2: version
```

---

## 7. Risks & Mitigation

### 7.1 Technology Risks

**Risk 1**: [위험 - 예: 선택한 기술의 성숙도 부족]
- **Impact**: [영향]
- **Probability**: Low | Medium | High
- **Mitigation**: [완화 방안]

**Risk 2**: [위험 - 예: 팀의 기술 경험 부족]
- **Impact**: [영향]
- **Probability**: Low | Medium | High
- **Mitigation**: [완화 방안]

### 7.2 Vendor Lock-in

- **Cloud Provider**: [정도 - Low | Medium | High]
  - Mitigation: [방안]
  
- **Third-party Services**: [정도]
  - Mitigation: [방안]

---

## 8. Migration Path

<!--
기존 시스템이 있는 경우
-->

### 8.1 Current State
- [현재 기술 스택]

### 8.2 Migration Strategy
- [마이그레이션 전략]
- [단계별 계획]

---

## 9. Team Readiness

### 9.1 Current Expertise
- Backend: [팀 경험 수준 - 1-5]
- Frontend: [팀 경험 수준]
- Infrastructure: [팀 경험 수준]

### 9.2 Learning Plan
- [학습 필요 기술]
- [교육 계획]
- [예상 학습 시간]


---

## 10. Decision Log

<!--
주요 의사결정 기록
-->

| Date | Decision | Rationale | Decision Maker |
|------|----------|-----------|----------------|
| [날짜] | [결정 사항] | [이유] | [담당자] |

---

## 11. Approval

- [ ] Technical Lead
- [ ] Backend Team
- [ ] Frontend Team
- [ ] DevOps Team
- [ ] Security Team

**Approved by**: [이름들]
**Date**: [날짜]

---

## 12. References

- PRD: [링크]
- Technology Documentation: [링크들]
- Comparison Articles: [링크들]
- Team Discussion: [링크]

---

## 13. Change Log

| Date | Author | Change | Reason |
|------|--------|--------|--------|
| [날짜] | [작성자] | Initial version | First draft |