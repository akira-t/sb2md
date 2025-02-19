# sb2md for Logseq

エクスポートされた Scrapbox の JSON ファイルから、Markdown 形式のファイルを生成します。

Logseq (や Obsidian) へのインポート用を想定しています。

## 対応している記法

- ~~ハッシュタグ~~ → そのまま出力
  <!-- - 見出しとして解釈されないよう`コードブロック`に変換 -->
- 複数行コード
- リスト表記
- 太字
  - アスタリスク 2 個と 3 個は見出し`### hoge`、`## hoge`に変換するようにしている
- 斜体
- 打消し
- リンク
- 表
- 数式
- 画像埋め込み
  - Gyazoへのリンクをそのまま埋め込み
  - タイトル無し外部リンク `[http://~~]` はすべて画像と決め打ち
  - 埋め込み画像のサイズ記法 `[** [http://~~] ]` に関してはサイズを無視

## Fork元からの変更点

機能追加
- 数式
- 画像埋め込み
- 内部リンク (wikilink)

Logseq への移行を目指した修正

- 行頭に空白がない場合もリスト記号`- `を追加
- ページタイトルは削除（Logseqではファイル名をタイトルとして扱う）
- ハッシュタグ `#AAA` をそのまま使う
- Scrapboxからインポートしたページである旨をタグとして付ける。
  - ```tags:: fromScrapbox```
- ページタイトルにスラッシュがある場合のエスケープ
  - `/`→`_`へ置き換え
- ~~ページタイトルに階層記法を導入している場合の引き継ぎ~~
  - 安全のためコメントアウトしてあります
  - `：`→`/`へ置き換え
  - ファイル名は`/`→`%2F`にエスケープ (for Logseq)

その他修正・差分

- 空白を含むリンクタイトルに対応
  - `[aaa bbb http://~]` → `[aaa bbb](http://~)`
- ScrapboxのJSONバックアップ形式変更への対応
  - 各行のタイムスタンプが入った → 無視する
- exe化していません

## 既知の問題等
- 空白入りリンクとハッシュタグの同一視ができていない
  - Scrapbox では `#AAA_BBB` と `[AAA BBB]` が同じページを指すが現状別々の扱い
- 上位階層のページが存在しない場合
  - `AAA: BBB` のようなページがあって`AAA`のページがない場合に自動的には作らない

## 使い方

<!-- dist フォルダ内の sb2md.exe に JSON ファイルをドラッグ&ドロップしてください。 -->
```console
$ python ./sb2md.py YOUR_SB_BACKUP.json
```

<!-- ## exe 化

pyinstaller を使って exe 化しています。 -->


