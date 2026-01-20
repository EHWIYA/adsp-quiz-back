#!/bin/bash
# SSH 설정 스크립트
# 사용법: ./scripts/deploy/ssh/setup-ssh.sh

set -e

mkdir -p ~/.ssh
chmod 700 ~/.ssh
ssh-keyscan -p ${SERVER_PORT:-22} -H ${SERVER_HOST} >> ~/.ssh/known_hosts || true
chmod 600 ~/.ssh/known_hosts
