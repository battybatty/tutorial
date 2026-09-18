# tutorial

Claude Code の練習用リポジトリです。

## Claude Code 環境

- `CLAUDE.md`: プロジェクトの方針（日本語運用、文章フォーマット、機密ルール、Git 運用）
- `.claude/settings.json`: 権限設定と SessionStart フック
- `.claude/hooks/session-start.sh`: Web セッション開始時に依存パッケージを自動インストール
- `.claude/skills/chat-text-format/`: チャット向け文章フォーマット（既定）
- `.claude/skills/slack-post-structure/`: Slack 投稿の構造ルール
- `docs/memory/MEMORY.md`: セッションをまたいで引き継ぐメモリ（CLAUDE.md から自動読み込み）
- `docs/chat-logs/`: セッションごとのチャットログ

個人用の設定は `.claude/settings.local.json` に書く（Git 管理外）。
