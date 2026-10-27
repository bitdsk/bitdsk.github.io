#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
brand-fix.py — 把全站页头的占位菱形替换为原站真实 logo，并补齐 favicon。

用法:
    python scripts/brand-fix.py            # 执行
    python scripts/brand-fix.py --dry-run  # 只报告不写入

做三件事:
1. 页头 .brand 里的 <span class="logo">&#9670;</span> + 文字块 → <img> 原站 logo
2. 把内联 SVG data-URI favicon → favicon.ico + PNG + apple-touch-icon
3. 缺 favicon 的页面（docs 下 9 个镜像页）在样式表后补上

可重复执行：已替换过的页面检测不到旧标记，会跳过。
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRY = '--dry-run' in sys.argv

BRAND_RE = re.compile(
    r'(<a class="brand" href="[^"]*">)(.*?)(</a>)',
    re.S,
)
OLD_LOGO_RE = re.compile(r'&#9670;|\u25c6')

# 内联 SVG favicon 的整行
ICON_LINE_RE = re.compile(r'^.*<link rel="icon" href="data:image/svg\+xml.*?>\s*$', re.M)


def prefix_for(path):
    """相对站点根的路径前缀。"""
    rel = os.path.relpath(path, ROOT).replace('\\', '/')
    depth = rel.count('/')
    return '../' * depth


def brand_html(href, p):
    return (
        f'{href}\n'
        f'   <img class="brand-logo" src="{p}images/logo.png"'
        f' srcset="{p}images/logo@2x.png 2x" alt="Bitdsk" width="102" height="26">\n'
        f'   <span class="bname">LAB <span>Docs</span></span>\n'
        f'  </a>'
    )


def icon_html(p):
    return (
        f'<link rel="icon" href="{p}favicon.ico" sizes="any">\n'
        f'<link rel="icon" type="image/png" sizes="32x32" href="{p}images/favicon-32.png">\n'
        f'<link rel="apple-touch-icon" href="{p}images/apple-touch-icon.png">'
    )


def main():
    changed_brand = []
    changed_icon = []
    skipped = []

    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if not d.startswith(('.', '_'))]
        for fn in filenames:
            if not fn.endswith('.html'):
                continue
            path = os.path.join(dirpath, fn)
            rel = os.path.relpath(path, ROOT).replace('\\', '/')
            p = prefix_for(path)

            with open(path, encoding='utf-8') as f:
                s = f.read()
            orig = s

            # ---- 1. 页头品牌区 ----
            m = BRAND_RE.search(s)
            if m and OLD_LOGO_RE.search(m.group(2)):
                href = m.group(1)
                s = s[:m.start()] + brand_html(href, p) + s[m.end():]
                changed_brand.append(rel)

            # ---- 2. favicon ----
            if ICON_LINE_RE.search(s):
                s = ICON_LINE_RE.sub(icon_html(p), s, count=1)
                changed_icon.append(rel)
            elif 'rel="icon"' not in s:
                # docs 镜像页：插在样式表之后
                m2 = re.search(r'^<link rel="stylesheet"[^>]*>\s*$', s, re.M)
                if m2:
                    s = s[:m2.end()] + '\n' + icon_html(p) + s[m2.end():]
                    changed_icon.append(rel)
                else:
                    skipped.append(rel)
                    continue

            if s != orig:
                if not DRY:
                    with open(path, 'w', encoding='utf-8', newline='') as f:
                        f.write(s)

    tag = '[dry-run] ' if DRY else ''
    print(f'{tag}品牌区替换 {len(changed_brand)} 个页面')
    for r in changed_brand:
        print('   ·', r)
    print(f'{tag}favicon 处理 {len(changed_icon)} 个页面')
    for r in changed_icon:
        print('   ·', r)
    if skipped:
        print(f'⚠ 找不到样式表、未插入 favicon: {len(skipped)}')
        for r in skipped:
            print('   ·', r)


if __name__ == '__main__':
    main()
