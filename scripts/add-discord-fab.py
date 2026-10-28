#!/usr/bin/env python3
"""Insert the floating Discord button into every page that lacks it.

The button is plain markup plus a class in css/style.css, so the same block
works at any directory depth. Existing pages are left untouched.

    python scripts/add-discord-fab.py            # apply
    python scripts/add-discord-fab.py --check    # report only
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP = {".git", "node_modules", "firmware", "js"}

ICON = (
    '<svg viewBox="0 0 24 24" width="22" height="22" fill="currentColor" aria-hidden="true">'
    '<path d="M20.317 4.37a19.79 19.79 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.865-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.058a.082.082 0 0 0 .031.056 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028c.462-.63.874-1.295 1.226-1.994a.076.076 0 0 0-.041-.106 13.1 13.1 0 0 1-1.872-.892.077.077 0 0 1-.008-.128c.126-.094.252-.192.372-.291a.074.074 0 0 1 .078-.01c3.928 1.793 8.18 1.793 12.061 0a.074.074 0 0 1 .079.009c.12.099.246.198.373.292a.077.077 0 0 1-.007.128 12.3 12.3 0 0 1-1.873.891.077.077 0 0 0-.04.107c.36.698.772 1.363 1.225 1.993a.076.076 0 0 0 .084.028 19.84 19.84 0 0 0 6.002-3.029.077.077 0 0 0 .032-.055c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.029zM8.02 15.331c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.211 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.211 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z"/></svg>'
)

FAB = f"""
<a class="discord-fab" href="https://discord.com/invite/qJ7zMcj88a" target="_blank" rel="noopener" aria-label="Join the Bitdsk Discord">
 {ICON}
 <span class="dfab-tip">Join us on Discord</span>
</a>
"""


def pages() -> list[Path]:
    out = []
    for p in ROOT.rglob("*.html"):
        if any(part in SKIP for part in p.relative_to(ROOT).parts):
            continue
        out.append(p)
    return sorted(out)


def main() -> int:
    check = "--check" in sys.argv
    todo, done = [], []
    for p in pages():
        text = p.read_text(encoding="utf-8")
        if "discord-fab" in text:
            done.append(p)
            continue
        marker = '<button class="backtop"'
        if marker not in text:
            print(f"skip (no anchor): {p.relative_to(ROOT)}")
            continue
        if not check:
            text = text.replace(marker, FAB.strip() + "\n\n" + marker, 1)
            p.write_text(text, encoding="utf-8")
        todo.append(p)

    verb = "would add" if check else "added"
    print(f"{verb} Discord button on {len(todo)} page(s), already present on {len(done)}")
    for p in todo:
        print("  +", p.relative_to(ROOT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
