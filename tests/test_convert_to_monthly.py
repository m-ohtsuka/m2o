import subprocess
import sys
from pathlib import Path

from src.org_writer import parse_org

FIXTURE_ORG = Path(__file__).parent / "fixtures" / "sample_mastodon.org"
FIXTURE_ATTACH = Path(__file__).parent / "fixtures" / ".attach"


def _copy_fixture(tmp_path):
    """フィクスチャを tmp_path にコピーし、変換元パスを返す（元のフィクスチャは変更しない）。"""
    import shutil

    source_org = tmp_path / "source" / "mastodon.org"
    source_org.parent.mkdir(parents=True)
    shutil.copy2(FIXTURE_ORG, source_org)
    shutil.copytree(FIXTURE_ATTACH, source_org.parent / ".attach")
    return source_org


def _run_converter(source_org, org_directory):
    result = subprocess.run(
        [sys.executable, "convert_to_monthly.py", str(source_org), str(org_directory)],
        cwd=Path(__file__).parent.parent,
        capture_output=True,
        text=True,
    )
    return result


def _count_toots(org_path):
    with open(org_path, encoding="utf-8") as f:
        lines = f.readlines()
    root = parse_org(lines)
    count = 0
    for year in root.children:
        for month in year.children:
            for day in month.children:
                count += len(day.children)
    return count


def test_convert_creates_monthly_files_with_matching_content(tmp_path):
    source_org = _copy_fixture(tmp_path)
    org_directory = tmp_path / "out"

    result = _run_converter(source_org, org_directory)
    assert result.returncode == 0, result.stderr

    dec_path = org_directory / "mastodon" / "2025" / "12.org"
    jan_path = org_directory / "mastodon" / "2026" / "01.org"
    feb_path = org_directory / "mastodon" / "2026" / "02.org"

    assert dec_path.exists()
    assert jan_path.exists()
    assert feb_path.exists()

    dec_content = dec_path.read_text(encoding="utf-8")
    assert "Last toot of 2025." in dec_content
    # 各月ファイルの先頭にATTACH_DIRプロパティが挿入されている
    assert dec_content.startswith("#+PROPERTY: ATTACH_DIR images/\n")

    jan_content = jan_path.read_text(encoding="utf-8")
    assert jan_content.startswith("#+PROPERTY: ATTACH_DIR images/\n")
    assert "Hello from January." in jan_content
    assert "Photo toot in January." in jan_content

    feb_content = feb_path.read_text(encoding="utf-8")
    assert "#+BEGIN_QUOTE" in feb_content
    assert "Original boosted content in February." in feb_content
    assert "#+END_QUOTE" in feb_content


def test_convert_preserves_total_toot_count(tmp_path):
    source_org = _copy_fixture(tmp_path)
    org_directory = tmp_path / "out"

    source_count = _count_toots(source_org)
    result = _run_converter(source_org, org_directory)
    assert result.returncode == 0, result.stderr

    total = 0
    for org_path in (org_directory / "mastodon").rglob("*.org"):
        total += _count_toots(org_path)

    assert total == source_count


def test_convert_copies_attachments_and_preserves_source(tmp_path):
    source_org = _copy_fixture(tmp_path)
    org_directory = tmp_path / "out"
    source_bytes_before = source_org.read_bytes()
    source_attach_file = (
        source_org.parent / ".attach" / "aa" / "bbccdd-1111-2222-3333-444455556666" / "toot_1001_1.jpg"
    )
    source_attach_bytes_before = source_attach_file.read_bytes()

    result = _run_converter(source_org, org_directory)
    assert result.returncode == 0, result.stderr

    # 変換先はID分割なしでimages/直下にフラットに保存される
    copied_path = org_directory / "mastodon" / "2026" / "images" / "toot_1001_1.jpg"
    assert copied_path.exists()
    assert copied_path.read_bytes() == source_attach_bytes_before

    # 変換元は非破壊であること（FR-007, FR-011）
    assert source_org.read_bytes() == source_bytes_before
    assert source_attach_file.read_bytes() == source_attach_bytes_before

    assert "Copied attachments:" in result.stdout
    assert str(source_attach_file) in result.stdout
    assert str(copied_path) in result.stdout


def test_convert_reports_converted_and_skipped_months(tmp_path):
    source_org = _copy_fixture(tmp_path)
    org_directory = tmp_path / "out"

    result = _run_converter(source_org, org_directory)
    assert result.returncode == 0, result.stderr

    assert "Converted:" in result.stdout
    assert "2025-12" in result.stdout
    assert "2026-01" in result.stdout
    assert "2026-02" in result.stdout
    assert "Skipped (already exists): (none)" in result.stdout


def test_convert_skips_existing_month_without_overwriting(tmp_path):
    source_org = _copy_fixture(tmp_path)
    org_directory = tmp_path / "out"

    # 2026-01 を先に「ダミー内容」で作成しておく（競合させる）
    existing_jan = org_directory / "mastodon" / "2026" / "01.org"
    existing_jan.parent.mkdir(parents=True)
    sentinel_content = "* 2026\n** 2026-01 1月\nSENTINEL: do not overwrite\n"
    existing_jan.write_text(sentinel_content, encoding="utf-8")

    result = _run_converter(source_org, org_directory)
    assert result.returncode == 0, result.stderr

    # 競合した2026-01は変更されていない（FR-006, SC-004）
    assert existing_jan.read_text(encoding="utf-8") == sentinel_content

    # 競合しない2025-12, 2026-02は正常に変換される
    dec_path = org_directory / "mastodon" / "2025" / "12.org"
    feb_path = org_directory / "mastodon" / "2026" / "02.org"
    assert dec_path.exists()
    assert feb_path.exists()


def test_convert_lists_skipped_months_in_report(tmp_path):
    source_org = _copy_fixture(tmp_path)
    org_directory = tmp_path / "out"

    existing_jan = org_directory / "mastodon" / "2026" / "01.org"
    existing_jan.parent.mkdir(parents=True)
    existing_jan.write_text("SENTINEL\n", encoding="utf-8")

    result = _run_converter(source_org, org_directory)
    assert result.returncode == 0, result.stderr

    assert "Skipped (already exists): 2026-01" in result.stdout

    converted_line = next(
        line for line in result.stdout.splitlines() if line.startswith("Converted:")
    )
    assert "2026-01" not in converted_line
    assert "2025-12" in converted_line
    assert "2026-02" in converted_line
