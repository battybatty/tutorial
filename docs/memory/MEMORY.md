# プロジェクトメモリ

Claude Code がセッションをまたいで引き継ぐ事実・決定・好みをここに残す。CLAUDE.md から `@docs/memory/MEMORY.md` で読み込まれる。
更新ルール: 新しい決定や好みが分かったら該当セクションに 1 行追加する。古くなった項目は削除せず「（旧）」を付けて残す。

## ユーザーについて

- 日本語でやりとりする。呼びかけは「僕」を使う。
- 文章作成の既定はチャット向け（字下げなし・空行区切り）。Slack 投稿は親 1〜2 行＋スレッド構成。
- Cowork / Claude 側に同期しているカスタムスキル: chat-text-format、slack-post-structure、zenshakai-deep-briefing、obata-slack-voice（未同期・参照のみ）。
- 主な利用ツール: Slack、Asana、Google Drive、Google カレンダー、Gmail。

## このリポジトリについて

- `battybatty/tutorial` は Claude Code の練習用。**public リポジトリ**。
- 社内固有の ID（Slack チャンネル ID、Drive フォルダ ID、Asana gid）や個人名はコミットしない。
- デフォルトブランチは `master`。作業ブランチは Claude Code の UI が割り当てる `claude/...` ブランチ。
- 2026-09-18 時点でアプリケーションコードは無い。依存マニフェストが追加されたら SessionStart フックが自動で拾う。

## 決定事項

- 2026-09-18: Claude Code 環境を CLAUDE.md + `.claude/` 配下で管理する。個人設定は `.claude/settings.local.json`（Git 管理外）。
- 2026-09-18: SessionStart フックは同期モード。起動速度を優先したくなったら非同期に変更する。
- 2026-09-18: zenshakai-deep-briefing スキルは社内 ID を含むためリポジトリに入れず、機密ルールだけを CLAUDE.md に一般化して記載する。
- 2026-09-18: セッションの記録は `docs/chat-logs/` に日付付き Markdown で残す。生の転記ログ（JSONL）はローカルのみ。

## 未決事項・次にやること

- Lint / テストのコマンドが未定（コードが無いため）。追加時に CLAUDE.md に追記する。
- obata-slack-voice スキルはこの環境に同期されていない。必要なら内容を共有してもらい `.claude/skills/` に追加する。
- PR [#1](https://github.com/battybatty/tutorial/pull/1) を master にマージすると全 Web セッションでこの設定が有効になる。
