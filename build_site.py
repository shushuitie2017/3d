#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
蓝猫3D 站点构建器
读 src/data/*.json + src/i18n/<lang>.json + src/data/modules/NN.json
→ 生成 out/<lang>/ 全站静态页（首页 + 九步产线详情页）+ out/static/ + out/index.html(跳转)

用法:  python build_site.py
"""
import json, os, re, shutil, html, glob

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src")
OUT = os.path.join(ROOT, "out")

# 已就绪语言（zh 用 modules/，en/ja 用 modules_<lang>/）
LANGS = ["zh", "en", "ja"]
DOMAIN = "https://3d.bluecatbot.com"
LANG_LABEL = {"zh": "中", "en": "EN", "ja": "日"}
LANG_FULL = {"zh": "中文", "en": "English", "ja": "日本語"}
MOD_WORD = {"zh": "模块", "en": "Module", "ja": "モジュール"}

# 导航菜单图标（14px 线性，stroke:currentColor 继承链接色）
def _svg(inner):
    return ('<svg width="14" height="14" viewBox="0 0 24 24" fill="none" style="stroke:currentColor;'
            'stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round;flex-shrink:0">' + inner + '</svg>')
NAV_ICONS = {
    "board": _svg('<path d="M4 20V13M12 20V4M20 20V9"/>'),                                  # 榜单=排名柱
    "pipeline": _svg('<path d="M12 2 2 7l10 5 10-5L12 2Z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>'),  # 产线=层叠
    "course": _svg('<path d="M22 10 12 5 2 10l10 5 10-5Z"/><path d="M6 12v5c0 1.1 2.7 3 6 3s6-1.9 6-3v-5"/>'),        # 课程=学位帽
    "mentor": _svg('<circle cx="12" cy="8" r="4"/><path d="M4 21v-1a6 6 0 0 1 6-6h4a6 6 0 0 1 6 6v1"/>'),           # 导师=人
}

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700'
         '&family=JetBrains+Mono:wght@400;500;700'
         '&family=Noto+Sans+SC:wght@400;500;600;700;900&display=swap" rel="stylesheet">')

# 立方体 logo（与主页 brand 一致）
CUBE = ('<svg viewBox="0 0 24 24" fill="none" style="stroke:var(--ac);stroke-width:1.6;'
        'stroke-linejoin:round;stroke-linecap:round">'
        '<polygon points="12,2.6 20.4,7.3 20.4,16.7 12,21.4 3.6,16.7 3.6,7.3"></polygon>'
        '<path d="M12,12 L12,21.4 M12,12 L20.4,7.3 M12,12 L3.6,7.3"></path></svg>')

DIFF_CLASS = [("AI 提速", "ai"), ("带练", "hand"), ("手修", "mixed")]


def e(s):
    return html.escape(s or "", quote=False)


def lang_switch(paths, cur):
    """语言切换器 —— 下拉框（globe + 当前语言 + 展开面板）。行内样式，首页/模块页通用。
    每页加载即把当前语言存入 localStorage，供 apex 页按浏览器/偏好自动分流。"""
    globe = _svg('<circle cx="12" cy="12" r="9"/><path d="M3 12h18"/>'
                 '<path d="M12 3c2.6 2.6 2.6 15.4 0 18M12 3c-2.6 2.6-2.6 15.4 0 18"/>')
    caret = ('<svg width="11" height="11" viewBox="0 0 24 24" fill="none" style="stroke:currentColor;'
             'stroke-width:2;stroke-linecap:round;stroke-linejoin:round;opacity:.7"><path d="M6 9l6 6 6-6"/></svg>')
    summary = ('<summary style="list-style:none;cursor:pointer;display:inline-flex;align-items:center;gap:7px;'
               "font-family:'JetBrains Mono',monospace;font-size:12.5px;color:#8B95AC;"
               'border:1px solid rgba(130,160,220,.16);border-radius:9px;padding:6px 11px">'
               f'{globe}<span>{LANG_FULL[cur]}</span>{caret}</summary>')
    items = ""
    for L in LANGS:
        st = ("display:flex;align-items:center;gap:9px;text-decoration:none;padding:9px 13px;border-radius:8px;"
              "font-size:13.5px;white-space:nowrap;"
              + ("color:#32E0FF;background:rgba(91,140,255,.13)" if L == cur else "color:#C7CEDC"))
        chk = ('<span style="margin-left:auto;color:#32E0FF">✓</span>' if L == cur else '')
        items += f'<a href="{paths[L]}" style="{st}">{LANG_FULL[L]}{chk}</a>'
    panel = ('<div style="position:absolute;top:calc(100% + 8px);right:0;min-width:150px;background:#0E121C;'
             'border:1px solid rgba(130,160,220,.16);border-radius:12px;padding:5px;z-index:70;'
             f'box-shadow:0 18px 44px rgba(0,0,0,.55);display:grid;gap:2px">{items}</div>')
    css = ('<style>details.lang-dd>summary::-webkit-details-marker{display:none}'
           'details.lang-dd>summary::marker{content:""}'
           'details.lang-dd[open]>summary{color:#EAEFF8;border-color:rgba(91,140,255,.32)}</style>')
    js = f"<script>try{{localStorage.setItem('lang3d','{cur}')}}catch(e){{}}</script>"
    return f'{css}<details class="lang-dd" style="position:relative">{summary}{panel}</details>{js}'


def hreflang_tags(paths):
    """hreflang 备用链接（多语言 SEO）"""
    links = "".join(f'<link rel="alternate" hreflang="{L}" href="{DOMAIN}{paths[L]}">' for L in LANGS)
    return links + f'<link rel="alternate" hreflang="x-default" href="{DOMAIN}{paths["zh"]}">'


def diff_kind(meta):
    """从模块 meta 的『难度』推断 ai/hand/mixed"""
    val = next((m["v"] for m in meta if m["k"] == "难度"), "")
    for key, cls in DIFF_CLASS:
        if key in val:
            return cls, val
    return "mixed", val


def prompt_html(text):
    """转义 + 把 [占位符] 高亮为青色"""
    esc = e(text)
    return re.sub(r"\[([^\]]+)\]", r'<span class="ph">[\1]</span>', esc)


# ---------- 模块详情页 section 渲染 ----------
def r_prose(s):
    box = ""
    if s.get("box"):
        box = '<div class="why">' + "".join(f"<p>{e(p)}</p>" for p in s["box"]) + "</div>"
    paras = "".join(f'<p class="tx">{e(p)}</p>' for p in s.get("paras", []))
    return f'<div class="snum">{e(s["snum"])}</div><h2 class="sh">{e(s["h2"])}</h2>{paras}{box}'


def r_rules(s):
    intro = f'<p class="tx">{e(s["intro"])}</p>' if s.get("intro") else ""
    rules = "".join(
        f'<div class="rule"><div><h4>{e(r["h4"])}</h4><p>{e(r["p"])}</p></div></div>'
        for r in s["rules"])
    return (f'<div class="snum">{e(s["snum"])}</div><h2 class="sh">{e(s["h2"])}</h2>'
            f'{intro}<div class="rules">{rules}</div>')


def r_workflow(s):
    intro = f'<p class="tx">{e(s["intro"])}</p>' if s.get("intro") else ""
    steps = []
    for st in s["substeps"]:
        opt = f' <span class="opt">{e(st["opt"])}</span>' if st.get("opt") else ""
        paras = "".join(f"<p>{e(p)}</p>" for p in st.get("paras", []))
        bullets = ""
        if st.get("bullets"):
            bullets = "<ul>" + "".join(f"<li>{e(b)}</li>" for b in st["bullets"]) + "</ul>"
        prompts = ""
        for p in st.get("prompts", []):
            prompts += (
                '<div class="prompt"><div class="prompt-bar">'
                f'<span class="prompt-label">{e(p["label"])}</span>'
                '<button class="copy" onclick="cp(this)">复制</button></div>'
                f'<pre>{prompt_html(p["text"])}</pre></div>')
        calls = ""
        for c in st.get("calls", []):
            icon = {"tip": "💡", "warn": "⚠️", "rule": "🔬"}.get(c["type"], "💡")
            calls += (f'<div class="call {e(c["type"])}"><span class="ci">{icon}</span>'
                      f'<span>{e(c["text"])}</span></div>')
        steps.append(
            f'<div class="substep"><div class="ss-tag">{e(st["tag"])}</div>'
            f'<div class="ss-title">{e(st["title"])}{opt}</div>'
            f"{paras}{bullets}{prompts}{calls}</div>")
    return (f'<div class="snum">{e(s["snum"])}</div><h2 class="sh">{e(s["h2"])}</h2>'
            f'{intro}{"".join(steps)}')


def r_branches(s):
    cards = "".join(
        f'<div class="bcard"><h4>{e(b["name"])}</h4><p>{e(b["p"])}</p><code>{e(b["code"])}</code></div>'
        for b in s["branches"])
    return (f'<div class="snum">{e(s["snum"])}</div><h2 class="sh">{e(s["h2"])}</h2>'
            f'<div class="branch">{cards}</div>')


def r_pitfalls(s):
    items = "".join(f"<div><span>{e(i)}</span></div>" for i in s["items"])
    return (f'<div class="snum">{e(s["snum"])}</div><h2 class="sh">{e(s["h2"])}</h2>'
            f'<div class="pit">{items}</div>')


def r_checklist(s):
    rows = ""
    for i in s["items"]:
        small = f'<small>{e(i["small"])}</small>' if i.get("small") else ""
        rows += ('<div class="ci-row" onclick="tk(this)"><div class="ci-box"></div>'
                 f'<div class="ci-text">{e(i["text"])}{small}</div></div>')
    return (f'<div class="snum">{e(s["snum"])}</div><h2 class="sh">{e(s["h2"])}</h2>'
            f'<div class="check">{rows}</div>')


def r_selfcheck(s):
    qs = "".join(f"<li>{e(q)}</li>" for q in s["questions"])
    return (f'<div class="snum">{e(s["snum"])}</div><div class="selfcheck">'
            f'<h3>{e(s["title"])}</h3><ol>{qs}</ol>'
            f'<p class="pass">{e(s["pass"])}</p></div>')


RENDER = {"prose": r_prose, "rules": r_rules, "workflow": r_workflow, "branches": r_branches,
          "pitfalls": r_pitfalls, "checklist": r_checklist, "selfcheck": r_selfcheck}


# ---------- 页面骨架 ----------
OG_IMAGE = "https://3d.bluecatbot.com/og-cover.png"


def og_tags(title, desc, url):
    """Open Graph / Twitter Card 社交缩略图标签"""
    et, ed = e(title), e(desc)
    return (f'<meta property="og:type" content="website">'
            '<meta property="og:site_name" content="蓝猫 3D">'
            '<meta property="og:locale" content="zh_CN">'
            f'<meta property="og:title" content="{et}">'
            f'<meta property="og:description" content="{ed}">'
            f'<meta property="og:image" content="{OG_IMAGE}">'
            '<meta property="og:image:width" content="1200">'
            '<meta property="og:image:height" content="630">'
            f'<meta property="og:url" content="{url}">'
            '<meta name="twitter:card" content="summary_large_image">'
            f'<meta name="twitter:title" content="{et}">'
            f'<meta name="twitter:description" content="{ed}">'
            f'<meta name="twitter:image" content="{OG_IMAGE}">')


def head(t, title, desc, canonical, hreflang=""):
    return (f'<!DOCTYPE html><html lang="{t["htmlLang"]}"><head><meta charset="UTF-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
            f'<title>{e(title)}</title><meta name="description" content="{e(desc)}">'
            f'<link rel="canonical" href="{canonical}">{hreflang}'
            f'{og_tags(title, desc, canonical)}'
            '<script type="application/ld+json">'
            + json.dumps({"@context": "https://schema.org", "@type": "TechArticle",
                          "headline": title, "description": desc, "url": canonical,
                          "inLanguage": "zh-CN",
                          "publisher": {"@type": "Organization", "name": "蓝猫 BlueCat", "url": "https://bluecatbot.com"}},
                         ensure_ascii=False) + '</script>'
            '<link rel="icon" href="/static/assets/favicon.svg" type="image/svg+xml">'
            f'{FONTS}<link rel="stylesheet" href="/static/style.css"></head>')


def navbar(t, base, langnav=""):
    """模块页导航 —— 与主页同款（立方体 brand + 榜单/产线链接 + 语言切换 + 报名课程）"""
    return (f'<nav><div class="nav-in">'
            f'<a href="{base}/" class="brand">{CUBE}<b>{e(t["siteName"])}</b></a>'
            f'<div class="nav-links">'
            f'<a href="{base}/#board" class="nav-link" style="display:inline-flex;align-items:center;gap:6px">{NAV_ICONS["board"]}{e(t["nav"]["leaderboard"])}</a>'
            f'<a href="{base}/#pipeline" class="nav-link" style="display:inline-flex;align-items:center;gap:6px">{NAV_ICONS["pipeline"]}{e(t["nav"]["pipeline"])}</a></div>'
            f'{langnav}'
            f'<a href="{base}/#course" class="nav-cta">{e(t["nav"]["cta"])}</a>'
            f'</div></nav>')


def footer(t):
    return (f'<footer><div class="wrap"><div class="fm">{e(t["tagline"])}<br>'
            f'{e(t["footer"])}</div></div></footer>')


SCRIPT = '''<script>
function cp(b){const p=b.closest('.prompt').querySelector('pre');navigator.clipboard.writeText(p.innerText).then(()=>{b.textContent='已复制 ✓';b.classList.add('done');setTimeout(()=>{b.textContent='复制';b.classList.remove('done')},1800)}).catch(()=>{b.textContent='复制失败';setTimeout(()=>b.textContent='复制',1800)})}
function tk(r){r.classList.toggle('done')}
const io=new IntersectionObserver(es=>{es.forEach(x=>{if(x.isIntersecting){x.target.classList.add('in');io.unobserve(x.target)}})},{threshold:.08});
document.querySelectorAll('.reveal').forEach(el=>io.observe(el));
</script>'''


# ---------- 模块详情页 ----------
def build_module(t, m, base, canonical, total=9):
    n = int(m["num"])
    lang = t["lang"]
    paths = {L: f'/{L}/pipeline/{m["num"]}.html' for L in LANGS}
    langnav = lang_switch(paths, lang)
    hl = hreflang_tags(paths)
    mw = MOD_WORD.get(lang, "模块")
    bars = ""
    for i in range(1, total + 1):
        cls = "cur" if i == n else ("on" if i < n else "")
        bars += f'<i class="{cls}"></i>'
    prog = (f'<div class="prog"><div class="prog-in"><div class="prog-bars">{bars}</div>'
            f'<div class="prog-label"><b>{m["num"]}</b> {e(t["module"]["of"])}</div></div></div>')

    kind, dval = diff_kind(m["meta"])
    metas = "".join(
        f'<div class="meta"><span class="mk">{e(x["k"])}</span>'
        f'<span class="mv{(" "+kind) if x["k"]=="难度" else ""}">{e(x["v"])}</span></div>'
        for x in m["meta"])
    hero = (f'<header class="lhead"><div class="wrap">'
            f'<div class="crumb"><a href="{base}/">{e(t["module"]["crumb_home"])}</a> / '
            f'<a href="{base}/#pipeline">{e(t["module"]["crumb_pipeline"])}</a> / {mw} {m["num"]}</div>'
            f'<div class="mod-badge">{e(m["badge"])}</div>'
            f'<h1 class="ltitle">{e(m["title"])}</h1>'
            f'<p class="lobjective">{e(m["objective"])}</p>'
            f'<div class="meta-row">{metas}</div></div></header>')

    secs = ""
    for s in m["sections"]:
        secs += f'<section class="reveal"><div class="wrap">{RENDER[s["type"]](s)}</div></section>'

    # prev / next
    prev_n = f"{n-1:02d}" if n > 1 else None
    next_n = f"{n+1:02d}" if n < total else None
    if prev_n:
        prev = (f'<a href="{base}/pipeline/{prev_n}.html"><span class="ln-k">{e(t["module"]["prev"])}</span>'
                f'<span class="ln-v">{mw} {prev_n}</span></a>')
    else:
        prev = (f'<a class="disabled"><span class="ln-k">{e(t["module"]["prev"])}</span>'
                f'<span class="ln-v">{e(t["module"]["first"])}</span></a>')
    if next_n:
        nxt = (f'<a class="next" href="{base}/pipeline/{next_n}.html"><span class="ln-k">{e(t["module"]["next"])}</span>'
               f'<span class="ln-v">{mw} {next_n}</span></a>')
    else:
        nxt = (f'<a class="next disabled"><span class="ln-k">{e(t["module"]["next"])}</span>'
               f'<span class="ln-v">{e(t["module"]["last"])}</span></a>')
    lnav = f'<div class="wrap"><div class="lnav">{prev}{nxt}</div></div>'

    body = (f'<body><div class="bg"></div>{navbar(t, base, langnav)}'
            f'{prog}{hero}{secs}{lnav}{footer(t)}{SCRIPT}</body></html>')
    title = f'{mw} {m["num"]} · {m["title"]} — {t["siteName"]} {t["tagline"]}'
    return head(t, title, m["objective"][:150], canonical, hl) + body


def load(p):
    return json.load(open(p, encoding="utf-8"))


def main():
    # 清空并重建 out
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)

    # static（语言无关，共享）
    shutil.copytree(os.path.join(SRC, "static"), os.path.join(OUT, "static"))

    # 社交缩略图（og:image）→ 站点根目录 /og-cover.png
    og_src = os.path.join(SRC, "og-cover.png")
    if os.path.exists(og_src):
        shutil.copy(og_src, os.path.join(OUT, "og-cover.png"))

    nums = [os.path.splitext(os.path.basename(f))[0]
            for f in sorted(glob.glob(os.path.join(SRC, "data", "modules", "*.json")))]
    home_paths = {L: f"/{L}/" for L in LANGS}

    pages = 0
    for lang in LANGS:
        t = load(os.path.join(SRC, "i18n", f"{lang}.json"))
        base = f"/{lang}"
        ldir = os.path.join(OUT, lang)
        os.makedirs(os.path.join(ldir, "pipeline"), exist_ok=True)

        # 该语言的模块内容（zh 用 modules/，en/ja 用 modules_<lang>/）
        mdir = "modules" if lang == "zh" else f"modules_{lang}"
        modules = [load(f) for f in sorted(glob.glob(os.path.join(SRC, "data", mdir, "*.json")))]

        # 首页：忠实复刻的模板（各语言 home.<lang>.html，zh 回退 home.html）+ 占位替换
        htpl = os.path.join(SRC, "templates", f"home.{lang}.html")
        home_tpl = open(htpl if os.path.exists(htpl)
                        else os.path.join(SRC, "templates", "home.html"), encoding="utf-8").read()
        home_out = (home_tpl.replace("__BASE__", base)
                    .replace("__CANONICAL__", f"{DOMAIN}/{lang}/")
                    .replace("__HREFLANG__", hreflang_tags(home_paths))
                    .replace("__LANGNAV__", lang_switch(home_paths, lang)))
        with open(os.path.join(ldir, "index.html"), "w", encoding="utf-8") as f:
            f.write(home_out)
        pages += 1

        # 模块页
        for m in modules:
            with open(os.path.join(ldir, "pipeline", f'{m["num"]}.html'), "w", encoding="utf-8") as f:
                f.write(build_module(t, m, base, f'{DOMAIN}/{lang}/pipeline/{m["num"]}.html'))
            pages += 1

    # apex：按 localStorage 偏好 → 浏览器语言 → 默认 zh 自动分流（无 JS 回退 /zh/）
    apex_title = "蓝猫 3D · AI × 3D 角色产线 · 工具榜单 + 实战课"
    apex_desc = ("AI 3D tool leaderboard + a 9-step hands-on pipeline course. "
                 "把主流 AI 3D 工具按九道工序实测排名，跟蓝猫的课做出能进 Unity / UE5 的成品角色。")
    detect_js = ("(function(){var L=['zh','en','ja'],s=null;try{s=localStorage.getItem('lang3d')}catch(e){}"
                 "var p=(s&&L.indexOf(s)>=0)?s:null;if(!p){var b=(navigator.language||navigator.userLanguage||'zh')"
                 ".toLowerCase();p=b.indexOf('ja')===0?'ja':b.indexOf('zh')===0?'zh':b.indexOf('en')===0?'en':'zh';}"
                 "location.replace('/'+p+'/');})();")
    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as f:
        f.write('<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8">'
                '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
                f'<title>{e(apex_title)}</title><meta name="description" content="{e(apex_desc)}">'
                f'<link rel="canonical" href="{DOMAIN}/">'
                f'{hreflang_tags(home_paths)}'
                f'{og_tags(apex_title, apex_desc, DOMAIN + "/")}'
                '<link rel="icon" href="/static/assets/favicon.svg" type="image/svg+xml">'
                '<script type="application/ld+json">'
                + json.dumps({"@context": "https://schema.org", "@type": "WebSite",
                              "name": "蓝猫 3D / BlueCat 3D", "url": f"{DOMAIN}/",
                              "description": apex_desc, "inLanguage": ["zh-CN", "en", "ja"]},
                             ensure_ascii=False) + '</script>'
                f'<script>{detect_js}</script>'
                '<noscript><meta http-equiv="refresh" content="0; url=/zh/"></noscript>'
                '</head><body style="background:#06080E;color:#EAEFF8;font-family:\'Noto Sans SC\',system-ui,sans-serif;'
                'text-align:center;padding:90px 24px">'
                '<h1 style="font-size:26px;font-weight:700;margin:0 0 12px">蓝猫 3D · BlueCat 3D</h1>'
                '<p style="color:#8B95AC;margin:0 0 20px">AI × 3D 角色产线 · 工具榜单 + 实战课</p>'
                '<p><a href="/zh/" style="color:#5B8CFF;text-decoration:none">进入</a> · '
                '<a href="/en/" style="color:#5B8CFF;text-decoration:none">Enter</a> · '
                '<a href="/ja/" style="color:#5B8CFF;text-decoration:none">入る</a></p>'
                '</body></html>')

    # robots.txt
    with open(os.path.join(OUT, "robots.txt"), "w", encoding="utf-8") as f:
        f.write("User-agent: *\nAllow: /\nSitemap: https://3d.bluecatbot.com/sitemap.xml\n")

    # sitemap.xml（apex + 各语言首页 + 模块页）
    urls = [f"{DOMAIN}/"]
    for lang in LANGS:
        urls.append(f"{DOMAIN}/{lang}/")
        urls += [f'{DOMAIN}/{lang}/pipeline/{nn}.html' for nn in nums]
    loc = "".join(f"<url><loc>{u}</loc><changefreq>weekly</changefreq></url>" for u in urls)
    with open(os.path.join(OUT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>'
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                f'{loc}</urlset>')

    # 404 页（Caddy handle_errors rewrite 到此）
    t0 = load(os.path.join(SRC, "i18n", f"{LANGS[0]}.json"))
    with open(os.path.join(OUT, "404.html"), "w", encoding="utf-8") as f:
        f.write(head(t0, "404 · 蓝猫 3D", "页面走丢了", f"{DOMAIN}/404.html") +
                '<body><div class="bg"></div>'
                '<div class="wrap" style="text-align:center;padding:120px 24px;position:relative;z-index:1">'
                '<h1 class="ltitle" style="font-size:64px">404</h1>'
                '<p class="lobjective" style="margin:0 auto 28px">这一步走丢了——回到九步产线重新出发。</p>'
                f'<a class="nav-cta" href="/{LANGS[0]}/">返回首页</a></div></body></html>')

    print(f"✓ 构建完成：{pages} 页 + robots/sitemap/404（语言 {','.join(LANGS)}）→ {OUT}")


if __name__ == "__main__":
    main()
