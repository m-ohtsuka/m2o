# Implementation Plan: 月別Orgファイルレイアウトと移行コンバーター

**Branch**: `001-monthly-org-layout` | **Date**: 2026-08-02 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-monthly-org-layout/spec.md`

## Summary

tootの保存先として、既存の単一ファイル（`ORG_FILE_PATH`）に加え、
`<Org Directory>/mastodon/YYYY/MM.org` の形式で年ディレクトリ・月ファイルに分割する
レイアウトモードを新しい環境変数 `ORG_LAYOUT`（既定 `single` / 新規 `monthly`）と
`ORG_DIRECTORY` で選択可能にする。月別ファイル内の見出し階層は既存と同一
（年→月→日→toot）を維持し、既存の `OrgWriter` のツリー操作ロジックは変更せず、
`m2o.py` 側でtootごとに出力先パスを計算して渡す薄い変更のみで実現する。
併せて、既存の単一 `mastodon.org` を月別レイアウトへ一括変換する非破壊的な
コンバータースクリプト `convert_to_monthly.py`（`migrate_org.py` と同じ手動実行パターン）
を新規追加する。変換時、添付ファイルはコピー（元は保持）し、変換先に既存ファイルが
ある月はスキップして一覧を警告表示、コピーした添付ファイルの一覧も表示する。

## Technical Context

**Language/Version**: Python 3.8以上（既存の対応バージョンを踏襲）

**Primary Dependencies**: 既存の `Mastodon.py`, `beautifulsoup4`, `python-dotenv`,
`requests` のみ。新規依存追加なし。

**Storage**: ファイルシステム上のOrg-modeテキストファイルと画像ファイル（DB等は使用しない）

**Testing**: pytest（既存 `tests/` 配下に追加。`.venv/bin/python -m pytest`）

**Target Platform**: ローカルCLI（macOS/Linux、cronによる定期実行を想定）

**Project Type**: single（CLIスクリプト群。フロントエンド/バックエンド分離なし）

**Performance Goals**: 定量的な性能目標なし（N/A）。個人アカウントの想定toot件数
（数百〜数千件、spec Edge Cases参照）の変換が実用的な時間（数分程度）で完了すればよい。

**Constraints**:
- 既存の単一ファイルレイアウトの出力形式・`org-attach` 互換性を変更しない。
- コンバーターは非破壊的（変換元のOrgファイル・添付ファイルを変更/削除しない）。
- `state.json` ベースの冪等な増分同期（constitution原則III）を壊さない。

**Scale/Scope**: 単一ユーザー・単一Mastodonアカウント（constitution原則I前提）。
既存3ソースファイル（`src/config.py`, `m2o.py`, 新規`convert_to_monthly.py`）への変更・
追加が中心で、`src/org_writer.py` のコア関数（`parse_org`/`serialize_org`/
`insert_sorted`/`get_node_sort_key`）は変更しない。

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| 原則 | 判定 | 根拠 |
|---|---|---|
| I. シンプルさ優先 | PASS | `OrgWriter`のコアロジックは無変更、`m2o.py`にパス解決の薄いロジックのみ追加。設定は既存の`BOOST_HANDLING`と同じ「デフォルト値ありの環境変数」パターンを踏襲。新規スクリプトは`migrate_org.py`と同じ手動実行パターンを再利用し、新しい抽象化層は導入しない。 |
| II. テストによる回帰防止 | PASS（実行時に担保） | Phase設計で`tests/test_convert_to_monthly.py`新規追加と`test_org_writer.py`への月別パス動作テスト追加を計画（research.md §5）。実装フェーズ（`/speckit-tasks`以降）でテスト未整備のままマージしない。 |
| III. 冪等な増分同期 | PASS | `state.json`の更新ロジック・`add_toot()`のファイル単位の再パース＆上書き保存という既存の冪等性保証の仕組みをレイアウトに関わらず維持する（research.md §3）。 |
| IV. 型安全性 | PASS（実装時に担保） | `Config`に追加する`org_layout`/`org_directory`フィールドに型注釈を付与する（data-model.md参照）。 |
| V. 日本語での開発コミュニケーション | PASS | 本ドキュメント一式・今後のコミットメッセージも日本語で記述する。 |

違反なし。Complexity Trackingセクションは不要。

## Project Structure

### Documentation (this feature)

```text
specs/001-monthly-org-layout/
├── plan.md              # 本ファイル（/speckit-plan コマンド出力）
├── research.md          # Phase 0 出力
├── data-model.md        # Phase 1 出力
├── quickstart.md        # Phase 1 出力
├── contracts/           # Phase 1 出力
│   ├── env-config.md
│   └── convert-to-monthly-cli.md
└── tasks.md             # Phase 2 出力（/speckit-tasks コマンド、本コマンドでは作成しない）
```

### Source Code (repository root)

既存の単一プロジェクト構成をそのまま維持する（新しいトップレベルディレクトリは作らない）。

```text
src/
├── config.py           # 変更: ORG_LAYOUT / ORG_DIRECTORY の読込・バリデーションを追加
├── org_writer.py        # 変更なし（OrgNode / parse_org / serialize_org / insert_sorted / OrgWriter を再利用）
├── org_formatter.py     # 変更なし
└── mastodon_client.py   # 変更なし

m2o.py                   # 変更: tootごとにレイアウトモードへ応じた出力先パス(org_path/attach_dir)を
                          #       計算してから OrgWriter を呼び出すよう変更
convert_to_monthly.py    # 新規: 既存 mastodon.org を月別レイアウトへ変換するコンバータースクリプト

tests/
├── test_org_writer.py       # 変更: 月別パスでの OrgWriter 呼び出しのテストケースを追加
├── test_org_formatter.py    # 変更なし
├── test_boost_handling.py   # 変更なし
└── test_convert_to_monthly.py  # 新規: コンバーターのテスト
```

**Structure Decision**: 既存のフラットな単一プロジェクト構成（`src/` + ルート直下の
エントリースクリプト + `tests/`）を維持する。新機能はこの構成に自然に収まるため、
ディレクトリ構成自体の変更は行わない（constitution原則I）。

## Complexity Tracking

*本セクションは記入不要（Constitution Checkに違反なし）。*
