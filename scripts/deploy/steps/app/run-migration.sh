#!/bin/bash
# 마이그레이션 실행 스크립트
# 사용법: ./scripts/deploy/steps/run-migration.sh

set -e

PROJECT_DIR="${PROJECT_DIR:-/opt/adsp-quiz-backend}"
ENV_FILE="${ENV_FILE:-${PROJECT_DIR}/env/.env}"

if [ -f "${PROJECT_DIR}/scripts/db/start-postgres.sh" ]; then
    chmod +x "${PROJECT_DIR}/scripts/db/start-postgres.sh"
    "${PROJECT_DIR}/scripts/db/start-postgres.sh" || exit 1
fi

if [ -f "${PROJECT_DIR}/scripts/db/migration/run-migration.sh" ]; then
    chmod +x "${PROJECT_DIR}/scripts/db/migration/run-migration.sh"
    "${PROJECT_DIR}/scripts/db/migration/run-migration.sh" || exit 1
else
    echo "⚠️  마이그레이션 스크립트를 찾을 수 없습니다."
    exit 1
fi
