#!/bin/bash
# PostgreSQL 컨테이너 시작 확인 스크립트
# 사용법: ./scripts/db/password/start-postgres-if-needed.sh

set -e

PROJECT_DIR="${PROJECT_DIR:-/opt/adsp-quiz-backend}"
ENV_FILE="${ENV_FILE:-${PROJECT_DIR}/env/.env}"

if [ -f "${PROJECT_DIR}/scripts/db/start-postgres.sh" ]; then
    chmod +x "${PROJECT_DIR}/scripts/db/start-postgres.sh"
    "${PROJECT_DIR}/scripts/db/start-postgres.sh" || exit 1
else
    if ! docker-compose --env-file "$ENV_FILE" ps postgres 2>/dev/null | grep -q "Up"; then
        echo "⚠️  PostgreSQL 컨테이너가 실행 중이 아닙니다. 시작합니다..."
        docker-compose --env-file "$ENV_FILE" up -d postgres
        sleep 5
    fi
fi
