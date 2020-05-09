from datetime import datetime
from pathlib import Path

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

    style_catalogue = {
        '\n\n': ("<br>", "<br/>"),  # break
        # --- straight line
        # **bold**
        # _underline_
        # *italic*
        # ALLCAPS = headline.
        # [text](url)  = hyperlink / href
        # ![image](url) = image.
        # [1] = foot note
        # - list item
        # 1. numerical item

    }

    doc = text
    doc = doc.replace('\n\n', "<br/>")
    doc = common_markdown_items(doc)
    doc = list_of_items(doc)

    now = datetime.now().date()
    date_of_publication = f"""<div style="margin-bottom: 3ch;text-transform: none;">{now}</div><div class="heading">{title}</div><hr/>"""
    doc = html_.format(head=head_, body=body_.format(header + date_of_publication + doc))
    return doc


def common_markdown_items(text):
    new_text = []
    for line in text.split('\n'):
        if set(line) == set('-'):
            new_text.append("<hr>")

        elif line.startswith('#'):  # it's a heading.
            t = f"""<div class="heading">{line}</div><hr/><p style="text-align: left;">"""
            new_text.append(t)

        elif "[" in line:
            t = replace_urls(line)
            new_text.append(t)
        else:
            new_text.append(line)

    return "\n".join(new_text)


def replace_urls(line):
    a, b, c = line.count('['), line.count(']('), line.count(')')
    if b <= a and c <= a:
        start_ix = 0
        while "[" in line[start_ix:]:
            a = line.find("[", start_ix)
            b = line.find('](', a)
            c = line.find(')', b)
            if a < b < c:
                md_url, text, url = line[a:c], line[a:b], line[b + 2:c]
                html = f'<a href="{url}">{text}</a>'
                line.replace(md_url, html)
                start_ix = c + 1
    return line


def list_of_items(text):
    """
    turns:
        - Coffee
        - Tea
        - Mile
    into:
        <ul>
            <li>Coffee</li>
            <li>Tea</li>
            <li>Milk</li>
        </ul>

    :param text:
    :return:
    """
    assert isinstance(text, str)
    new_text = []
    started = False
    for line in text.split('\n'):
        if line.startswith('- '):
            if not started:
                started = True
                new_text.append("<ul>")

            new_text.append(f"<li>{line[2:]}</li>")
        else:
            if started:
                started = False
                new_text.append("</ul>")
            new_text.append(line)

    if started:  # the last item might be the end of the document.
        new_text.append("</ul>")
    return "\n".join(new_text)