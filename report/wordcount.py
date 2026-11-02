"""Count the report's words as the brief defines them.

Counted: the abstract and the main report (sections 1 to 5), including table text.
Not counted: headings, figures, figure captions, references, links and the front matter.
Usage: python report/wordcount.py
"""

import re
from html.parser import HTMLParser
from pathlib import Path

SKIP = {"h1", "h2", "h3", "figcaption", "style", "script", "nav"}


class Counter(HTMLParser):

    def __init__(self):
        super().__init__()
        self.part = None
        self.depth = 0
        self.skip = 0
        self.text = {"abstract": [], "main": []}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "section" and "counted" in (attrs.get("class") or ""):
            self.part, self.depth = attrs.get("data-part"), 0
        if self.part and tag == "section":
            self.depth += 1
        if tag in SKIP:
            self.skip += 1

    def handle_endtag(self, tag):
        if tag in SKIP:
            self.skip -= 1
        if self.part and tag == "section":
            self.depth -= 1
            if self.depth == 0:
                self.part = None

    def handle_data(self, data):
        if self.part and not self.skip:
            self.text[self.part].append(data)


def words(chunks):
    return len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'.,:;()\"%&/]*", " ".join(chunks)))


counter = Counter()
counter.feed((Path(__file__).parent / "report.html").read_text(encoding="utf-8"))
abstract, main = words(counter.text["abstract"]), words(counter.text["main"])
print(f"abstract {abstract}, main {main}, total {abstract + main}")
