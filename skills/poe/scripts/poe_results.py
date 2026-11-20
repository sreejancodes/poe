#!/usr/bin/env python3
"""Build the project-wide results page from the analysis log and records.

Usage: python3 poe_results.py [session-dir]     (default: .)

Three parts: Load reads poe/docs/ANALYSIS_LOG.md and every
poe/<slug>/analysis/NN-*.md (except under poe/docs/ and poe/trash/), Arrange
groups the analyses into one section per task, nested by their `Follows`
chain, and places untracked (`manual`) log entries, and Render writes
<session-dir>/poe/docs/all_analysis.html (inline CSS, no JavaScript, no
external resources, no dates, so the same input gives the same bytes).
Python 3 standard library only.

Records and log entries are free-form markdown, so only headings and the
fixed log bullet keys are parsed. A record without a `# NN: <question>`
title and a log heading that does not match the entry format are skipped
and counted in the page footer, never fatal.
"""

import argparse
import html
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote

LOG_PATH = Path("poe") / "docs" / "ANALYSIS_LOG.md"
PAGE_PATH = Path("poe") / "docs" / "all_analysis.html"
SKIPPED_TASK_DIRS = {"docs", "trash"}

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".svg", ".gif"}
# Extensions that make a token a file path even without a "/" in it.
FILE_EXTENSIONS = IMAGE_EXTENSIONS | {
    ".csv", ".tsv", ".pdf", ".html", ".txt", ".json", ".xlsx", ".parquet", ".ipynb", ".md", ".py",
}
RECORD_STATUSES = {"done", "failed", "abandoned"}
DIMMED_STATUSES = {"failed", "abandoned"}

RECORD_NAME = re.compile(r"^(\d+)-.*\.md$")
RECORD_TITLE = re.compile(r"^#\s*(\d+)\s*:\s*(.+?)\s*$")
LOG_HEADING = re.compile(r"^##\s+\d{4}-\d{2}-\d{2}\s*:\s*(.+?)\s*\[\s*([^\]]+?)\s*\]\s*$")
LOG_BULLET = re.compile(r"^-\s*(Result|By|Follows|Links)\s*:\s*(.*?)\s*$", re.IGNORECASE)
ANALYSIS_REF = re.compile(r"^([A-Za-z0-9][\w.-]*)/(\d+)$")
PATH_TOKEN = re.compile(r"^[\w.~/-]+\.[A-Za-z][A-Za-z0-9]*$")
MARKDOWN_LINK_TARGET = re.compile(r"\]\(([^)\s]+)\)")
BACKTICK_TEXT = re.compile(r"`([^`]+)`")


@dataclass
class Analysis:
    """One analysis shown on the page: a poe record or an untracked log entry."""

    key: str  # "<slug>/<NN>" for poe analyses, "manual-<k>" for untracked work
    anchor: str
    question: str
    slug: Optional[str] = None  # None for untracked work
    number: Optional[int] = None
    status: str = ""
    result: str = ""
    interpretation: str = ""
    follows: Optional[str] = None  # "<slug>/<NN>"
    by: str = ""
    record: Optional[str] = None  # paths relative to the session dir
    notebook: Optional[str] = None
    figures: List[str] = field(default_factory=list)
    files: List[str] = field(default_factory=list)
    log_index: int = 0  # position in the log, orders untracked work
    is_latest: bool = False
    children: List["Analysis"] = field(default_factory=list)


@dataclass
class LogEntry:
    index: int
    question: str
    ref: str  # "<slug>/<NN>" or "manual"
    result: str = ""
    by: str = ""
    follows: Optional[str] = None
    links: List[str] = field(default_factory=list)


@dataclass
class TaskSection:
    slug: str
    roots: List[Analysis] = field(default_factory=list)


@dataclass
class Page:
    tasks: List[TaskSection] = field(default_factory=list)
    untracked: List[Analysis] = field(default_factory=list)
    latest: Optional[Analysis] = None
    record_count: int = 0
    entry_count: int = 0
    skipped: int = 0


# ------------------------------------------------------------------- parsing


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def analysis_ref(text: str) -> Optional[str]:
    """Return "<slug>/<NN>" (NN two digits or more) for a "slug/NN" text, else None."""
    match = ANALYSIS_REF.match(text.strip().strip("`"))
    if not match:
        return None
    return f"{match.group(1)}/{int(match.group(2)):02d}"


def looks_like_path(token: str) -> bool:
    if not PATH_TOKEN.match(token):
        return False
    return "/" in token or Path(token).suffix.lower() in FILE_EXTENSIONS


def extract_paths(text: str) -> List[str]:
    """Return the file paths in text, in order, without duplicates.

    A path may be written plain, in backticks, or as a markdown link target.
    A "#heading" after a path (notebook#heading) is dropped.
    """
    candidates = MARKDOWN_LINK_TARGET.findall(text)
    candidates += BACKTICK_TEXT.findall(text)
    candidates += text.split()
    paths = []
    for candidate in candidates:
        token = candidate.split("#")[0].strip("`*_'\"()[]<>,;:!")
        token = token.rstrip(".")
        if looks_like_path(token) and token not in paths:
            paths.append(token)
    return paths


def split_sections(text: str) -> Dict[str, str]:
    """Map each lowercased `## heading` to the text under it."""
    sections: Dict[str, List[str]] = {}
    current = None
    for line in text.splitlines():
        if line.startswith("## "):
            current = line[3:].strip().lower()
            sections[current] = []
        elif current is not None:
            sections[current].append(line)
    return {name: "\n".join(lines).strip() for name, lines in sections.items()}


def section(sections: Dict[str, str], name: str) -> str:
    """Text of the first section whose heading starts with name."""
    for heading, text in sections.items():
        if heading.startswith(name):
            return text
    return ""


def first_block(text: str) -> str:
    """The lines of text up to its first blank line (a paragraph or a list)."""
    lines = []
    for line in text.strip().splitlines():
        if not line.strip():
            break
        lines.append(line.rstrip())
    return "\n".join(lines)


def parse_follows_from(text: str, slug: str) -> Optional[str]:
    """Read a record's `Follows from`: "slug/NN", a record path, or a bare NN of the same task."""
    for token in text.replace(",", " ").split():
        token = token.strip("`*_'\"()[]<>.;:")
        path_match = re.search(r"(?:poe/([\w.-]+)/)?analysis/(\d+)-", token)
        if path_match:
            return f"{path_match.group(1) or slug}/{int(path_match.group(2)):02d}"
        ref = analysis_ref(token)
        if ref:
            return ref
    bare_number = re.match(r"^\W*(\d+)\b", text)
    if bare_number:
        return f"{slug}/{int(bare_number.group(1)):02d}"
    return None


def split_paths(paths: List[str]) -> Tuple[Optional[str], Optional[str], List[str], List[str]]:
    """Sort paths into (record, notebook, figures, other files)."""
    record = notebook = None
    figures, files = [], []
    for path in paths:
        suffix = Path(path).suffix.lower()
        if suffix == ".md" and record is None:
            record = path
        elif suffix == ".ipynb" and notebook is None:
            notebook = path
        elif suffix in IMAGE_EXTENSIONS:
            figures.append(path)
        elif suffix not in (".md", ".ipynb"):
            files.append(path)
    return record, notebook, figures, files


# ---------------------------------------------------------------------- load


def load_record(path: Path, slug: str, number: int) -> Optional[Analysis]:
    """Parse one analysis record; None if it has no `# NN: <question>` title."""
    text = read_text(path)
    title = next((line for line in text.splitlines() if line.startswith("# ")), "")
    match = RECORD_TITLE.match(title)
    if not match:
        return None
    question, status = match.group(2), ""
    if ":" in question:
        before, after = question.rsplit(":", 1)
        if after.strip().lower() in RECORD_STATUSES:
            question, status = before.strip(), after.strip().lower()

    sections = split_sections(text)
    _, notebook, _, _ = split_paths(extract_paths(section(sections, "what was run")))
    result = section(sections, "result")
    _, _, figures, files = split_paths(extract_paths(result))
    key = f"{slug}/{number:02d}"
    return Analysis(
        key=key,
        anchor=f"analysis-{slug}-{number:02d}",
        question=question,
        slug=slug,
        number=number,
        status=status,
        result=result,
        interpretation=first_block(section(sections, "interpretation")),
        follows=parse_follows_from(section(sections, "follows from"), slug),
        record=f"poe/{slug}/analysis/{path.name}",
        notebook=notebook,
        figures=figures,
        files=files,
    )


def load_records(session_dir: Path) -> Tuple[List[Analysis], int]:
    """Return every task's analysis records, by slug then NN, and the count skipped."""
    analyses, skipped = [], 0
    poe_dir = session_dir / "poe"
    if not poe_dir.is_dir():
        return analyses, skipped
    for task_dir in sorted(poe_dir.iterdir()):
        if task_dir.name in SKIPPED_TASK_DIRS or not (task_dir / "analysis").is_dir():
            continue
        for path in sorted((task_dir / "analysis").glob("*.md")):
            name_match = RECORD_NAME.match(path.name)
            if not name_match:
                continue
            try:
                analysis = load_record(path, task_dir.name, int(name_match.group(1)))
            except OSError:
                analysis = None
            if analysis is None:
                skipped += 1
            else:
                analyses.append(analysis)
    analyses.sort(key=lambda analysis: (analysis.slug, analysis.number))
    return analyses, skipped


def load_log(session_dir: Path) -> Tuple[List[LogEntry], int]:
    """Return the log entries in log order and the count of malformed headings."""
    log_path = session_dir / LOG_PATH
    if not log_path.is_file():
        return [], 0
    entries, skipped = [], 0
    entry = None
    for line in read_text(log_path).splitlines():
        if line.startswith("## "):
            match = LOG_HEADING.match(line)
            if match:
                entry = LogEntry(index=len(entries) + 1, question=match.group(1), ref=match.group(2))
                entries.append(entry)
            else:
                entry = None
                skipped += 1
            continue
        bullet = LOG_BULLET.match(line.strip())
        if entry is None or not bullet:
            continue
        key, value = bullet.group(1).lower(), bullet.group(2)
        if key == "result":
            entry.result = value
        elif key == "by":
            entry.by = value
        elif key == "follows":
            entry.follows = analysis_ref(value)
        elif key == "links":
            entry.links = extract_paths(value)
    return entries, skipped


# ------------------------------------------------------------------- arrange


def analysis_from_log(entry: LogEntry) -> Analysis:
    record, notebook, figures, files = split_paths(entry.links)
    ref = analysis_ref(entry.ref)
    if ref:
        slug, number = ref.split("/")
        key, anchor = ref, f"analysis-{slug}-{number}"
        slug_or_none, number_or_none = slug, int(number)
    else:
        key, anchor = f"manual-{entry.index}", f"manual-{entry.index}"
        slug_or_none = number_or_none = None
    return Analysis(
        key=key,
        anchor=anchor,
        question=entry.question,
        slug=slug_or_none,
        number=number_or_none,
        result=entry.result,
        follows=entry.follows,
        by=entry.by,
        record=record,
        notebook=notebook,
        figures=figures,
        files=files,
        log_index=entry.index,
    )


def add_log_links(analysis: Analysis, entry: LogEntry) -> None:
    """Add a poe entry's figures and files that its record does not list."""
    _, notebook, figures, files = split_paths(entry.links)
    analysis.notebook = analysis.notebook or notebook
    analysis.figures += [path for path in figures if path not in analysis.figures]
    analysis.files += [path for path in files if path not in analysis.files]


def notebook_task(notebook: Optional[str], task_notebooks: Dict[str, List[str]]) -> Optional[str]:
    """Slug of the task whose records name this notebook, else one in the same directory."""
    if not notebook:
        return None
    for slug in sorted(task_notebooks):
        if notebook in task_notebooks[slug]:
            return slug
    directory = Path(notebook).parent
    for slug in sorted(task_notebooks):
        if any(Path(path).parent == directory for path in task_notebooks[slug]):
            return slug
    return None


def thread_order(analysis: Analysis):
    """Poe analyses by NN, then untracked work in log order."""
    if analysis.number is not None:
        return (0, analysis.number)
    return (1, analysis.log_index)


def arrange(analyses: List[Analysis], entries: List[LogEntry]) -> Page:
    page = Page(record_count=len(analyses), entry_count=len(entries))
    by_key = {analysis.key: analysis for analysis in analyses}

    untracked_entries = []
    for entry in entries:
        ref = analysis_ref(entry.ref)
        if ref is None:
            untracked_entries.append(analysis_from_log(entry))
        elif ref in by_key:
            add_log_links(by_key[ref], entry)
        else:  # logged by poe but its record is missing
            by_key[ref] = analysis_from_log(entry)
    poe_analyses = sorted(by_key.values(), key=lambda analysis: (analysis.slug, analysis.number))

    if entries:
        last = entries[-1]
        ref = analysis_ref(last.ref)
        page.latest = by_key[ref] if ref else untracked_entries[-1]
        page.latest.is_latest = True

    sections: Dict[str, TaskSection] = {}
    task_notebooks: Dict[str, List[str]] = {}
    for analysis in poe_analyses:
        sections.setdefault(analysis.slug, TaskSection(slug=analysis.slug))
        if analysis.notebook:
            task_notebooks.setdefault(analysis.slug, []).append(analysis.notebook)

    # A poe analysis nests under an earlier analysis of the same task; any
    # other parent (unknown, later, another task) makes it a root.
    for analysis in poe_analyses:
        parent = by_key.get(analysis.follows or "")
        if parent is not None and parent.slug == analysis.slug and parent.number < analysis.number:
            parent.children.append(analysis)
        else:
            sections[analysis.slug].roots.append(analysis)

    for analysis in untracked_entries:
        parent = by_key.get(analysis.follows or "")
        slug = notebook_task(analysis.notebook, task_notebooks)
        if parent is not None:
            parent.children.append(analysis)
        elif slug is not None:
            sections[slug].roots.append(analysis)
        else:
            page.untracked.append(analysis)

    for analysis in poe_analyses:
        analysis.children.sort(key=thread_order)
    for task in sections.values():
        task.roots.sort(key=thread_order)
    page.tasks = [sections[slug] for slug in sorted(sections)]
    return page


def build_page(session_dir: Path) -> Page:
    analyses, skipped_records = load_records(session_dir)
    entries, skipped_entries = load_log(session_dir)
    page = arrange(analyses, entries)
    page.skipped = skipped_records + skipped_entries
    return page


# -------------------------------------------------------------------- render

CSS = """
:root {
  --bg: #f7f7f8; --panel: #ffffff; --text: #1d1d1f; --muted: #6b6b73;
  --border: #dcdce0; --link: #0b5cad; --latest: #2e8b57; --error: #c62828; --thread: #c9c9d0;
  --code-bg: #f0f0f3;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #17171a; --panel: #212125; --text: #e6e6ea; --muted: #9d9da6;
    --border: #3a3a40; --link: #7ab4ff; --latest: #5cc28a; --error: #ff6b6b; --thread: #4a4a52;
    --code-bg: #2c2c31;
  }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--text);
  font: 14px/1.45 -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; }
main { max-width: 1000px; margin: 0 auto; padding: 16px 16px 64px; }
a { color: var(--link); }
h1 { font-size: 22px; margin: 0 0 12px; }
h2 { font-size: 18px; margin: 32px 0 12px; }
nav ul { margin: 4px 0; padding-left: 18px; }
.meta { color: var(--muted); font-size: 12px; }
.analysis { background: var(--panel); border: 1px solid var(--border); border-radius: 6px;
  padding: 10px 12px; margin: 8px 0; }
.analysis.latest { border-color: var(--latest); border-width: 2px; }
.analysis.dimmed { opacity: 0.55; }
.children { margin: 8px 0 0 12px; padding-left: 12px; border-left: 2px solid var(--thread); }
.head { font-weight: 600; }
.head .number { color: var(--muted); margin-right: 6px; }
.badge { display: inline-block; padding: 0 6px; border-radius: 8px; font-size: 11px; font-weight: 600;
  margin-left: 6px; border: 1px solid var(--border); color: var(--muted); }
.badge.latest { color: #fff; background: var(--latest); border-color: var(--latest); }
.result { overflow-wrap: anywhere; margin: 6px 0; }
.interpretation { margin: 6px 0; color: var(--muted); }
.result p, .interpretation p { margin: 4px 0; }
.result ul, .result ol, .interpretation ul, .interpretation ol { margin: 4px 0; padding-left: 22px; }
.result li, .interpretation li { margin: 2px 0; }
.md-heading { font-size: 13px; margin: 10px 0 4px; }
.table-wrap { overflow-x: auto; margin: 6px 0; }
.table-wrap table { border-collapse: collapse; font-size: 13px; overflow-wrap: normal; }
.table-wrap th, .table-wrap td { border: 1px solid var(--border); padding: 3px 8px; text-align: left; vertical-align: top; }
.table-wrap th { background: var(--code-bg); }
code { font: 12px/1.4 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  background: var(--code-bg); padding: 0 3px; border-radius: 3px; }
.figures { display: flex; flex-wrap: wrap; gap: 8px 16px; align-items: flex-start; }
figure { margin: 8px 0; max-width: 100%; }
figure img { max-width: min(100%, 7.2in); max-height: 3.5in; width: auto; height: auto;
  border: 1px solid var(--border); border-radius: 4px; background: #fff; }
figcaption { color: var(--muted); font-size: 12px; overflow-wrap: anywhere; }
.links { font-size: 12px; overflow-wrap: anywhere; }
.missing { color: var(--error); }
footer { margin-top: 32px; color: var(--muted); font-size: 12px; }
"""


def escape(text) -> str:
    return html.escape(str(text), quote=True)


def page_href(path: str) -> str:
    """Href for a session-relative path, as seen from poe/docs/."""
    if Path(path).is_absolute():
        return quote(path)
    return quote("../../" + path)


# Records are agent-written markdown, so only a small subset is rendered:
# paragraphs, lists nested by indent, pipe tables, **bold**, *italic*, `code`
# and [links](target). Text is always HTML-escaped before markup is added;
# anything else shows as escaped text.

LIST_ITEM = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$")
TABLE_SEPARATOR = re.compile(r"^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)*\|?\s*$")
INLINE_CODE = re.compile(r"`([^`]+)`")
INLINE_LINK = re.compile(r"!?\[([^\]]*)\]\(([^)\s]+)\)")
# Emphasis markers must not touch a letter or digit, so A*02:01 or a*b stay literal.
BOLD = re.compile(r"(?<![\w*])\*\*(?=\S)(.+?)(?<=\S)\*\*(?![\w*])")
ITALIC = re.compile(r"(?<![\w*])\*(?=[^\s*])([^*]*?)(?<=[^\s*])\*(?![\w*])")
HEADING = re.compile(r"^\s*#{1,6}\s+(.*?)\s*#*\s*$")
URL_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
PLACEHOLDER = re.compile(r"\x00(\d+)\x00")
NESTED_INDENT = 2  # a line indented this much past a list item belongs to that item


def link_href(target: str) -> Optional[str]:
    """Href for a markdown link target; None for a scheme other than http(s) or mailto."""
    if target.startswith("#"):
        return target
    if URL_SCHEME.match(target):
        if target.lower().startswith(("http://", "https://", "mailto:")):
            return target
        return None
    path, hash_sign, fragment = target.partition("#")
    return page_href(path) + hash_sign + quote(fragment)


def render_inline(text: str) -> str:
    """Escape one line of text, then render `code`, [links](target), **bold** and *italic*.

    Code spans and links are rendered first and parked as numbered
    placeholders, so bold and italic never reach inside them.
    """
    rendered_pieces: List[str] = []

    def park(rendered: str) -> str:
        rendered_pieces.append(rendered)
        return f"\x00{len(rendered_pieces) - 1}\x00"

    def restore(text_with_placeholders: str) -> str:
        return PLACEHOLDER.sub(lambda match: rendered_pieces[int(match.group(1))], text_with_placeholders)

    def emphasis(escaped: str) -> str:
        escaped = BOLD.sub(r"<strong>\1</strong>", escaped)
        return ITALIC.sub(r"<em>\1</em>", escaped)

    def code(match) -> str:
        return park(f"<code>{escape(match.group(1))}</code>")

    def link(match) -> str:
        label = restore(emphasis(escape(match.group(1)))) or escape(match.group(2))
        href = link_href(match.group(2))
        if href is None:
            return park(label)
        return park(f'<a href="{escape(href)}">{label}</a>')

    text = text.replace("\x00", "")
    text = INLINE_CODE.sub(code, text)
    text = INLINE_LINK.sub(link, text)
    return restore(emphasis(escape(text)))


def indent_of(line: str) -> int:
    return len(line) - len(line.lstrip())


def dedent(lines: List[str]) -> List[str]:
    """Remove the indent all non-blank lines share."""
    indents = [indent_of(line) for line in lines if line.strip()]
    common = min(indents) if indents else 0
    return [line[common:] if line.strip() else "" for line in lines]


def is_table_start(lines: List[str], index: int) -> bool:
    """A pipe table starts with a header row followed by a `|---|---|` row."""
    if index + 1 >= len(lines):
        return False
    header, separator = lines[index], lines[index + 1]
    return "|" in header and "|" in separator and bool(TABLE_SEPARATOR.match(separator))


def table_cells(line: str) -> List[str]:
    row = line.strip()
    if row.startswith("|"):
        row = row[1:]
    if row.endswith("|"):
        row = row[:-1]
    return [cell.strip() for cell in row.split("|")]


def render_table(lines: List[str], start: int) -> Tuple[str, int]:
    """Render the table starting at lines[start]; return (html, index after it)."""
    header = table_cells(lines[start])
    index = start + 2  # skip the separator row
    rows = []
    while index < len(lines) and lines[index].strip() and "|" in lines[index]:
        rows.append(table_cells(lines[index]))
        index += 1
    head = "".join(f"<th>{render_inline(cell)}</th>" for cell in header)
    body = []
    for row in rows:
        row = row + [""] * (len(header) - len(row))
        body.append("<tr>" + "".join(f"<td>{render_inline(cell)}</td>" for cell in row) + "</tr>")
    return (
        f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead>'
        f"<tbody>{''.join(body)}</tbody></table></div>",
        index,
    )


def render_paragraph(lines: List[str], start: int) -> Tuple[str, int]:
    """Render lines up to a blank line, list item or table; line breaks are kept."""
    index = start
    paragraph = []
    while index < len(lines):
        line = lines[index]
        if not line.strip() or (
            index > start and (LIST_ITEM.match(line) or HEADING.match(line) or is_table_start(lines, index))
        ):
            break
        paragraph.append(render_inline(line.strip()))
        index += 1
    return f"<p>{'<br>'.join(paragraph)}</p>", index


def render_list(lines: List[str], start: int) -> Tuple[str, int]:
    """Render the list starting at lines[start]; return (html, index after it).

    Lines indented at least NESTED_INDENT past the list's items belong to the
    item above them (sub-lists, tables, more text) and are rendered as blocks
    inside it.
    """
    first_item = LIST_ITEM.match(lines[start])
    list_indent = len(first_item.group(1))
    ordered = first_item.group(2)[0].isdigit()

    def is_sibling_item(line: str) -> bool:
        item = LIST_ITEM.match(line)
        return bool(
            item
            and list_indent <= len(item.group(1)) < list_indent + NESTED_INDENT
            and item.group(2)[0].isdigit() == ordered
        )

    items: List[Tuple[List[str], List[str]]] = []  # (item text lines, nested lines)
    index = start
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            next_index = index + 1
            while next_index < len(lines) and not lines[next_index].strip():
                next_index += 1
            if next_index == len(lines):
                break
            next_line = lines[next_index]
            if indent_of(next_line) >= list_indent + NESTED_INDENT:
                items[-1][1].append("")
            elif not is_sibling_item(next_line):
                break
            index = next_index
        elif indent_of(line) >= list_indent + NESTED_INDENT:
            items[-1][1].append(line)
            index += 1
        elif is_sibling_item(line):
            items.append(([LIST_ITEM.match(line).group(3)], []))
            index += 1
        elif LIST_ITEM.match(line) or HEADING.match(line) or is_table_start(lines, index) or items[-1][1]:
            break
        else:  # unindented text right under an item continues its text
            items[-1][0].append(line.strip())
            index += 1

    rendered_items = []
    for text_lines, nested_lines in items:
        nested = dedent(nested_lines)
        while nested and nested[0].strip() and not LIST_ITEM.match(nested[0]) and not is_table_start(nested, 0):
            text_lines.append(nested.pop(0).strip())
        text = render_inline(" ".join(text_lines))
        rendered_items.append(f"<li>{text}{render_blocks(nested)}</li>")
    tag = "ol" if ordered else "ul"
    return f"<{tag}>{''.join(rendered_items)}</{tag}>", index


def render_blocks(lines: List[str]) -> str:
    parts = []
    index = 0
    while index < len(lines):
        if not lines[index].strip():
            index += 1
            continue
        heading = HEADING.match(lines[index])
        if heading:
            rendered, index = f'<h4 class="md-heading">{render_inline(heading.group(1))}</h4>', index + 1
        elif is_table_start(lines, index):
            rendered, index = render_table(lines, index)
        elif LIST_ITEM.match(lines[index]):
            rendered, index = render_list(lines, index)
        else:
            rendered, index = render_paragraph(lines, index)
        parts.append(rendered)
    return "".join(parts)


def render_markdown(text: str) -> str:
    """Render record markdown (the subset above) as HTML; never raises."""
    lines = [line.expandtabs(4).rstrip() for line in text.replace("\x00", "").splitlines()]
    try:
        return render_blocks(lines)
    except Exception:  # loose markdown must never break the page: show it escaped
        return f"<p>{'<br>'.join(escape(line) for line in lines)}</p>"


def file_link(session_dir: Path, path: str, label: str) -> str:
    href = page_href(path)
    if (session_dir / path).exists():
        return f'<a href="{escape(href)}">{escape(label)}</a>'
    return f'<a class="missing" href="{escape(href)}">{escape(label)} (missing)</a>'


def render_figure(session_dir: Path, path: str) -> str:
    if not (session_dir / path).exists():
        return f"<p>{file_link(session_dir, path, path)}</p>"
    href = escape(page_href(path))
    return (
        f'<figure><a href="{href}"><img src="{href}" alt="{escape(path)}" loading="lazy"></a>'
        f"<figcaption>{escape(path)}</figcaption></figure>"
    )


def render_analysis(session_dir: Path, analysis: Analysis) -> str:
    classes = ["analysis"]
    if analysis.status in DIMMED_STATUSES:
        classes.append("dimmed")
    if analysis.is_latest:
        classes.append("latest")

    if analysis.number is not None:
        label = f"{analysis.number:02d}"
    else:
        label = "untracked" + (f" ({analysis.by})" if analysis.by else "")
    head = f'<span class="number">{escape(label)}</span>{escape(analysis.question)}'
    if analysis.status:
        head += f'<span class="badge">{escape(analysis.status)}</span>'
    if analysis.is_latest:
        head += '<span class="badge latest">latest</span>'

    parts = [f'<div class="{" ".join(classes)}" id="{escape(analysis.anchor)}">', f'<div class="head">{head}</div>']
    if analysis.result:
        parts.append(f'<div class="result">{render_markdown(analysis.result)}</div>')
    if analysis.interpretation:
        parts.append(f'<div class="interpretation">{render_markdown(analysis.interpretation)}</div>')
    if analysis.figures:
        figures = "".join(render_figure(session_dir, path) for path in analysis.figures)
        parts.append(f'<div class="figures">{figures}</div>')

    links = []
    if analysis.record:
        links.append("record: " + file_link(session_dir, analysis.record, analysis.record))
    if analysis.notebook:
        links.append("notebook: " + file_link(session_dir, analysis.notebook, analysis.notebook))
    links += [file_link(session_dir, path, path) for path in analysis.files]
    if links:
        parts.append(f'<div class="links">{" · ".join(links)}</div>')

    if analysis.children:
        children = "".join(render_analysis(session_dir, child) for child in analysis.children)
        parts.append(f'<div class="children">{children}</div>')
    parts.append("</div>")
    return "".join(parts)


def render_page(session_dir: Path, page: Page) -> str:
    body = ["<h1>Results</h1>"]
    if not page.tasks and not page.untracked:
        body.append("<p>No analyses yet: no entries in poe/docs/ANALYSIS_LOG.md and no poe/&lt;slug&gt;/analysis/ records.</p>")
    else:
        if page.latest is not None:
            body.append(
                f'<p>Latest: <a href="#{escape(page.latest.anchor)}">{escape(page.latest.question)}</a></p>'
            )
        contents = [f'<li><a href="#task-{escape(task.slug)}">{escape(task.slug)}</a></li>' for task in page.tasks]
        if page.untracked:
            contents.append('<li><a href="#untracked-work">Untracked work</a></li>')
        body.append(f"<nav><ul>{''.join(contents)}</ul></nav>")
        for task in page.tasks:
            body.append(f'<section id="task-{escape(task.slug)}"><h2>{escape(task.slug)}</h2>')
            body += [render_analysis(session_dir, analysis) for analysis in task.roots]
            body.append("</section>")
        if page.untracked:
            body.append('<section id="untracked-work"><h2>Untracked work</h2>')
            body += [render_analysis(session_dir, analysis) for analysis in page.untracked]
            body.append("</section>")
    body.append(
        f"<footer>Built from poe/docs/ANALYSIS_LOG.md ({page.entry_count} entries) and "
        f"{page.record_count} analysis records. Skipped {page.skipped} malformed entries.</footer>"
    )
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        "<title>poe results</title>"
        f'<meta name="color-scheme" content="light dark"><style>{CSS}</style></head>'
        f"<body><main>{''.join(body)}</main></body></html>\n"
    )


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Write poe/docs/all_analysis.html for a session directory.")
    parser.add_argument("session_dir", nargs="?", default=".", help="the directory holding poe/ (default: .)")
    args = parser.parse_args(argv)
    session_dir = Path(args.session_dir)
    if not session_dir.is_dir():
        print(f"poe_results: session directory not found: {session_dir}", file=sys.stderr)
        return 1

    try:
        page = build_page(session_dir)
    except OSError as error:
        print(f"poe_results: could not read the analyses: {error}", file=sys.stderr)
        return 1

    page_path = session_dir / PAGE_PATH
    try:
        page_path.parent.mkdir(parents=True, exist_ok=True)
        page_path.write_text(render_page(session_dir, page), encoding="utf-8")
    except OSError as error:
        print(f"poe_results: could not write the results page: {error}", file=sys.stderr)
        return 1
    print(page_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
