#!/usr/bin/env python3
"""
convert_to_monthly.py: 既存の単一 mastodon.org を月別レイアウトへ変換する。

使い方:
  python convert_to_monthly.py <path/to/mastodon.org> <Org Directory>

変換元フォーマット（年見出しあり、migrate_org.py 適用後）:
  * YYYY
  ** YYYY-MM MM月
  *** YYYY-MM-DD 曜日
  **** [YYYY-MM-DD 曜 HH:MM]

変換先: <Org Directory>/mastodon/YYYY/MM.org （各ファイルは同じ4階層をそのまま維持する）
添付ファイルは <Org Directory>/mastodon/YYYY/.attach/ へコピーする（元は変更・削除しない）。
"""
import datetime
import re
import shutil
import sys
from pathlib import Path

from src.org_writer import OrgNode, parse_org, serialize_org, monthly_paths

ATTACHMENT_LINK_RE = re.compile(r'\[\[attachment:([^\]]+)\]\]')
PROPERTY_ID_RE = re.compile(r':ID:\s+([a-f0-9\-]+)')


def _extract_toot_entry_id(day_node: OrgNode) -> str | None:
    """toot見出し(level4)直下のコンテンツ行から :PROPERTIES: :ID: を抽出する。"""
    m = PROPERTY_ID_RE.search("".join(day_node.content_lines))
    return m.group(1) if m else None


def _copy_attachments_for_toot(
    toot_node: OrgNode, source_attach_dir: Path, dest_attach_dir: Path
) -> list[tuple[Path, Path]]:
    entry_id = _extract_toot_entry_id(toot_node)
    if not entry_id:
        return []

    filenames = ATTACHMENT_LINK_RE.findall("".join(toot_node.content_lines))
    if not filenames:
        return []

    id_prefix = entry_id[:2]
    id_suffix = entry_id[2:]
    copied = []
    for filename in filenames:
        src_path = source_attach_dir / id_prefix / id_suffix / filename
        if not src_path.exists():
            print(f"Warning: attachment not found, skipping copy: {src_path}", file=sys.stderr)
            continue
        dest_path = dest_attach_dir / id_prefix / id_suffix / filename
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_path, dest_path)
        copied.append((src_path, dest_path))
    return copied


def convert(source_org_path: Path, org_directory: Path) -> None:
    with open(source_org_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    root = parse_org(lines)
    source_attach_dir = source_org_path.parent / ".attach"

    converted_months: list[str] = []
    skipped_months: list[str] = []
    copied_attachments: list[tuple[Path, Path]] = []

    for year_node in root.children:
        if year_node.level != 1:
            continue
        year_match = re.search(r'\* (\d{4})', year_node.title)
        if not year_match:
            continue
        year_str = year_match.group(1)

        for month_node in year_node.children:
            if month_node.level != 2:
                continue
            month_match = re.search(r'\*\* (\d{4})-(\d{2})', month_node.title)
            if not month_match:
                continue
            month_str = month_match.group(2)
            year_month = f"{year_str}-{month_str}"

            # このY-Mに対応する出力先パスは、月初のダミー日時から monthly_paths() で算出する
            probe_dt = datetime.datetime(int(year_str), int(month_str), 1)
            target_org_path, target_attach_dir = monthly_paths(org_directory, probe_dt)

            if target_org_path.exists():
                skipped_months.append(year_month)
                continue

            # 年ノード1つ・月ノード1つだけを含む新しいツリーを組み立てる
            new_root = OrgNode(0, "ROOT")
            new_year_node = OrgNode(1, year_node.title)
            new_year_node.children.append(month_node)
            new_root.children.append(new_year_node)

            target_org_path.parent.mkdir(parents=True, exist_ok=True)
            with open(target_org_path, 'w', encoding='utf-8') as out_f:
                out_f.writelines(serialize_org(new_root))

            # 添付ファイルのコピー
            for day_node in month_node.children:
                if day_node.level != 3:
                    continue
                for toot_node in day_node.children:
                    if toot_node.level != 4:
                        continue
                    copied_attachments.extend(
                        _copy_attachments_for_toot(toot_node, source_attach_dir, target_attach_dir)
                    )

            converted_months.append(year_month)

    _print_report(converted_months, skipped_months, copied_attachments)


def _print_report(
    converted_months: list[str],
    skipped_months: list[str],
    copied_attachments: list[tuple[Path, Path]],
) -> None:
    converted_str = ", ".join(sorted(converted_months)) if converted_months else "(none)"
    skipped_str = ", ".join(sorted(skipped_months)) if skipped_months else "(none)"

    print(f"Converted: {converted_str}")
    print(f"Skipped (already exists): {skipped_str}")
    print("Copied attachments:")
    if copied_attachments:
        for src, dest in copied_attachments:
            print(f"  {src} -> {dest}")
    else:
        print("  (none)")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python convert_to_monthly.py <path/to/mastodon.org> <Org Directory>")
        sys.exit(1)

    source_path = Path(sys.argv[1])
    if not source_path.exists():
        print(f"Error: source file not found: {source_path}", file=sys.stderr)
        sys.exit(1)

    convert(source_path, Path(sys.argv[2]))
