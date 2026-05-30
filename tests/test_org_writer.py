import datetime
from pathlib import Path
from src.org_writer import OrgWriter, parse_org, serialize_org

def test_org_parsing_and_serialization():
    org_lines = [
        "** 2026-05 5月\n",
        "*** 2026-05-02 土曜日\n",
        "**** [2026-05-02 土 17:04]\n",
        "Hello World\n",
        "\n",
    ]
    root = parse_org(org_lines)
    assert len(root.children) == 1
    assert root.children[0].level == 2
    assert root.children[0].children[0].level == 3
    assert root.children[0].children[0].children[0].level == 4

    serialized = serialize_org(root)
    assert serialized == org_lines

def test_org_writer_add_toot(tmp_path):
    org_file = tmp_path / "test.org"
    attach_dir = tmp_path / ".attach"
    
    writer = OrgWriter(org_file, attach_dir)
    
    # JST (+09:00) タイムゾーンの日時
    tz_jst = datetime.timezone(datetime.timedelta(hours=9))
    dt1 = datetime.datetime(2026, 5, 2, 17, 4, tzinfo=tz_jst)
    
    writer.add_toot("11111", dt1, "First toot content", [])
    
    assert org_file.exists()
    content = org_file.read_text(encoding='utf-8')
    assert "** 2026-05 5月" in content
    assert "*** 2026-05-02 土曜日" in content
    assert "**** [2026-05-02 土 17:04]" in content
    assert "First toot content" in content

    # 2つ目のtootを追加（同じ日、より古い時間。時系列の昇順でソートされることをテスト）
    dt2 = datetime.datetime(2026, 5, 2, 16, 0, tzinfo=tz_jst)
    writer.add_toot("11112", dt2, "Second toot content (earlier)", [])

    content_lines = org_file.read_text(encoding='utf-8').splitlines()
    
    idx_16 = -1
    idx_17 = -1
    for i, line in enumerate(content_lines):
        if "[2026-05-02 土 16:00]" in line:
            idx_16 = i
        if "[2026-05-02 土 17:04]" in line:
            idx_17 = i
            
    assert idx_16 != -1
    assert idx_17 != -1
    assert idx_16 < idx_17  # 16:00 が 17:04 より上に配置されていること

def test_org_writer_different_months(tmp_path):
    org_file = tmp_path / "test.org"
    attach_dir = tmp_path / ".attach"
    
    writer = OrgWriter(org_file, attach_dir)
    tz_jst = datetime.timezone(datetime.timedelta(hours=9))
    
    dt_may = datetime.datetime(2026, 5, 10, 10, 0, tzinfo=tz_jst)
    dt_apr = datetime.datetime(2026, 4, 20, 12, 0, tzinfo=tz_jst)
    
    writer.add_toot("22222", dt_may, "May content", [])
    writer.add_toot("22221", dt_apr, "April content", [])
    
    content = org_file.read_text(encoding='utf-8')
    
    # 4月の見出しが5月の見出しより上に位置しているか確認
    lines = content.splitlines()
    idx_apr = -1
    idx_may = -1
    for i, line in enumerate(lines):
        if "** 2026-04 4月" in line:
            idx_apr = i
        if "** 2026-05 5月" in line:
            idx_may = i
            
    assert idx_apr != -1
    assert idx_may != -1
    assert idx_apr < idx_may

def test_org_writer_add_toot_with_images(tmp_path):
    from unittest.mock import MagicMock, patch
    import re
    
    org_file = tmp_path / "test.org"
    attach_dir = tmp_path / ".attach"
    
    writer = OrgWriter(org_file, attach_dir)
    tz_jst = datetime.timezone(datetime.timedelta(hours=9))
    dt = datetime.datetime(2026, 5, 2, 17, 4, tzinfo=tz_jst)
    
    media_attachments = [
        {
            'type': 'image',
            'url': 'https://example.com/media/test_image.jpg',
            'remote_url': 'https://example.com/media/test_image.jpg'
        }
    ]
    
    # requests.get の応答をモック化
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.iter_content = lambda chunk_size: [b"fake_image_data"]
    
    with patch('requests.get', return_value=mock_response) as mock_get:
        writer.add_toot("11113", dt, "Toot with image content", media_attachments)
        
        mock_get.assert_called_once_with('https://example.com/media/test_image.jpg', headers={'User-Agent': 'm2o-sync-bot/1.0'}, stream=True, timeout=20)
        
    assert org_file.exists()
    content = org_file.read_text(encoding='utf-8')
    assert ":PROPERTIES:" in content
    assert ":ID:" in content
    assert "[[attachment:toot_11113_1.jpg]]" in content
    
    # UUIDプロパティを抽出
    m = re.search(r':ID:\s+([a-f0-9\-]+)', content)
    assert m is not None
    entry_id = m.group(1)
    
    img_path = attach_dir / entry_id[:2] / entry_id[2:] / "toot_11113_1.jpg"
    assert img_path.exists()
    assert img_path.read_bytes() == b"fake_image_data"

