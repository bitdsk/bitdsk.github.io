#!/usr/bin/env python3
"""
fix-docs.py — 修整 docs/*.html（由 WordPress 导出的页面）

处理四类问题：
  1. 导航/页脚相对路径错误（docs/ 下应指向 ../index.html 等）
  2. 图片路径少了 wp-content/uploads/
  3. 原站转换残留的嵌套 <a> 标签
  4. ../_www./... 这类指向原站的外链 → 本地对应页面

可重复执行，不会叠加改动。

用法：
    python scripts/fix-docs.py
"""
import json
import os
import re
import glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, 'docs')

NAV = '''  <nav class="nav" id="nav">
   <a href="../index.html">Home</a>
   <a href="../firmware.html">Firmware</a>
   <a href="../flash.html">Flash</a>
   <a href="docs.html">Docs</a>
   <a href="api.html">API</a>
   <a href="version-comparison.html">Versions</a>
   <a href="../guides/index.html">Guides</a>
  </nav>'''

FOOT_LINKS = '''  <div class="links">
   <a href="../index.html">Home</a>
   <a href="../firmware.html">Firmware</a>
   <a href="../flash.html">Flash tool</a>
   <a href="docs.html">Docs</a>
   <a href="api.html">API</a>
   <a href="version-comparison.html">Versions</a>
  </div>'''

# 原站功能页 -> 本地对应页面
SITE_MAP = [
    ('../_www./archives/', '@BLOG@'),
    ('../_www./bitdsk-api-document', 'api.html'),
    ('../_www./s1firware/', '../flash.html#s1'),
    ('../_www./u_touch_update_init/update_firmware', '../flash.html#u-series'),
    ('../_www./u_touch_update_init/u1_init', '../flash.html#u-series'),
    ('../_www./u_touch_update_init/u2_init', '../flash.html#u-series'),
    ('../_www./u1_update_init/init', '../flash.html#u-series'),
    ('../_www./bitdsk-s1-for-esp32-firmware-cyd-esp32-2432s028', 'fw-s1.html'),
    ('../_www./ui-lab-for-u-series', '../blog/bitdsk-u-series-ui-design-guidelines.html'),
    ('../_www./u_ui_design/', '../blog/bitdsk-u-series-ui-design-guidelines.html'),
    ('../_www./', '../index.html'),
]


def load_slugs():
    p = os.path.join(ROOT, 'data', 'blog-slugs.json')
    if not os.path.exists(p):
        return {}
    with open(p, encoding='utf-8') as f:
        return json.load(f)


def fix(path, slugs):
    with open(path, encoding='utf-8') as f:
        s = f.read()
    orig = s

    # 1. 嵌套 <a href="<a href="X" ...>Y</a>" ...>  ->  <a href="X">
    s = re.sub(r'<a href="<a href="([^"]+)"[^>]*>[^<]*</a>"[^>]*>', r'<a href="\1">', s)
    # 1b. 修复上一版脚本误替换出的 ../index.htmlproduct/...
    s = re.sub(r'\.\./index\.htmlproduct/[^"]*', '../firmware.html', s)
    # 1c. 商品页已随原站下线，统一指向固件页
    s = re.sub(r'\.\./_www\./product/[^"]*', '../firmware.html', s)

    # 2. 图片路径补 wp-content/uploads/
    s = re.sub(r'(\.\./images/)(\d{4}/\d{2}/)', r'\1wp-content/uploads/\2', s)

    # 2b. 去掉 srcset/sizes —— 缩略图变体没有一起下载，留着会让浏览器选中 404 的地址
    s = re.sub(r'\s(srcset|sizes)="[^"]*"', '', s, flags=re.I)

    # 3. _www 外链映射
    for old, new in SITE_MAP:
        if new == '@BLOG@':
            def blog_repl(m):
                pid = m.group(1)
                slug = slugs.get(pid)
                return '../guides/%s.html' % slug if slug else '../guides/index.html'
            s = re.sub(re.escape(old) + r'(\d+)', blog_repl, s)
        else:
            s = s.replace(old, new)

    # 4. 导航与页脚
    s = re.sub(r'  <nav class="nav" id="nav">.*?</nav>', NAV, s, flags=re.S)
    s = re.sub(r'  <div class="links">\s*<a href="[^"]*">Firmware</a>.*?</div>', FOOT_LINKS, s, flags=re.S)

    # 5. 脚本：统一用 config + site（提供移动端菜单与返回顶部）
    s = s.replace('<script src="../js/main.js"></script>',
                  '<script src="../js/config.js"></script>\n<script src="../js/site.js"></script>')

    # 6. 去掉重复的标题后缀
    s = re.sub(r'<title>([^<]*?) &middot; BITDSK LAB &middot; BITDSK LAB</title>',
               r'<title>\1 — BITDSK LAB</title>', s)

    if s != orig:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(s)
        return True
    return False


def main():
    slugs = load_slugs()
    changed = 0
    for path in sorted(glob.glob(os.path.join(DOCS, '*.html'))):
        if fix(path, slugs):
            changed += 1
            print('  ~ %s' % os.path.basename(path))
    print('已修整 %d 个文档页' % changed)


if __name__ == '__main__':
    main()
