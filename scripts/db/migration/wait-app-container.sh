#!/bin/bash
# 애플리케이션 컨테이너 대기 스크립트
# 사용법: ./scripts/db/migration/wait-app-container.sh

set -e

PROJECT_DIR="${PROJECT_DIR:-/opt/adsp-quiz-backend}"
ENV_FILE="${ENV_FILE:-${PROJECT_DIR}/env/.env}"
MAX_WAIT=30
WAIT_COUNT=0

while [ $WAIT_COUNT -lt $MAX_WAIT ]; do
    CONTAINER_ID=$(docker-compose --env-file "$ENV_FILE" ps -q app 2>/dev/null || echo "")
    if [ -n "$CONTAINER_ID" ]; then
        CONTAINER_STATUS=$(docker inspect --format='{{.State.Status}}' "$CONTAINER_ID" 2>/dev/null || echo "")
        if [ "$CONTAINER_STATUS" = "running" ]; then
            RESTARTING=$(docker inspect --format='{{.State.Restarting}}' "$CONTAINER_ID" 2>/dev/null || echo "false")
            if [ "$RESTARTING" = "false" ]; then
                echo "✅ 컨테이너가 안정적으로 실행 중입니다"
                exit 0
            fi
        fi
    fi
    echo "컨테이너 대기 중... ($WAIT_COUNT/$MAX_WAIT)"
    sleep 2
    WAIT_COUNT=$((WAIT_COUNT + 2))
done

echo "❌ 컨테이너가 안정화되지 않았습니다"
docker-compose --env-file "$ENV_FILE" ps app
docker-compose --env-file "$ENV_FILE" logs --tail=50 app
exit 1
