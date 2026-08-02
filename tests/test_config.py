import pytest
from pathlib import Path
from src.config import Config


def _write_env(tmp_path, monkeypatch, extra_lines=""):
    org_file = tmp_path / "test.org"
    env_file = tmp_path / ".env"
    env_content = f"""
MASTODON_INSTANCE_URL=https://example.com
MASTODON_ACCESS_TOKEN=fake_token
{extra_lines}
"""
    env_file.write_text(env_content)
    monkeypatch.chdir(tmp_path)
    return org_file


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


def test_org_layout_defaults_to_single(tmp_path, monkeypatch):
    _clean_env(monkeypatch)
    org_file = tmp_path / "test.org"
    _write_env(tmp_path, monkeypatch, f"ORG_FILE_PATH={org_file}")

    config = Config()

    assert config.org_layout == "single"
    assert config.org_file_path == org_file.resolve()


def test_org_layout_monthly_with_org_directory(tmp_path, monkeypatch):
    _clean_env(monkeypatch)
    org_directory = tmp_path / "org"
    _write_env(
        tmp_path,
        monkeypatch,
        f"ORG_LAYOUT=monthly\nORG_DIRECTORY={org_directory}",
    )

    config = Config()

    assert config.org_layout == "monthly"
    assert config.org_directory == org_directory.resolve()


def test_org_layout_monthly_requires_org_directory(tmp_path, monkeypatch):
    _clean_env(monkeypatch)
    _write_env(tmp_path, monkeypatch, "ORG_LAYOUT=monthly")

    with pytest.raises(ValueError):
        Config()


def test_org_layout_single_requires_org_file_path(tmp_path, monkeypatch):
    _clean_env(monkeypatch)
    _write_env(tmp_path, monkeypatch, "")

    with pytest.raises(ValueError):
        Config()


def test_org_layout_monthly_does_not_require_org_file_path(tmp_path, monkeypatch):
    _clean_env(monkeypatch)
    org_directory = tmp_path / "org"
    _write_env(
        tmp_path,
        monkeypatch,
        f"ORG_LAYOUT=monthly\nORG_DIRECTORY={org_directory}",
    )

    config = Config()

    assert config.org_layout == "monthly"
    assert config.org_directory == org_directory.resolve()


def test_org_layout_invalid_value_raises(tmp_path, monkeypatch):
    _clean_env(monkeypatch)
    org_file = tmp_path / "test.org"
    _write_env(
        tmp_path,
        monkeypatch,
        f"ORG_FILE_PATH={org_file}\nORG_LAYOUT=weekly",
    )

    with pytest.raises(ValueError):
        Config()
