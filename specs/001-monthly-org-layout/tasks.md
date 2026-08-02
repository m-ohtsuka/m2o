---

description: "Task list template for feature implementation"
---

# Tasks: 月別Orgファイルレイアウトと移行コンバーター

**Input**: Design documents from `/specs/001-monthly-org-layout/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/](./contracts/), [quickstart.md](./quickstart.md)

**Tests**: constitution原則II（テストによる回帰防止）により、Orgファイル構造・コンバーターに
関わる変更にはテストタスクを含める。

**Organization**: タスクはユーザーストーリー（spec.mdのUser Story 1〜3）ごとにグループ化し、
各ストーリーを独立して実装・検証できるようにする。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 並列実行可能（別ファイル・依存関係なし）
- **[Story]**: 対応するユーザーストーリー（US1, US2, US3）
- 各タスクの説明には具体的なファイルパスを含める

## Path Conventions

既存の単一プロジェクト構成（`src/`, `tests/`, リポジトリルート直下のエントリースクリプト）を
そのまま使用する（plan.md の Project Structure 参照）。

---

## Phase 1: Setup

**Purpose**: 新しい設定項目を利用者が発見できるようにするドキュメント整備

- [X] T001 [P] `.env.example` に `ORG_LAYOUT`（コメントで既定値`single`と`monthly`の説明）と
      `ORG_DIRECTORY`（`monthly`使用時のみ必須である旨）の記述を追加する
      (`.env.example`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: User Story 1・2・3のすべてが依存する、月別パス解決の共通ロジック

**⚠️ CRITICAL**: このフェーズが完了するまで、いずれのユーザーストーリーの実装にも着手しない

- [X] T002 [P] `tests/test_org_writer.py` に `monthly_paths()` 関数の単体テストを追加する
      （`ORG_DIRECTORY/mastodon/{YYYY}/{MM}.org` と `ORG_DIRECTORY/mastodon/{YYYY}/.attach` を
      返すこと、月が1桁の場合に0埋めされること、年またぎのケースを検証。関数が未実装のため
      このテストは失敗する）
      (`tests/test_org_writer.py`)
- [X] T003 `src/org_writer.py` に純粋関数 `monthly_paths(org_directory: Path, local_dt:
      datetime) -> tuple[Path, Path]` を実装し、T002のテストをパスさせる
      （data-model.md の MonthlyOrgFile 定義に従う）
      (`src/org_writer.py`)

**Checkpoint**: `monthly_paths()` が実装され、全ユーザーストーリーの実装に着手できる

---

## Phase 3: User Story 1 - 月別ファイルへの分割保存 (Priority: P1) 🎯 MVP

**Goal**: `ORG_LAYOUT=monthly` を設定すると、tootが `<Org Directory>/mastodon/YYYY/MM.org`
へ年月ごとに自動振り分けされ、既存の単一ファイルモードと同じ時系列順・重複なしの保証を
保ったまま記録される。

**Independent Test**: `.env` に `ORG_LAYOUT=monthly` と `ORG_DIRECTORY` を設定して
`m2o.py` を実行し、該当月のパスにファイルが作成され、tootが正しい見出し階層で記録される
ことを確認する。再実行しても重複しないこと、月をまたぐと別ファイルになることも確認する。

### Tests for User Story 1

> **NOTE: 先にテストを書き、実装前に失敗することを確認する**

- [X] T004 [P] [US1] `tests/test_config.py`（新規）に `Config` のレイアウト設定バリデーション
      テストを追加する: (a) `ORG_LAYOUT` 未設定時は `org_layout == "single"` になり既存動作を
      維持する, (b) `ORG_LAYOUT=monthly` かつ `ORG_DIRECTORY` 設定時は正常に読み込める, (c)
      `ORG_LAYOUT=monthly` かつ `ORG_DIRECTORY` 未設定は `ValueError`, (d) `ORG_LAYOUT=single`
      （または未設定）かつ `ORG_FILE_PATH` 未設定は既存通り `ValueError`, (e)
      `ORG_LAYOUT=monthly` の場合は `ORG_FILE_PATH` が未設定でもエラーにならない, (f) 許容値
      以外の `ORG_LAYOUT` は `ValueError`
      (`tests/test_config.py`)
- [X] T005 [P] [US1] `tests/test_monthly_layout.py`（新規、`tests/test_boost_handling.py`と
      同じ「`.env`をtmp_pathに書き`MastodonClient`をモックして`m2o.main()`を呼ぶ」パターンを
      踏襲）に、月別レイアウト有効時の同期テストを追加する: (a) 2026年8月のtootを同期すると
      `<ORG_DIRECTORY>/mastodon/2026/08.org` が作成され、既存と同じ見出し階層
      （`* 2026`→`** 2026-08 8月`→`*** ...`→`**** [...]`）で記録される（Acceptance Scenario
      1）, (b) 同月内で再実行しても重複しない（Acceptance Scenario 2）, (c) 月をまたぐ2件の
      toot（8月・9月）を同期すると `2026/08.org` と `2026/09.org` の2ファイルが作られ、
      互いの内容を上書きしない（Acceptance Scenario 3）
      (`tests/test_monthly_layout.py`)

### Implementation for User Story 1

- [X] T006 [US1] `src/config.py` の `Config.__init__` に `ORG_LAYOUT`（既定 `"single"`）と
      `ORG_DIRECTORY` の読込・バリデーションを実装し、T004のテストをパスさせる
      （contracts/env-config.md 参照。`org_layout: str` / `org_directory: Path | None` の
      型注釈を追加し、`ORG_LAYOUT=monthly` のときのみ `ORG_FILE_PATH` を必須から外す）
      (`src/config.py`)
- [X] T007 [US1] `m2o.py` の同期ループを変更し、`config.org_layout` に応じてtootごとに
      出力先を切り替える: `single` のときは従来通り `config.org_file_path`/
      `config.attach_dir` を使い、`monthly` のときは `monthly_paths(config.org_directory,
      created_at.astimezone())` で得た `(org_path, attach_dir)` を使って都度
      `OrgWriter` を生成してから `add_toot()` を呼ぶ。T005・T006完了後にT005のテストを
      パスさせる
      (`m2o.py`)

**Checkpoint**: User Story 1が単独で完全に動作し、テスト可能な状態になる（MVP）

---

## Phase 4: User Story 2 - 既存mastodon.orgからの一括変換 (Priority: P2)

**Goal**: 既存の単一 `mastodon.org` を入力に、`convert_to_monthly.py` を実行すると
`<Org Directory>/mastodon/YYYY/MM.org` 群が生成され、本文・引用ブロック・画像添付が
過不足なく引き継がれる。添付ファイルはコピーされ、コピー一覧が表示される。

**Independent Test**: 複数年月・引用ブロック・画像添付を含むサンプル `mastodon.org` に
対してコンバーターを実行し、生成された月別ファイル群の内容とtoot件数が元と一致し、
添付ファイルがコピーされてリンクが解決可能であることを確認する。

### Tests for User Story 2

- [X] T008 [P] [US2] `tests/fixtures/sample_mastodon.org` と対応する
      `tests/fixtures/.attach/` 配下の画像ファイルを新規作成する。2つ以上の年・月にまたがる
      toot、`#+BEGIN_QUOTE`〜`#+END_QUOTE` のブースト引用を含むtoot、
      `:PROPERTIES: :ID: ...` ドロワーと `[[attachment:filename]]` リンクを持つ画像添付toot
      を含める（US2・US3のテストで共有する固定フィクスチャ）
      (`tests/fixtures/sample_mastodon.org`, `tests/fixtures/.attach/`)
- [X] T009 [US2] `tests/test_convert_to_monthly.py`（新規）に、T008のフィクスチャを入力として
      コンバーターを実行し、(a) 元ファイルに含まれる年月それぞれについて
      `<出力先>/mastodon/{YYYY}/{MM}.org` が生成され本文・引用ブロックの内容が元と一致する
      こと（FR-004, FR-005）, (b) 生成された全月別ファイルのtoot見出し数の合計が元ファイルの
      toot数と一致すること（SC-002）を検証するテストを追加する
      (`tests/test_convert_to_monthly.py`)
- [X] T010 [US2] `tests/test_convert_to_monthly.py` に追加のテストを書く: (a) 画像添付を含む
      tootについて、コピー先 `<出力先>/mastodon/{YYYY}/.attach/{id[:2]}/{id[2:]}/{filename}`
      にファイルが作成され、元の `tests/fixtures/.attach/` 配下のファイルはバイト単位で
      変更されないこと（FR-011）, (b) コンバーター実行後、標準出力に変換元・変換先パスの
      対応を含む `Copied attachments:` の一覧が表示されること（FR-012, SC-005）, (c) 実行後も
      `tests/fixtures/sample_mastodon.org` の内容が実行前とバイト単位で一致すること
      （非破壊性、FR-007）
      (`tests/test_convert_to_monthly.py`)

### Implementation for User Story 2

- [X] T011 [US2] `convert_to_monthly.py`（新規、`migrate_org.py` と同様の構成）を作成する:
      コマンドライン引数 `<path/to/mastodon.org> <Org Directory>` を受け取り
      （contracts/convert-to-monthly-cli.md 参照）、`src/org_writer.py` の
      `parse_org`/`OrgNode`/`serialize_org` と `monthly_paths()` を再利用して、変換元ツリーを
      年ノード1つ・月ノード1つだけを含む月別ツリーへ分解し、各月のOrgファイルを書き出す
      コア変換ロジックを実装する。T009のテストをパスさせる
      (`convert_to_monthly.py`)
- [X] T012 [US2] `convert_to_monthly.py` に添付ファイルのコピー処理を実装する: 各tootの
      `:PROPERTIES: :ID:` と本文中の `[[attachment:filename]]` を突き合わせて元の添付ファイル
      パス（`<mastodon.orgのあるディレクトリ>/.attach/{id[:2]}/{id[2:]}/{filename}`、
      `src/config.py` の既存の導出規約と同じ）を特定し、
      `<Org Directory>/mastodon/{YYYY}/.attach/{id[:2]}/{id[2:]}/{filename}` へコピーする
      （`shutil.copy2`等でメタデータを保持しつつ元ファイルは変更しない）。コピーした
      (元パス, 先パス) のペアをリストに記録する。T010(a)のテストをパスさせる
      (`convert_to_monthly.py`)
- [X] T013 [US2] `convert_to_monthly.py` の実行末尾に、`Converted:`・
      `Skipped (already exists):`（現時点では常に空）・`Copied attachments:` の3セクションを
      標準出力に表示するレポート機能を実装する（contracts/convert-to-monthly-cli.md の出力
      フォーマットに従う）。T010(b)のテストをパスさせる
      (`convert_to_monthly.py`)

**Checkpoint**: 変換先に競合ファイルが存在しない前提で、User Story 2が単独で完全に動作する

---

## Phase 5: User Story 3 - 変換時の安全確認 (Priority: P3)

**Goal**: 変換先に既に同名の月別ファイルが存在する場合、その月はスキップされ上書きされない。
競合しない月は変換が続行され、スキップされた月の一覧が警告として表示される。

**Independent Test**: 変換先に既に `2026/08.org` が存在する状態でコンバーターを実行し、
その内容が変更されないこと、競合しない他の月は変換されること、スキップ一覧が表示される
ことを確認する。

### Tests for User Story 3

- [X] T014 [US3] `tests/test_convert_to_monthly.py` に追加のテストを書く: (a) 実行前に
      `<出力先>/mastodon/{YYYY}/{MM}.org` の1つをダミー内容で作成しておき、コンバーター実行後も
      その内容が変更されていないこと、かつ競合しない他の月は正常に変換されること
      （FR-006, SC-004、Acceptance Scenario 1）, (b) 標準出力の
      `Skipped (already exists):` に競合した月が、`Converted:` には競合しなかった月のみが
      列挙されること（Acceptance Scenario 2）
      (`tests/test_convert_to_monthly.py`)

### Implementation for User Story 3

- [X] T015 [US3] `convert_to_monthly.py` に、各月を書き出す前に対象の `.org` ファイルが
      既に存在するかどうかのチェックを追加する。存在する場合はその月の書き出し・添付コピーを
      スキップし `skipped_months` に記録、存在しない場合のみT011/T012の処理を実行して
      `converted_months` に記録する。T013のレポート出力の `Skipped (already exists):`
      セクションに `skipped_months` を反映する。T014のテストをパスさせる
      (`convert_to_monthly.py`)

**Checkpoint**: User Story 1・2・3のすべてが独立して動作する

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: ドキュメント整備と最終検証

- [X] T016 [P] `README.md` に `ORG_LAYOUT`/`ORG_DIRECTORY` の設定方法と
      `convert_to_monthly.py` の使い方を追記する
      (`README.md`)
- [X] T017 [P] `README-ja.md` に同内容を日本語で追記する
      (`README-ja.md`)
- [X] T018 [P] `CLAUDE.md` のアーキテクチャ節に月別レイアウト・コンバーターの説明を追記し、
      「実装履歴（Issue対応ログ）」に今回の対応を1行追記する（開発ワークフロー参照）
      (`CLAUDE.md`)
- [X] T019 [quickstart.md](./quickstart.md) の3シナリオ（新規同期・変換・競合スキップ）を
      手動で実行し、記載の期待結果と一致することを確認する
- [X] T020 リポジトリ全体で `.venv/bin/python -m pytest` を実行し、既存テストを含む全テストが
      パスすることを確認する（constitution原則II）

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 依存なし。即座に開始可能
- **Foundational (Phase 2)**: Setupから独立して開始可能だが、全ユーザーストーリーを
  ブロックする
- **User Stories (Phase 3-5)**: すべてFoundational完了後に開始可能
  - 優先度順（P1→P2→P3）に進めることを推奨するが、US1とUS2は互いに依存しないため並行も可能
  - US3はUS2（`convert_to_monthly.py`のコア実装）に依存する
- **Polish (Phase 6)**: 実装対象の全ユーザーストーリー完了後

### User Story Dependencies

- **User Story 1 (P1)**: Foundational完了後に開始可能。他ストーリーへの依存なし
- **User Story 2 (P2)**: Foundational完了後に開始可能。他ストーリーへの依存なし
  （US1とはファイル単位で独立: `src/config.py`/`m2o.py` vs `convert_to_monthly.py`）
- **User Story 3 (P3)**: User Story 2で作成される `convert_to_monthly.py` のコア変換・
  レポート機能（T011〜T013）に依存する

### Within Each User Story

- テストを先に書き、実装前に失敗することを確認する
- 同じファイルを編集するタスクは順番に実行する（並列化しない）
- ストーリーが完了してから次の優先度のストーリーに進む

### Parallel Opportunities

- T001とT002は別ファイルのため並列実行可能
- Foundational完了後、US1のテストタスク（T004, T005）は別ファイルのため並列実行可能
- US1とUS2はファイルが重複しないため、Foundational完了後は並行して着手可能
  （US3はUS2のT011〜T013完了が前提）
- T016, T017, T018（Polish内のドキュメント更新）は別ファイルのため並列実行可能

---

## Parallel Example: Foundational + User Story 1

```bash
# Setup と Foundational のテストは並列可能:
Task: "tests/test_org_writer.py に monthly_paths() の単体テストを追加 (T002)"
Task: ".env.example に ORG_LAYOUT/ORG_DIRECTORY の説明を追加 (T001)"

# Foundational完了後、User Story 1のテストは並列可能:
Task: "tests/test_config.py に Config のレイアウト設定バリデーションテストを追加 (T004)"
Task: "tests/test_monthly_layout.py に月別レイアウト同期テストを追加 (T005)"
```

---

## Implementation Strategy

### MVP First (User Story 1 のみ)

1. Phase 1: Setup を完了
2. Phase 2: Foundational を完了（`monthly_paths()`）— 全ストーリーをブロックするため必須
3. Phase 3: User Story 1 を完了
4. **STOP and VALIDATE**: User Story 1 を独立して検証（quickstartシナリオ1）
5. ここまでで「月別レイアウトへの新規同期」が利用可能になる（MVP）

### Incremental Delivery

1. Setup + Foundational → 基盤完成
2. User Story 1 を追加 → 独立検証 → MVP
3. User Story 2 を追加 → 独立検証（quickstartシナリオ2）→ 既存ユーザーの移行が可能に
4. User Story 3 を追加 → 独立検証（quickstartシナリオ3）→ 変換の安全性が向上
5. Polish（ドキュメント・最終テスト）で完了

---

## Notes

- [P] タスク = 別ファイル・依存関係なし
- [Story] ラベルはトレーサビリティのためユーザーストーリーに対応付ける
- 各ユーザーストーリーは独立して完了・検証可能であること
- 実装前にテストが失敗することを確認する
- タスクごと、または論理的なまとまりごとにコミットする（コミットメッセージは日本語、
  constitution原則V）
- 各チェックポイントでストーリー単位の独立動作を検証してから次に進む
- 同一ファイルを編集するタスクの並列実行、ストーリー間の不要な依存は避ける
