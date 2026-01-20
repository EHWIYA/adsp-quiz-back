#!/bin/bash
# 헬스체크 스크립트
# 사용법: ./scripts/deploy/steps/health-check.sh

set -e

PROJECT_DIR="${PROJECT_DIR:-/opt/adsp-quiz-backend}"
ENV_FILE="${ENV_FILE:-${PROJECT_DIR}/env/.env}"

if [ -f "${PROJECT_DIR}/scripts/utils/health-check.sh" ]; then
    chmod +x "${PROJECT_DIR}/scripts/utils/health-check.sh"
    "${PROJECT_DIR}/scripts/utils/health-check.sh" "https://adsp-api.livbee.co.kr/health" 5 10 "$ENV_FILE" || exit 1
else
    echo "⚠️  헬스체크 스크립트를 찾을 수 없습니다. 건너뜁니다."
fi
