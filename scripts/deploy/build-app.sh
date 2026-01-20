#!/bin/bash
# 애플리케이션 빌드 및 시작 스크립트
# 사용법: ./scripts/build-app.sh

set -e

PROJECT_DIR="${PROJECT_DIR:-/opt/adsp-quiz-backend}"
ENV_FILE="${ENV_FILE:-${PROJECT_DIR}/env/.env}"

cd "$PROJECT_DIR" || exit 1

echo "기존 서비스 중지 및 컨테이너 제거 중..."
# docker-compose down으로 먼저 정리
docker-compose --env-file "$ENV_FILE" down || true

# 모든 관련 컨테이너 완전 제거 (ContainerConfig 오류 방지)
if [ -f "${PROJECT_DIR}/scripts/utils/docker/remove-containers.sh" ]; then
    chmod +x "${PROJECT_DIR}/scripts/utils/docker/remove-containers.sh"
    "${PROJECT_DIR}/scripts/utils/docker/remove-containers.sh" "adsp-quiz-backend"
    "${PROJECT_DIR}/scripts/utils/docker/remove-containers.sh" "adsp-quiz-postgres"
fi

# 네트워크 정리 (선택적)
docker network prune -f 2>/dev/null || true

echo "Docker 이미지 빌드 중..."
# 캐시 사용하여 빌드 (첫 빌드가 아니면 캐시 활용)
docker-compose --env-file "$ENV_FILE" build

echo "애플리케이션 컨테이너 시작 중..."
docker-compose --env-file "$ENV_FILE" up -d

echo "컨테이너 시작 대기 중..."
sleep 3

if [ -f "${PROJECT_DIR}/scripts/deploy/docker/wait-container.sh" ]; then
    chmod +x "${PROJECT_DIR}/scripts/deploy/docker/wait-container.sh"
    MAX_WAIT=30 "${PROJECT_DIR}/scripts/deploy/docker/wait-container.sh" || exit 1
else
    echo "⚠️  컨테이너 대기 스크립트를 찾을 수 없습니다."
    exit 1
fi
