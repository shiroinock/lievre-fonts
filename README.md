# Lievre Term

[lievre](https://github.com/shiroinock/lievre) の等幅フォントです。端末と、Web の等幅（ログ・コマンドの出力・差分・コード・桁をそろえる表など、日本語も含めて丸ごと等幅で組む場面）の両方で使います。IBM Plex Mono の英数字と IBM Plex Sans JP の日本語を、ちょうど 1:2 の幅に組み合わせています。

PlemolJP も同じ2つから作った 1:2 のフォントですが、Lievre Term には次の違いがあります。

1. **lievre 専用の字形**：カードの角と辺、ボタンの両端、フォーカスの括弧を私用領域 U+E500–E509 に入れています。どれもセルの端までつながるので、`@lievre/tui` の枠が途切れずに描けます。
2. **縦の位置**：Plex Sans JP の漢字は、Plex Sans JP の行の中央より 0.07em 上に寄っています。Lievre Term では行の箱（ascent・descent）のほうを動かして表意文字の字面の枠を行の中央に置き、英数字の字形も行の中央まで上げています。Web の 'Lievre Sans'（Plex Sans JP を `ascent-override` で直したもの）と同じ値です。
3. **英数字の縮め方**：Plex Mono を 5/6 に縮めます。Web の Lievre Mono（`size-adjust: 83.333%`）と同じなので、Web と端末で字の大きさがそろいます。
4. **幅のあいまいな記号**：`○`・`×`・`−`・`↑`・`↓`・罫線などの幅を、`@lievre/tui` が使う string-width と同じ表で決めています。表は `lievre-term-widths.json` として一緒に配ります。

## バリエーション

英字（Plex Mono を 5/6 に縮め、lievre の字形を足したもの）を土台に、日本語の範囲と Nerd Fonts の記号を組み合わせた6つがあります。どれも 400（Regular）・500（Medium）・600（SemiBold）の3つの太さがあります。

| パッケージ | 書体名 | 日本語 | Nerd Fonts | 収録字数 | ttf | woff2 |
|---|---|---|---|--:|--:|--:|
| `lievre-term` | Lievre Term | なし | なし | 1,053 | 106 KB | 27 KB |
| `lievre-term-nf` | Lievre Term NF | なし | あり | 11,677 | 2.2 MB | 938 KB |
| `lievre-term-jp1` | Lievre Term JP1 | JIS 第1水準まで | なし | 5,661 | 1.0 MB | 462 KB |
| `lievre-term-jp1-nf` | Lievre Term JP1 NF | JIS 第1水準まで | あり | 16,284 | 3.1 MB | 1.3 MB |
| `lievre-term-jp` | Lievre Term JP | 全部 | なし | 16,108 | 3.7 MB | 1.7 MB |
| `lievre-term-jp-nf` | Lievre Term JP NF | 全部 | あり | 26,731 | 5.8 MB | 2.6 MB |

大きさは 400 の1ファイルのものです（500・600 もほぼ同じ）。

### どれを選ぶか

- **端末で日本語を表示する、普段使い**：`lievre-term-jp1-nf`。日常の文章とプロンプトの記号がそろい、大きさは JP の半分ほどです。
- **人名・地名・古い文書など、JIS 第2水準以上の漢字も出る**：`lievre-term-jp-nf`（記号が要らなければ `lievre-term-jp`）。
- **日本語はほかのフォントに任せる、英数字と lievre の字形だけ欲しい**：`lievre-term`。端末のフォールバックに日本語のフォントを並べる使い方です。
- **プロンプトやファイラーのアイコンが要る**：名前に `-nf` の付くもの。
- **Web の等幅**：`web/` の CSS を読み込みます。日本語も等幅で組むなら `lievre-term-jp`（字の分だけ読み込まれるので、全部入りでも重くなりません）。英数字だけなら `lievre-term`。

### 日本語の範囲の区切り方

- **なし**：日本語は入れません。
- **JP1（JIS 第1水準まで）**：漢字は JIS X 0208 の第1水準の 2965 字に絞り、かなと記号（JIS X 0208 の非漢字、半角カナ、全角英数など）は Plex Sans JP にあるものをすべて残します。第1水準は使われることの多い漢字を集めた水準で、日常の文章に出る漢字のほとんどを含みます。それでいて Plex Sans JP の漢字の4分の1以下で済みます。2010 年に常用漢字に加わった字の一部（「曖」「嗅」「丼」「喩」「籠」など第2水準のもの）は入らないので、ときどき端末のフォールバックに回ります。
- **JP（全部）**：Plex Sans JP にある 1万3千字あまりの漢字をすべて入れます。

区切りを JIS の水準にしたのは、Python の EUC-JP の表から引けて、外部の一覧を持たずにビルドできるからです。

### Nerd Fonts の記号

`-nf` の付くものには、Nerd Fonts 3.5.1 の Symbols Nerd Font Mono の記号を**すべて**入れています（Powerline、Font Awesome、Material Design、Codicons、Devicons、Octicons など 13 の集合、1万字あまり）。一部だけにしないのは、starship・eza・lazygit・Neovim のプラグインなどが集合をまたいで記号を使い、どれかを外すと気づきにくい欠けが出るからです。大きさの多くは Material Design（約 6900 字）が占めます。

lievre の私用領域 U+E500–U+E53F は、Nerd Fonts 3.5.1 が使っていない隙間（U+E3E3 で終わり U+E5FA から再開）なので重なりません。集合ごとのライセンスは [LICENSES/README.md](LICENSES/README.md) にまとめ、本文を同梱しています。

## 寸法

- 全角が 1000、半角が 500（UPM 1000）。どの字の送り幅も、幅の表のセルの数 × 500 です。
- セルの高さは 1.2em（ascent 980、descent 220）。中心はベースラインの 0.38em 上です（下の「縦の位置」）。
- 罫線とブロック（U+2500–259F）は、縦もセルの高さに合わせて引き伸ばすので、上下の行とつながります。
- Powerline の区切り（U+E0B0–E0D7）は、セルいっぱいに引き伸ばします。そのほかの Nerd Fonts の記号は、セルの幅に合わせて縮め、セルの中央に置きます。
- 幅の表で 1 セルなのに全角で描かれている字（Plex Mono にない `○` など）は、形を変えずに縮めて半角に収めます。
- lievre の字形の線の太さは、太さによらず一定（42）です。Plex Mono の罫線も太さによって変わらないので、`─` と並べても継ぎ目がずれません。

寸法の数は [src/lievre_term/config.py](src/lievre_term/config.py) にまとめています。

### 縦の位置

決まりは「表意文字の字面の枠を、行の箱の中央に置く」です。Web の 'Lievre Sans' と同じ決まりで、同じ値になります。

- Plex Sans JP の表意文字の字面の枠は -0.12〜0.88em（BASE テーブルの ideo。字の墨の枠 icfb・icft も -0.075〜0.835em）で、中央はベースラインの 0.38em 上です。
- Plex Sans JP そのままの行の箱（ascent 1.06em、descent 0.44em）の中央は 0.31em 上なので、漢字は 0.07em 上に寄ります。
- Lievre Term は ascent 0.98em、descent 0.22em にして、行の箱の中央を 0.38em 上に置きます。日本語の字形は動かしません（`JP_SHIFT = 0`）。
- 英数字（Plex Mono を 5/6 に縮めた字）は、英大文字の高さ 0.582em の中央 0.291em が行の中央 0.38em に来るように、字形を 0.089em 上げます（`LATIN_SHIFT = 89`）。罫線・ブロック・lievre の字形はセルに合わせて描くので動かしません。
- Web の 'Lievre Sans' は `ascent-override: 113%; descent-override: 37%; line-gap-override: 0%` で、同じく中央が 0.38em 上に来ます（(1.13 − 0.37) / 2 = 0.38）。

日本語の字形を動かさないのは、Web で本文（Lievre Sans）の中に等幅（Lievre Term）を並べたとき、ブラウザがベースラインで字をそろえるからです。行の箱のほうで直すので、等幅の漢字は本文の漢字と同じ高さに並びます。

英数字だけは、本文と中央をそろえるかベースラインをそろえるかのどちらかしか選べません。等幅の英大文字（0.582em）は本文の英大文字より背が低いので、中央をそろえるとベースラインがずれます。Lievre Term は中央をそろえるほうを取りました。端末のセルの中でも、等幅の段落でも、本文の中に並べても、英数字・かな・漢字の見た目の中央が行の中央に来ます。代わりに、本文の中に並べた等幅の英数字のベースラインは、本文より 0.089em（16px で約 1.4px）上になります。

測り方は Web 側と同じで、Chromium の canvas に 10000px で描き、`measureText` から上寄りを (A − D − 墨の上 − (−墨の下)) / 2 で出しました（A・D は fontBoundingBox、墨は actualBoundingBox。正なら中央より下）。400 の値は次のとおりです。

| 字 | Plex Sans JP そのまま | Lievre Sans | Lievre Term |
|---|--:|--:|--:|
| 漢字（永・国） | −0.074〜−0.078em | −0.006〜+0.019em | −0.006〜+0.021em |
| かな（あ） | −0.072〜−0.074em | −0.009em | −0.009em |
| 英大文字・数字（H・0） | −0.061em | +0.013em | 0.000em |

Lievre Sans の列は、Plex Sans JP に `ascent-override: 113%; descent-override: 37%` を付けて同じページで測った値です。

テストは、行の箱の中央が字面の枠の中央（0.38em）にあること、代表的な漢字の墨の中央がそこから 0.012em 以内、英大文字と数字の墨の中央が 0.006em 以内にあることを確かめます。数は [src/lievre_term/config.py](src/lievre_term/config.py) の `CELL_CENTER`・`ASCENT`・`DESCENT`・`JP_SHIFT`・`LATIN_SHIFT` です。

## 幅の表

`lievre-term-widths.json` は、すべての符号位置のセルの数です。`@lievre/tui` が使う string-width 8（`ambiguousIsNarrow: true`）の決まりを1文字ずつに当てはめ、Unicode 18.0.0 のデータ（get-east-asian-width 1.7.0 と同じ版）から作ります。

```json
{ "format": 1, "unicode": "18.0.0", "default": 1, "zero": [[0, 31], ...], "wide": [[4352, 4447], ...] }
```

`zero` と `wide` に含まれない符号位置は `default`（1）です。

- 0：Default_Ignorable_Code_Point、一般カテゴリが Cc・Cf・Mn・Me・Cs
- 2：RGI の絵文字（1文字のもの）、East Asian Width が W か F
- 1：それ以外。幅のあいまいな A も、私用領域も 1

string-width 8.3.0 と全符号位置で比べると、East Asian Width による幅はすべて一致します。違うのは、Unicode 17・18 で足された結合文字 70 字だけです（Node 24 の正規表現のデータがまだその版でないため、string-width は 1 を返します）。このフォントにその字は入っていません。

## 使う

### Nix

```sh
nix build github:shiroinock/lievre-fonts#lievre-term-jp1-nf
ls result/share/fonts/truetype
```

`result/share/lievre-term/` に ttf・woff2・`widths.json`・`LICENSES` がそろいます。`nix build` だけなら、6つのバリエーションすべて（`packages.default`）を作ります。

nix-darwin や NixOS では、flake の入力に足して `fonts.packages` に入れます。

```nix
{
  inputs.lievre-fonts.url = "github:shiroinock/lievre-fonts";
  # ...
  fonts.packages = [ inputs.lievre-fonts.packages.${pkgs.system}.lievre-term-jp1-nf ];
}
```

### Web

`result/share/lievre-term/web/`（Releases では `lievre-term-web-<版>.zip` か、バリエーションごとの zip の `web/`）に、バリエーションごとの CSS と、`unicode-range` で分けた woff2（`files/`）があります。CSS は `files/` を相対の URL で読むので、`web/` をそのまま置いて読み込みます。

```html
<link rel="stylesheet" href="/fonts/lievre-term/lievre-term-jp.css">
<style>
  pre, code, .log { font-family: 'Lievre Term JP', monospace; }
</style>
```

- 書体名は端末用と同じ（`'Lievre Term JP'` など）で、太さは 400・500・600 です。
- ファイルは `base`（英数字・記号・罫線・lievre の字形）、`kana`（かな・全角の記号）、`kanji1-0`〜（JIS 第1水準を 500 字ずつ）、`kanji2-0`〜（そのほかの漢字を 1000 字ずつ）、`nf-pl`・`nf`・`nf-md`（Nerd Fonts）に分かれています。ブラウザはページに出る字を含むものだけを読み込みます。英数字だけのページなら `base` の 1 つ（約 30〜60 KB）で、ふつうの日本語のページなら `base`・`kana`・第1水準のいくつか（合わせて 500 KB ほどまで）です。
- 1つにまとまった woff2 も `woff2/` にあります。

### GitHub Releases

[Releases](https://github.com/shiroinock/lievre-fonts/releases) に、各バリエーションの ttf・woff2、バリエーションごとの zip、`lievre-term-widths.json`、`LICENSES.zip` があります。

### 端末の設定

書体名（`Lievre Term JP1 NF` など）を指定します。幅のあいまいな字を全角で描く設定は切ってください（iTerm2 の「Ambiguous characters are double-width」、WezTerm の `treat_east_asian_ambiguous_width_as_wide` など）。このフォントと `@lievre/tui` は、あいまいな字を半角として扱います。

```text
# Ghostty の設定
font-family = "Lievre Term JP1 NF"
```

### 持たないもの

- 合字や `zero` などの OpenType の機能（GSUB・GPOS）は持ちません。端末ではほとんど使わないためです。
- ヒントは持たず、どの大きさでも滑らかに描く設定（gasp）にしています。
- 斜体はありません。

## 作る

```sh
nix develop
lievre-term-build fonts --sources "$LIEVRE_TERM_SOURCES" --ucd "$LIEVRE_TERM_UCD" --out out --variant lievre-term-jp1 --weight 400
lievre-term-build widths --ucd "$LIEVRE_TERM_UCD" --out out/widths.json
LIEVRE_TERM_FONTS=out pytest
```

`nix develop` の中では `lievre-term-build` の代わりに `python -m lievre_term.build` でも動きます。元にする Plex・Nerd Fonts・Unicode のデータは [nix/sources.nix](nix/sources.nix) で版とハッシュを固定していて、ビルドの中ではネットワークに出ません。

確かめるのは次の2つです。`nix flake check` は全バリエーションを作ってからテストを流します。

```sh
nix flake check
nix fmt
```

テスト（[tests/test_fonts.py](tests/test_fonts.py)）は、どのフォントでも次を確かめます。

- すべての字の送り幅が幅の表と一致する（英数字は日本語のちょうど半分）
- lievre の字形がセルの外へ出ず、つながる辺がセルの端に届く
- 罫線が隣のセルとつながる
- 漢字の字面がセルの中央にある
- バリエーションごとの収録範囲（JP1 は第1水準の 2965 字だけ、など）
- 書体名に予約された名前（Plex など）を使っていない

### 公開する

1. `src/lievre_term/config.py` と `pyproject.toml` と `flake.nix` の版を上げる PR をマージする。
2. `v0.1.0` のようにタグを打って push する。GitHub Actions（[release.yml](.github/workflows/release.yml)）が Releases を作ります。

## ライセンス

SIL Open Font License 1.1（[LICENSES/OFL.txt](LICENSES/OFL.txt)）。Nerd Fonts の記号は集合ごとのライセンスに従います（[LICENSES/README.md](LICENSES/README.md)）。
