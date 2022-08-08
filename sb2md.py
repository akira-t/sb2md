import json
import sys
import re
import os


def main():
    filename = sys.argv[1]
    with open(filename, 'r', encoding='utf-8') as fr:
        sb = json.load(fr)
        outdir = 'pages/'
        if not os.path.exists(outdir):
            os.mkdir(outdir)
        for p in sb['pages']:
            title = convert_title(p['title'])
            lines = p['lines']
            is_in_codeblock = False
            is_in_table = False
            row = -1
            filename = title.replace('/', '%2F')  # for Logseq
            with open(f'{outdir}{filename}.md', 'w', encoding='utf-8') as fw:
                for i, line in enumerate(lines):
                    # line <- {'text': '4月1日。今日はいい天気だ。', 'created': 1587518753, 'updated': 1650352301}
                    l = line['text']
                    if i == 0:
                        # l = '# ' + l  # Logseqではページタイトルはファイル名
                        fw.write('tags:: fromScrapbox' + '\n\n')  # for Logseq tag
                        continue
                    else:
                        # 複数行コードブロックの処理
                        if l.startswith('code:'):
                            is_in_codeblock = True
                            l += f'\n```'
                        elif is_in_codeblock and not l.startswith(('\t', ' ', '　')):
                            is_in_codeblock = False
                            fw.write('```\n')
                        # テーブルの処理
                        if l.startswith('table:'):
                            is_in_table = True
                        elif is_in_table and not l.startswith(('\t', ' ', '　')):
                            is_in_table = False
                        if is_in_table:
                            row += 1
                            if row != 0:
                                l = l.replace('\t', '|') + '|'
                                if l.startswith(' '):
                                    l = l.replace(' ', '|', 1)
                            if row == 1:
                                col = l.count('|')
                                l += f'\n{"|-----" * col}|'
                        # コードブロックでなければ変換
                        if not is_in_codeblock:
                            l = convert(l)
                    # リストや見出し以外には改行を入れる
                    if not (is_in_codeblock or is_in_table or l.startswith('#') or re.match(r' *- | *[0-9]+. ', l) or l == ""):
                        l += '  '
                    fw.write(l + '\n')
                if is_in_codeblock:
                    fw.write('```\n')


def convert_title(l: str) -> str:
    '''
    ページタイトルの変換
    上位階層のページのリスト
    '''
    l = l.replace('/', '_')
    # l = l.replace('：', '/')  # for Logseq hierarchy (ページ階層を「：」で表現していた場合)
    return l

def convert(l: str) -> str:
    # l = escape_hash_tag(l)  # ハッシュタグはそのまま使う (for LogSeq)
    l = convert_list(l)
    l = convert_bold(l)  # 画像の拡大[* [http://~]] は中身だけ取り出す
    l = convert_decoration(l)
    l = convert_latex(l)
    l = convert_link(l)  # convert_bold よりも後に実行する必要（[[]]のため）
    return l


def escape_hash_tag(l: str) -> str:
    '''
    ハッシュタグをコードブロックに変換。
    '''
    for m in re.finditer(r'#(.+?)[ \t]', ignore_code(l)):
        l = l.replace(m.group(0), '`' + m.group(0) + '`')
    if l.startswith('#'):  # 1行全てタグの場合
        l = '`' + l + '`'
    return l


def convert_list(l: str) -> str:
    '''
    先頭の空白をMarkdownのリストに変換。
    空白がない場合もリストにする `AAA` → `- AAA`
    '''
    m = re.match(r'[ \t　]+', l)
    if m:
        # 空白の個数分インデントする
        l = l.replace(m.group(0),
                      (len(m.group(0)) - 1) * '  ' + '- ', 1)
    elif len(l)>1:
        if not re.match(r'[-\*]+', l):
            l = '- ' + l  # Logseq では全てはリスト
    return l


def convert_bold(l: str) -> str:
    '''
    太字([[]]、**、***)をMarkdownに変換。
    '''
    for m in re.finditer(r'\[\[(.+?)\]\]', ignore_code(l)):
        l = l.replace(m.group(0), '**' + m.group(1) + '**')
    for m in re.finditer(r'\[\*+?\s+?(\[[^ \]]+?\])\s*?\]', ignore_code(l)):
        # 画像の拡大？ → 中身だけ取り出す
        # [*** [https://gyazo.com] ] -> [https://gyazo.com]
        l = m.group(1)
    m = re.match(r'\[(\*\*|\*\*\*) (.+?)\]', ignore_code(l))  # おそらく見出し
    if m:
        l = '#' * (5 - len(m.group(1))) + ' ' + \
            m.group(2)  # Scrapboxは*が多い方が大きい
    return l


def convert_decoration(l: str) -> str:
    '''
    文字装飾をMarkdownに変換。
    '''
    for m in re.finditer(r'\[([-\*/]+) (.+?)\]', ignore_code(l)):
        deco_s, deco_e = ' ', ' '
        if '/' in m.group(0):
            deco_s += '_'
            deco_e = '_' + deco_e
        if '-' in m.group(0):
            deco_s += '~~'
            deco_e = '~~' + deco_e
        if '*' in m.group(0):
            deco_s += '**'
            deco_e = '**' + deco_e
        l = l.replace(m.group(0), deco_s + m.group(2) + deco_e)
    return l


def convert_latex(l: str) -> str:
    # LaTeXはネストがありうるので正規言語ではないため逐次処理
    '''
    数式をMarkdownに変換。
    Inline style (一重$) に統一、前後のスペースを削除
    E.g., [$ E[y|x]] -> $E[y|x]$
    '''
    convert_latex_deco = lambda s: '$'+s[2:-1].strip()+'$'
    l = ignore_code(l)
    latex_clauses = []
    cnt = 0
    st = 0
    for i in range(len(l)):
        if l[i:i+2] == r'[$':
            st = i
            cnt = 1
        elif cnt>0 and l[i] == r'[':
            cnt += 1
        elif cnt>0 and l[i] == r']':
            cnt -= 1
            if cnt == 0:
                latex_clauses.append(l[st:i+1])
    for clause in latex_clauses:
        l = l.replace(clause, convert_latex_deco(clause))
    return l

def convert_link(l: str) -> str:
    '''
    リンクをMarkdownに変換。
    '''
    for m in re.finditer(r'\[(.+?)\]', ignore_code(l)):
        # タイトル+リンク形式の場合を考慮する
        tmp = m.group(1).split(' ')
        if len(tmp) >= 2:
            # ここが3つ以上の場合、、つまり [Hoge fuga piyo http://~~] とか [http://~~ hoge fuga piyo] の場合に対応してない
            # さらに [hoge fuga piyo] の場合は内部リンク
            if tmp[0].startswith('http'):
                link, title = tmp[0], ' '.join(tmp[1:])
            elif tmp[-1].startswith('http'):
                link, title = tmp[-1], ' '.join(tmp[:-1])
            else:
                # 最初も最後もURLじゃない → 内部リンク
                page_title = convert_title(m.group(1))
                l = l.replace(m.group(0), f'[[{page_title}]]')
                continue
            l = l.replace(m.group(0), f'[{title}]({link})')
        else:
            # [AAA]→内部リンク [http://~]→画像 と決め打ち
            if tmp[0].startswith('http'):  # 画像
                # 画像として解釈させるため.pngをつける 　![image.png]([https://gyazo.com/c913278aaaaaaaaaaaaa0c3])]  
                l = l.replace(m.group(0), f'![image.png]({m.group(1)}.png)') \
                    .replace('.png.png', '.png')  # for 元々 png がついてる場合
            else:
                page_title = m.group(1).replace('/', '_')  # ページタイトルのエスケープ
                l = l.replace(m.group(0), f'[[{page_title}]]')
    return l


def ignore_code(l: str) -> str:
    '''
    コード箇所を削除した文字列を返す。
    '''
    for m in re.finditer(r'`.+?`', l):
        l = l.replace(m.group(0), '')
    return l


if __name__ == "__main__":
    main()
