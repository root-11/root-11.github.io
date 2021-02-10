from pathlib import Path
from datetime import datetime
from markdown import markdown

root = Path(__file__).parent
content = root / 'content'
drafts = root / 'drafts'

dont_index = ['about', 'contact']

html_ = """<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="{root}style.css" rel="stylesheet" type="text/css">
    <title>{title}</title>
</head>
<body>
<br>
<div class = "center">
    <a href="{root}index.html" style="text-decoration: none;"><b>BJORN MADSEN'S WEBSITE</b><br></a>
    <hr id="hrid"/>
    <div style="text-align: center; display: inline-block; width: 100%;">
        <a class="title" href="{root}about.html">ABOUT</a> &nbsp;
        <a class="title" href="{root}contact.html">EMAIL</a> &nbsp;
        <a class="title" href="https://paypal.me/BjornMadsen">DONATE</a>
    </div>
</div>
    <br><br>
    <div style="margin-bottom: 3ch;text-transform: none;"></div>

{dop}    
{body}

</body>
</html>
"""


def markdown_to_html(text, title, root="../../"):
    doc = markdown(text, extensions=['tables'])
    now = datetime.now().date()
    date_of_publication = f"""<div style="margin-bottom: 3ch;text-transform: none;">{now}</div><div class="heading">{title}</div><hr/>"""
    doc = html_.format(title=title, dop=date_of_publication, body=doc, root=root)
    return doc


def main():
    assert content.exists()
    assert content.is_dir()
    assert drafts.exists()
    assert drafts.is_dir()

    # discover files.
    files = []
    queue = [content, drafts]
    while queue:
        target = queue.pop(0)
        assert target.is_dir()
        for item in target.iterdir():
            if item.is_dir():
                queue.append(item)

            if str(item).endswith('.md'):
                files.append(item)

    for item in files:
        title = item.name.replace(".md", "")
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
    index_file = root / 'articles.md'
    new_file = root / 'index.html'
    assert new_file.exists()
    text = index_file.read_text()

    html = markdown_to_html(text=text, title="BJORN MADSEN'S WEBSITE", root="")
    html = remove_table_head(html)
    with new_file.open('w') as fo:
        fo.write(html)


def remove_table_head(html):
    start = html.find("<thead>")
    end = html.find("</thead>")
    end_of_tag = html.find(">", end)
    html_after = html[:start] + html[end_of_tag+1:]
    return html_after


if __name__ == "__main__":
    main()
