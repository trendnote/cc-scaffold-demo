/**
 * Test Data Fixtures
 *
 * Task 4.3a: E2E Testing
 */

/**
 * 테스트용 검색 쿼리
 */
export const testQueries = [
  '연차 사용 방법',
  '휴가 신청 절차',
  '급여 지급일',
  '출퇴근 시간',
  '회의실 예약 방법',
];

/**
 * 테스트용 사용자 정보
 */
export const testUsers = {
  user: {
    email: 'user@example.com',
    password: 'password123',
    name: '일반 사용자',
    accessLevel: 1,
  },
  teamlead: {
    email: 'teamlead@example.com',
    password: 'password123',
    name: '팀장',
    accessLevel: 2,
  },
  admin: {
    email: 'admin@example.com',
    password: 'password123',
    name: '관리자',
    accessLevel: 3,
  },
};

/**
 * 테스트용 피드백 데이터
 */
export const testFeedback = {
  positive: {
    rating: 5,
    comment: '매우 유용한 답변입니다.',
  },
  negative: {
    rating: 1,
    comment: '답변이 부정확합니다.',
  },
  neutral: {
    rating: 3,
    comment: '보통입니다.',
  },
};
