#!/bin/bash
# 배포 실행 스크립트
# 사용법: ./scripts/deploy/steps/run-deploy.sh

set -e

PROJECT_DIR="${PROJECT_DIR:-/opt/adsp-quiz-backend}"
ENV_FILE="${ENV_FILE:-${PROJECT_DIR}/env/.env}"

if [ -f "${PROJECT_DIR}/scripts/deploy/deploy.sh" ]; then
    chmod +x "${PROJECT_DIR}/scripts/deploy/deploy.sh"
    "${PROJECT_DIR}/scripts/deploy/deploy.sh" || exit 1
else
    echo "⚠️  배포 스크립트를 찾을 수 없습니다. 기본 배포 프로세스를 실행합니다."
    docker-compose --env-file "$ENV_FILE" down || true
    docker-compose --env-file "$ENV_FILE" build
    docker-compose --env-file "$ENV_FILE" up -d
    sleep 10
    docker-compose --env-file "$ENV_FILE" exec -T app alembic upgrade head || exit 1
    echo "✅ 기본 배포 프로세스 완료"
fi
