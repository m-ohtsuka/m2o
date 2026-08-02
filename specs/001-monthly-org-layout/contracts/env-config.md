# Contract: `.env` 設定項目（追加分）

**Feature**: [spec.md](../spec.md)

既存の `.env` 契約（`MASTODON_INSTANCE_URL`, `MASTODON_ACCESS_TOKEN`, `ORG_FILE_PATH`,
`BOOST_HANDLING`）に、以下2項目を追加する。

## `ORG_LAYOUT`

| 項目 | 内容 |
|---|---|
| 必須/任意 | 任意 |
| 既定値 | `single` |
| 許容値 | `single`（既存の単一ファイル挙動） / `monthly`（年ディレクトリ・月ファイル分割） |
| 大文字小文字 | 小文字化して比較（`BOOST_HANDLING` と同じ扱い） |
| 不正値 | 起動時に `Configuration error` として中断する（既存の `ValueError` パターン） |

## `ORG_DIRECTORY`

| 項目 | 内容 |
|---|---|
| 必須/任意 | `ORG_LAYOUT=monthly` のとき必須。`ORG_LAYOUT=single`（既定）のときは無視される |
| 値 | `<Org Directory>` の絶対パスまたは相対パス（相対パスは実行時に絶対パスへ解決） |
| 導出パス | tootの保存先: `ORG_DIRECTORY/mastodon/{YYYY}/{MM}.org` |
| 導出パス | 添付ファイル保存先: `ORG_DIRECTORY/mastodon/{YYYY}/.attach/` |
| 不正値（`ORG_LAYOUT=monthly` かつ未設定） | 起動時に `Configuration error` として中断する |

## `ORG_FILE_PATH` の必須条件の変更

`ORG_LAYOUT=monthly` のときは `ORG_FILE_PATH` を必須としない（`monthly` モードのみで
使う新規ユーザーが単一ファイル用のパスを設定する必要をなくすため）。
`ORG_LAYOUT=single`（既定）のときは、これまで通り `ORG_FILE_PATH` が必須。

## 後方互換性

- `.env` に `ORG_LAYOUT` を追加しない既存ユーザーは、これまで通り `ORG_FILE_PATH` へ
  単一ファイルとして書き込まれる（デフォルト `single`）。既存の `.env` は変更不要。
