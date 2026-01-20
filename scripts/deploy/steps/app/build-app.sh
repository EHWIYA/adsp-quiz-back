#!/bin/bash
# 애플리케이션 빌드 스크립트
# 사용법: ./scripts/deploy/steps/build-app.sh

set -e

PROJECT_DIR="${PROJECT_DIR:-/opt/adsp-quiz-backend}"
ENV_FILE="${ENV_FILE:-${PROJECT_DIR}/env/.env}"

if [ -f "${PROJECT_DIR}/scripts/deploy/build-app.sh" ]; then
    chmod +x "${PROJECT_DIR}/scripts/deploy/build-app.sh"
    "${PROJECT_DIR}/scripts/deploy/build-app.sh" || exit 1
else
    echo "⚠️  빌드 스크립트를 찾을 수 없습니다."
    exit 1
fi
