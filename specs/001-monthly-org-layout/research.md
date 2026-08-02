# Research: 月別Orgファイルレイアウトと移行コンバーター

**Feature**: [spec.md](./spec.md) | **Date**: 2026-08-02

spec.mdの `Assumptions` で「Plan フェーズで決定する」とされていた技術的な決定事項を
ここで確定する。既存コード（`src/config.py`、`src/org_writer.py`、`m2o.py`、
`migrate_org.py`）の実装を踏まえた設計判断。

## 1. レイアウトモードの設定方法

**Decision**: `.env` に新しい環境変数 `ORG_LAYOUT`（`single`（デフォルト）| `monthly`）と
`ORG_DIRECTORY`（`ORG_LAYOUT=monthly` の場合のみ必須）を追加する。`ORG_DIRECTORY` が
`<Org Directory>` に相当し、ツールはその配下に `mastodon/YYYY/MM.org` を生成する。

**Rationale**: 既存の `BOOST_HANDLING` と同じ「デフォルト値ありのオプション環境変数」
パターンを踏襲することで、既存ユーザーは `.env` を変更しなければ今まで通り単一ファイル
モードのまま動作する（後方互換性を破らない = constitution原則I「シンプルさ優先」・
既存ユーザーデータ保護に合致）。

**Alternatives considered**:
- `ORG_FILE_PATH` の値自体をディレクトリかファイルかで自動判別する案 → 既存ユーザーの
  設定を暗黙的に再解釈することになり、意図しない挙動変化のリスクが高いため却下。
- コマンドライン引数でモードを切り替える案 → `m2o.py` は cron 実行を想定しており、
  環境変数の方が既存の運用（`.env` 経由の設定）と一貫する。

## 2. 月別ファイルへの書き込み方式

**Decision**: `src/org_writer.py` の `parse_org` / `serialize_org` / `insert_sorted` は
ロジックを一切変更しない。`OrgWriter` には後日（実機検証後、§6参照）任意引数
`attach_property_dir` を追加した。`m2o.py` 側で、tootごとに `created_at` の
ローカル年月から出力先パス（`ORG_LAYOUT=monthly` の場合は
`ORG_DIRECTORY/mastodon/{year}/{month:02d}.org`、`attach_dir` は
`ORG_DIRECTORY/mastodon/{year}/images`）を都度計算し、その都度
`OrgWriter(target_path, target_attach_dir, attach_property_dir="images/")` を生成して
`add_toot()` を呼び出す。

**Rationale**: FR-010（月別ファイル内でも年→月→日→tootの4階層をそのまま維持する）を
選択したことで、月別ファイルは「年ノードが1つ・その下に月ノードが1つだけ存在する
単一ファイルレイアウトのサブセット」として扱える。既存の `add_toot()` は年/月/日見出しを
探索・作成するロジックを既に持っているため、出力先ファイルパスだけを差し替えれば
そのまま正しく動作する。constitution原則I（シンプルさ優先: 時期尚早な抽象化の禁止）に
最も合致するアプローチ。

**Alternatives considered**:
- 月別ファイル内の見出し階層を年/月を省略した3階層（日→toot）に変更する案 →
  clarifyセッションでFR-010として既存階層維持が確定したため不採用。
- `OrgWriter` にレイアウトモードの概念を持ち込み、内部でパス解決も行わせる案 →
  `OrgWriter` の責務（Orgツリーの読み書き）が肥大化し、単一ファイルモードの既存動作の
  リスクが増えるため、パス解決は呼び出し側（`m2o.py`）に留める。

## 3. 冪等性・部分失敗時の整合性

**Decision**: `m2o.py` の同期ループ・`state.json` 更新ロジックは変更しない。月別レイアウト
でも、tootごとに独立して対象ファイルを再パース・再シリアライズして上書き保存する既存の
`add_toot()` の動作がそのまま使えるため、追加の考慮は不要。

**Rationale**: `state.json` の `last_sync_toot_id` はMastodon APIとの同期位置のみを追跡し、
出力先ファイルのレイアウトとは独立している。月をまたぐtootのバッチでも、tootごとに
対象月ファイルへ振り分けて書き込むだけなので、既存の冪等性保証（constitution原則III）は
そのまま維持される。

**Alternatives considered**: 月ファイルごとにトランザクション的な書き込み保証を追加する案 →
既存の単一ファイルモードでも同様の保証はなく、スコープ外の一般的な信頼性強化になるため
不採用（constitution原則Iに反する時期尚早な複雑化）。

## 4. 既存mastodon.orgからのコンバーター設計

**Decision**: 新規スクリプト `convert_to_monthly.py`（`migrate_org.py` と同じ「手動実行の
単体スクリプト」パターン）を追加する。使い方: `python convert_to_monthly.py
<path/to/mastodon.org> <Org Directory>`。

処理内容:
1. `parse_org()` で変換元ファイルを読み込み、既存の年見出し（`* YYYY`）ツリーを取得する
   （変換元は `migrate_org.py` 適用後の「年見出しあり」フォーマットであることを前提とする）。
2. ツリーの各 `* YYYY` ノード配下の各 `** YYYY-MM` ノードについて:
   - 出力先 `ORG_DIRECTORY/mastodon/{YYYY}/{MM}.org` が既に存在する場合は、その月を
     スキップし、スキップ一覧に記録する（FR-006）。
   - 存在しない場合、その年ノード1つ・月ノード1つだけを含む新しいツリーを組み立てて
     `serialize_org()` で書き出す（既存の階層をそのまま維持 = FR-010 と整合）。
3. 各月のコンテンツ行から `[[attachment:filename]]` リンクと、同じtoot見出し直下の
   `:PROPERTIES: :ID: ...` を突き合わせて元の添付ファイルパス
   （`<変換元.attachディレクトリ>/{id[:2]}/{id[2:]}/{filename}`）を特定し、
   `ORG_DIRECTORY/mastodon/{YYYY}/images/{filename}`（ID分割なしのフラット構成）へ
   コピーする（元ファイルは変更しない = FR-011。詳細は§6参照）。
4. 実行完了後、スキップした月の一覧（FR-006）とコピーした添付ファイルの
   変換元・変換先パスの一覧（FR-012）を標準出力に表示する。

**Rationale**: `org_writer.py` が提供する `parse_org`/`serialize_org`/`OrgNode` を
そのまま再利用でき、`migrate_org.py` が既に実証しているパターン（読み込み→ツリー再構成→
書き出し）を踏襲することで実装リスクを最小化できる。添付ファイルの実体は
`[[attachment:filename]]` というファイル名のみのリンクで、実際の格納ディレクトリは
見出し直下の `:PROPERTIES: :ID:` から `org-attach` 規約（`id[:2]/id[2:]/`）で算出する
必要があるため、変換時に両者を突き合わせる処理が必須となる。

**Alternatives considered**:
- `m2o.py` 本体に変換モードを統合する案 → spec のAssumptionsで「`migrate_org.py` と同様の
  手動スクリプトとして提供し、`m2o.py` には統合しない」と明記済みのため不採用。
- 変換元が「年見出しなし」旧フォーマットの場合の自動対応 → 現行の `mastodon.org` は
  既に `migrate_org.py`（コミット `48b5a68`）で年見出し形式に移行済みであり、スコープ外の
  後方互換ケースとして扱う（CLAUDE.md記載の既存アーキテクチャに準拠）。

## 5. テスト方針

**Decision**: 以下のテストを追加する（constitution原則II）。
- `tests/test_org_writer.py` または新規ファイルに、`OrgWriter` を月別ファイルパス・
  年別attachパスで呼び出した場合でも既存同様に動作することを確認するテストケースを追加。
- 新規 `tests/test_convert_to_monthly.py` で、複数月・複数年にまたがるサンプル
  `mastodon.org`（引用ブロック・画像添付を含む）を用意し、
  - 全toot件数が変換前後で一致すること（SC-002）
  - 既存の月別ファイルがある場合にスキップされ、上書きされないこと（SC-004）
  - 添付ファイルがコピーされ、コピー一覧が出力されること（SC-005）
  を検証する。

**Rationale**: constitution原則II「テストによる回帰防止」により、Orgファイル構造や
コンバーターの変更には対応するテストが必須。

## 6. Emacs実機検証で判明した添付ディレクトリの解決方式（実装後の修正）

**Decision**: 当初FR-009で決めた「`.attach/{id[:2]}/{id[2:]}/` のID分割ディレクトリ構成」
から、「`images/` 直下へのID分割なしのフラット構成 ＋ 各月別ファイル先頭への
`#+PROPERTY: ATTACH_DIR images/` 自動挿入」に変更した。この変更は**月別レイアウトのみ**
が対象で、単一ファイルモードの保存形式（`.attach/`のID分割構成、`attachment:`リンク、
`ATTACH_DIR`プロパティなし）は一切変更しない。あわせて、月別レイアウトはID分割を
行わずファイル名（`toot_{toot_id}_{index}.{ext}`）の一意性のみでパスが一意に定まる
ため、パス解決用のUUID生成・`:PROPERTIES: :ID: :END:` ドロワーの挿入自体も
月別レイアウトでは行わない（単一ファイルモードは引き続き挿入する）。

**Rationale**: 実機（Doom Emacs）検証の結果、`[[attachment:filename]]` リンクの
インライン画像表示は、Emacsのグローバル変数 `org-attach-id-dir`
（Doomの `+org` モジュールは既定で `org-directory` 直下の `.attach/` に固定する）に
依存して解決されることが判明した。単一ファイルモードでは `ORG_FILE_PATH` の親
ディレクトリがこの値とたまたま一致していたため問題が表面化しなかったが、月別
レイアウトでは `mastodon/{YYYY}/` という追加の階層があるため一致せず、画像が
表示できなかった。

Orgの `ATTACH_DIR` プロパティを明示すればグローバル設定に依存せず解決できることを
確認したが、`ATTACH_DIR` が明示されている場合、Emacsは `{ATTACH_DIR}/{filename}`
という**ID分割なしのフラットパス**を期待することも判明した。既存のID分割構成
（`.attach/{id[:2]}/{id[2:]}/`）とは非互換であり、単一ファイルモードに既に保存済みの
画像添付（もしあれば）が壊れるリスクがあるため、単一ファイルモードでは採用しない。
月別レイアウトは新規機能でまだ既存データがないため、影響なく採用できる。

**Alternatives considered**:
- `[[file:相対パス]]` リンクへの変更（`attachment:`をやめる）→ 実機で動作確認済みだが、
  ユーザーの意向により不採用。`ATTACH_DIR` プロパティ方式の方が `org-attach-open` 等の
  org-attach管理コマンドとの互換性を保てるため。
- 単一ファイルモードにも同じ修正を適用する案 → 既存データ破壊のリスクがあるため、
  ユーザーの判断で月別レイアウトのみに限定。
- 各年ディレクトリに `.dir-locals.el` を自動生成し `org-attach-id-dir` を上書きする案 →
  実装が複雑になり、Emacsのグローバル設定を部分的に上書きする形になるため不採用。
