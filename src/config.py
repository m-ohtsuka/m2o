import os
from pathlib import Path
from dotenv import load_dotenv

class Config:
    instance_url: str
    access_token: str
    org_file_path: Path | None
    attach_dir: Path | None
    boost_handling: str
    org_layout: str
    org_directory: Path | None

    def __init__(self):
        # .env ファイルをロード
        # カレントディレクトリ、またはスクリプトの親ディレクトリから探す
        env_path = Path(".env").resolve()
        if not env_path.exists():
            env_path = Path(__file__).resolve().parents[1] / ".env"

        load_dotenv(dotenv_path=env_path)

        instance_url = os.getenv("MASTODON_INSTANCE_URL")
        access_token = os.getenv("MASTODON_ACCESS_TOKEN")
        org_file_path_str = os.getenv("ORG_FILE_PATH")
        boost_handling = os.getenv("BOOST_HANDLING", "quote").lower()
        org_layout = os.getenv("ORG_LAYOUT", "single").lower()
        org_directory_str = os.getenv("ORG_DIRECTORY")

        if not instance_url:
            raise ValueError("MASTODON_INSTANCE_URL is not set in .env")
        if not access_token:
            raise ValueError("MASTODON_ACCESS_TOKEN is not set in .env")
        if org_layout not in ("single", "monthly"):
            raise ValueError("ORG_LAYOUT must be 'single' or 'monthly'")
        if org_layout == "single" and not org_file_path_str:
            raise ValueError("ORG_FILE_PATH is not set in .env")
        if org_layout == "monthly" and not org_directory_str:
            raise ValueError("ORG_DIRECTORY is not set in .env (required when ORG_LAYOUT=monthly)")

        self.instance_url = instance_url
        self.access_token = access_token
        self.boost_handling = boost_handling
        self.org_layout = org_layout

        if org_file_path_str:
            self.org_file_path = Path(org_file_path_str).resolve()
            self.attach_dir = self.org_file_path.parent / ".attach"
        else:
            self.org_file_path = None
            self.attach_dir = None

        self.org_directory = Path(org_directory_str).resolve() if org_directory_str else None
