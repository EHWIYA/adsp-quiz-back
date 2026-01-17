#!/bin/bash
# 환경변수 파일 설정 스크립트
# 사용법: ./scripts/setup-env.sh

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_DIR="/opt/adsp-quiz-backend"
TEMPLATE_FILE="${PROJECT_DIR}/env/.env.template"
ENV_FILE="${PROJECT_DIR}/env/.env"

echo -e "${GREEN}=== ADsP Quiz Backend 환경변수 설정 ===${NC}"

# 1. 템플릿 파일 확인
if [ ! -f "$TEMPLATE_FILE" ]; then
    echo -e "${RED}❌ 템플릿 파일이 없습니다: $TEMPLATE_FILE${NC}"
    exit 1
fi

# 2. 환경변수 파일 생성
if [ -f "$ENV_FILE" ]; then
    echo -e "${YELLOW}⚠️  환경변수 파일이 이미 존재합니다: $ENV_FILE${NC}"
    read -p "덮어쓰시겠습니까? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}취소되었습니다.${NC}"
        exit 0
    fi
fi

# 템플릿 복사
cp "$TEMPLATE_FILE" "$ENV_FILE"
chmod 600 "$ENV_FILE"
echo -e "${GREEN}✅ 환경변수 파일 생성 완료: $ENV_FILE${NC}"

# 3. 데이터베이스 정보 입력 (자동 입력)
echo -e "\n${BLUE}[1/4] 데이터베이스 정보 설정${NC}"
sed -i "s|DATABASE_URL=.*|DATABASE_URL=postgresql+asyncpg://adsp_quiz_user:oXRulAw4AwNBP1ERkg3lSOlBg@localhost:5432/adsp_quiz_db|g" "$ENV_FILE"
sed -i "s|DB_USER=.*|DB_USER=adsp_quiz_user|g" "$ENV_FILE"
sed -i "s|DB_PASSWORD=.*|DB_PASSWORD=oXRulAw4AwNBP1ERkg3lSOlBg|g" "$ENV_FILE"
echo -e "${GREEN}✅ 데이터베이스 정보 설정 완료${NC}"

# 4. SECRET_KEY 생성
echo -e "\n${BLUE}[2/4] SECRET_KEY 생성${NC}"
if command -v openssl &> /dev/null; then
    SECRET_KEY=$(openssl rand -hex 32)
elif command -v python3 &> /dev/null; then
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
else
    echo -e "${RED}❌ openssl 또는 python3가 필요합니다.${NC}"
    exit 1
fi

sed -i "s|SECRET_KEY=.*|SECRET_KEY=$SECRET_KEY|g" "$ENV_FILE"
echo -e "${GREEN}✅ SECRET_KEY 생성 완료${NC}"

# 5. 환경 설정
echo -e "\n${BLUE}[3/4] 환경 설정${NC}"
sed -i "s|ENVIRONMENT=.*|ENVIRONMENT=production|g" "$ENV_FILE"
sed -i "s|PORT=.*|PORT=8001|g" "$ENV_FILE"
echo -e "${GREEN}✅ 환경 설정 완료${NC}"

# 6. 필수 환경변수 입력 요청
echo -e "\n${BLUE}[4/4] 필수 환경변수 입력${NC}"
echo -e "${YELLOW}다음 환경변수들을 설정해야 합니다:${NC}"
echo -e "  - GEMINI_API_KEY: Gemini API 키"
echo -e "  - ALLOWED_ORIGINS: 프론트엔드 도메인 (콤마로 구분)"

read -p "지금 설정하시겠습니까? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # GEMINI_API_KEY 입력
    read -p "GEMINI_API_KEY: " GEMINI_KEY
    if [ -n "$GEMINI_KEY" ]; then
        sed -i "s|GEMINI_API_KEY=.*|GEMINI_API_KEY=$GEMINI_KEY|g" "$ENV_FILE"
        echo -e "${GREEN}✅ GEMINI_API_KEY 설정 완료${NC}"
    fi
    
    # ALLOWED_ORIGINS 입력
    read -p "ALLOWED_ORIGINS (예: http://localhost:3000,https://your-domain.com): " ALLOWED_ORIGINS
    if [ -n "$ALLOWED_ORIGINS" ]; then
        sed -i "s|ALLOWED_ORIGINS=.*|ALLOWED_ORIGINS=$ALLOWED_ORIGINS|g" "$ENV_FILE"
        echo -e "${GREEN}✅ ALLOWED_ORIGINS 설정 완료${NC}"
    fi
else
    echo -e "${YELLOW}나중에 다음 명령어로 수정하세요:${NC}"
    echo "  nano $ENV_FILE"
fi

echo -e "\n${GREEN}=== 환경변수 설정 완료 ===${NC}"
echo -e "${GREEN}환경변수 파일: $ENV_FILE${NC}"
echo -e "${YELLOW}⚠️  파일 권한이 600으로 설정되어 있습니다.${NC}"
