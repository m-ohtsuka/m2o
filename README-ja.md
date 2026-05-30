# m2o - Mastodon to Org-mode 同期ツール

`m2o` は、Mastodonへの投稿（toot）をダウンロードし、EmacsのOrg-modeファイルに差分保存するPythonツールです。画像の自動ダウンロード機能に対応し、`org-download` および `org-attach` と互換性のある形式で添付を管理できます。

## 主な機能

- **差分同期（インクリメンタル同期）**: 同期した最新のToot IDを `state.json` に記録・保持するため、2回目以降は新規の追加投稿のみを高速に差分同期します。
- **インテリジェントなOrgツリー構造の自動生成・挿入**: 既存のOrgファイルを自動解析し、正しい年月見出し（`** YYYY-MM MM月`）と日付見出し（`*** YYYY-MM-DD 曜日`）の下に、時系列の昇順（古い順）でToot（`**** [YYYY-MM-DD 曜日 HH:MM]`）を自動でソート挿入します。
- **HTMLからOrg-modeへのクリーンアップ**: Mastodonから取得されるHTML形式の本文をパースし、改行や段落を綺麗に整形します。メンションやハッシュタグ、通常のリンクは自動でOrg-modeのリンク記法（`[[URL][表示テキスト]]`）に変換されます。
- **柔軟なブースト（reblog）ハンドリング**: ブーストされた他人の投稿をスキップするか、元の投稿者情報とともに引用形式（`#+BEGIN_QUOTE`）で保存するかを選択可能です。
- **強力な画像アタッチメント連携 (org-attach / org-download仕様)**:
  - 画像を含む投稿の場合、UUID形式の `ID` プロパティを持つ `:PROPERTIES:` セクションを自動で生成し、Toot見出し直下に付与します。
  - 画像ファイルは、Orgファイルと同じ階層の `.attach/XX/XXXX.../` ディレクトリ配下に自動保存します（ファイル名: `toot_{toot_id}_{index}.{ext}`）。
  - 本文内には `[[attachment:画像ファイル名]]` を自動挿入して画像へリンクします。

## 必要要件

- Python 3.8 以上
- `requirements.txt` に定義されている依存パッケージ（`Mastodon.py`, `beautifulsoup4`, `python-dotenv`, `requests`）

## セットアップ手順

1. **リポジトリのクローン**:
   ```bash
   git clone https://github.com/m-ohtsuka/m2o.git
   cd m2o
   ```

2. **仮想環境の初期化と依存関係のインストール**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # macOS / Linux の場合
   pip install -r requirements.txt
   ```

3. **環境変数の設定**:
   設定テンプレートファイルをコピーして編集します。
   ```bash
   cp .env.example .env
   ```
   `.env` ファイルを開き、以下の各項目を設定してください。
   - `MASTODON_INSTANCE_URL`: 利用しているMastodonのインスタンスURL（例: `https://mastodon.social`）。
   - `MASTODON_ACCESS_TOKEN`: Mastodonの開発者設定から生成したアクセストークン（`read:statuses` スコープが必要）。
   - `ORG_FILE_PATH`: 出力先となる `.org` ファイルの絶対パス（例: `/Users/username/org/mastodon.org`）。
   - `BOOST_HANDLING`（任意）: ブースト（reblog）の扱い。`quote`（デフォルト）を指定すると引用として保存し、`skip` を指定すると無視します。

## 使用方法

以下のコマンドを実行して同期を行います。
```bash
.venv/bin/python m2o.py
```

初回実行時は、最新のToot（デフォルト40件、ページネーションでそれ以上も遡及取得）を取得します。次回以降は前回の続きの差分のみを取得・追記します。

### 自動定期実行の設定
`cron` などを利用して、自動で定期実行させることができます。以下は1時間ごとに実行する設定例です。
```cron
0 * * * * cd /path/to/m2o && .venv/bin/python m2o.py >/dev/null 2>&1
```

## テストの実行

`pytest` を用いた自動単体テストを実行できます。
```bash
.venv/bin/python -m pytest
```

## ライセンス

本プロジェクトは MIT ライセンスの下で提供されています。詳細は [LICENSE](LICENSE) ファイルを参照してください。
