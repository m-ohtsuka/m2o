import os
import re
import uuid
import requests
from pathlib import Path

WEEKDAYS_FULL = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]
WEEKDAYS_SHORT = ["月", "火", "水", "木", "金", "土", "日"]

class OrgNode:
    def __init__(self, level, title, content_lines=None):
        self.level = level  # 1 (年), 2 (月), 3 (日), 4 (Toot) などの見出しレベル
        self.title = title  # 見出し行そのもの（星を含む）
        self.content_lines = content_lines or []  # この見出しの直下にあるコンテンツ行
        self.children = []  # サブノードのリスト

def parse_org(lines):
    """
    Orgファイルの内容を行単位のリストからパースして
    ツリー構造（OrgNode）を構築する。
    """
    root = OrgNode(0, "ROOT")
    stack = [root]
    
    for line in lines:
        stripped = line.rstrip('\r\n')
        # 星から始まる見出し行を検出
        m = re.match(r'^(\*+)\s+(.*)', stripped)
        if m:
            stars = m.group(1)
            level = len(stars)
            node = OrgNode(level, stripped)
            
            # 適切な親ノードを見つけるまでスタックをポップ
            while len(stack) > 1 and stack[-1].level >= level:
                stack.pop()
            stack[-1].children.append(node)
            stack.append(node)
        else:
            stack[-1].content_lines.append(line)
            
    return root

def serialize_org(node):
    """
    ツリー構造（OrgNode）を再帰的にOrgファイルのテキスト行リストに変換する。
    """
    lines = []
    if node.level > 0:
        lines.append(node.title + "\n")
    lines.extend(node.content_lines)
    for child in node.children:
        lines.extend(serialize_org(child))
    return lines

def get_node_sort_key(node):
    """
    ノードのソート用キーを抽出する。
    - * YYYY -> YYYY
    - ** YYYY-MM -> YYYY-MM
    - *** YYYY-MM-DD -> YYYY-MM-DD
    - **** [YYYY-MM-DD 曜日 HH:MM] -> YYYY-MM-DD HH:MM
    """
    if node.level == 1:
        m = re.search(r'\* (\d{4})', node.title)
        return m.group(1) if m else node.title
    elif node.level == 2:
        m = re.search(r'\*\* (\d{4}-\d{2})', node.title)
        return m.group(1) if m else node.title
    elif node.level == 3:
        m = re.search(r'\*\*\* (\d{4}-\d{2}-\d{2})', node.title)
        return m.group(1) if m else node.title
    elif node.level == 4:
        m = re.search(r'\[(\d{4}-\d{2}-\d{2})\s+\w+\s+(\d{2}:\d{2})\]', node.title)
        return f"{m.group(1)} {m.group(2)}" if m else node.title
    return node.title

def insert_sorted(parent_node, new_node):
    """
    親ノードの children リストに、ソート順を維持して新しいノードを挿入する。
    """
    key = get_node_sort_key(new_node)
    insert_idx = len(parent_node.children)
    for i, child in enumerate(parent_node.children):
        if get_node_sort_key(child) > key:
            insert_idx = i
            break
    parent_node.children.insert(insert_idx, new_node)

class OrgWriter:
    def __init__(self, org_file_path: Path, attach_dir: Path):
        self.org_file_path = Path(org_file_path).resolve()
        self.attach_dir = Path(attach_dir).resolve()

    def add_toot(self, toot_id: str, created_at, content_text: str, media_attachments):
        """
        単一のTootをOrgファイルに追加する。
        - 既存Orgファイルをロードしパース
        - 適切な年見出し・年月見出し・日付見出しを探す（なければ作成）
        - 画像がある場合はUUIDを生成し、:PROPERTIES:セクションを付与し画像をダウンロード保存
        - 時系列昇順で正しい位置に見出しを追加
        - ファイルに再保存
        """
        # 既存ファイルの読込
        if self.org_file_path.exists():
            with open(self.org_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        else:
            lines = []

        root = parse_org(lines)

        # タイムゾーン考慮の上でローカル時刻に変換
        local_dt = created_at.astimezone()
        year_str = local_dt.strftime('%Y')
        year_month = local_dt.strftime('%Y-%m')
        month_num = local_dt.month
        date_str = local_dt.strftime('%Y-%m-%d')
        wd_idx = local_dt.weekday()
        weekday_full = WEEKDAYS_FULL[wd_idx]
        weekday_short = WEEKDAYS_SHORT[wd_idx]
        time_str = local_dt.strftime('%H:%M')

        # 0. 年見出しの取得・作成
        year_node = None
        for child in root.children:
            if child.level == 1:
                m = re.search(r'\* (\d{4})$', child.title)
                if m and m.group(1) == year_str:
                    year_node = child
                    break
        if not year_node:
            year_node = OrgNode(1, f"* {year_str}")
            insert_sorted(root, year_node)

        # 1. 月見出しの取得・作成
        month_node = None
        for child in year_node.children:
            if child.level == 2:
                m = re.search(r'\*\* (\d{4}-\d{2})', child.title)
                if m and m.group(1) == year_month:
                    month_node = child
                    break
        if not month_node:
            month_node = OrgNode(2, f"** {year_month} {month_num}月")
            insert_sorted(year_node, month_node)

        # 2. 日見出しの取得・作成
        day_node = None
        for child in month_node.children:
            if child.level == 3:
                m = re.search(r'\*\*\* (\d{4}-\d{2}-\d{2})', child.title)
                if m and m.group(1) == date_str:
                    day_node = child
                    break
        if not day_node:
            day_node = OrgNode(3, f"*** {date_str} {weekday_full}")
            insert_sorted(month_node, day_node)

        # 3. Toot見出しの作成
        time_header = f"**** [{date_str} {weekday_short} {time_str}]"
        
        # 4. コンテンツ行の構築
        content_lines = []

        # 画像ファイルの抽出・ダウンロード
        images = [m for m in media_attachments if m.get('type') == 'image']
        if images:
            # org-attach 規約用の UUID の生成
            entry_id = str(uuid.uuid4())
            
            # PROPERTIESセクションの追加
            content_lines.append(":PROPERTIES:\n")
            content_lines.append(f":ID:       {entry_id}\n")
            content_lines.append(":END:\n")

            # 保存先ディレクトリ: .attach/XX/XXXX...
            id_prefix = entry_id[:2]
            id_suffix = entry_id[2:]
            dest_dir = self.attach_dir / id_prefix / id_suffix
            dest_dir.mkdir(parents=True, exist_ok=True)

            for i, media in enumerate(images, 1):
                url = media.get('url') or media.get('remote_url')
                if not url:
                    continue
                
                # 拡張子の判定
                ext = "png"
                ext_match = re.search(r'\.([a-zA-Z0-9]+)(?:\?|$)', url)
                if ext_match:
                    ext = ext_match.group(1).lower()

                # ファイル名 (toot_id と index を利用して衝突を防止)
                filename = f"toot_{toot_id}_{i}.{ext}"
                dest_path = dest_dir / filename

                try:
                    headers = {'User-Agent': 'm2o-sync-bot/1.0'}
                    r = requests.get(url, headers=headers, stream=True, timeout=20)
                    if r.status_code == 200:
                        with open(dest_path, 'wb') as img_f:
                            for chunk in r.iter_content(chunk_size=8192):
                                img_f.write(chunk)
                        
                        # attachment形式のリンクを追加
                        content_lines.append(f"[[attachment:{filename}]]\n")
                    else:
                        print(f"Failed to download image {url}: HTTP {r.status_code}")
                except Exception as e:
                    print(f"Error downloading image {url}: {e}")

        # 本文の追加 (行ごとに分割して追加)
        for line in content_text.splitlines():
            content_lines.append(line + "\n")
            
        # 読みやすさのため末尾に空行を整理
        if content_lines:
            # 最後の行を空行にする
            if content_lines[-1] == "\n":
                content_lines[-1] = "\n"  # 1行の空行
            else:
                content_lines[-1] = content_lines[-1].rstrip('\r\n') + "\n"
                content_lines.append("\n")
        else:
            content_lines.append("\n")

        # 5. Tootノードの挿入
        toot_node = OrgNode(4, time_header, content_lines)
        insert_sorted(day_node, toot_node)

        # 6. シリアライズして書き出し
        new_lines = serialize_org(root)
        
        self.org_file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.org_file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
