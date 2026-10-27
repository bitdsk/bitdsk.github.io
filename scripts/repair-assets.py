#!/usr/bin/env python3
"""
repair-assets.py — 校验并修复二进制资源

之前的批量下载把图片当文本解码，导致文件头被替换成 EF BF BD，图片全部失效。
本脚本按文件头校验 images/、doc/、firmware/ 下的文件，损坏的从原站重新下载。

用法：
    python scripts/repair-assets.py          # 只检查
    python scripts/repair-assets.py --fix    # 检查并重新下载损坏文件
"""
import os
import sys
import glob
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://www.bitdsk.org'

SIGS = [
    b'\xff\xd8\xff',      # jpg
    b'\x89PNG',           # png
    b'GIF8',              # gif
    b'RIFF',              # webp
    b'%PDF',              # pdf
    b'PK\x03\x04',        # zip
    b'PK\x05\x06',        # zip 空档
    b'\x1f\x8b',          # gzip（部分 .zip 实际是 gz）
    b'<?xml', b'<svg',    # svg
    b'\xe9',              # esp32 镜像
]

# 原始分区数据没有统一魔数，不做校验
SKIP_EXT = ('.bin',)


def ok(path):
    if path.lower().endswith(SKIP_EXT):
        return True
    with open(path, 'rb') as f:
        head = f.read(8)
    return any(head.startswith(s) for s in SIGS)


def remote_url(path):
    """把站内路径还原成原站 URL"""
    rel = path.replace(os.sep, '/')
    if rel.startswith('images/wp-content/uploads/'):
        return SITE + '/' + rel[len('images/'):]
    if rel.startswith('doc/'):
        return SITE + '/' + rel
    return None


def main():
    fix = '--fix' in sys.argv
    targets = []
    for pat in ('images/**/*', 'doc/*.pdf', 'firmware/**/*.zip', 'firmware/**/*.bin'):
        targets += [p for p in glob.glob(os.path.join(ROOT, pat), recursive=True) if os.path.isfile(p)]

    broken = [p for p in targets if not ok(p)]
    print('共 %d 个文件，损坏 %d 个' % (len(targets), len(broken)))

    if not broken:
        return

    if not fix:
        for p in broken[:20]:
            print('  损坏 %s' % os.path.relpath(p, ROOT))
        print('加 --fix 参数可自动重新下载')
        return

    fixed = failed = 0
    for p in broken:
        rel = os.path.relpath(p, ROOT)
        url = remote_url(rel)
        if not url:
            print('  ? 无法定位原地址 %s' % rel)
            failed += 1
            continue
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
            with open(p, 'wb') as f:
                f.write(data)
            if ok(p):
                fixed += 1
                print('  + %s (%d KB)' % (rel, len(data) // 1024))
            else:
                print('  ! %s 下载后仍无效（原站可能已返回错误页）' % rel)
                failed += 1
        except Exception as e:
            print('  ! %s -> %s' % (rel, e))
            failed += 1

    print('修复 %d 个，失败 %d 个' % (fixed, failed))


if __name__ == '__main__':
    main()
