#!/bin/bash
# DB 자격증명 추출 스크립트
# 사용법: ./scripts/db/password/extract-db-credentials.sh

set -e

PROJECT_DIR="${PROJECT_DIR:-/opt/adsp-quiz-backend}"
ENV_FILE="${ENV_FILE:-${PROJECT_DIR}/env/.env}"

if [ -f "${PROJECT_DIR}/scripts/db/connection/extract-db-info.sh" ]; then
    chmod +x "${PROJECT_DIR}/scripts/db/connection/extract-db-info.sh"
    eval $("${PROJECT_DIR}/scripts/db/connection/extract-db-info.sh")
    DB_USER_FROM_ENV="$DB_USER"
    DB_PASSWORD_FROM_ENV="$DB_PASSWORD"
else
    DB_USER_FROM_ENV=$(grep "^DB_USER=" "$ENV_FILE" | cut -d'=' -f2 | tr -d '"' | tr -d "'" || echo "")
    DB_PASSWORD_FROM_ENV=$(grep "^DB_PASSWORD=" "$ENV_FILE" | cut -d'=' -f2 | tr -d '"' | tr -d "'" || echo "")
    DB_NAME=$(grep "^DATABASE_URL=" "$ENV_FILE" | sed -n 's/.*\/\([^?]*\).*/\1/p' | head -1)
    DB_NAME="${DB_NAME:-adsp_quiz_db}"
    
    if [ -z "$DB_USER_FROM_ENV" ] || [ -z "$DB_PASSWORD_FROM_ENV" ]; then
        echo "❌ .env 파일에서 DB_USER 또는 DB_PASSWORD를 찾을 수 없습니다."
        exit 1
    fi
fi

export DB_USER_FROM_ENV DB_PASSWORD_FROM_ENV DB_NAME
