#!/usr/bin/env python3
"""Check all [[wikilinks]] in an Obsidian vault resolve to real files.

Usage: python check_wikilinks.py <vault_root>
Exit code 0 = zero broken links; 1 = broken links found (printed).
"""
import re
import sys
from pathlib import Path


def main() -> int:
    vault = Path(sys.argv[1]).resolve()
    if not vault.is_dir():
        print(f"not a directory: {vault}")
        return 2

    # Index every note by filename (Obsidian resolves shortest-unique names,
    # but a full path index covers both [[Note]] and [[dir/Note]] forms).
    notes = {}
    for p in vault.rglob("*.md"):
        if ".obsidian" in p.parts or ".git" in p.parts:
            continue
        notes.setdefault(p.stem, []).append(p.relative_to(vault))

    # A link resolves if the target name matches any note stem (basename match,
    # mirroring Obsidian's default shortest-path resolution).
    link_re = re.compile(r"\[\[([^\]|#]+?)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")
    fence_re = re.compile(r"```")
    broken = {}
    total_links = 0
    for p in sorted(vault.rglob("*.md")):
        if ".obsidian" in p.parts or ".git" in p.parts:
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        # Mask fenced code blocks (```...```) and inline code spans (`...`)
        # so Python like df[["Age"]] is not mistaken for a wikilink,
        # mirroring Obsidian's parser.
        masked, inside = [], False
        for line in text.splitlines():
            if fence_re.search(line):
                inside = not inside
                masked.append(line)
                continue
            masked.append("" if inside else line)
        visible = "\n".join(masked)
        visible = re.sub(r"`[^`\n]*`", "", visible)
        for m in link_re.finditer(visible):
            target = m.group(1).strip()
            # Strip an optional leading path: [[dir/Note]] -> match by basename too.
            base = target.split("/")[-1]
            total_links += 1
            if base not in notes:
                broken.setdefault(p.relative_to(vault), set()).add(target)

    print(f"vault: {vault}")
    print(f"notes indexed: {len(notes)}  wikilinks checked: {total_links}")
    if not broken:
        print("BROKEN WIKILINKS: 0")
        return 0
    count = 0
    for src, targets in sorted(broken.items()):
        for t in sorted(targets):
            print(f"BROKEN: [[{t}]]  referenced in {src}")
            count += 1
    print(f"BROKEN WIKILINKS: {count}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
