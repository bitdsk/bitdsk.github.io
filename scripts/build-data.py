#!/usr/bin/env python3
"""
build-data.py — 从 docs/*.json 的原站表格生成 data/firmware.json

用途：以后新增固件版本时，把文件放进 firmware/<型号>/，在对应表格里补一行，
再跑一次本脚本即可重建数据清单。

用法：
    python scripts/build-data.py

输出：
    data/firmware.json   —— 站点唯一的固件数据源（前端按此渲染）
"""
import json
import os
import re
import hashlib
import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, 'docs')
OUT = os.path.join(ROOT, 'data', 'firmware.json')


# ---------------------------------------------------------------- 文本工具
def strip_tags(s):
    s = re.sub(r'<br\s*/?>', '\n', s, flags=re.I)
    s = re.sub(r'</p>', '\n', s, flags=re.I)
    s = re.sub(r'<[^>]+>', '', s)
    for a, b in [('&nbsp;', ' '), ('&amp;', '&'), ('&lt;', '<'), ('&gt;', '>'),
                 ('&quot;', '"'), ('&#8217;', "'"), ('&#8216;', "'"),
                 ('&#8220;', '"'), ('&#8221;', '"'), ('&#8211;', '-'),
                 ('&#8212;', '—'), ('&#39;', "'"), ('&#215;', 'x')]:
        s = s.replace(a, b)
    return s


def parse_date(raw):
    """兼容 M.D.YYYY 与 YYYY.M.D 两种格式，返回 YYYY-MM-DD"""
    nums = re.findall(r'\d+', raw)
    if len(nums) != 3:
        return None
    a, b, c = (int(x) for x in nums)
    if a > 1900:
        y, m, d = a, b, c
    else:
        m, d, y = a, b, c
    try:
        return datetime.date(y, m, d).isoformat()
    except ValueError:
        return None


def split_changes(text):
    """把说明文本切成条目列表，返回 (条目列表, 是否重要版本)"""
    lines = [l.strip(' ·•-\t') for l in text.split('\n')]
    important = False
    out = []
    for l in lines:
        if not l:
            continue
        if re.fullmatch(r'[*＊]?\s*important\s*[*＊]?', l, re.I):
            important = True
            continue
        if l.startswith('*') and 'important' in l.lower():
            important = True
            l = re.sub(r'[*＊]?\s*important\s*[*＊]?', '', l, flags=re.I).strip(' :：')
            if not l:
                continue
        # "1.Fixed xxx2.Fixed yyy" 这种被合并的，按序号再拆一次
        parts = re.split(r'(?<=[a-z\)\.])\s*(?=\d{1,2}[.、]\s*[A-Za-z])', l)
        for p in parts:
            p = re.sub(r'^\d{1,2}[.、]\s*', '', p.strip()).strip()
            if p:
                out.append(p)
    return out, important


# 原站 /down/ 路径 -> 本地按型号的路径
URL_PREFIX_MAP = [
    ('/down/all/', 'firmware/n5-series/'),
    ('/down/c/', 'firmware/n8-series/'),
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

# 下载按钮文案 -> 中文标签
LABEL_MAP = [
    ('watchdog_sec', 'Watchdog SEC build'),
    ('watchdog', 'Watchdog build'),
    ('nowatchdog', 'No-watchdog build'),
    ('www_down', 'www partition'),
    ('miner_down', 'miner partition'),
    ('miner_dow', 'miner partition'),
]


def normalize_href(href):
    """把原站绝对链接 / 相对链接统一成本地站内路径；非文件链接返回 (None, 原链接)"""
    h = href.strip()
    h = re.sub(r'^https?://(www\.)?bitdsk\.org', '', h)
    h = re.sub(r'^\.\./', '', h)

    for prefix, local in URL_PREFIX_MAP:
        if h.startswith(prefix):
            h = local + h[len(prefix):]
            break

    if h.startswith(('firmware/', 'doc/', 'docs/')):
        return h, None
    return None, ('https://www.bitdsk.org' + h if h.startswith('/') else h)


def clean_label(text, default='Download'):
    t = strip_tags(text).strip()
    t = re.sub(r'\(ver:[^)]*\)', '', t, flags=re.I)
    t = re.sub(r'\s+', '', t)
    low = t.lower()
    for key, cn in LABEL_MAP:
        if key in low:
            return cn
    if low in ('down', 'download', '下载'):
        return default
    return t or default


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def human_size(n):
    if n >= 1 << 20:
        return '%.1f MB' % (n / (1 << 20))
    return '%d KB' % max(1, round(n / 1024))


def describe_file(rel_path):
    """给站内相对路径补齐 size / bytes / sha256"""
    disk = os.path.join(ROOT, rel_path.replace('/', os.sep))
    if not os.path.exists(disk):
        return None
    size = os.path.getsize(disk)
    return {'path': rel_path, 'bytes': size, 'size': human_size(size), 'sha256': sha256_of(disk)}


# ---------------------------------------------------------------- 解析表格
def parse_table(doc_json, default_label='Download', flash_versions=()):
    """返回 [{version, date, changes[], important, files[], status, noteLink}]，按日期倒序"""
    with open(os.path.join(DOCS, doc_json), encoding='utf-8') as f:
        d = json.load(f)
    html = d.get('raw_html') or d.get('html') or ''
    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.S)
    out = []
    for r in rows:
        cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', r, re.S)
        if len(cells) < 3 or 'Time' in strip_tags(cells[0]):
            continue
        date = parse_date(strip_tags(cells[0]))
        version = strip_tags(cells[1]).strip()
        if not version or not date:
            continue

        down_cell = cells[3] if len(cells) > 3 else ''
        files, note_link = [], None
        for href, text in re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', down_cell, re.S):
            path, note = normalize_href(href)
            if path:
                info = describe_file(path)
                if info:
                    info['label'] = clean_label(text, default_label)
                    files.append(info)
            elif note and not note_link:
                note_link = note

        down_text = strip_tags(down_cell).strip().lower()
        struck = bool(re.search(r'<s[ >]', down_cell, re.I))
        if files:
            status = 'available'
        elif struck:
            status = 'withdrawn'
        elif version.lower() in flash_versions:
            status = 'flash'          # 通过浏览器烧录页提供
        elif 'abandon' in down_text or 'follow' in down_text:
            status = 'abandoned'
        elif 'expire' in down_text:
            status = 'expired'
        else:
            status = 'none'

        changes, important = split_changes(strip_tags(cells[2]))
        item = {
            'version': version,
            'date': date,
            'changes': changes,
            'important': important,
            'status': status,
            'files': files,
        }
        if note_link:
            item['noteLink'] = note_link
        out.append(item)

    out.sort(key=lambda x: x['date'], reverse=True)
    return out


def build_flashers(model):
    """把 esp-web-tools manifest 展开成前端可展示的分区列表"""
    result = []
    for fl in model.get('flashers', []):
        mpath = os.path.join(ROOT, fl['manifest'].replace('/', os.sep))
        if not os.path.exists(mpath):
            continue
        with open(mpath, encoding='utf-8') as f:
            man = json.load(f)
        parts = []
        for build in man.get('builds', []):
            for p in build.get('parts', []):
                rel = os.path.dirname(fl['manifest']).replace(os.sep, '/') + '/' + p['path']
                info = describe_file(rel)
                if info:
                    info['offset'] = p['offset']
                    parts.append(info)
        item = dict(fl)
        item['parts'] = parts
        item['bytes'] = sum(p['bytes'] for p in parts)
        item['size'] = human_size(item['bytes'])
        result.append(item)
    return result


# ---------------------------------------------------------------- 型号定义
MODELS = [
    {
        'id': 'n5-series',
        'name': 'N5 Series',
        'title': 'N5.Rex / N5.Rexi / D12 / D12-T',
        'chips': ['N5.Rex', 'N5.Rexi', 'D12', 'D12-T'],
        'summary': '1.9" colour-screen single-ASIC SHA256 miner. The main production line.',
        'status': 'active',
        'statusText': 'In production',
        'family': 'ASIC · SHA256',
        'method': 'ota',
        'methodText': 'Web UI (OTA)',
        'docPage': 'docs/fw-n5d12.html',
        'specs': [
            ['Screen', '1.9" colour'],
            ['Hashrate', '200G – 1T'],
            ['Power', '≈8.9 – 24W'],
            ['Supply', 'DC 12V'],
        ],
        'source': 'fw-n5d12.json',
    },
    {
        'id': 'n8-series',
        'name': 'N8 Series',
        'title': 'N8 / N8-T / N5.Rexi-T',
        'chips': ['N8', 'N8-T', 'N5.Rexi-T'],
        'summary': '0.91" monochrome mini miner — low power, pocket sized.',
        'status': 'active',
        'statusText': 'In production',
        'family': 'ASIC · SHA256',
        'method': 'ota',
        'methodText': 'Web UI (OTA)',
        'docPage': 'docs/fw-n8.html',
        'specs': [
            ['Screen', '0.91" mono'],
            ['Hashrate', '200G'],
            ['Power', '≈8.9W'],
            ['Supply', 'Type-C 5V/3A'],
        ],
        'source': 'fw-n8.json',
        'extraFiles': [
            {'label': 'BLACKBOX debug build (C_1.3.7)', 'path': 'firmware/n8-series/blackbox/bitdsk-miner-c.1.3.7_blackbox.zip'},
        ],
    },
    {
        'id': 'u-series',
        'name': 'U Series',
        'title': 'U1 Touch / U2 Touch',
        'chips': ['U1 Touch', 'U2 Touch'],
        'summary': '2.8" touchscreen models. Flash images live in the separate Flash Tool repository; the OTA image and UI themes are hosted here.',
        'status': 'active',
        'statusText': 'In production',
        'family': 'ASIC · SHA256',
        'method': 'flash',
        'methodText': 'Browser flash (USB)',
        'flashPage': '#u-series',
        # 烧录包（u1/u2 的 bin + manifest）已迁到独立仓库 bitdsk-flash。
        # 主站只保留索引条目 + OTA 单镜像与主题背景这类常规下载。
        'flashExternal': True,
        'latestVersion': 'v_1.5.2',
        'docPage': 'docs/fw-u1u2.html',
        'specs': [
            ['Screen', '2.8" touch'],
            ['Hashrate', 'U1 200G · U2 1100–1500G'],
            ['Power', '≈22W · ≈27W'],
            ['Supply', 'DC / Type-C'],
        ],
        'source': 'fw-u1u2.json',
        'extraFiles': [
            {'label': 'U1/U2 single image (OTA)', 'path': 'firmware/u-series/ota/v_1.5.2/bitdsk-miner.bin'},
            {'label': 'UI background — Bit Horizon', 'path': 'firmware/u-series/themes/Bit_Horizon_bg.bin'},
            {'label': 'UI background — VioletPulse', 'path': 'firmware/u-series/themes/VioletPulse_bg.bin'},
        ],
    },
    {
        'id': 's1',
        'name': 'S1',
        'title': 'S1 (ESP32-CYD 2432S028)',
        'chips': ['S1'],
        'summary': 'Display-only terminal with no ASIC, running on the generic ESP32-2432S028 board. The full flash image lives in the Flash Tool repository.',
        'status': 'active',
        'statusText': 'In production',
        'family': 'ESP32 · 无 ASIC',
        'method': 'flash',
        'methodText': 'Browser flash (USB)',
        'flashPage': '#s1',
        # S1 只有烧录包，已整体迁到 bitdsk-flash，主站保留索引。
        'flashExternal': True,
        'latestVersion': 'v_1.5',
        'docPage': 'docs/fw-s1.html',
        'specs': [
            ['MCU', 'ESP32 dual-core'],
            ['Screen', '2.8" touch'],
            ['Hashrate', '600k – 800k H/s'],
            ['Supply', 'USB 5V'],
        ],
        'source': 'fw-s1.json',
    },
    {
        'id': 'legacy',
        'name': 'Legacy',
        'title': 'Discontinued / legacy boards',
        'chips': ['N5.lite', 'N5.chi', 'Q2', 'H0', 'Y5', 'M0', 'D9', 'D10', 'D11', 'D13', 'Y7'],
        'summary': 'Archived firmware for discontinued boards, kept in the original N-series, D-series and early-N5 tables.',
        'status': 'legacy',
        'statusText': 'Discontinued',
        'family': 'ASIC · archive',
        'method': 'ota',
        'methodText': 'Web UI (OTA)',
        'docPage': 'docs/fw-other.html',
        'specs': [
            ['N series', 'N5.lite / N5.chi / Q2 / H0 / Y5 / M0'],
            ['D series', 'D9 / D10 / D11 / D13 / Y7'],
            ['Status', 'Out of production — archive only'],
        ],
        'source': 'fw-other.json',
    },
    {
        'id': 'tools',
        'name': 'PC Tools',
        'title': 'PC batch manager',
        'chips': ['Windows'],
        'summary': 'Windows batch manager for monitoring and upgrading several miners at once.',
        'status': 'tool',
        'statusText': 'Tool',
        'family': 'Windows tool',
        'method': 'download',
        'methodText': 'Direct download',
        'docPage': 'docs/miner-tools.html',
        'specs': [
            ['Platform', 'Windows'],
            ['Purpose', 'Batch manage / batch upgrade'],
            ['Requires', 'Miner firmware ≥ all_3.0.0'],
        ],
        'source': 'miner-tools.json',
        'fileLabel': 'Download',
    },
]


def main():
    # 固件已拆到独立仓库（bitdsk-site 只做索引）。
    # 本地没有 firmware/ 时直接退出，避免把所有 files 清空、把 data/firmware.json 写坏。
    if not os.path.isdir(os.path.join(ROOT, 'firmware')):
        print('firmware/ 目录不存在 —— 固件已拆到 Bitdsk_Miner_Archive 仓库。')
        print('data/firmware.json 保持不变，本站通过 js/config.js 的 firmwareBase 指向外部仓库。')
        print('确实要重新生成的话：先把固件仓库检出到 firmware/，再跑本脚本。')
        return

    models_out = []
    total_files = 0
    total_bytes = 0

    for m in MODELS:
        # ---- 烧录包已迁到独立仓库（bitdsk-flash）的型号 ----
        # 主站只保留索引条目：不扫描本地 bin、不生成下载链接，避免死链。
        if m.get('flashExternal'):
            entry = {k: v for k, v in m.items() if k != 'source'}
            entry['releases'] = []
            entry['flashers'] = []
            entry['count'] = 0
            entry['latest'] = m.get('latestVersion')
            entry['latestDate'] = None
            # u-series 的 OTA 单镜像与主题背景仍托管在主站，属于常规下载
            if m.get('extraFiles'):
                extras = []
                for e in m['extraFiles']:
                    info = describe_file(e['path'])
                    if info:
                        info['label'] = e['label']
                        extras.append(info)
                        total_files += 1
                        total_bytes += info['bytes']
                        entry['count'] += 1
                entry['extraFiles'] = extras
            models_out.append(entry)
            continue

        flash_versions = {fl['version'].lower() for fl in m.get('flashers', [])}
        releases = parse_table(
            m['source'],
            default_label=m.get('fileLabel', 'Download'),
            flash_versions=flash_versions,
        )
        for r in releases:
            for f in r['files']:
                total_files += 1
                total_bytes += f['bytes']

        entry = {k: v for k, v in m.items() if k != 'source'}
        entry['releases'] = releases
        entry['count'] = sum(len(r['files']) for r in releases)
        latest = next((r for r in releases if r['files']), None)
        entry['latest'] = latest['version'] if latest else None
        entry['latestDate'] = latest['date'] if latest else None

        if m.get('flashers'):
            entry['flashers'] = build_flashers(m)
            for fl in entry['flashers']:
                total_files += len(fl['parts'])
                total_bytes += fl['bytes']
                entry['count'] += len(fl['parts'])
            if not entry['latest'] and entry['flashers']:
                entry['latest'] = entry['flashers'][0]['version']
                hit = next((r for r in releases
                            if r['version'].lower() == entry['latest'].lower()), None)
                entry['latestDate'] = hit['date'] if hit else None

        if m.get('extraFiles'):
            extras = []
            for e in m['extraFiles']:
                info = describe_file(e['path'])
                if info:
                    info['label'] = e['label']
                    extras.append(info)
                    total_files += 1
                    total_bytes += info['bytes']
                    entry['count'] += 1
            entry['extraFiles'] = extras

        models_out.append(entry)

    # 硬件图纸等附加资源
    extras = []
    hw_dir = os.path.join(ROOT, 'firmware', 'hardware')
    for fn in sorted(os.listdir(hw_dir)) if os.path.isdir(hw_dir) else []:
        p = os.path.join(hw_dir, fn)
        if os.path.isfile(p):
            size = os.path.getsize(p)
            extras.append({
                'name': fn,
                'label': 'PCB Gerber files',
                'path': 'firmware/hardware/' + fn,
                'size': human_size(size),
                'bytes': size,
                'sha256': sha256_of(p),
            })
            total_files += 1
            total_bytes += size

    data = {
        'site': {
            'name': 'BITDSK LAB',
            'tagline': 'SHA256 miner firmware & documentation archive',
            'generated': datetime.date.today().isoformat(),
            'firmwareBase': '',
        },
        'stats': {
            'files': total_files,
            'bytes': total_bytes,
            'size': human_size(total_bytes),
            'models': len(models_out),
        },
        'models': models_out,
        'extras': extras,
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)

    print('已生成 %s' % OUT)
    print('  型号 %d 个 / 文件 %d 个 / 合计 %s'
          % (len(models_out), total_files, human_size(total_bytes)))
    for m in models_out:
        print('  - %-11s %2d 个文件  最新 %s'
              % (m['id'], m['count'],
                 m['latest'] or '-'))


if __name__ == '__main__':
    main()
