#!/usr/bin/env python3
"""
migrate_org.py: 既存の mastodon.org を新フォーマット（トップレベル年見出し）に変換する。

変換前:
  ** YYYY-MM MM月
  *** YYYY-MM-DD 曜日
  **** [YYYY-MM-DD 曜 HH:MM]

変換後:
  * YYYY
  ** YYYY-MM MM月
  *** YYYY-MM-DD 曜日
  **** [YYYY-MM-DD 曜 HH:MM]
"""
import re
import sys
from pathlib import Path
from src.org_writer import parse_org, serialize_org, OrgNode, insert_sorted

def migrate(org_path: Path) -> None:
    print(f"Reading: {org_path}")
    with open(org_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    root = parse_org(lines)

    # root 直下の月ノード (level == 2) を年ごとにグループ化して year_node に移動する
    new_root = OrgNode(0, "ROOT")
    # root の content_lines (ファイル先頭のコメント等) はそのまま保持
    new_root.content_lines = root.content_lines

    year_nodes: dict[str, OrgNode] = {}

    for child in root.children:
        if child.level == 2:
            # ** YYYY-MM MM月 -> 年を抽出
            m = re.search(r'\*\* (\d{4})-\d{2}', child.title)
            if m:
                year_str = m.group(1)
                if year_str not in year_nodes:
                    yn = OrgNode(1, f"* {year_str}")
                    year_nodes[year_str] = yn
                    insert_sorted(new_root, yn)
                year_nodes[year_str].children.append(child)
                continue
        # level != 2 (何らかの level 1 ノードなど) はそのまま残す
        new_root.children.append(child)

    new_lines = serialize_org(new_root)

    # バックアップ
    backup_path = org_path.with_suffix('.org.bak')
    org_path.rename(backup_path)
    print(f"Backup saved: {backup_path}")

    with open(org_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    print(f"Migration complete: {org_path}")
    print(f"  Year nodes created: {sorted(year_nodes.keys())}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python migrate_org.py <path/to/mastodon.org>")
        sys.exit(1)
    migrate(Path(sys.argv[1]))
