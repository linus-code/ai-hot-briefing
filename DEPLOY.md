# AI HOT 简报 · GitHub Pages 部署指南

> 当前仓库目录已含 `index.html`（2026-08-06 这一期精选简报）。
> 本机 GitHub 未连接 WorkBuddy，所以 `push` 步骤需你手动执行（或先在 WorkBuddy 连上 GitHub 后让我代劳）。

## 前置条件
- 一个 GitHub 账号
- 本地已装 git（macOS 自带，终端 `git --version` 验证）
- 推荐用 **SSH 方式**（`git@github.com:...`），需本地有 `~/.ssh/id_ed25519` 且公钥已加到 GitHub；否则用 HTTPS + Personal Access Token。

---

## 方式一：用户页（推荐，URL 最干净）

仓库名**必须**是 `<你的用户名>.github.io`，内容放 `main` 分支根目录。
最终访问地址：`https://<你的用户名>.github.io`

```bash
# 1) 去 GitHub 新建空仓库，名为 <你的用户名>.github.io（不要勾 README / .gitignore）
# 2) 本地初始化并推送（在 ai-hot-ghpages 目录内）
cd /Users/melody/WorkBuddy/日常研究/ai-hot-ghpages
git init
git add index.html
git commit -m "AI HOT 简报 2026-08-06"
git branch -M main
git remote add origin git@github.com:<你的用户名>/<你的用户名>.github.io.git
git push -u origin main

# 3) 打开仓库 Settings → Pages → Source 选 "Deploy from a branch" / main / (root) → Save
# 4) 等 1~2 分钟，浏览器访问 https://<你的用户名>.github.io
```

---

## 方式二：项目页（任意仓库名）

```bash
cd /Users/melody/WorkBuddy/日常研究/ai-hot-ghpages
git init
git add index.html
git commit -m "AI HOT 简报 2026-08-06"
git branch -M main
git remote add origin git@github.com:<你的用户名>/<仓库名>.git
git push -u origin main
# Settings → Pages → Source: main / (root) → Save
# 访问地址：https://<你的用户名>.github.io/<仓库名>/
```

---

## 每天自动更新（进阶）

让 WorkBuddy 定时任务每天生成新的 `index.html` 覆盖此文件，然后一句提交推送即可：

```bash
cd /Users/melody/WorkBuddy/日常研究/ai-hot-ghpages
git add index.html
git commit -m "daily: $(date +%Y-%m-%d)"
git push
```

可把上面三行存成 `publish.sh`，由 WorkBuddy 自动化在「生成简报」之后调用（需本机 GitHub 已配好 SSH / credential helper，否则 push 会卡在鉴权）。

---

## 自定义域名（可选）

1. 仓库根放一个 `CNAME` 文件，内容写你的域名，如 `ai.yourdomain.com`
2. 仓库 Settings → Pages → Custom domain 填入并 Save
3. 域名 DNS 加一条 `CNAME` 记录指向 `<你的用户名>.github.io`
4. 勾选 Enforce HTTPS（证书自动签发，约需几分钟）

---

## 常见问题

- **404**：确认仓库 Settings → Pages 的 Source 分支/目录选对，且 `index.html` 确实在该分支根目录。
- **样式没生效 / 白屏**：GitHub Pages 不支持服务端处理，本简报是纯静态单文件、CSS 已内联，正常可直接显示；如用了相对路径资源才需额外处理（当前没有）。
- **想换默认分支名**：GitHub Pages 现支持任意分支，不强制 `main`，按需改上面命令即可。
