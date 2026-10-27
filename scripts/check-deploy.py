#!/usr/bin/env python3
"""
check-deploy.py — 部署前体检（面向 GitHub Pages）

本地是 Windows（不区分大小写），GitHub Pages 跑在 Linux（区分大小写）。
本地能打开的链接，推上去可能 404。这个脚本按"严格区分大小写"的方式
重新解析所有站内链接，并检查其它部署风险。

用法：
    python scripts/check-deploy.py
"""
import os
import re
import sys
import glob
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# GitHub 限制
MAX_FILE_MB = 100        # 单文件硬上限
WARN_FILE_MB = 50        # 单文件建议上限
REPO_WARN_MB = 1024      # 仓库建议上限

GREEN, RED, YELLOW, DIM, RESET = '\033[32m', '\033[31m', '\033[33m', '\033[2m', '\033[0m'


def all_files():
    out = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d != '.git']
        for fn in filenames:
            out.append(os.path.relpath(os.path.join(dirpath, fn), ROOT))
    return out


def exact_exists(rel_path):
    """按大小写精确判断文件是否存在（模拟 Linux 行为）"""
    cur = ROOT
    for part in rel_path.replace('\\', '/').split('/'):
        if part in ('', '.'):
            continue
        if part == '..':
            cur = os.path.dirname(cur)
            continue
        try:
            entries = os.listdir(cur)
        except OSError:
            return False
        if part not in entries:
            return False
        cur = os.path.join(cur, part)
    return os.path.exists(cur)


def main():
    problems = []
    warnings = []
    files = all_files()
    total = sum(os.path.getsize(os.path.join(ROOT, f)) for f in files)

    print('仓库文件 %d 个，合计 %.1f MB\n' % (len(files), total / 1048576))

    # ---------- 1. 链接严格大小写校验 ----------
    case_bad, missing_bad = [], []
    htmls = [f for f in files if f.lower().endswith(('.html', '.htm'))]
    for h in htmls:
        base = os.path.dirname(h)
        with open(os.path.join(ROOT, h), encoding='utf-8') as fh:
            s = fh.read()
        for attr, val in re.findall(r'(href|src)="([^"]+)"', s):
            v = val.strip()
            if not v or v.startswith(('http', '#', 'data:', 'mailto:', 'javascript:', '/')):
                continue
            v = v.split('#')[0].split('?')[0]
            if not v:
                continue
            rel = os.path.normpath(os.path.join(base, v)).replace('\\', '/')
            if rel.startswith('..'):
                continue
            if not exact_exists(rel):
                if os.path.exists(os.path.join(ROOT, rel)):
                    case_bad.append((h, val, rel))       # 本地能开，线上会 404
                else:
                    missing_bad.append((h, val))

    if case_bad:
        problems.append('大小写不一致的链接 %d 处（本地能开，GitHub 会 404）' % len(case_bad))
        for h, v, r in case_bad[:15]:
            print('%s✗ 大小写%s  %s → %s' % (RED, RESET, h, v))
    if missing_bad:
        problems.append('失效链接 %d 处' % len(missing_bad))
        for h, v in missing_bad[:15]:
            print('%s✗ 缺失%s  %s → %s' % (RED, RESET, h, v))
    if not case_bad and not missing_bad:
        print('%s✓%s 站内链接全部有效（严格区分大小写校验通过）' % (GREEN, RESET))

    # ---------- 2. 非 ASCII / 空格路径 ----------
    weird = [f for f in files if re.search(r'[^\x00-\x7F]', f) or ' ' in f]
    if weird:
        warnings.append('非 ASCII 或含空格的文件名 %d 个（换 CDN / 非 UTF-8 环境易断）' % len(weird))
        for f in weird[:12]:
            print('%s! 文件名%s  %s' % (YELLOW, RESET, f))
    else:
        print('%s✓%s 文件名全部为 ASCII 且无空格' % (GREEN, RESET))

    # ---------- 3. Unicode 归一化冲突（macOS NFD vs NFC） ----------
    nfc = {}
    for f in files:
        nfc.setdefault(unicodedata.normalize('NFC', f), []).append(f)
    dup = {k: v for k, v in nfc.items() if len(v) > 1}
    if dup:
        problems.append('Unicode 归一化后重名 %d 组' % len(dup))

    # ---------- 4. 体积 ----------
    big = [(f, os.path.getsize(os.path.join(ROOT, f))) for f in files
           if os.path.getsize(os.path.join(ROOT, f)) > WARN_FILE_MB * 1048576]
    if big:
        problems.append('超过 %dMB 的单文件 %d 个' % (WARN_FILE_MB, len(big)))
        for f, s in big:
            print('%s✗ 过大%s  %.1f MB  %s' % (RED, RESET, s / 1048576, f))
    if total > REPO_WARN_MB * 1048576:
        warnings.append('仓库超过 %dMB，建议把 firmware/ 拆到独立仓库' % REPO_WARN_MB)
    else:
        print('%s✓%s 体积 %.1f MB，单文件最大 %.1f MB，均在 GitHub Pages 限制内'
              % (GREEN, RESET, total / 1048576,
                 max(os.path.getsize(os.path.join(ROOT, f)) for f in files) / 1048576))

    # ---------- 5. Jekyll ----------
    if os.path.exists(os.path.join(ROOT, '.nojekyll')):
        print('%s✓%s .nojekyll 存在（关闭 Jekyll，避免下划线开头的路径被忽略）' % (GREEN, RESET))
    else:
        problems.append('缺少 .nojekyll')

    # ---------- 6. 不会被 Pages 发布的路径 ----------
    hidden = [f for f in files if any(p.startswith(('_', '.')) and p not in ('.nojekyll',)
                                      for p in f.split(os.sep))]
    if hidden:
        warnings.append('以下路径以 _ 或 . 开头，Pages 不会发布：' + ', '.join(hidden[:5]))

    # ---------- 7. 服务器端能力 ----------
    php = [f for f in files if f.lower().endswith('.php')]
    if php:
        problems.append('存在 PHP 文件 %d 个，GitHub Pages 不支持' % len(php))

    # ---------- 汇总 ----------
    print()
    if problems:
        print('%s阻断项 %d 个：%s' % (RED, len(problems), RESET))
        for p in problems:
            print('  - %s' % p)
    if warnings:
        print('%s提醒 %d 个：%s' % (YELLOW, len(warnings), RESET))
        for w in warnings:
            print('  - %s' % w)
    if not problems:
        print('%s可以直接部署到 GitHub Pages%s' % (GREEN, RESET))
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
