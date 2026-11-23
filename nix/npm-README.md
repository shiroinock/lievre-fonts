# @lievre/fonts

lievre の書体です。SIL Open Font License 1.1（`LICENSES/OFL.txt`）。

- `Lievre Sans`：本文の書体。IBM Plex Sans JP の行の箱を、表意文字の字面の枠が行の中央に来るように直したもの。
- `Lievre Term`・`Lievre Term JP`：等幅。英数字は日本語のちょうど半分の幅で、行の中央は Lievre Sans と同じ。

```css
@import '@lievre/fonts';          /* Lievre Sans と Lievre Term JP */
@import '@lievre/fonts/sans.css'; /* Lievre Sans だけ */
@import '@lievre/fonts/term.css'; /* Lievre Term（英数字だけ） */
```

どの CSS も、woff2 を文字の範囲（`unicode-range`）ごとに分けて読み込みます。ページに出る字のファイルだけが読まれます。太さは 400・500・600 です。

`widths.json` は Lievre Term の字の幅（セルの数）の表です。

自分で `@font-face` を書くときは、woff2 を `@lievre/fonts/files/…` で指せます（ファイルの名前と `unicode-range` は CSS を見てください）。

詳しくは https://github.com/shiroinock/lievre-fonts を見てください。
