#!/bin/bash
# 컨테이너 대기 스크립트
# 사용법: ./scripts/deploy/docker/wait-container.sh

set -e

PROJECT_DIR="${PROJECT_DIR:-/opt/adsp-quiz-backend}"
ENV_FILE="${ENV_FILE:-${PROJECT_DIR}/env/.env}"
MAX_WAIT="${MAX_WAIT:-30}"

WAIT_COUNT=0
CONTAINER_ID=""

while [ -z "$CONTAINER_ID" ] && [ $WAIT_COUNT -lt 5 ]; do
    CONTAINER_ID=$(docker-compose --env-file "$ENV_FILE" ps -q app 2>/dev/null || echo "")
    if [ -z "$CONTAINER_ID" ]; then
        sleep 1
        WAIT_COUNT=$((WAIT_COUNT + 1))
    fi
done

if [ -z "$CONTAINER_ID" ]; then
    echo "❌ 컨테이너 ID를 찾을 수 없습니다"
    docker-compose --env-file "$ENV_FILE" ps
    exit 1
fi

WAIT_COUNT=0
while [ $WAIT_COUNT -lt $MAX_WAIT ]; do
    CONTAINER_STATUS=$(docker inspect --format='{{.State.Status}}' "$CONTAINER_ID" 2>/dev/null || echo "")
    IS_RESTARTING=$(docker inspect --format='{{.State.Restarting}}' "$CONTAINER_ID" 2>/dev/null || echo "false")
    
    if [ "$CONTAINER_STATUS" = "running" ] && [ "$IS_RESTARTING" = "false" ]; then
        HEALTH_STATUS=$(docker inspect --format='{{.State.Health.Status}}' "$CONTAINER_ID" 2>/dev/null || echo "")
        if [ -z "$HEALTH_STATUS" ] || [ "$HEALTH_STATUS" = "healthy" ] || [ "$HEALTH_STATUS" = "" ]; then
            echo "✅ 컨테이너 실행 중"
            exit 0
        fi
    fi
    sleep 1
    WAIT_COUNT=$((WAIT_COUNT + 1))
done

echo "❌ 컨테이너 시작 실패 (타임아웃)"
docker-compose --env-file "$ENV_FILE" ps app
docker-compose --env-file "$ENV_FILE" logs --tail=50 app
exit 1
