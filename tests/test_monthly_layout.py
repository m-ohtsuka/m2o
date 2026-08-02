import datetime
from unittest.mock import MagicMock, patch
from m2o import main


def _write_env(tmp_path, org_directory):
    env_file = tmp_path / ".env"
    env_content = f"""
MASTODON_INSTANCE_URL=https://example.com
MASTODON_ACCESS_TOKEN=fake_token
ORG_LAYOUT=monthly
ORG_DIRECTORY={org_directory}
"""
    env_file.write_text(env_content)


def _clean_env(monkeypatch):
    for key in [
        "MASTODON_INSTANCE_URL",
        "MASTODON_ACCESS_TOKEN",
        "ORG_FILE_PATH",
        "BOOST_HANDLING",
        "ORG_LAYOUT",
        "ORG_DIRECTORY",
    ]:
        monkeypatch.delenv(key, raising=False)


def _toot(toot_id, dt, content):
    return {
        'id': toot_id,
        'created_at': dt,
        'content': f'<p>{content}</p>',
        'media_attachments': [],
        'reblog': None,
    }


def test_monthly_layout_creates_file_for_toot_month(tmp_path, monkeypatch):
    _clean_env(monkeypatch)
    org_directory = tmp_path / "org"
    _write_env(tmp_path, org_directory)
    monkeypatch.chdir(tmp_path)

    tz_jst = datetime.timezone(datetime.timedelta(hours=9))
    dt = datetime.datetime(2026, 8, 2, 17, 4, tzinfo=tz_jst)

    with patch('m2o.MastodonClient') as MockClient:
        mock_instance = MockClient.return_value
        mock_instance.fetch_toots.side_effect = [[_toot(100, dt, "August toot")], []]
        main()

    org_path = org_directory / "mastodon" / "2026" / "08.org"
    assert org_path.exists()
    content = org_path.read_text(encoding='utf-8')
    assert "* 2026" in content
    assert "** 2026-08 8月" in content
    assert "*** 2026-08-02" in content
    assert "**** [2026-08-02" in content
    assert "August toot" in content


def test_monthly_layout_rerun_does_not_duplicate(tmp_path, monkeypatch):
    _clean_env(monkeypatch)
    org_directory = tmp_path / "org"
    _write_env(tmp_path, org_directory)
    monkeypatch.chdir(tmp_path)

    tz_jst = datetime.timezone(datetime.timedelta(hours=9))
    dt = datetime.datetime(2026, 8, 2, 17, 4, tzinfo=tz_jst)

    with patch('m2o.MastodonClient') as MockClient:
        mock_instance = MockClient.return_value
        mock_instance.fetch_toots.side_effect = [[_toot(100, dt, "August toot")], []]
        main()

    # 2回目の同期は state.json により新規tootがないため何も追加されないはず
    with patch('m2o.MastodonClient') as MockClient:
        mock_instance = MockClient.return_value
        mock_instance.fetch_toots.side_effect = [[]]
        main()

    org_path = org_directory / "mastodon" / "2026" / "08.org"
    content = org_path.read_text(encoding='utf-8')
    assert content.count("August toot") == 1
    assert content.count("**** [2026-08-02") == 1


def test_monthly_layout_crosses_month_boundary(tmp_path, monkeypatch):
    _clean_env(monkeypatch)
    org_directory = tmp_path / "org"
    _write_env(tmp_path, org_directory)
    monkeypatch.chdir(tmp_path)

    tz_jst = datetime.timezone(datetime.timedelta(hours=9))
    dt_aug = datetime.datetime(2026, 8, 31, 23, 0, tzinfo=tz_jst)
    dt_sep = datetime.datetime(2026, 9, 1, 1, 0, tzinfo=tz_jst)

    with patch('m2o.MastodonClient') as MockClient:
        mock_instance = MockClient.return_value
        mock_instance.fetch_toots.side_effect = [
            [_toot(101, dt_sep, "September toot"), _toot(100, dt_aug, "August toot")],
            [],
        ]
        main()

    aug_path = org_directory / "mastodon" / "2026" / "08.org"
    sep_path = org_directory / "mastodon" / "2026" / "09.org"

    assert aug_path.exists()
    assert sep_path.exists()

    aug_content = aug_path.read_text(encoding='utf-8')
    sep_content = sep_path.read_text(encoding='utf-8')

    assert "August toot" in aug_content
    assert "September toot" not in aug_content
    assert "September toot" in sep_content
    assert "August toot" not in sep_content


def test_monthly_layout_image_toot_uses_attach_dir_property_and_flat_storage(tmp_path, monkeypatch):
    """monthlyレイアウトでの画像添付tootは、ATTACH_DIRプロパティ付きでimages/へ
    フラットに保存される（org-attach-id-dirのグローバル設定に依存しないため）。"""
    _clean_env(monkeypatch)
    org_directory = tmp_path / "org"
    _write_env(tmp_path, org_directory)
    monkeypatch.chdir(tmp_path)

    tz_jst = datetime.timezone(datetime.timedelta(hours=9))
    dt = datetime.datetime(2026, 8, 2, 17, 4, tzinfo=tz_jst)

    toot = {
        'id': 100,
        'created_at': dt,
        'content': '<p>Photo toot</p>',
        'media_attachments': [
            {
                'type': 'image',
                'url': 'https://example.com/media/test_image.jpg',
                'remote_url': 'https://example.com/media/test_image.jpg',
            }
        ],
        'reblog': None,
    }

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.iter_content = lambda chunk_size: [b"fake_image_data"]

    with patch('m2o.MastodonClient') as MockClient, \
            patch('requests.get', return_value=mock_response):
        mock_instance = MockClient.return_value
        mock_instance.fetch_toots.side_effect = [[toot], []]
        main()

    org_path = org_directory / "mastodon" / "2026" / "08.org"
    content = org_path.read_text(encoding='utf-8')

    assert content.startswith("#+PROPERTY: ATTACH_DIR images/\n")
    assert ":PROPERTIES:" in content
    assert ":ID:" in content
    assert "[[attachment:toot_100_1.jpg]]" in content

    # ID分割なしで images/ 直下にフラット保存されている
    img_path = org_directory / "mastodon" / "2026" / "images" / "toot_100_1.jpg"
    assert img_path.exists()
    assert img_path.read_bytes() == b"fake_image_data"
