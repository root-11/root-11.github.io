from pathlib import Path
from datetime import datetime
from markdown import markdown


root = Path(__file__).parent
content = root / 'content'

index_file = content / 'index.md'
index_text = index_file.read_text('utf-8')

dont_index = ['about', 'contact']


# css_file = content / 'css.css'
# css = css_file.read_text('utf-8')
css = '<meta name="viewport" content="width=device-width, initial-scale=1.0">'

header_file = content / 'header.txt'
header = header_file.read_text('utf-8')


def markdown_to_html(text, title):
    """
    :param path:
    :return: nice readable html

    page guide:

    [date of publication]

    [title]
    --------- line -----------------
    text
    ...
    end of text
                  <--- deliberate white space.
    [sub title]
    --------- line -----------------
    text
    ...
                <--- deliberate white space.

    """
    style_ = '<style type="text/css">{}</style>'
    title_ = '<title>{}</title>'
    head_ = "<head>{}{}</head>".format(style_.format(css), title_.format(title))
    html_ = "<html>{head}{body}</html>"
    body_ = "<body>{}</body>"

    doc = markdown(text)

    now = datetime.now().date()
    date_of_publication = f"""<div style="margin-bottom: 3ch;text-transform: none;">{now}</div><div class="heading">{title}</div><hr/>"""
    doc = html_.format(head=head_, body=body_.format(header + date_of_publication + doc))
    return doc


# def common_markdown_items(text):
#     new_text = []
#     for line in text.split('\n'):
#         if set(line) == set('-'):
#             new_text.append("<hr/>")
#
#         elif line.startswith('#'):  # it's a heading.
#             new_line = line.upper().strip("#")
#             t = f"""<div class="heading">{new_line}</div><hr/>"""
#             new_text.append(t)
#
#         # elif "[" in line and not line.startswith(" " * 4):
#         #     t = replace_urls(line)
#         #     new_text.append(t)
#         else:
#             new_text.append(line)
#
#     return "\n".join(new_text)
#
#
# def paragraphs(text):
#     NL = '\n\n'
#     start_ix = 0
#     outside_paragraph = True
#     inside_paragraph = False
#     sop, eop = '<p style="text-align: left;">', '</p>'
#
#     while True:
#         if outside_paragraph:
#             text.replace(NL, sop, 1)
#             outside_paragraph = False
#             inside_paragraph = True
#             continue
#
#         if inside_paragraph:
#             if text.count(NL) % 2 == 1:
#                 text.replace(NL, eop+sop, 1)
#             else:
#                 text.replace(NL, eop, 1)
#                 outside_paragraph = True
#                 inside_paragraph = False
#             continue
#
#     if outside_paragraph:
#         text += '</p>'
#
#
# def replace_urls(line):
#     a, b, c = line.count('['), line.count(']('), line.count(')')
#     if b <= a and c <= a:
#         start_ix = 0
#         while "[" in line[start_ix:]:
#             a = line.find("[", start_ix)
#             b = line.find('](', a)
#             c = line.find(')', b)
#             if a < b < c:
#                 md_url, text, url = line[a:c + 1], line[a + 1:b], line[b + 2:c]
#                 html = f'<a href="{url}">{text}</a>'
#                 line = line.replace(md_url, html)
#                 start_ix = c + 1
#     return line
#


def main():
    content = root / 'content'
    assert content.exists()
    assert content.is_dir()

    # discover files.
    files = []
    queue = [content]
    while queue:
        target = queue.pop(0)
        assert target.is_dir()
        for item in target.iterdir():
            if item.is_dir():
                queue.append(item)

            if item.name == 'index.md':
                continue  # It's the index.

            if str(item.name).startswith("-"):
                continue  # It's a draft.

            if str(item).endswith('.md'):
                files.append(item)

    for item in files:

        title = item.name.replace(".md", "")
        if title in dont_index:
            continue

        relative_path = f'content/{title}/index.html'
        check_index(path=relative_path, title=title)

        new_file = item.parent / "index.html"

        if new_file.exists():
            continue
        print(f"creating {new_file} ")

        text = item.read_text()
        title_as_text = title.replace("-", " ")
        html = markdown_to_html(text=text, title=title_as_text)
        with new_file.open('w') as fo:
            fo.write(html)

    # create index.html at the end.
    new_file = root / 'index.html'
    html = markdown_to_html(text=index_file.read_text('utf-8'), title="BJORN MADSEN'S WEBSITE")
    with new_file.open('w') as fo:
        fo.write(html)


def check_index(path, title):
    # assert isinstance(path, Path)
    now = datetime.now().date()
    title_as_text = title.replace("-", " ")

    new_entry = f"""{now}: <a href="{path}">{title_as_text}</a><br>"""

    with index_file.open('r') as fi:
        text = fi.read()
        if new_entry in text:
            return

    print(f"adding {title} to index.")
    text = text.split('\n')
    text.insert(4, new_entry)

    with index_file.open('w') as fo:
        fo.write("\n".join(text))


def make_index_html():
    pass


if __name__ == "__main__":
    main()
