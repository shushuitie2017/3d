# 蓝猫 3D（3d.bluecatbot.com）— 项目说明

AI × 3D 角色产线站点：**工具榜单（Leaderboard）+ 九步产线实战课（The Course）**。
数据驱动的三语静态站，由 `build_site.py` 从 `src/` 生成 `out/`，部署到 `3d.bluecatbot.com`。

> 完整落地依据见 `design/蓝猫3D-落地文档.md`（产品定位 / IA / 内容资产 / 技术方案 / 部署 / 排期）。
> `design/` 下的 10 份 HTML 是**原始设计稿**（9 模块页 + 1 工具榜单落地页），是内容与视觉的真相源，仅作参照，不参与构建。

## 架构：一个模板 + 一份数据

```
src/
├── templates/home.html             # 首页（忠实复刻 design/ 的工具榜单落地页，去打包后的干净源）
├── data/modules/01.json … 09.json  # 九步产线详情页内容（verbatim，从设计稿提取）
├── i18n/zh.json                    # 模块页 UI 文案（一语一文件；en/ja 待补）
└── static/style.css  assets/       # 模块页设计系统（收敛自模块页设计令牌）
build_site.py                       # 渲染器（纯 Python，无依赖）
out/                                # 构建产物（gitignore），部署用
```

两条线，各自的真相源不同：

- **首页 = `src/templates/home.html`**：忠实复刻 `design/蓝猫3D 工具榜单落地页 (standalone).html`。该 standalone 是 component-bundler 导出(6.7MB)，真正的 HTML 藏在 `__bundler/template` 脚本的转义 JSON 串里；已 `json.loads` 去打包 + 剥除 `<sc-if>`/`style-hover`/`{{ }}` 等框架残留 + 换成 Google Fonts，落成这份干净自包含模板。**改首页内容/榜单分数/课程定价 → 改这里**（自带内联样式 + 自己的 `<style>`，不走 `static/style.css`）。`build_site.py` 仅把 `__BASE__` 占位替换为 `/zh` 并把 9 张产线卡片接到模块详情页。
- **模块页 = `src/data/modules/NN.json`**：`sections[]` 装有序「类型块」(prose/rules/workflow/branches/pitfalls/checklist/selfcheck)，`build_site.py` 里每类型一个 `r_*()` 渲染函数，各模块 section 顺序/数量不同如实还原。设计系统在 `src/static/style.css`，**已适配主页设计语言**：深空 `--bg:#06080E` + 卡片 `#0E121C` + Space Grotesk 标题 + 钴蓝→青 `--ac:#5B8CFF`/`--ac2:#32E0FF` 渐变强调 + 立方体 logo。难度色：AI 提速=青 / AI+手修=钴 / 蓝猫带练=紫 `#9B8CFF`（与主页产线卡片一致）。模块 nav 也换成主页同款（立方体 brand + 榜单/产线链接 + 报名课程）。

> 重要教训：首页不要凭提取的数据「重写」，要**严格照 standalone 设计复刻**——榜单是带评分(9.2/9.0…)的 4 卡矩阵(含 Rodin Gen 2.5 / 3D AI Studio)、hero 有 23/9/180+/1 计数器 + A/B 盲测 demo 卡、课程有 6 格特性条 + 划线价、版块序是 Hero→榜单→产线→课程→导师→FAQ→CTA。

## 构建 / 本地预览

```bash
python build_site.py                          # → out/（10 页 × 语言数）
cd out && python -m http.server 5018           # 本地 5018 预览
# 访问 http://127.0.0.1:5018/zh/
```

> Windows 坑：本地 `http.server` 占用 `out/` 句柄会导致 `build_site.py` 的 `shutil.rmtree(out)` 失败（WinError 32）。重建前先停掉预览服务。

## URL / 路由

- `/zh/`（首页）· `/zh/pipeline/01.html … 09.html`（模块页）
- 顶层 `/index.html` = meta-refresh 跳转到 `/zh/`
- 资源走根相对路径 `/static/…`（部署 nginx root = `out/`，本地 server root = `out/` 都成立）

## 加语言（en / ja，Phase 2）

1. `build_site.py` 的 `LANGS` 加 `"en"` / `"ja"`。
2. **首页**：复制 `src/templates/home.html` 为 `home.en.html` / `home.ja.html` 并翻译文案（`build_site` 已会优先取 `home.<lang>.html`，否则回退 `home.html`）。
3. **模块页**：加 `src/i18n/en.json`（照 `zh.json` 结构译 UI 文案）；模块正文当前用 `modules/NN.json`（中文），要真三语需建 `modules.en/ja` 并让 `build_site` 按语言择源。译稿过三语校对（`_shared-proofreading/glossary.md` + 校对 skill），硬伤清零再发。
4. apex 跳转语言、`hreflang` 待补。

## 部署（Phase 2，未执行）

走 `bluecat-deploy`（静态站路径）：`out/` → nginx root + certbot SSL；连接信息落 `servers.json`（gitignore）。坑：nginx 静态站 404 多为目录权限，上线后 `chmod -R o+rX`。门户加三语卡片先拉后改先备份。

## 商业化（Phase 3，未执行）

课程支付走 `stripe-payments`（一次性付费 ¥999 / ¥3999）。**红线：密钥只进服务器 `.env`，绝不进 git / 聊天 / 代码。** 亲传档「每月限 10 席」需服务端计数。

## 现状

- ✅ P0 数据化 + P1 中文站构建：`build_site.py` 生成 zh 全站（首页 + 9 模块页），本地 Chrome 实测通过。
- ⏳ 待办：P2 部署（需确认目标服务器并落 `servers.json`）、P3 三语、P4 支付。
