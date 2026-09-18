# 2026-09-18 Claude Code 環境の初期セットアップ

- セッション: https://claude.ai/code/session_0193dhSyUXT7Q4Qfw4D8shfb
- ブランチ / PR: `claude/quirky-goldberg-pl40ka` / [PR #1](https://github.com/battybatty/tutorial/pull/1)
- 状態: 完了（マージ待ち）

## 依頼内容

1. 「僕とのチャットの内容等をもとに Claude Code の環境もセットアップしてください」
2. 「チャットのログやメモリーなど必要事項もこちらにファイルとして作成してください」

## やったこと

### 1 回目: 環境セットアップ

- リポジトリは `.gitattributes` のみの空状態だった。過去のチャット履歴はこのセッションから参照できないため、アカウントに同期されているカスタムスキル（chat-text-format、slack-post-structure、zenshakai-deep-briefing）を「これまで決めたルール」の情報源にした。
- リポジトリが public であることを確認し、社内 ID・個人名・Slack のリンクは除いた。
- 作成したファイル
  - `CLAUDE.md`: 日本語運用、チャット向け文章フォーマット、Slack 投稿ルール、機密ルール、Git 運用
  - `.claude/settings.json`: 読み取り系コマンドの許可、`.env` と鍵ファイルの読み取り拒否、force push 拒否、SessionStart フック登録
  - `.claude/hooks/session-start.sh`: 依存マニフェスト検出時のみインストールする Web 用フック（同期モード）
  - `.claude/skills/chat-text-format/SKILL.md`: 同期スキルをそのまま同梱
  - `.claude/skills/slack-post-structure/SKILL.md`: 実名とリンクを汎用例に置き換えて同梱
  - `.gitignore`、`README.md`
- 検証: フックを `CLAUDE_CODE_REMOTE=true` で実行し正常終了。settings.json の JSON 構文を確認。Lint / テストは対象コード無し。
- コミットして push。ユーザーが UI から PR #1 を作成。

### 2 回目: ログとメモリの作成

- `docs/memory/MEMORY.md`: セッションをまたいで引き継ぐ事実・決定・未決事項。CLAUDE.md から `@` インポートで自動読み込み。
- `docs/chat-logs/`: README（ルールと一覧）、TEMPLATE、このログ。
- CLAUDE.md にメモリの読み込みと、セッション終了時にログ・メモリを更新するルールを追記。

## 決めたこと

- Claude Code の設定は CLAUDE.md と `.claude/` 配下で管理し、個人設定は `settings.local.json` に分ける。
- zenshakai-deep-briefing はリポジトリに入れず、機密ルールのみ一般化して CLAUDE.md に書く。
- SessionStart フックは同期モードで運用する。
- セッション記録は `docs/chat-logs/` に Markdown で残し、生ログはコミットしない。

## 次にやること

- PR #1 を master にマージする。
- コードを追加したら Lint / テストのコマンドを CLAUDE.md に追記する。
- obata-slack-voice スキルが必要なら内容を共有して `.claude/skills/` に追加する。
