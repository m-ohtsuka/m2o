import datetime
from unittest.mock import MagicMock, patch
from pathlib import Path
import json
from m2o import main

def test_boost_handling_skip(tmp_path, monkeypatch):
    # Ensure environment variables are clean
    monkeypatch.delenv("BOOST_HANDLING", raising=False)
    monkeypatch.delenv("MASTODON_INSTANCE_URL", raising=False)
    monkeypatch.delenv("MASTODON_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("ORG_FILE_PATH", raising=False)

    # Setup temporary files
    org_file = tmp_path / "test.org"
    state_file = tmp_path / "state.json"
    env_file = tmp_path / ".env"
    
    env_content = f"""
MASTODON_INSTANCE_URL=https://example.com
MASTODON_ACCESS_TOKEN=fake_token
ORG_FILE_PATH={org_file}
BOOST_HANDLING=skip
"""
    env_file.write_text(env_content)
    
    # Change current working directory to tmp_path so .env and state.json are found there
    monkeypatch.chdir(tmp_path)
    
    # Mock MastodonClient class used in m2o module
    with patch('m2o.MastodonClient') as MockClient:
        mock_instance = MockClient.return_value
        
        # Mock fetch_toots to return one normal toot and one boost
        tz_jst = datetime.timezone(datetime.timedelta(hours=9))
        dt = datetime.datetime(2026, 5, 30, 10, 0, tzinfo=tz_jst)
        
        toots = [
            {
                'id': 100,
                'created_at': dt,
                'content': '<p>Normal toot</p>',
                'media_attachments': [],
                'reblog': None
            },
            {
                'id': 101,
                'created_at': dt + datetime.timedelta(minutes=1),
                'content': '',
                'media_attachments': [],
                'reblog': {
                    'id': 50,
                    'url': 'https://example.com/orig/50',
                    'content': '<p>Original boosted content</p>',
                    'media_attachments': [],
                    'account': {
                        'username': 'otheruser',
                        'acct': 'otheruser@example.com',
                        'display_name': 'Other User'
                    }
                }
            }
        ]
        
        # First call returns toots, second returns empty list to break loop
        mock_instance.fetch_toots.side_effect = [toots, []]
        
        # Run main
        main()
        
    # Verify results
    assert org_file.exists()
    content = org_file.read_text(encoding='utf-8')
    assert "Normal toot" in content
    assert "Original boosted content" not in content
    assert "Boosted:" not in content
    
    # Verify state.json updated to 101 even though it was skipped
    with open(state_file, 'r') as f:
        state = json.load(f)
        assert state['last_sync_toot_id'] == 101

def test_boost_handling_quote(tmp_path, monkeypatch):
    monkeypatch.delenv("BOOST_HANDLING", raising=False)
    monkeypatch.delenv("MASTODON_INSTANCE_URL", raising=False)
    monkeypatch.delenv("MASTODON_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("ORG_FILE_PATH", raising=False)

    # Setup temporary files
    org_file = tmp_path / "test.org"
    state_file = tmp_path / "state.json"
    env_file = tmp_path / ".env"
    
    env_content = f"""
MASTODON_INSTANCE_URL=https://example.com
MASTODON_ACCESS_TOKEN=fake_token
ORG_FILE_PATH={org_file}
BOOST_HANDLING=quote
"""
    env_file.write_text(env_content)
    
    monkeypatch.chdir(tmp_path)
    
    with patch('m2o.MastodonClient') as MockClient:
        mock_instance = MockClient.return_value
        
        tz_jst = datetime.timezone(datetime.timedelta(hours=9))
        dt = datetime.datetime(2026, 5, 30, 10, 0, tzinfo=tz_jst)
        
        toots = [
            {
                'id': 101,
                'created_at': dt,
                'content': '',
                'media_attachments': [],
                'reblog': {
                    'id': 50,
                    'url': 'https://example.com/orig/50',
                    'content': '<p>Original boosted content</p>',
                    'media_attachments': [],
                    'account': {
                        'username': 'otheruser',
                        'acct': 'otheruser@example.com',
                        'display_name': 'Other User'
                    }
                }
            }
        ]
        
        mock_instance.fetch_toots.side_effect = [toots, []]
        
        main()
        
    assert org_file.exists()
    content = org_file.read_text(encoding='utf-8')
    assert "Boosted: [[https://example.com/orig/50][Other User (@otheruser@example.com)]]" in content
    assert "#+BEGIN_QUOTE" in content
    assert "Original boosted content" in content
    assert "#+END_QUOTE" in content
