---
date: 2026-07-01
updated: 2026-07-01
project: server-projects/3d（蓝猫3D）
context_pct: ~55%
---

# 进度交接

## 当前目标
蓝猫3D（AI×3D 角色产线站 = 工具榜单 + 九步产线实战课）已**部署上线 https://3d.bluecatbot.com 且完成三语 + 语言切换升级**。剩两条独立线未做：P4 课程支付、九步产线「真跑一遍」手順書（Session 1 卡在等 Gemini 登录）。

## 已完成（本会话累计）
1. **首页忠实复刻**（`src/templates/home.html`，从 bundler 导出去打包而来）+ **9 模块页数据驱动**（`src/data/modules/NN.json`，`build_site.py` 每 section 类型一个 `r_*()`）。
2. **模块页设计适配主页语言**（`src/static/style.css`：深空 #06080E + 钴蓝→青 + Space Grotesk + 立方体 logo；难度色 青/钴/紫）。
3. **✅ 部署上线**：静态站 → **Caddy 游戏服 54.248.150.201**（非真 chi；servers.json 里 name 写 chi 但 host 是游戏服，同 svg/tianya/sakata；remote `/home/ubuntu/3d`）。Caddy site block 仿 svgsafe。`build_site.py` 生成 robots/sitemap/404 + og-cover.png。
4. **✅ 三语全站**（zh/en/ja，30 页）：`LANGS=[zh,en,ja]`；en/ja 模块内容在 `src/data/modules_en|ja/`，UI 串 `src/i18n/en|ja.json`，首页 `src/templates/home.en|ja.html`。翻译靠 **Workflow 扇出 22 agent**（agent 直接写文件；prompt 原文保持不译、结构/文件命名不动、只译可见中文）。hreflang（zh/en/ja/x-default）+ 每语 canonical。MOD_WORD 本地化「模块/Module/モジュール」。修了 crumb `#pipe`→`#pipeline` 死锚。
5. **✅ 语言切换升级（仿 top3d.ai，最新一轮）**：
   - **下拉框切换器**：`lang_switch()` 改 `<details>`（globe 图标 + 当前语言全称 + caret + 勾选面板），**行内样式**（首页自包含 + 模块页外链 CSS 通用），内联 scoped `<style>` 隐 marker。
   - **浏览器语言自动分流**：apex `/` 不再 Caddy 308，改 serve `index.html` 探测页（JS：localStorage `lang3d` 偏好 → `navigator.language`(ja/en/else zh) → `location.replace`；`<noscript>` 回退 /zh/；带 h1 + WebSite JSON-LD + hreflang + og）。每个语言页加载即存 `lang3d`=当前语言。
   - **导航菜单图标**：`NAV_ICONS` + `_svg()`（榜单=排名柱/产线=层叠/课程=学位帽/导师=人，14px stroke:currentColor）。首页 4 链接靠 Python 脚本注入（三语 opening tag 字节相同 + 幂等 assert），模块页 navbar 内联。
   - Caddy 改动：只删 3d 块的 `@root path /` + `redir /zh/ 308`（锚定唯一 `root * /home/ubuntu/3d`，没误伤 svgsafe 同款配置），validate + reload。
6. **门户三语卡片**：chi（57.181.215.147，key `Polymarketchi.pem`）的 `website-main/{,en,ja}/index.html` **午前 morning 区** i-crystal「3D · Course」卡（先拉→备份→回推，三语各验=2）。
7. **SEO 闸**：内容页 `/zh/`（及 en/ja）**100/100**；探测 apex **97/100**（唯一 warn = 路由页无 @media，无碍）。全部 0 fail。

## 进行中 / 未完成
- **P4 课程支付**：未做。走 [[stripe-payments]]，密钥只进服务器 .env，亲传 ¥3999「每月限 10 席」需服务端计数。
- **九步产线真跑手順書**（`手順書/`，见 plan `C:\Users\1\.claude\plans\polymorphic-conjuring-nebula.md`）：Session 1 脚手架已建（README/00/01 + assets 目录树），**卡在步骤 01——等用户在受控 Chrome 里登录 Gemini**。本机无 Blender、磁盘紧（C: 15G/D: 8G）。与站点部署互不影响。
- 榜单 `testedAt: 2026-06`，AI 工具迭代快，建议定期复测。
- **未推 GitHub**（`server-projects/3d` 非 git repo）。

## 关键决策与原因
- 首页**严格照 standalone 设计复刻**，不凭数据重写（曾因重排被用户打回）。
- 三语翻译用 Workflow 并行（22 agent），prompt 原文（英文生图提示）保持不译。
- 语言切换按 top3d.ai：下拉框 + 浏览器自动分流 + 菜单图标。

## 下一步（可直接执行）
1. 若用户要继续手順書：等其「登好了」→ chrome-devtools 驱动 Gemini 跑步骤 01（prompt 在 `手順書/01_概念设定.md`）→ 下载图到 `手順書/assets/蓝猫剑客/01_concept/`。
2. 若要 P4 支付：调 stripe-payments skill，接散养¥999/亲传¥3999 一次性付费。
3. 若要推 GitHub：`git init` + 推 `shushuitie2017/3d`（私有；HTTPS token 见 [[git-push-shushuitie2017-https]]），排除 servers.json/.env/HANDOFF。
4. 站点内容再改：改首页/榜单分数/定价 → `src/templates/home.html`(+en/ja)；改模块 → `src/data/modules*/NN.json`；`python build_site.py` → tar `out/` → scp 54.248.150.201:/home/ubuntu/3d。

## 继续 / 复现方式
- 构建+本地预览：`cd server-projects/3d && python build_site.py && cd out && python -m http.server 5019`。**Windows 坑**：预览服务占 out/ 句柄 → rmtree WinError32，重建前先 Stop-Process 掉 http.server。
- 部署：`tar czf /tmp/3d-site.tgz --force-local -C out .` → `scp -i C:/Users/1/Downloads/claude.pem ... ubuntu@54.248.150.201:/tmp/` → 服务器 `rm -rf /home/ubuntu/3d && mkdir && tar xzf`。
- SEO 闸：`bash ~/.claude/skills/bluecat-deploy/scripts/seo-check.sh 3d.bluecatbot.com/zh/`。
- **验证浏览器自动分流要用带 query 的新 URL + 清 localStorage**（Caddy 旧 308 被浏览器硬缓存）。

## 未决问题
- P4 支付要不要现在做？
- 手順書 Session 1 要不要继续（需用户登录 Gemini + 装 Blender + 腾工作盘）？
- 要不要推 GitHub？
- 注意：`build_site.py` 本会话被外部加过 OG/og_tags，别回退。
