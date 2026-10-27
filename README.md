# bitdsk-site

bitdsk.org 的静态替代站，定位是**资源索引**：固件下载、使用文档、操作指南。

原站是 WordPress，到期后这里继续提供服务。纯静态，无后端、无数据库，直接托管 GitHub Pages。

> 内容取舍：只保留「文档 + 操作类页面」。原站的产品发布稿、UI 主题宣传、
> 站务新闻、商品页、旧版对比页都没有搬过来（详见第五节）。

> **配套仓库**：浏览器烧录功能与 S1 / U1 / U2 的烧录包已拆到独立的
> [`bitdsk-flash`](../bitdsk-flash/)。本站保留索引条目，点「Flash tool」跳过去。

---

## 一、目录结构

```
bitdsk-site/
├─ index.html              首页：型号选择入口
├─ firmware.html           固件总览（数据驱动，按型号分组）
├─ flash.html              烧录入口页 → 跳转 bitdsk-flash（不再含烧录逻辑）
├─ 404.html                自定义 404
├─ .nojekyll               关掉 Jekyll，避免下划线开头的路径被忽略
├─ robots.txt
├─ favicon.ico             取自原站 favicon
│
├─ css/style.css           全站样式
├─ js/config.js            ★ 站点配置（固件地址、烧录站地址、仓库地址）
├─ js/site.js              前端渲染（读 data/firmware.json）
│
├─ data/
│  ├─ firmware.json        ★ 固件清单（站点唯一数据源，已生成好）
│  ├─ posts-source.json    原站文章导出（生成 guides/ 的原料，21 篇全量）
│  └─ blog-slugs.json      文章 id → 本地文件名 映射
│
├─ doc/                    8 份 PDF 用户手册（中英）
├─ docs/                   原站文档页（导航/图片/死链已修复）
│  ├─ docs.html            文档总览
│  ├─ api.html             API 说明
│  ├─ version-comparison.html  硬件参数对比
│  ├─ fw-n5d12.html        各型号固件更新说明
│  ├─ fw-n8.html
│  ├─ fw-u1u2.html
│  ├─ fw-s1.html
│  ├─ fw-other.html
│  ├─ miner-tools.html
│  └─ *.json               ↑ 这些页面的原始数据，build-data.py 会读
│
├─ guides/                 11 篇操作指南 / 技术文档
├─ images/                 图片（wp-content/uploads 原样保留，文件名已转 ASCII）
│  ├─ logo.png             ★ 页头 logo（原站 logo-1.png 裁切，透明底）
│  └─ favicon-*.png / apple-touch-icon.png
└─ scripts/                维护脚本
   ├─ build-data.py        ★ 生成 data/firmware.json
   ├─ mirror-blog.py       生成 guides/（按 KEEP_IDS 筛选）
   ├─ fix-docs.py          修整 docs/
   ├─ repair-assets.py     校验并修复图片/固件文件
   ├─ brand-fix.py         统一页头 logo 与 favicon（可重复执行）
   ├─ check-deploy.py      ★ 部署前体检（GitHub Pages 规则）
   └─ serve.py             本地预览服务器
```

### 四个仓库怎么分工

| 仓库 | 放什么 |
|---|---|
| **bitdsk-site**（本仓库） | 索引页、文档、指南、PDF、图片 |
| [bitdsk-flash](https://github.com/bitdsk/bitdsk-flash) | 烧录页 + S1 / U1 / U2 的烧录包 |
| [Bitdsk_Miner_Archive](https://github.com/bitdsk/Bitdsk_Miner_Archive) | 其余全部固件 bin（OTA、legacy、工具、Gerber） |
| [Bitdsk-s1-Miner](https://github.com/bitdsk/Bitdsk-s1-Miner) | S1 固件源码（MIT） |

本站**不含任何固件文件**，只保留 `data/firmware.json` 这份清单（文件名、大小、SHA256）
和索引页面。下载链接由 `js/config.js` 的 `firmwareBase` 拼出，指向
`Bitdsk_Miner_Archive` 的 jsDelivr 地址。

`flash.html` 保留为一个说明 + 跳转页，这样站内所有指向它的链接都不会断。

> **版本日期是迁移来的，可能不准。** 版本号准确，旁边的日期取自原站的下拉表格，
> 可能差几天 —— 固件页上已加说明。

---

## 二、本地预览

```bash
python scripts/serve.py 8000
# 浏览器打开 http://127.0.0.1:8000/
```

不要直接双击 `index.html`：`file://` 下浏览器不允许 fetch JSON，固件列表会空白。

也不要用 `python -m http.server`：Windows 上它会把 `.css` 的 MIME 报成 `application/x-css`，
Chrome 会拒绝加载样式（页面变白底无样式）。`scripts/serve.py` 已经修好。

---

## 三、部署到 GitHub Pages

```bash
cd bitdsk-site
git init
git add .
git commit -m "static resource index"
git branch -M main
git remote add origin git@github.com:<你的账号>/bitdsk-site.git
git push -u origin main
```

仓库 → Settings → Pages → Source 选 `Deploy from a branch`，分支 `main`、目录 `/ (root)`。

自定义域名：仓库根放 `CNAME` 文件写域名（如 `bitdsk.org`），DNS 里 `bitdsk.org` 的 A 记录
指向 GitHub Pages 的四个 IP，`www` 用 CNAME 指向 `<账号>.github.io`。

### 推送前先跑体检

```bash
python scripts/check-deploy.py
```

它会按 **Linux 的大小写敏感规则**重新解析所有站内链接（本地 Windows 不区分大小写，
能打开不代表线上能打开），并检查体积、非 ASCII 文件名、`.nojekyll`、PHP 残留等。

当前状态：

| 检查项 | 结果 |
|---|---|
| 站内链接（严格区分大小写） | 全部有效 |
| 单文件最大 | 3.4 MB（`bitdsk-miner.bin`），远低于 100MB 硬上限 |
| 仓库总体积 | 约 79 MB，低于 1GB 建议上限 |
| 非 ASCII 文件名 | 0（6 个中文名已转 ASCII） |
| `.nojekyll` | 已存在 |
| PHP | 无（原站 PHP 烧录已替换为纯静态） |

### 关于带宽

GitHub Pages 有 **100 GB/月软带宽限制**，且官方条款不鼓励把 Pages 当纯文件分发 CDN。
按固件平均 1.5 MB 估算，大约 **6 万次下载/月** 才会触顶，日常够用。
如果下载量变大，两个更合适的出口：

1. **GitHub Releases** —— 专为二进制分发设计，单文件 2 GB、无带宽限制。
   `data/firmware.json` 里的 `path` 支持填完整 URL（`https://github.com/<账号>/<仓库>/releases/download/<tag>/all.3.3_sec.zip`），
   前端会原样使用，不需要改代码。
2. **jsDelivr** —— 见第四节，顺带解决国内访问速度。

---

## 四、固件仓库配置

固件**已经全部拆出去**了，本站不含任何 bin 文件。两个配置项决定文件去哪找。

### firmwareBase —— 普通固件下载

```js
// js/config.js
firmwareBase: 'https://cdn.jsdelivr.net/gh/bitdsk/Bitdsk_Miner_Archive@main/firmware'
```

[Bitdsk_Miner_Archive](https://github.com/bitdsk/Bitdsk_Miner_Archive) 的根目录有
`firmware/`，里面是 `n5-series/` `n8-series/` `legacy/` `tools/` `hardware/` `u-series/`。

前端会把 `firmware/n5-series/all.3.3_sec.zip` 拼成
`<firmwareBase>/n5-series/all.3.3_sec.zip` —— 也就是会去掉 `firmware/` 前缀。
所以：

- 仓库根有 `firmware/` 目录 → 保持默认（末尾带 `/firmware`）
- 仓库根直接就是 `n5-series/` 这些目录 → 把末尾的 `/firmware` 去掉

jsDelivr 有 CDN 缓存，国内访问更稳；也可以换成 GitHub Pages 地址。

`docs/*.html` 里原有的 `../firmware/...` 相对链接（38 处）已经批量替换成
同一个 CDN 地址，改仓库时记得一起换：

```bash
# 全站替换（在 bitdsk-site 根目录执行）
grep -rl 'cdn.jsdelivr.net/gh/bitdsk/Bitdsk_Miner_Archive' docs guides
```

### flashBase —— 烧录站

S1 / U1 / U2 的烧录包在 `bitdsk-flash`，本站通过 `flashBase` 指过去：

```js
// js/config.js
flashBase: '../bitdsk-flash/'
```

同级 GitHub Pages 仓库用相对路径即可（`https://<账号>.github.io/bitdsk-flash/`）；
自定义域名就填绝对地址。**留空则相关按钮自动隐藏**，不会产生死链。

对应地，`bitdsk-flash/js/config.js` 里的 `mainSite` 指回本站。两边各配一个，
换仓库名或域名时两个都要改。

---

## 五、内容取舍：留了什么，砍了什么

原站 21 篇文章，按「资源索引」定位保留 **11 篇**：

**保留（操作指南 / 技术文档）**

| 文章 | 性质 |
|---|---|
| How to fix all_3.0.9_4 cannot connect to hotspot | 故障处理 |
| Fix inability to access backend (incorrect static IP) | 故障处理 |
| How to change the running frequency | 操作 |
| How to use redir for mining pool forwarding（中/英两篇） | 操作 |
| esp32 How to install an antenna（中/英两篇） | 硬件改造 |
| Bitdsk U Series UI Design Guidelines | 开发文档 |
| BLACKBOX 1.3.7 firmware for N8 | 固件说明 |
| 8 reasons to turn down Wi-Fi transmit power | 参考 |
| Bitcoin address generation algorithm | 参考 |

**砍掉（新闻 / 产品 / 站务）**

`Bit Horizon`、`VioletPulse UI`（UI 主题宣传）、`U1 touch launch`、`U2 touch launch`（新品发布）、
`Bitdsk D9`、`Bitdsk Q2`、`Bitdsk N5.Lite & N5.Rex`、`Bitdsk D11`（商品页）、
`We successfully changed the website server`（站务）、`Version comparison`（与
`docs/version-comparison.html` 重复）。

UI 主题的 **资源文件没有删**（`firmware/u-series/themes/`），只是没有宣传文章。

要恢复某篇：在 `scripts/mirror-blog.py` 的 `KEEP_IDS` 里加上它的 id，重跑脚本即可
（`data/posts-source.json` 保留了 21 篇全量导出）。

---

## 六、新增一个固件版本

以 N5 系列发 `all.3.4` 为例：

1. **放文件**：`firmware/n5-series/all.3.4_sec.zip`
2. **改源数据**：在 `docs/fw-n5d12.json` 的表格里加一行（照着现有行的 HTML 结构写），
   下载链接写 `../firmware/n5-series/all.3.4_sec.zip`
3. **重新生成**：

```bash
python scripts/build-data.py
```

脚本会重新计算大小和 SHA256，输出 `data/firmware.json`，首页统计和固件页自动更新，
不需要手改任何 HTML。

**S1 / U1 / U2 的烧录包不在本仓库**，发版时去 `bitdsk-flash` 改：
换 `firmware/<型号>/v_*/` 目录 + 改对应 `manifest.json` 的 `version` 和 5 个 `path`。
本站的 `build-data.py` 里这三个型号标了 `flashExternal`，不会去扫本地文件，
版本号写在 `MODELS` 的 `latestVersion` 字段，记得同步改。

---

## 七、脚本说明

| 脚本 | 作用 | 什么时候跑 |
|---|---|---|
| `build-data.py` | 解析 `docs/*.json` 表格 + 扫描 `firmware/`，生成 `data/firmware.json`（含大小、SHA256、状态） | 增删固件后 |
| `mirror-blog.py` | 按 `KEEP_IDS` 从 `posts-source.json` 生成 `guides/`，并下载正文图片 | 需要重生成指南时 |
| `fix-docs.py` | 修 `docs/*.html` 的导航路径、图片路径、嵌套 `<a>`、`_www` 死链、多余 `srcset` | 文档页被重新导入后 |
| `repair-assets.py` | 按文件头校验 `images/` `doc/` `firmware/`，坏文件从原站重下（`--fix`） | 怀疑文件损坏时 |
| `brand-fix.py` | 把页头占位符换成原站 logo，补齐 favicon（可重复执行，`--dry-run` 预览） | 新增页面后 |
| `check-deploy.py` | 部署前体检：大小写敏感链接、体积、文件名、Pages 限制 | 每次推送前 |
| `serve.py` | 本地预览服务器（修正 MIME） | 本地调试 |

---

## 八、已知说明

- **原站图片曾经全是坏的**：早期那批下载把二进制当文本解码，图片文件头被替换成
  `EF BF BD`，114 张里 80 张无法显示。已用 `repair-assets.py --fix` 全部重下修复。
- **`images/` 里有约 65 张未被引用的图片（8.5 MB）**：原站媒体库的遗留，
  主要是商品图（D9 / Q2 / D12 系列产品照）和已砍掉的新闻稿配图。
  目前保留着没删，需要精简的话可以按引用关系清理。
- **商品页已下线**：原站 `/product/*` 指向 WooCommerce 商品，站不续费后不可用，
  `version-comparison.html` 里的 BUY 链接统一改指 `../firmware.html`。
- **UI 设计器没有搬**：原站 `/u_ui_design/` 是带后端的在线 UI 编辑器，纯静态无法保留，
  相关规范已存档在 `guides/bitdsk-u-series-ui-design-guidelines.html`。
- **烧录已拆到独立仓库**：`bitdsk-flash` 里用了本地化的 `esp-web-tools`
  （`js/vendor/`，不依赖 CDN），且烧录页与镜像同源，加载 manifest 不需要跨域。
  本站的 `flash.html` 只是入口页。
- **界面是英文**：原站面向海外买家，正文（固件说明、PDF、文章）也都是英文，
  所以界面保持英文。需要中文版可以再加一套页面。
