from pathlib import Path
from datetime import datetime

from static_page_generator.markdown_parser import markdown_to_html

root = Path(__file__).parent.parent
parent = Path(__file__).parent

index_file = parent / 'index.md'
index_text = index_file.read_text('utf-8')

dont_index = ['about', 'contact']


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
                continue

            if str(item).endswith('.md'):
                files.append(item)

    for item in files:
        title = item.name.replace(".md", "")
        new_name = str(item.name).replace(".md", ".html")
        new_file = root / new_name

        if new_file.exists():
            continue
        print(f"creating {new_name} ")

        text = item.read_text()
        html = markdown_to_html(text=text, title=title)
        with new_file.open('w') as fo:
            fo.write(html)

        if title in dont_index:
            continue
        add_entry_to_index(path=new_name, title=title)

    # create index.html at the end.
    new_file = root / 'index.html'
    html = markdown_to_html(text=index_file.read_text('utf-8'), title="BJORN MADSEN'S WEBSITE")
    with new_file.open('w') as fo:
        fo.write(html)


def add_entry_to_index(path, title):
    now = datetime.now().date()
    new_entry = f"""{now}: <a href="{path}">{title}</a><br>"""

    with index_file.open('r') as fi:
        text = fi.read().split('\n')
        if any(title in line for line in text):
            return  # skip.

    print(f"adding {title} to index.")
    text.insert(4, new_entry)

    with index_file.open('w') as fo:
        fo.write("\n".join(text))


def make_index_html():
    pass


if __name__ == "__main__":
    main()
