# Quickstart: 月別Orgファイルレイアウトと移行コンバーター

**Feature**: [spec.md](./spec.md) | 関連: [data-model.md](./data-model.md), [contracts/](./contracts/)

このガイドは、実装後に本機能が仕様通り動作することを手動で確認するための手順。

## 前提

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## シナリオ1: 新規に月別レイアウトで同期する（User Story 1）

1. `.env` に以下を追加する（[env-config contract](./contracts/env-config.md)参照）。

   ```env
   ORG_LAYOUT=monthly
   ORG_DIRECTORY=/path/to/org
   ```

2. 同期を実行する。

   ```bash
   .venv/bin/python m2o.py
   ```

3. **期待結果**:
   - `/path/to/org/mastodon/<今年>/<今月>.org` が新規作成されている。
   - ファイル内が既存の単一ファイルと同じ見出し階層
     （`* YYYY` → `** YYYY-MM` → `*** YYYY-MM-DD` → `**** [YYYY-MM-DD 曜 HH:MM]`）に
     なっている（FR-010）。
   - 画像添付があるtootについては
     `/path/to/org/mastodon/<今年>/.attach/` にファイルが保存され、Orgファイル内の
     `[[attachment:...]]` リンクをEmacsで開くと画像が表示される。

4. 再度同期を実行し、**期待結果**: 重複するtoot見出しが増えないこと（FR-003, SC-001）。

5. 翌月になってから同期を実行し、**期待結果**: 新しい月のファイルが作られ、前月の
   ファイルは変更されないこと（Acceptance Scenario 3）。

## シナリオ2: 既存の `mastodon.org` を変換する（User Story 2）

1. サンプルの既存 `mastodon.org`（複数年・複数月のtoot、ブースト引用、画像添付を含む）を
   用意する。

2. コンバーターを実行する（[CLI contract](./contracts/convert-to-monthly-cli.md)参照）。

   ```bash
   .venv/bin/python convert_to_monthly.py /path/to/mastodon.org /path/to/org
   ```

3. **期待結果**:
   - `Converted: ...` に変換元に含まれていた全ての年月が列挙される。
   - `/path/to/org/mastodon/<YYYY>/<MM>.org` が各月ごとに生成され、該当月のtoot本文・
     `#+BEGIN_QUOTE` 引用ブロック・添付リンクが元と同じ内容で含まれている（FR-005）。
   - 変換前後で全月別ファイルのtoot件数合計が、元の `mastodon.org` のtoot件数と一致する
     （SC-002）。
   - 元の `mastodon.org` および元の `.attach` 配下のファイルが一切変更されていない
     （`git diff` や `diff` で確認、FR-007・FR-011）。
   - `Copied attachments: ...` に、コピーされた添付ファイルの変換元・変換先パスの対応が
     すべて列挙されている（FR-012, SC-005）。
   - 変換後のOrgファイルをEmacsで開き、添付画像リンクを辿るとすべて画像が表示される
     （SC-003）。

## シナリオ3: 変換の競合を安全にスキップする（User Story 3）

1. シナリオ2を一度実行済みの状態（`/path/to/org/mastodon/<YYYY>/<MM>.org` が存在する）で、
   同じコンバーターを再度実行する。

2. **期待結果**:
   - 既存の月別ファイルの内容が変更されていない（`diff` で確認、FR-006・SC-004）。
   - `Skipped (already exists): ...` に、既に存在していた月がすべて列挙され、警告として
     表示される。
   - 新規の年月（変換先にまだ存在しなかった月）があれば、それらは正常に変換される。

## 自動テストの実行

手動確認に加え、実装時に追加される自動テストも実行して回帰がないことを確認する
（constitution原則II）。

```bash
.venv/bin/python -m pytest
```
