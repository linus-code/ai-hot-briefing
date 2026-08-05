#!/bin/bash
# 提交并推送 ai-hot-ghpages 到 GitHub Pages 仓库（本机 gh 已认证）
set -e
cd "$(dirname "$0")"
git add -A
if git diff --cached --quiet; then
  echo "no changes to publish"
  exit 0
fi
git commit -m "daily: $(date +%Y-%m-%d)"
git push
echo "pushed."
