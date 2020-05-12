from datetime import datetime
from pathlib import Path
from markdown import markdown

parent = Path(__file__).parent

css_file = parent / 'css.css'
css = css_file.read_text('utf-8')

header_file = parent / 'header.txt'
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

    doc = text
    doc = common_markdown_items(doc)
    doc = markdown(doc)

    now = datetime.now().date()
    date_of_publication = f"""<div style="margin-bottom: 3ch;text-transform: none;">{now}</div><div class="heading">{title}</div><hr/>"""
    doc = html_.format(head=head_, body=body_.format(header + date_of_publication + doc))
    return doc


def common_markdown_items(text):
    new_text = []
    for line in text.split('\n'):
        if set(line) == set('-'):
            new_text.append("<hr/>")

        elif line.startswith('#'):  # it's a heading.
            new_line = line.upper().strip("#")
            t = f"""<div class="heading">{new_line}</div><hr/>"""
            new_text.append(t)

        elif "[" in line and not line.startswith(" " * 4):
            t = replace_urls(line)
            new_text.append(t)
        else:
            new_text.append(line)

    return "\n".join(new_text)


def paragraphs(text):
    NL = '\n\n'
    start_ix = 0
    outside_paragraph = True
    inside_paragraph = False
    sop, eop = '<p style="text-align: left;">', '</p>'

    while True:
        if outside_paragraph:
            text.replace(NL, sop, 1)
            outside_paragraph = False
            inside_paragraph = True
            continue

        if inside_paragraph:
            if text.count(NL) % 2 == 1:
                text.replace(NL, eop+sop, 1)
            else:
                text.replace(NL, eop, 1)
                outside_paragraph = True
                inside_paragraph = False
            continue

    if outside_paragraph:
        text += '</p>'


def replace_urls(line):
    a, b, c = line.count('['), line.count(']('), line.count(')')
    if b <= a and c <= a:
        start_ix = 0
        while "[" in line[start_ix:]:
            a = line.find("[", start_ix)
            b = line.find('](', a)
            c = line.find(')', b)
            if a < b < c:
                md_url, text, url = line[a:c + 1], line[a + 1:b], line[b + 2:c]
                html = f'<a href="{url}">{text}</a>'
                line = line.replace(md_url, html)
                start_ix = c + 1
    return line


