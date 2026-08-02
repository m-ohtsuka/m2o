# Data Model: 月別Orgファイルレイアウトと移行コンバーター

**Feature**: [spec.md](./spec.md) | **Date**: 2026-08-02

このツールはデータベースを持たず、設定値・ファイルシステム上のパス・実行結果レポートが
主な「データ」となる。各エンティティはPythonの値オブジェクト（既存コードの延長）として
表現する。

## LayoutMode（レイアウトモード）

tootの保存先形式を表す設定値。`src/config.py` の `Config` に追加するフィールド。

| フィールド | 型 | 説明 |
|---|---|---|
| `org_layout` | `Literal["single", "monthly"]` | `.env` の `ORG_LAYOUT` から読み込む。未設定時は `"single"`（既存互換）。 |
| `org_directory` | `Path \| None` | `.env` の `ORG_DIRECTORY` から読み込む。`org_layout == "monthly"` のとき必須、それ以外は `None`。 |

**バリデーションルール**:
- `org_layout` は `"single"` または `"monthly"` のいずれかでなければならない（それ以外は
  設定エラーとして起動時に中断、既存の `ValueError` パターンを踏襲）。
- `org_layout == "monthly"` のとき `ORG_DIRECTORY` が未設定なら設定エラー。
- `org_layout == "single"`（既定）のとき、これまで通り `ORG_FILE_PATH` が未設定なら
  設定エラー。`org_layout == "monthly"` のときは `ORG_FILE_PATH` は不要（未設定を許容）。

## MonthlyOrgFile（月別Orgファイル）

`ORG_DIRECTORY/mastodon/{YYYY}/{MM}.org` に対応するファイル。永続化されたエンティティでは
なく、実行時にtootの日時から都度パスを導出する。

| フィールド | 型 | 説明 |
|---|---|---|
| `year` | `str`（4桁） | tootのローカル日時の年 |
| `month` | `str`（2桁, 0埋め） | tootのローカル日時の月 |
| `org_path` | `Path` | `ORG_DIRECTORY/mastodon/{year}/{month}.org` |
| `attach_dir` | `Path` | `ORG_DIRECTORY/mastodon/{year}/.attach` |

**関係**: 内部のOrgツリー構造は既存の単一ファイルレイアウトと同一
（`OrgNode` level 1=年, 2=月, 3=日, 4=toot）。1つの `MonthlyOrgFile` は常に
level-1ノードを1つ・その下にlevel-2ノードを1つだけ持つ（FR-010）。

**ライフサイクル**: 対象月の最初のtoot同期時に新規作成（ディレクトリ含む）。以後のtoot
同期では既存ファイルをパースし、時系列順の位置に追記して上書き保存する
（`OrgWriter.add_toot()` の既存動作をそのまま利用）。

## ConversionReport（変換実行レポート）

`convert_to_monthly.py` の実行結果。永続化はせず、実行完了時に標準出力へ表示する。

| フィールド | 型 | 説明 |
|---|---|---|
| `skipped_months` | `list[str]`（`"YYYY-MM"`） | 変換先に既にファイルが存在したためスキップした月（FR-006） |
| `converted_months` | `list[str]`（`"YYYY-MM"`） | 正常に変換された月 |
| `copied_attachments` | `list[tuple[Path, Path]]` | コピーした添付ファイルの (変換元パス, 変換先パス) 一覧（FR-012） |

**バリデーションルール**:
- `skipped_months` と `converted_months` は互いに素（同じ月が両方に入らない）。
- `copied_attachments` は `skipped_months` に属する月のtootの添付ファイルを含まない
  （スキップした月は一切書き込み・コピーを行わない）。

## 既存エンティティとの関係（変更なし）

- **OrgNode**（`src/org_writer.py`）: 見出しレベル・タイトル・コンテンツ行・子ノードを
  保持するツリーノード。本機能では構造・フィールドとも変更しない。
- **Toot**（Mastodon APIレスポンス）: `id`, `created_at`, `content`, `media_attachments`,
  `reblog` 等。本機能では新しいフィールドを追加しない。
