# Contract: `convert_to_monthly.py` CLI

**Feature**: [spec.md](../spec.md)

`migrate_org.py` と同じ「手動で一度だけ実行する単体スクリプト」として提供する。

## 使い方

```bash
.venv/bin/python convert_to_monthly.py <path/to/mastodon.org> <Org Directory>
```

| 引数 | 必須 | 説明 |
|---|---|---|
| `<path/to/mastodon.org>` | 必須 | 変換元の単一Orgファイルのパス。既存の年見出しフォーマット（`* YYYY`）であること。 |
| `<Org Directory>` | 必須 | 変換先のベースディレクトリ（`.env` の `ORG_DIRECTORY` と同じ値を想定）。この配下に `mastodon/{YYYY}/{MM}.org` が生成される。 |

添付ファイルの変換元ディレクトリは、既存の `Config` の導出ルールと同じく
`<mastodon.orgのあるディレクトリ>/.attach` を自動的に使用する（追加の引数は不要）。

## 前提条件

- 変換元ファイルは変更・削除されない（FR-007）。
- 変換元の添付ファイル（`.attach` 配下）は変更・削除されない（FR-011）。

## 標準出力（実行結果レポート）

実行完了後、以下の情報を標準出力に表示する。

```text
Converted: 2025-01, 2025-02, 2025-03, ...
Skipped (already exists): 2025-04, ...
Copied attachments:
  <元パス> -> <変換先パス>
  ...
```

- `Converted`: 正常に変換され新規作成された月（`YYYY-MM`）の一覧。
- `Skipped (already exists)`: 変換先に同名ファイルが既に存在したためスキップした月の一覧
  （FR-006）。0件の場合は `Skipped (already exists): (none)` のように明示する。
- `Copied attachments`: コピーした添付ファイルの変換元パス・変換先パスの対応一覧
  （FR-012）。0件の場合は `Copied attachments: (none)` と表示する。

## 終了コード

| コード | 意味 |
|---|---|
| `0` | 正常終了（スキップされた月が0件以上あっても、致命的エラーがなければ0） |
| `1` | 引数不足・変換元ファイルが存在しない等、実行前提条件を満たさない場合 |

## 非対象（スコープ外）

- 月別レイアウトから単一ファイルレイアウトへの逆変換は提供しない（spec Assumptions参照）。
- 既に年見出しのない旧フォーマットの `mastodon.org` の自動判別・変換は行わない
  （`migrate_org.py` を先に実行することが前提）。
