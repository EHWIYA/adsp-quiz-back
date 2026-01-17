#!/bin/bash
# 데이터베이스 비밀번호 검증 스크립트
# 사용법: ./scripts/verify-db-password.sh

set -e  # 에러 발생 시 스크립트 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 프로젝트 디렉토리
PROJECT_DIR="${PROJECT_DIR:-/opt/adsp-quiz-backend}"
ENV_FILE="${ENV_FILE:-${PROJECT_DIR}/env/.env}"

echo -e "${YELLOW}=== 데이터베이스 비밀번호 검증 ===${NC}"

# 프로젝트 디렉토리로 이동
cd "$PROJECT_DIR" || {
    echo -e "${RED}❌ 프로젝트 디렉토리로 이동 실패: $PROJECT_DIR${NC}"
    exit 1
}

# PostgreSQL 컨테이너가 실행 중인지 확인
if ! docker-compose --env-file "$ENV_FILE" ps postgres 2>/dev/null | grep -q "Up"; then
    echo -e "${YELLOW}⚠️  PostgreSQL 컨테이너가 실행 중이 아닙니다. 시작합니다...${NC}"
    docker-compose --env-file "$ENV_FILE" up -d postgres
    echo "PostgreSQL 컨테이너 시작 대기 중..."
    sleep 5
fi

# .env 파일에서 데이터베이스 정보 추출
DB_USER_FROM_ENV=$(grep "^DB_USER=" "$ENV_FILE" | cut -d'=' -f2 | tr -d '"' | tr -d "'" || echo "")
DB_PASSWORD_FROM_ENV=$(grep "^DB_PASSWORD=" "$ENV_FILE" | cut -d'=' -f2 | tr -d '"' | tr -d "'" || echo "")
DB_NAME=$(grep "^DATABASE_URL=" "$ENV_FILE" | sed -n 's/.*\/\([^?]*\).*/\1/p' | head -1)
if [ -z "$DB_NAME" ]; then
    DB_NAME="adsp_quiz_db"
fi

if [ -z "$DB_USER_FROM_ENV" ] || [ -z "$DB_PASSWORD_FROM_ENV" ]; then
    echo -e "${RED}❌ .env 파일에서 DB_USER 또는 DB_PASSWORD를 찾을 수 없습니다.${NC}"
    echo "환경변수 파일 내용 확인:"
    grep -E "(DB_USER|DB_PASSWORD|DATABASE_URL)" "$ENV_FILE" | sed 's/\(PASSWORD=\).*/\1***/g' || echo "관련 환경변수가 없습니다."
    exit 1
fi

echo "데이터베이스 연결 정보:"
echo "  - 사용자: $DB_USER_FROM_ENV"
echo "  - 데이터베이스: $DB_NAME"
echo "  - 비밀번호: *** (마스킹됨)"

# PostgreSQL 컨테이너의 실제 비밀번호 확인
POSTGRES_PASSWORD_FROM_CONTAINER=$(docker-compose --env-file "$ENV_FILE" exec -T postgres env 2>/dev/null | grep "^POSTGRES_PASSWORD=" | cut -d'=' -f2 | tr -d '"' | tr -d "'" || echo "")

if [ -n "$POSTGRES_PASSWORD_FROM_CONTAINER" ]; then
    echo "  - PostgreSQL 컨테이너 비밀번호: *** (확인됨)"
    
    # 비밀번호 일치 확인
    if [ "$DB_PASSWORD_FROM_ENV" != "$POSTGRES_PASSWORD_FROM_CONTAINER" ]; then
        echo -e "${RED}❌ 비밀번호 불일치 감지!${NC}"
        echo "  - .env 파일의 DB_PASSWORD와 PostgreSQL 컨테이너의 POSTGRES_PASSWORD가 일치하지 않습니다."
        echo ""
        echo "🔧 조치 방법:"
        echo "  1. 서버의 PostgreSQL 컨테이너 비밀번호 확인:"
        echo "     docker exec adsp-quiz-postgres env | grep POSTGRES_PASSWORD"
        echo ""
        echo "  2. GitHub Secrets의 DB_PASSWORD를 서버 비밀번호와 일치하도록 업데이트"
        echo "     또는 서버의 .env 파일을 GitHub Secrets와 일치하도록 수정"
        echo ""
        echo "  3. PostgreSQL 컨테이너 재생성 (데이터 백업 필수):"
        echo "     cd /opt/adsp-quiz-backend"
        echo "     docker-compose stop postgres"
        echo "     docker-compose rm -f postgres"
        echo "     docker-compose up -d postgres"
        echo ""
        exit 1
    else
        echo -e "${GREEN}✅ 비밀번호 일치 확인됨${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  PostgreSQL 컨테이너에서 비밀번호를 확인할 수 없습니다. 연결 테스트로 검증합니다.${NC}"
fi

# PostgreSQL 연결 테스트 (psql 사용)
echo "PostgreSQL 연결 테스트 중..."
MAX_CONNECTION_RETRIES=3
CONNECTION_RETRY_DELAY=2

for i in $(seq 1 $MAX_CONNECTION_RETRIES); do
    if docker-compose --env-file "$ENV_FILE" exec -T postgres psql -U "$DB_USER_FROM_ENV" -d "$DB_NAME" -c "SELECT 1;" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 데이터베이스 연결 성공 (비밀번호 인증 통과)${NC}"
        exit 0
    else
        if [ $i -eq $MAX_CONNECTION_RETRIES ]; then
            echo -e "${RED}❌ 데이터베이스 연결 실패 (비밀번호 인증 실패)${NC}"
            echo ""
            echo "🔍 상세 진단:"
            echo "  1. PostgreSQL 컨테이너 상태:"
            docker-compose --env-file "$ENV_FILE" ps postgres || echo "컨테이너 상태 확인 실패"
            echo ""
            echo "  2. .env 파일의 데이터베이스 설정:"
            grep -E "(DATABASE_URL|DB_USER|DB_PASSWORD)" "$ENV_FILE" | sed 's/\(PASSWORD=\).*/\1***/g' || echo "환경변수 확인 실패"
            echo ""
            echo "  3. PostgreSQL 컨테이너 환경변수:"
            docker-compose --env-file "$ENV_FILE" exec -T postgres env 2>/dev/null | grep -E "(POSTGRES_USER|POSTGRES_PASSWORD|POSTGRES_DB)" | sed 's/\(PASSWORD=\).*/\1***/g' || echo "컨테이너 환경변수 확인 실패"
            echo ""
            echo "🔧 조치 방법:"
            echo "  - GitHub Secrets의 DB_PASSWORD와 서버 PostgreSQL 컨테이너의 비밀번호가 일치하는지 확인"
            echo "  - 서버의 .env 파일의 DB_PASSWORD와 DATABASE_URL 내 비밀번호가 일치하는지 확인"
            echo "  - PostgreSQL 컨테이너 재생성 또는 비밀번호 동기화 필요"
            echo ""
            exit 1
        else
            echo -e "${YELLOW}⚠️  연결 실패 (시도 $i/$MAX_CONNECTION_RETRIES), 재시도 중...${NC}"
            sleep $CONNECTION_RETRY_DELAY
        fi
    fi
done
