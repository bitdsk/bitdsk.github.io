#!/usr/bin/env python3
"""
mirror-blog.py — 把原站博客/教程文章生成静态页面

输入：data/posts-source.json（原站 wp-json/wp/v2/posts 的导出）
输出：blog/<slug>.html 与 blog/index.html，并把正文引用的图片下载到 images/

用法：
    python scripts/mirror-blog.py
"""
import json
import os
import re
import sys
import urllib.request
import urllib.parse
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'data', 'posts-source.json')
BLOG = os.path.join(ROOT, 'guides')
SITE = 'https://www.bitdsk.org'

# 只归档「操作指南 / 技术文档」类文章。
# 新闻稿、新品发布、商品页、旧版对比页不保留 —— 本站定位是资源索引。
KEEP_IDS = {
    1454,   # U Series UI Design Guidelines
    1272,   # BLACKBOX 1.3.7 firmware for N8
    984,    # 修 all_3.0.9_4 连不上热点
    810,    # 静态 IP 配错导致进不了后台
    717,    # 如何改运行频率
    591,    # redir 矿池转发（英文）
    602,    # redir 矿池转发（中文）
    575,    # esp32 安装天线（英文）
    605,    # esp32 安装天线（中文）
    580,    # 降低 Wi-Fi 发射功率的 8 个理由（参考）
    283,    # 比特币地址生成算法（参考）
}

HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — BITDSK LAB</title>
<meta name="description" content="{desc}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="../css/style.css">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><rect width='32' height='32' rx='8' fill='%235b8cff'/><text x='16' y='23' font-size='18' text-anchor='middle' fill='white' font-family='sans-serif'>&#9670;</text></svg>">
</head>
<body>

<div class="sitebar">
 <div class="wrap row">
  <a class="brand" href="../index.html">
   <span class="logo">&#9670;</span>
   <span class="bname"><b>BITDSK</b> LAB <span>Docs</span></span>
  </a>
  <nav class="nav" id="nav">
   <a href="../index.html">Home</a>
   <a href="../firmware.html">Firmware</a>
   <a href="../flash.html">Flash</a>
   <a href="../docs/docs.html">Docs</a>
   <a href="../docs/api.html">API</a>
   <a href="../docs/version-comparison.html">Versions</a>
   <a href="index.html">Guides</a>
  </nav>
  <button class="hamburger" aria-label="Menu">&#9776;</button>
 </div>
</div>
"""

FOOT = """
<footer>
 <div class="wrap">
  <div class="frow">
   <div class="fcol">
    <b>BITDSK LAB</b>
    <p style="margin:6px 0 0">Archived from the original Bitdsk documentation site. Kept online so the guides stay reachable.</p>
   </div>
   <div class="links">
    <a href="../index.html">Home</a>
    <a href="../firmware.html">Firmware</a>
    <a href="../flash.html">Flash tool</a>
    <a href="index.html">All guides</a>
   </div>
  </div>
  <div class="fine">Archived guide — content reproduced as published; some links point to external sites.</div>
 </div>
</footer>

<button class="backtop" id="backtop" onclick="window.scrollTo({top:0,behavior:'smooth'})" title="Back to top">&#8593;</button>
<script src="../js/config.js"></script>
<script src="../js/site.js"></script>
</body>
</html>
"""

# /down/ 路径 -> 本地路径（与 build-data.py 保持一致）
DOWN_MAP = [
    ('/down/all/', 'firmware/n5-series/'),
    ('/down/c/', 'firmware/n8-series/'),
    ('/down/blackbox/', 'firmware/n8-series/blackbox/'),
    ('/down/manager/', 'firmware/tools/'),
    ('/down/gerber/', 'firmware/hardware/'),
    ('/down/n_update/', 'firmware/legacy/n_update/'),
    ('/down/n_www/', 'firmware/legacy/n_www/'),
    ('/down/n_miner/', 'firmware/legacy/n_miner/'),
    ('/down/d_update/', 'firmware/legacy/d_update/'),
    ('/down/d_www/', 'firmware/legacy/d_www/'),
    ('/down/d_miner/', 'firmware/legacy/d_miner/'),
    ('/down/d9/', 'firmware/legacy/d9/'),
    ('/down/n5/', 'firmware/legacy/n5/'),
]


# 个别文章的 WP slug 是中文的百分号编码，手动指定更易读的地址
SLUG_OVERRIDE = {
    605: 'esp32-antenna-install-cn',
    602: 'redir-pool-forwarding-cn',
}


def slug_of(post, used):
    if post['id'] in SLUG_OVERRIDE:
        used.add(SLUG_OVERRIDE[post['id']])
        return SLUG_OVERRIDE[post['id']]

    slug = (post.get('slug') or '').strip()
    if not slug:
        link = post.get('link') or ''
        path = urlparse(link).path.strip('/')
        slug = path.split('/')[-1] if path else ''
    if not slug or slug.isdigit() or slug == 'archives':
        slug = 'post-%d' % post['id']
    slug = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fff_-]+', '-', slug).strip('-').lower() or ('post-%d' % post['id'])
    # 纯中文/十六进制残留的 slug 用 id 兜底，标题在索引页仍完整显示
    if not re.search(r'[a-z]{3,}', slug):
        slug = 'post-%d' % post['id']
    base, n = slug, 2
    while slug in used:
        slug = '%s-%d' % (base, n)
        n += 1
    used.add(slug)
    return slug


# 原站图片名含中文，本地统一改成 ASCII（避免 CDN / 非 UTF-8 环境断链）
RENAME = {
    '2副本.jpg': '2-copy.jpg',
    'd10_3副本.jpg': 'd10_3-copy.jpg',
    'd13_4副本.jpg': 'd13_4-copy.jpg',
    'd10_1副本.jpg': 'd10_1-copy.jpg',
    '图片-1.png': 'image-1.png',
    '图片-2.png': 'image-2.png',
}


def ensure_image(url):
    """把原站图片下载到 images/ 下，返回站内相对路径（相对 blog/ 目录）"""
    p = urlparse(url)
    if p.netloc and 'bitdsk.org' not in p.netloc:
        return None
    path = p.path
    if not path.startswith('/wp-content/uploads/'):
        return None
    fn = path.rsplit('/', 1)[-1]
    if fn in RENAME:
        path = path[:-len(fn)] + RENAME[fn]
    local_rel = 'images' + path                     # images/wp-content/uploads/...
    disk = os.path.join(ROOT, local_rel.replace('/', os.sep))
    if not os.path.exists(disk):
        os.makedirs(os.path.dirname(disk), exist_ok=True)
        try:
            remote = SITE + urllib.parse.quote(path)
            req = urllib.request.Request(remote, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=40) as r, open(disk, 'wb') as f:
                f.write(r.read())
        except Exception as e:
            print('  ! 图片下载失败 %s (%s)' % (path, e))
            return SITE + path
    return '../' + local_rel


def rewrite(html, slug_map, post_ids):
    # 去掉 srcset / sizes，避免为每个尺寸单独下载
    html = re.sub(r'\s(srcset|sizes)="[^"]*"', '', html, flags=re.I)

    # 图片
    def img_repl(m):
        src = m.group(2)
        local = ensure_image(src)
        return m.group(1) + '"' + (local or src) + '"'
    html = re.sub(r'(<img[^>]*?\ssrc=)"([^"]+)"', img_repl, html, flags=re.I)

    # 站内文章链接
    def link_repl(m):
        href = m.group(2)
        u = urlparse(href)
        path = u.path.strip('/')
        seg = path.split('/')[-1]
        if seg.isdigit():
            target = slug_map.get(int(seg))
            if target:
                return m.group(1) + '"./' + target + '.html"'
        return m.group(1) + '"' + href + '"'
    html = re.sub(r'(<a[^>]*?\shref=)"([^"]+)"', link_repl, html, flags=re.I)

    # 固件下载 / 烧录入口
    for old, new in DOWN_MAP:
        # blog/ 在下一级目录，路径要加 ../
        html = html.replace(SITE + old, '../' + new).replace('"' + old, '"../' + new)

    html = html.replace(SITE + '/s1firware/', '../flash.html#s1')
    html = html.replace(SITE + '/u_touch_update_init/update_firmware', '../flash.html#u-series')
    html = html.replace(SITE + '/u_touch_update_init/u1_init', '../flash.html#u-series')
    html = html.replace(SITE + '/u_touch_update_init/u2_init', '../flash.html#u-series')
    html = html.replace(SITE + '/bitdsk-api-document', '../docs/api.html')
    return html


def clean_text(s):
    s = re.sub(r'<[^>]+>', '', s)
    for a, b in [('&amp;', '&'), ('&#8217;', "'"), ('&#8220;', '"'), ('&#8221;', '"'),
                 ('&#8211;', '-'), ('&#215;', 'x'), ('&nbsp;', ' '), ('&#039;', "'"),
                 ('&#8216;', "'"), ('&#8226;', '·'), ('&#8230;', '...')]:
        s = s.replace(a, b)
    return re.sub(r'\s+', ' ', s).strip()


def main():
    if not os.path.exists(SRC):
        sys.exit('缺少 %s' % SRC)
    with open(SRC, encoding='utf-8') as f:
        posts = json.load(f)

    total = len(posts)
    posts = [p for p in posts if p['id'] in KEEP_IDS]
    print('原始 %d 篇，按资源索引定位保留 %d 篇' % (total, len(posts)))

    os.makedirs(BLOG, exist_ok=True)
    used = set()
    slug_map = {}
    for p in posts:
        slug_map[p['id']] = slug_of(p, used)

    # 供 fix-docs.py 把原站 /archives/<id> 链接指到本地文章
    with open(os.path.join(ROOT, 'data', 'blog-slugs.json'), 'w', encoding='utf-8') as f:
        json.dump({str(k): v for k, v in slug_map.items()}, f, ensure_ascii=False, indent=1)

    written = 0
    for p in posts:
        slug = slug_map[p['id']]
        title = clean_text(p['title']['rendered'])
        body = p['content']['rendered']
        body = rewrite(body, slug_map, slug_map.keys())
        desc = clean_text(body)[:150] or title

        page = HEAD.format(title=title, desc=desc.replace('"', '&quot;'))
        page += '\n<div class="wrap docpage">\n'
        page += ' <div class="crumb"><a href="../index.html">Home</a> &rsaquo; <a href="index.html">Articles</a> &rsaquo; <span>%s</span></div>\n' % title
        page += ' <article class="doc">\n'
        page += '  <h1>%s</h1>\n' % title
        page += '  <div class="desc">%s</div>\n' % p['date'][:10]
        page += '  <div class="panel"><content>\n%s\n</content></div>\n' % body
        page += ' </article>\n</div>\n'
        page += FOOT

        with open(os.path.join(BLOG, slug + '.html'), 'w', encoding='utf-8') as f:
            f.write(page)
        written += 1
        print('  + %s/%s.html' % (os.path.basename(BLOG), slug))

    # 索引页
    items = []
    for p in sorted(posts, key=lambda x: x['date'], reverse=True):
        slug = slug_map[p['id']]
        title = clean_text(p['title']['rendered'])
        excerpt = clean_text(p['content']['rendered'])[:120]
        items.append(
            '   <a class="card" href="%s.html">\n'
            '    <div style="color:var(--faint);font-size:12px;font-family:var(--mono)">%s</div>\n'
            '    <h3>%s</h3>\n'
            '    <p>%s…</p>\n'
            '    <span class="arrow">Read &rarr;</span>\n'
            '   </a>' % (slug, p['date'][:10], title, excerpt))

    page = HEAD.format(title='Guides & reference', desc='Bitdsk operating guides, firmware notes and technical references.')
    page += """
<div class="hero compact"><div class="wrap">
 <span class="badge"><span class="dot"></span>Archive</span>
 <h1>Guides &amp; <span class="grad">reference</span></h1>
 <p class="lead">Operating guides and technical references from the original site. Product announcements and news were not carried over.</p>
</div></div>
<section class="block"><div class="wrap">
 <div class="grid">
%s
 </div>
</div></section>
""" % '\n'.join(items)
    page += FOOT

    with open(os.path.join(BLOG, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(page)
    print('  + %s/index.html  (%d 篇)' % (os.path.basename(BLOG), written))


if __name__ == '__main__':
    main()
