import os
from pathlib import Path
from dotenv import load_dotenv

class Config:
    instance_url: str
    access_token: str
    org_file_path: Path
    attach_dir: Path
    boost_handling: str

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

        if not instance_url:
            raise ValueError("MASTODON_INSTANCE_URL is not set in .env")
        if not access_token:
            raise ValueError("MASTODON_ACCESS_TOKEN is not set in .env")
        if not org_file_path_str:
            raise ValueError("ORG_FILE_PATH is not set in .env")

        self.instance_url = instance_url
        self.access_token = access_token
        self.org_file_path = Path(org_file_path_str).resolve()
        self.attach_dir = self.org_file_path.parent / ".attach"
        self.boost_handling = boost_handling
