# -*- coding: utf-8 -*-
"""
AI HOT 每日简报生成器
- 拉取 aihot.virxact.com 最近 24 小时精选
- 生成 archive/<YYYY-MM-DD>.html 当日简报
- 更新 archive/manifest.json（所有日期倒序索引）
- 重新生成 index.html 目录页（内联 MANIFEST，默认展示最新一期，支持历史切换）
"""
import json, html, datetime, os, subprocess, sys

BASE = os.path.dirname(os.path.abspath(__file__))
ARCHIVE = os.path.join(BASE, 'archive')
MANIFEST = os.path.join(ARCHIVE, 'manifest.json')
SEEN = os.path.join(ARCHIVE, 'seen.json')
INDEX = os.path.join(BASE, 'index.html')

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
API = "https://aihot.virxact.com/api/public/items?mode=selected&since={since}&take=50"

CAT_CONFIG = [
    ('ai-models',   '模型发布 / 更新', '#6366f1'),
    ('ai-products', '产品发布 / 更新', '#0ea5e9'),
    ('industry',    '行业动态',       '#f59e0b'),
    ('paper',       '论文研究',       '#10b981'),
    ('tip',         '技巧与 观点',    '#ec4899'),
]

def bj(dtstr):
    if not dtstr:
        return None
    dt = datetime.datetime.fromisoformat(dtstr.replace('Z', '+00:00'))
    return dt.astimezone(datetime.timezone(datetime.timedelta(hours=8)))

def human(dt):
    if dt is None:
        return ''
    now = datetime.datetime.now(datetime.timezone.utc)
    s = (now - dt.astimezone(datetime.timezone.utc)).total_seconds()
    if s < 60:
        return '刚刚'
    if s < 3600:
        return f'{int(s//60)} 分钟前'
    if s < 86400:
        return f'{int(s//3600)} 小时前'
    if s < 172800:
        return f'昨天 {dt.strftime("%H:%M")}'
    return dt.strftime('%m/%d %H:%M')

def pull(since_iso):
    url = API.format(since=since_iso)
    out = subprocess.run(['curl', '-s', '-H', f'User-Agent: {UA}', url],
                         capture_output=True, text=True, timeout=60).stdout
    return json.loads(out)

def gen_report(items, date_str, win_str=''):
    groups = {k: [] for k, _, _ in CAT_CONFIG}
    for it in items:
        cat = it.get('category') or 'other'
        if cat in groups:
            groups[cat].append(it)
    total = len(items)
    gen_time = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime('%Y-%m-%d %H:%M')
    counter = 0
    sections = ''
    for key, label, color in CAT_CONFIG:
        lst = groups.get(key, [])
        if not lst:
            continue
        cards = ''
        for it in lst:
            counter += 1
            title = html.escape(it.get('title') or it.get('title_en') or '(无标题)')
            url = html.escape(it.get('url') or '#')
            source = html.escape(it.get('source') or '未知来源')
            summary = html.escape(it.get('summary') or '')
            dt = bj(it.get('publishedAt'))
            rel = human(dt)
            abt = dt.strftime('%Y-%m-%d %H:%M') if dt else ''
            cards += f'''
        <article class="card">
          <div class="num">{counter}</div>
          <div class="card-body">
            <a class="title" href="{url}" target="_blank" rel="noopener noreferrer">{title}</a>
            <div class="meta"><span class="source">{source}</span><span class="dot">·</span><span class="time" title="{abt}">{rel}</span></div>
            <p class="summary">{summary}</p>
          </div>
        </article>'''
        sections += f'''
    <section class="sec">
      <div class="sec-head" style="--c:{color}">
        <span class="badge" style="background:{color}"></span>
        <h2>{label}</h2>
        <span class="sec-count">{len(lst)}</span>
      </div>
      <div class="cards">{cards}</div>
    </section>'''
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI HOT 速递 · {date_str}</title>
<style>
  :root {{
    --bg:#ffffff; --bg2:#f8fafc; --card:#ffffff; --border:#e7e7ea;
    --text:#18181b; --muted:#52525b; --faint:#a1a1aa; --accent:#6366f1;
    --shadow:0 1px 3px rgba(0,0,0,.06),0 1px 2px rgba(0,0,0,.04);
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --bg:#0c0c0f; --bg2:#141418; --card:#16161a; --border:#26262c;
      --text:#f4f4f5; --muted:#a1a1aa; --faint:#71717a; --accent:#818cf8;
      --shadow:0 1px 3px rgba(0,0,0,.4);
    }}
  }}
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{ font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"PingFang SC","Microsoft YaHei",sans-serif;
    background:var(--bg); color:var(--text); line-height:1.6; -webkit-font-smoothing:antialiased; padding:32px 16px 64px; }}
  .wrap {{ max-width:860px; margin:0 auto; }}
  header {{ background:linear-gradient(135deg,var(--accent),#8b5cf6); color:#fff; border-radius:16px;
    padding:28px 28px 24px; margin-bottom:28px; box-shadow:var(--shadow); }}
  header h1 {{ font-size:26px; font-weight:800; letter-spacing:.5px; }}
  header .sub {{ margin-top:8px; font-size:14px; opacity:.92; }}
  header .win {{ margin-top:10px; font-size:13px; opacity:.85; font-family:"SF Mono",ui-monospace,monospace; }}
  .sec {{ margin-bottom:30px; }}
  .sec-head {{ display:flex; align-items:center; gap:10px; margin-bottom:14px; padding-bottom:8px; border-bottom:2px solid var(--border); }}
  .badge {{ width:10px; height:22px; border-radius:4px; display:inline-block; }}
  .sec-head h2 {{ font-size:18px; font-weight:700; flex:1; }}
  .sec-count {{ font-size:13px; color:var(--faint); font-family:"SF Mono",ui-monospace,monospace;
    background:var(--bg2); padding:2px 10px; border-radius:99px; border:1px solid var(--border); }}
  .cards {{ display:flex; flex-direction:column; gap:12px; }}
  .card {{ display:flex; gap:14px; background:var(--card); border:1px solid var(--border); border-radius:12px;
    padding:16px 18px; box-shadow:var(--shadow); transition:transform .15s ease,border-color .15s ease; }}
  .card:hover {{ transform:translateY(-2px); border-color:var(--accent); }}
  .num {{ flex:none; width:30px; height:30px; border-radius:8px; background:var(--bg2); border:1px solid var(--border);
    color:var(--accent); font-weight:700; font-size:14px; display:flex; align-items:center; justify-content:center;
    font-family:"SF Mono",ui-monospace,monospace; }}
  .card-body {{ flex:1; min-width:0; }}
  .title {{ font-size:16px; font-weight:650; color:var(--text); text-decoration:none; line-height:1.45; }}
  .title:hover {{ color:var(--accent); text-decoration:underline; }}
  .meta {{ margin-top:6px; font-size:12.5px; color:var(--muted); display:flex; align-items:center; gap:7px; flex-wrap:wrap; }}
  .source {{ font-weight:600; }}
  .dot {{ color:var(--faint); }}
  .time {{ color:var(--faint); font-family:"SF Mono",ui-monospace,monospace; }}
  .summary {{ margin-top:8px; font-size:14px; color:var(--muted); }}
  footer {{ margin-top:40px; text-align:center; font-size:12.5px; color:var(--faint); }}
  footer a {{ color:var(--accent); text-decoration:none; }}
  footer a:hover {{ text-decoration:underline; }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>🚀 AI HOT 速递</h1>
    <div class="sub">{date_str} · {win_str} · 共 {total} 条 · 按发布时间倒序</div>
    <div class="win">生成于 {gen_time}</div>
  </header>
  {sections}
  <footer>数据来源 <a href="https://aihot.virxact.com" target="_blank" rel="noopener noreferrer">aihot.virxact.com</a></footer>
</div>
</body>
</html>'''

def gen_index(manifest):
    data = json.dumps(manifest, ensure_ascii=False)
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI HOT 速递 · 归档</title>
<style>
  :root {{
    --bg:#ffffff; --bg2:#f8fafc; --card:#ffffff; --border:#e7e7ea;
    --text:#18181b; --muted:#52525b; --faint:#a1a1aa; --accent:#6366f1;
    --shadow:0 1px 3px rgba(0,0,0,.06),0 1px 2px rgba(0,0,0,.04);
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --bg:#0c0c0f; --bg2:#141418; --card:#16161a; --border:#26262c;
      --text:#f4f4f5; --muted:#a1a1aa; --faint:#71717a; --accent:#818cf8;
      --shadow:0 1px 3px rgba(0,0,0,.4);
    }}
  }}
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{ font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"PingFang SC","Microsoft YaHei",sans-serif;
    background:var(--bg); color:var(--text); line-height:1.6; -webkit-font-smoothing:antialiased; padding:24px 16px; }}
  .wrap {{ max-width:1200px; margin:0 auto; }}
  header {{ background:linear-gradient(135deg,var(--accent),#8b5cf6); color:#fff; border-radius:16px;
    padding:22px 26px; margin-bottom:20px; box-shadow:var(--shadow); }}
  header h1 {{ font-size:24px; font-weight:800; }}
  header .sub {{ margin-top:6px; font-size:13.5px; opacity:.92; }}
  main {{ display:flex; gap:18px; align-items:flex-start; }}
  .viewer-wrap {{ flex:1; min-width:0; }}
  iframe {{ width:100%; height:82vh; border:1px solid var(--border); border-radius:12px; background:var(--card);
    box-shadow:var(--shadow); }}
  aside {{ width:280px; flex:none; background:var(--card); border:1px solid var(--border); border-radius:12px;
    box-shadow:var(--shadow); padding:14px; position:sticky; top:24px; max-height:82vh; overflow:auto; }}
  .aside-head {{ font-size:13px; font-weight:700; color:var(--faint); text-transform:uppercase;
    letter-spacing:.5px; margin-bottom:10px; }}
  ul {{ list-style:none; display:flex; flex-direction:column; gap:4px; }}
  li a {{ display:block; padding:9px 12px; border-radius:8px; text-decoration:none; color:var(--text);
    font-size:14px; border:1px solid transparent; transition:all .12s ease; }}
  li a:hover {{ background:var(--bg2); }}
  li a.active {{ background:var(--accent); color:#fff; font-weight:600; }}
  li a .c {{ float:right; color:var(--faint); font-family:"SF Mono",ui-monospace,monospace; font-size:12px; }}
  li a.active .c {{ color:rgba(255,255,255,.85); }}
  li a .t {{ font-size:11px; color:var(--accent); margin-left:6px; }}
  li a.active .t {{ color:#fff; }}
  @media (max-width:820px) {{
    main {{ flex-direction:column; }}
    aside {{ width:100%; position:static; max-height:none; }}
    iframe {{ height:70vh; }}
  }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>🚀 AI HOT 速递 · 归档</h1>
    <div class="sub">每日 AI 资讯精选 · 默认展示最新一期，点击右侧日期查看历史</div>
  </header>
  <main>
    <div class="viewer-wrap"><iframe id="viewer" src="" title="简报预览"></iframe></div>
    <aside>
      <div class="aside-head">历史归档</div>
      <ul id="list"></ul>
    </aside>
  </main>
</div>
<script>
const MANIFEST = {data};
const viewer = document.getElementById('viewer');
const list = document.getElementById('list');
const today = new Date().toLocaleDateString('en-CA');
const def = MANIFEST.find(x => x.date === today) || MANIFEST[0];
function setActive(a) {{
  document.querySelectorAll('#list a').forEach(x => x.classList.remove('active'));
  a.classList.add('active');
}}
MANIFEST.forEach(it => {{
  const li = document.createElement('li');
  const a = document.createElement('a');
  a.href = 'archive/' + it.date + '.html';
  a.innerHTML = it.date + (it.date === today ? '<span class="t">· 今天</span>' : '') +
    '<span class="c">' + it.count + '</span>';
  if (it.date === def.date) {{ a.classList.add('active'); viewer.src = a.href; }}
  a.onclick = (e) => {{ e.preventDefault(); viewer.src = a.href; setActive(a); }};
  li.appendChild(a); list.appendChild(li);
}});
</script>
</body>
</html>'''

def load_seen():
    if os.path.exists(SEEN):
        try:
            with open(SEEN, encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_seen(seen):
    with open(SEEN, 'w', encoding='utf-8') as f:
        json.dump(seen, f, ensure_ascii=False, indent=2)

def main():
    os.makedirs(ARCHIVE, exist_ok=True)
    bj_now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    date_str = bj_now.strftime('%Y-%m-%d')
    # 固定窗口：北京时间 昨日 08:00 ~ 当日 08:00
    end_bj = bj_now.replace(hour=8, minute=0, second=0, microsecond=0)
    start_bj = end_bj - datetime.timedelta(hours=24)
    since_iso = start_bj.astimezone(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    data = pull(since_iso)
    min_dt = datetime.datetime.min.replace(tzinfo=start_bj.tzinfo)
    # 客户端兜底：严格落在窗口内
    items = [it for it in data.get('items', [])
             if start_bj <= (bj(it.get('publishedAt')) or min_dt) < end_bj]
    # 按发布时间倒序
    items.sort(key=lambda it: bj(it.get('publishedAt')) or min_dt, reverse=True)
    # 跨天去重：仅与「此前各日期」已收录的 id 比对（当前日期不去重自己，保证可重跑幂等）
    seen = load_seen()
    prev_seen = set()
    for d, ids in seen.items():
        if d != date_str:
            prev_seen.update(ids)
    kept, local = [], set()
    for it in items:
        kid = it.get('id') or it.get('url') or ''
        if not kid or kid in prev_seen or kid in local:
            continue
        kept.append(it)
        local.add(kid)
    items = kept
    win_str = f'北京时间 {start_bj.strftime("%Y-%m-%d")} 08:00 – {end_bj.strftime("%Y-%m-%d")} 08:00 精选'
    with open(os.path.join(ARCHIVE, f'{date_str}.html'), 'w', encoding='utf-8') as f:
        f.write(gen_report(items, date_str, win_str))
    # 记录当日去重指纹
    seen[date_str] = list(local)
    save_seen(seen)
    m = []
    if os.path.exists(MANIFEST):
        with open(MANIFEST, encoding='utf-8') as f:
            m = json.load(f)
    m = [x for x in m if x['date'] != date_str]
    m.append({'date': date_str, 'count': len(items), 'title': f'AI HOT 速递 · {date_str}'})
    m.sort(key=lambda x: x['date'], reverse=True)
    with open(MANIFEST, 'w', encoding='utf-8') as f:
        json.dump(m, f, ensure_ascii=False, indent=2)
    with open(INDEX, 'w', encoding='utf-8') as f:
        f.write(gen_index(m))
    print(f"OK date={date_str} items={len(items)} archive_total={len(m)}")

if __name__ == '__main__':
    main()
