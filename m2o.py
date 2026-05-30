import sys
import json
from pathlib import Path
from src.config import Config
from src.mastodon_client import MastodonClient
from src.org_formatter import html_to_org
from src.org_writer import OrgWriter

STATE_FILE = Path("state.json")

def load_state() -> dict:
    """
    前回の同期状態をファイルから読み込む。
    """
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load state.json: {e}", file=sys.stderr)
    return {}

def save_state(state: dict):
    """
    同期状態をファイルに保存する。
    """
    try:
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f"Error: Failed to save state.json: {e}", file=sys.stderr)

def main():
    # 1. 設定の読み込み
    try:
        config = Config()
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)

    # 2. 状態のロード
    state = load_state()
    last_sync_toot_id = state.get("last_sync_toot_id")

    # 3. Mastodon クライアントの初期化
    print("Initializing Mastodon client...")
    try:
        client = MastodonClient(config.instance_url, config.access_token)
    except Exception as e:
        print(f"Failed to initialize Mastodon client: {e}", file=sys.stderr)
        sys.exit(1)

    # 4. Toot の差分取得 (ページネーション対応)
    print(f"Fetching toots since ID: {last_sync_toot_id}")
    all_toots = []
    max_id = None
    limit = 40

    while True:
        try:
            toots = client.fetch_toots(since_id=last_sync_toot_id, max_id=max_id, limit=limit)
        except Exception as e:
            print(f"Error communicating with Mastodon API: {e}", file=sys.stderr)
            sys.exit(1)

        if not toots:
            break

        all_toots.extend(toots)

        # 降順で返るため、最後尾の要素が最も古い
        last_id = toots[-1]['id']
        max_id = int(last_id) - 1  # 次回取得用にmax_idを更新

        # 取得件数が limit 未満であれば、もう since_id までの間に新しい投稿はない
        if len(toots) < limit:
            break

    if not all_toots:
        print("No new toots to sync.")
        return

    # 5. 時系列順 (IDの昇順) にソート
    print(f"Found {len(all_toots)} new toots. Sorting in chronological order...")
    all_toots.sort(key=lambda t: t['id'])

    # 6. Orgファイルへの書き込みと画像ダウンロード
    print(f"Writing to org file: {config.org_file_path}")
    writer = OrgWriter(config.org_file_path, config.attach_dir)

    synced_count = 0
    new_last_id = last_sync_toot_id

    for toot in all_toots:
        toot_id = str(toot['id'])
        created_at = toot['created_at']
        html_content = toot['content']
        media_attachments = toot['media_attachments']

        # HTML 本文を Org 記法に変換
        org_content = html_to_org(html_content)

        print(f"  [{toot_id}] Processing toot from {created_at.astimezone().strftime('%Y-%m-%d %H:%M:%S')}...")

        # Orgファイルへ追加＆画像処理
        writer.add_toot(
            toot_id=toot_id,
            created_at=created_at,
            content_text=org_content,
            media_attachments=media_attachments
        )
        
        new_last_id = int(toot['id'])
        synced_count += 1

    # 7. 状態の更新と保存
    if new_last_id:
        state["last_sync_toot_id"] = new_last_id
        save_state(state)

    print(f"Successfully synced {synced_count} toots. Last sync ID updated to {new_last_id}.")

if __name__ == "__main__":
    main()
