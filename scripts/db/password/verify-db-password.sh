#!/bin/bash
# 데이터베이스 비밀번호 검증 스크립트
# 사용법: ./scripts/db/password/verify-db-password.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PROJECT_DIR="${PROJECT_DIR:-/opt/adsp-quiz-backend}"
ENV_FILE="${ENV_FILE:-${PROJECT_DIR}/env/.env}"

echo -e "${YELLOW}=== 데이터베이스 비밀번호 검증 ===${NC}"

cd "$PROJECT_DIR" || { echo -e "${RED}❌ 프로젝트 디렉토리로 이동 실패: $PROJECT_DIR${NC}"; exit 1; }

if [ -f "${PROJECT_DIR}/scripts/db/password/start-postgres-if-needed.sh" ]; then
    chmod +x "${PROJECT_DIR}/scripts/db/password/start-postgres-if-needed.sh"
    "${PROJECT_DIR}/scripts/db/password/start-postgres-if-needed.sh" || exit 1
fi

if [ -f "${PROJECT_DIR}/scripts/db/password/extract-db-credentials.sh" ]; then
    chmod +x "${PROJECT_DIR}/scripts/db/password/extract-db-credentials.sh"
    source "${PROJECT_DIR}/scripts/db/password/extract-db-credentials.sh"
else
    echo -e "${RED}❌ DB 자격증명 추출 스크립트를 찾을 수 없습니다.${NC}"
    exit 1
fi

echo "DB 연결: user=$DB_USER_FROM_ENV, db=$DB_NAME, pw=***"

if [ -f "${PROJECT_DIR}/scripts/db/password/check-password-match.sh" ]; then
    chmod +x "${PROJECT_DIR}/scripts/db/password/check-password-match.sh"
    "${PROJECT_DIR}/scripts/db/password/check-password-match.sh" "$DB_PASSWORD_FROM_ENV" || exit 1
fi

if [ -f "${PROJECT_DIR}/scripts/db/connection/test-db-connection.sh" ]; then
    chmod +x "${PROJECT_DIR}/scripts/db/connection/test-db-connection.sh"
    if "${PROJECT_DIR}/scripts/db/connection/test-db-connection.sh" "$DB_USER_FROM_ENV" "$DB_NAME" 3 2; then
        echo -e "${GREEN}✅ 데이터베이스 연결 성공 (비밀번호 인증 통과)${NC}"
        exit 0
    else
        echo -e "${RED}❌ 데이터베이스 연결 실패 (비밀번호 인증 실패)${NC}"
        exit 1
    fi
else
    echo -e "${RED}❌ 연결 테스트 스크립트를 찾을 수 없습니다.${NC}"
    exit 1
fi
