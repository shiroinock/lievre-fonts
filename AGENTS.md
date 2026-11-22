# エージェント向けの作業メモ

lievre-fonts のリポジトリで作業する AI エージェント向けです。書体の作りと使い方は [README.md](README.md) にあります。

## 場所

Python のパッケージ `lievre_term`（`src/lievre_term/`）と、それを組む Nix の flake です。

- `config.py`：寸法・太さ・バリエーション・版の決まり。数を変えるときはここだけを触る。
- `build.py`：Lievre Term を組む入り口（`fonts`・`widths`・`sans` の命令）。
- `condense.py`：英数字を横だけ縮めて線を補う。`glyphs.py`：lievre 専用の字形（U+E500–E509）。
- `widths.py`：幅の表（string-width 8 と同じ決まり、Unicode の版は `UNICODE_VERSION`）。`jis.py`：JIS 第1水準の表。
- `sans.py`：Lievre Sans。`web.py`：unicode-range で分けた woff2 と @font-face の CSS。
- テストは `tests/test_fonts.py`。元にする Plex・Nerd Fonts・Unicode のデータは `nix/sources.nix` で版とハッシュを固定する。npm のパッケージ `@lievre/fonts` の README は `nix/npm-README.md`。

## 確かめる

```sh
nix flake check
nix build
nix fmt
```

- `nix flake check` は全バリエーションを組んでからテストを流す。時間がかかるので、裏で流す。
- 手元で一部だけ試すときは `nix develop` の中で `python -m lievre_term.build ...` を使い、`LIEVRE_TERM_FONTS=out pytest` で確かめる（命令は README の「作る」）。組んでいないフォントのテストは飛ぶので、最後は `nix flake check` で全部を通す。
- ビルドの中ではネットワークに出ない。元のデータを足すときは `nix/sources.nix` に版とハッシュを書く。

## 約束

- 文書・コミット・PR は日本語。英大文字の飾りラベルは使わない。
- 寸法やバリエーションを変えたら、README の表と説明（収録字数・大きさ・寸法）も合わせて直す。
- 版を上げるときは `src/lievre_term/config.py` の `VERSION`、`pyproject.toml`、`flake.nix`（`version` と npm の .tgz の名前、いくつかある）をそろえる。そのあとタグ `v*` を push すると `release.yml` が Releases を作る（README の「公開する」）。
- main に直接 push せず、ブランチを切って PR にする。レビューは共通ワークフロー（shiroinock/workflows）の Claude が行い、検査 `review / verdict` が必須。指摘が 0 件になるとラベル「マージ予約」が付き、自動マージされる。
- `.github/workflows` を変える PR は手でマージする。マージはそのたびにユーザーの OK を取る。
- lievre の側の作業（`@lievre/tui` に幅の表をつなぐ、Web の書体を `@lievre/fonts` に置き換える）は lievre のリポジトリで行い、ここでは扱わない。
