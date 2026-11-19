#!/bin/bash
# 提交并推送 AI HOT 简报到 GitHub Pages 仓库（linus-code/ai-hot-briefing）
# 并把产物镜像同步到本机站点目录 /www/wwwroot/www.talentpulse.cn/ai-hot
set -u
cd "$(dirname "$0")"

PUB_DIR="/www/wwwroot/www.talentpulse.cn/ai-hot"   # 站点镜像目标目录
BRANCH="main"

if [ ! -d .git ]; then
  echo "ERROR: 未找到 git 仓库（请先 git clone https://github.com/linus-code/ai-hot-briefing.git 到本目录）"
  exit 1
fi

# ── 1) 暂存并判断有无新内容 ──────────────────────────────
git add -A
if git diff --cached --quiet; then
  echo "no changes to publish"
else
  git commit -m "daily: $(date +%Y-%m-%d)" || exit 1

  # ── 2) 推送（无凭证时明确跳过并回退本次提交，避免卡死/积压）──
  export GIT_TERMINAL_PROMPT=0    # 禁止交互式索要账号密码，直接失败
  TOKEN=""
  if command -v gh >/dev/null 2>&1; then
    TOKEN=$(gh auth token 2>/dev/null || true)
  fi
  if [ -z "$TOKEN" ] && [ -s "$HOME/.config/ai-hot/github_token" ]; then
    TOKEN=$(tr -d '\r\n "' < "$HOME/.config/ai-hot/github_token")
  fi

  PUSH_URL="origin"
  if [ -n "$TOKEN" ]; then
    PUSH_URL="https://x-access-token:${TOKEN}@github.com/linus-code/ai-hot-briefing.git"
  fi

  # 网络出口：直连 GitHub 国际链路不稳定（TLS 传输中途被断）。
  # 本机 127.0.0.1:7890 有 Clash 代理时自动经代理推送，否则回退直连。
  GIT_PROXY=()
  if (echo > /dev/tcp/127.0.0.1/7890) 2>/dev/null; then
    GIT_PROXY=(-c http.proxy=http://127.0.0.1:7890)
  fi
  # lowSpeed*：传输停滞（<1KB/s 持续 20s）时快速失败，timeout 90 兜底
  PUSH_ERR=$(timeout 90 git "${GIT_PROXY[@]}" -c http.lowSpeedLimit=1000 -c http.lowSpeedTime=20 push "$PUSH_URL" "HEAD:${BRANCH}" 2>&1); RC=$?
  if [ $RC -eq 0 ]; then
    echo "pushed."
  else
    git reset --soft "HEAD~1"   # 回退提交，保留改动，下次有凭证后再推
    if [ -z "$TOKEN" ]; then
      echo "push skipped: 未配置 GitHub 凭证（gh 未安装/未认证，且无 ~/.config/ai-hot/github_token），本次提交已暂存待推"
    else
      echo "push failed (rc=$RC): 凭证无效或网络异常，本次提交已暂存待推。错误摘要："
      echo "$PUSH_ERR" | tail -2
    fi
  fi
fi

# ── 3) 镜像同步到站点目录（目录可写才执行，否则跳过）────────
if [ -d "$PUB_DIR" ] && [ -w "$PUB_DIR" ]; then
  if rsync -a --delete --exclude='.git/' --exclude='DEPLOY.md' --exclude='push_err.log' ./ "$PUB_DIR"/; then
    echo "mirrored to $PUB_DIR"
  else
    echo "mirror failed: rsync 同步 $PUB_DIR 出错"
  fi
else
  echo "mirror skipped: $PUB_DIR 不可写（需授权，如：sudo setfacl -R -m u:$(id -un):rwx $PUB_DIR 或 sudo chown -R $(id -un) $PUB_DIR）"
fi
