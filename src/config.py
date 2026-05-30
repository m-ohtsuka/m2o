import os
from pathlib import Path
from dotenv import load_dotenv

class Config:
    def __init__(self):
        # .env ファイルをロード
        # カレントディレクトリ、またはスクリプトの親ディレクトリから探す
        env_path = Path(".env").resolve()
        if not env_path.exists():
            env_path = Path(__file__).resolve().parents[1] / ".env"
        
        load_dotenv(dotenv_path=env_path)

        self.instance_url = os.getenv("MASTODON_INSTANCE_URL")
        self.access_token = os.getenv("MASTODON_ACCESS_TOKEN")
        self.org_file_path = os.getenv("ORG_FILE_PATH")
        self.boost_handling = os.getenv("BOOST_HANDLING", "quote").lower()

        if not self.instance_url:
            raise ValueError("MASTODON_INSTANCE_URL is not set in .env")
        if not self.access_token:
            raise ValueError("MASTODON_ACCESS_TOKEN is not set in .env")
        if not self.org_file_path:
            raise ValueError("ORG_FILE_PATH is not set in .env")

        # パスを絶対パスに解決
        self.org_file_path = Path(self.org_file_path).resolve()
        
        # 画像保存用の .attach ディレクトリパス（Orgファイルと同じディレクトリ直下）
        self.attach_dir = self.org_file_path.parent / ".attach"
