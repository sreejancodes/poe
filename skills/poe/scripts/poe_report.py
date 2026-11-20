#!/usr/bin/env python3
"""Build a step-by-step report for a poe task directory.

Usage: python3 poe_report.py poe/<task-slug>

Three parts: Load reads a task's documents and Claude Code transcripts from
poe/<task-slug>/, Timeline turns them into plain dataclasses, and Render
writes them as one self-contained poe/<task-slug>/report.html (inline CSS,
no JavaScript, no external resources). Python 3 standard library only.

The transcript format is undocumented, so every field is read defensively.
Lines that are not valid JSON, records of unknown type and records without
the expected fields are skipped and counted, never fatal.
"""

import argparse
import base64
import html
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Set, Tuple

# Record types Claude Code writes for its own bookkeeping. They are ignored
# without being counted as skipped; any other unknown type is counted.
INTERNAL_RECORD_TYPES = {
    "attachment",
    "api-request",
    "api-request-blob",
    "api-request-shape",
    "mode",
    "session-owner",
    "atis-latch",
    "last-prompt",
    "ai-title",
    "permission-mode",
    "tools-used",
    "queue-operation",
}
INTERNAL_RECORD_PREFIXES = ("file-history-",)

TASK_DOCUMENT_NAMES = ["plan.md", "status.md", "summary.md"]
TASK_DOCUMENT_FOLDERS = ["phases", "progress", "analysis"]

# Only the start of a thinking block's signature is decoded (signatures can be
# several KB). Must be a multiple of 4 so the cut prefix is valid base64.
SIGNATURE_PREFIX_CHARS = 64


@dataclass
class Step:
    index: int
    timestamp: Optional[str]
    kind: str  # user, assistant, thinking, narration, tool_call, tool_result, system
    text: str
    anchor: str
    tool_name: Optional[str] = None
    tool_use_id: Optional[str] = None
    is_error: bool = False
    is_denied: bool = False
    result: Optional["Step"] = None
    worker: Optional["Transcript"] = None


@dataclass
class Transcript:
    name: str
    actor: str
    agent_type: Optional[str] = None
    description: Optional[str] = None
    steps: List[Step] = field(default_factory=list)
    models: Set[str] = field(default_factory=set)
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0
    tool_calls: int = 0
    errors: int = 0
    thinking_blocks: int = 0  # narration not included
    thinking_recorded: int = 0  # thinking blocks with text
    first_timestamp: Optional[str] = None
    last_timestamp: Optional[str] = None
    cost_usd: Optional[float] = None
    skipped: int = 0
    parent_step: Optional[Step] = None


@dataclass
class Session:
    session_id: str
    main: Transcript
    workers: List[Transcript] = field(default_factory=list)


@dataclass
class Task:
    slug: str
    task_dir: Path
    documents: List[Tuple[str, str]] = field(default_factory=list)
    sessions: List[Session] = field(default_factory=list)
    skipped: int = 0


# ---------------------------------------------------------------- documents


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def load_documents(task_dir: Path) -> List[Tuple[str, str]]:
    documents = []
    for name in TASK_DOCUMENT_NAMES:
        path = task_dir / name
        if path.is_file():
            documents.append((name, read_text(path)))
    for folder in TASK_DOCUMENT_FOLDERS:
        for path in sorted((task_dir / folder).glob("*.md")):
            documents.append((f"{folder}/{path.name}", read_text(path)))
    return documents


# -------------------------------------------------------------- transcripts


def read_json_lines(path: Path) -> Tuple[List[dict], int]:
    """Return the JSON object records of a .jsonl file and the count of bad lines."""
    records = []
    bad_lines = 0
    if not path.is_file():
        return records, bad_lines
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                bad_lines += 1
                continue
            if isinstance(record, dict):
                records.append(record)
            else:
                bad_lines += 1
    return records, bad_lines


def is_internal_record_type(record_type) -> bool:
    if not isinstance(record_type, str):
        return False
    return record_type in INTERNAL_RECORD_TYPES or record_type.startswith(INTERNAL_RECORD_PREFIXES)


def tool_result_text(content) -> str:
    """Flatten a tool_result's content, which is a string or a list of blocks."""
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    parts = []
    for block in content:
        if isinstance(block, dict) and block.get("type") == "text":
            parts.append(str(block.get("text", "")))
        elif isinstance(block, dict):
            parts.append(f"[{block.get('type', 'unknown')} block]")
        else:
            parts.append(str(block))
    return "\n".join(parts)


def is_denied_record(record: dict) -> bool:
    decision = record.get("permissionDecision")
    if not isinstance(decision, dict) or "decision" not in decision:
        return False
    return decision.get("decision") != "accept"


def system_text(record: dict) -> str:
    content = record.get("content")
    text = content if isinstance(content, str) and content else str(record.get("subtype") or "system")
    hook_errors = record.get("hookErrors")
    if hook_errors:
        text += "\nhook errors: " + json.dumps(hook_errors, indent=2)
    return text


def thinking_block_kind(signature) -> str:
    """Return "narration" or "thinking" for an assistant thinking block.

    Claude Code also writes short progress updates as thinking blocks. Their
    signature starts with a tag that reads "narration" once base64-decoded.
    This is undocumented, so anything unexpected falls back to "thinking".
    """
    if not isinstance(signature, str) or not signature:
        return "thinking"
    prefix = signature[:SIGNATURE_PREFIX_CHARS]
    # Pad a short signature so it decodes even without its trailing "=".
    prefix += "=" * (-len(prefix) % 4)
    try:
        decoded = base64.b64decode(prefix, validate=True)
    except ValueError:  # binascii.Error is a ValueError
        return "thinking"
    return "narration" if b"narration" in decoded else "thinking"


def add_usage(transcript: Transcript, usage) -> None:
    if not isinstance(usage, dict):
        return
    transcript.input_tokens += int(usage.get("input_tokens") or 0)
    transcript.output_tokens += int(usage.get("output_tokens") or 0)
    transcript.cache_read_tokens += int(usage.get("cache_read_input_tokens") or 0)
    transcript.cache_creation_tokens += int(usage.get("cache_creation_input_tokens") or 0)


class TimelineBuilder:
    """Turns one transcript's records into Steps and running totals."""

    def __init__(self, transcript: Transcript):
        self.transcript = transcript
        self.calls_by_id = {}
        # Claude Code writes one assistant record per content block, each
        # repeating message.id and message.usage, so usage is counted once per id.
        self.counted_message_ids = set()

    def add_step(self, record: dict, kind: str, text: str, **fields) -> Step:
        transcript = self.transcript
        index = len(transcript.steps) + 1
        timestamp = record.get("timestamp")
        if not isinstance(timestamp, str):
            timestamp = None
        step = Step(
            index=index,
            timestamp=timestamp,
            kind=kind,
            text=text,
            anchor=f"step-{transcript.name}-{index}",
            **fields,
        )
        transcript.steps.append(step)
        if timestamp:
            if transcript.first_timestamp is None or timestamp < transcript.first_timestamp:
                transcript.first_timestamp = timestamp
            if transcript.last_timestamp is None or timestamp > transcript.last_timestamp:
                transcript.last_timestamp = timestamp
        return step

    def add_record(self, record: dict) -> None:
        record_type = record.get("type")
        if record_type == "user":
            self.add_user_record(record)
        elif record_type == "assistant":
            self.add_assistant_record(record)
        elif record_type == "system":
            self.add_step(record, "system", system_text(record))
        elif record_type == "cost-state":
            cost = record.get("totalCostUSD")
            if isinstance(cost, (int, float)):
                self.transcript.cost_usd = float(cost)
            else:
                self.transcript.skipped += 1
        elif not is_internal_record_type(record_type):
            self.transcript.skipped += 1

    def add_user_record(self, record: dict) -> None:
        message = record.get("message")
        content = message.get("content") if isinstance(message, dict) else None
        if isinstance(content, str):
            self.add_step(record, "user", content)
            return
        if not isinstance(content, list):
            self.transcript.skipped += 1
            return
        for block in content:
            block_type = block.get("type") if isinstance(block, dict) else None
            if block_type == "tool_result":
                self.add_tool_result(record, block)
            elif block_type == "text":
                self.add_step(record, "user", str(block.get("text", "")))
            elif block_type is not None:
                self.add_step(record, "user", f"[{block_type} block]")
            else:
                self.transcript.skipped += 1

    def add_tool_result(self, record: dict, block: dict) -> None:
        tool_use_id = block.get("tool_use_id")
        call = self.calls_by_id.get(tool_use_id)
        step = self.add_step(
            record,
            "tool_result",
            tool_result_text(block.get("content")),
            tool_name=call.tool_name if call else None,
            tool_use_id=tool_use_id,
            is_error=block.get("is_error") is True,
            is_denied=is_denied_record(record),
        )
        if call is not None:
            call.result = step
        if step.is_error or step.is_denied:
            self.transcript.errors += 1

    def add_assistant_record(self, record: dict) -> None:
        message = record.get("message")
        if not isinstance(message, dict) or not isinstance(message.get("content"), list):
            self.transcript.skipped += 1
            return
        model = message.get("model")
        if isinstance(model, str) and model:
            self.transcript.models.add(model)
        message_id = message.get("id")
        if message_id is None or message_id not in self.counted_message_ids:
            add_usage(self.transcript, message.get("usage"))
            if message_id is not None:
                self.counted_message_ids.add(message_id)
        for block in message["content"]:
            self.add_assistant_block(record, block)

    def add_assistant_block(self, record: dict, block) -> None:
        block_type = block.get("type") if isinstance(block, dict) else None
        if block_type == "text":
            self.add_step(record, "assistant", str(block.get("text", "")))
        elif block_type in ("thinking", "redacted_thinking"):
            text = str(block.get("thinking") or "")
            kind = thinking_block_kind(block.get("signature"))
            self.add_step(record, kind, text)
            if kind == "thinking":
                self.transcript.thinking_blocks += 1
                if text:
                    self.transcript.thinking_recorded += 1
        elif block_type == "tool_use":
            tool_use_id = block.get("id")
            step = self.add_step(
                record,
                "tool_call",
                json.dumps(block.get("input"), indent=2, ensure_ascii=False),
                tool_name=block.get("name"),
                tool_use_id=tool_use_id,
            )
            self.transcript.tool_calls += 1
            if tool_use_id is not None:
                self.calls_by_id[tool_use_id] = step
        else:
            self.transcript.skipped += 1


def load_transcript(path: Path, name: str, actor: str) -> Transcript:
    transcript = Transcript(name=name, actor=actor)
    records, bad_lines = read_json_lines(path)
    transcript.skipped += bad_lines
    builder = TimelineBuilder(transcript)
    for record in records:
        builder.add_record(record)
    return transcript


def read_meta(path: Path) -> dict:
    try:
        meta = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return meta if isinstance(meta, dict) else {}


def load_worker(transcript_path: Path) -> Tuple[Transcript, Optional[str]]:
    """Load a worker transcript; also return the toolUseId from its .meta.json."""
    name = transcript_path.stem  # agent-<id>
    meta = read_meta(transcript_path.with_name(name + ".meta.json"))
    agent_type = meta.get("agentType")
    description = meta.get("description")
    actor = description or agent_type or name
    worker = load_transcript(transcript_path, name, actor)
    worker.agent_type = agent_type
    worker.description = description
    return worker, meta.get("toolUseId")


def sort_key_by_time(transcript: Transcript):
    # Transcripts without timestamps go last.
    return (transcript.first_timestamp is None, transcript.first_timestamp or "", transcript.name)


def load_session(session_dir: Path) -> Session:
    session_id = session_dir.name
    main = load_transcript(session_dir / f"{session_id}.jsonl", session_id, "orchestrator")

    workers = []
    worker_tool_use_ids = []
    for path in sorted((session_dir / "subagents").glob("agent-*.jsonl")):
        worker, tool_use_id = load_worker(path)
        workers.append(worker)
        worker_tool_use_ids.append(tool_use_id)

    # Link each worker to the call that started it, whatever the tool's name
    # (Agent, or Task in older versions). Search every transcript in case a
    # worker started its own workers.
    calls_by_id = {}
    for transcript in [main] + workers:
        for step in transcript.steps:
            if step.kind == "tool_call" and step.tool_use_id:
                calls_by_id[step.tool_use_id] = step
    for worker, tool_use_id in zip(workers, worker_tool_use_ids):
        call = calls_by_id.get(tool_use_id)
        if call is not None:
            call.worker = worker
            worker.parent_step = call

    workers.sort(key=sort_key_by_time)
    return Session(session_id=session_id, main=main, workers=workers)


def load_task(task_dir: Path) -> Task:
    task_dir = Path(task_dir)
    if not task_dir.is_dir():
        raise FileNotFoundError(f"task directory not found: {task_dir}")
    task = Task(slug=task_dir.name, task_dir=task_dir, documents=load_documents(task_dir))

    logs_dir = task_dir / "logs"
    if logs_dir.is_dir():
        for session_dir in sorted(path for path in logs_dir.iterdir() if path.is_dir()):
            task.sessions.append(load_session(session_dir))
    task.sessions.sort(key=lambda session: sort_key_by_time(session.main))

    for session in task.sessions:
        task.skipped += session.main.skipped + sum(worker.skipped for worker in session.workers)
    return task


# ------------------------------------------------------------------- render
#
# Every string that comes from a log or a document goes through escape().
# Nothing is truncated: long blocks are collapsed in <details> instead.

TOOL_PREVIEW_LINES = 3
TEXT_PREVIEW_LINES = 12
PREVIEW_CHARS_PER_LINE = 200

KIND_LABELS = {
    "user": "user",
    "assistant": "assistant",
    "thinking": "thinking",
    "narration": "narration",
    "tool_call": "tool call",
    "tool_result": "tool result",
    "system": "system",
}

CSS = """
:root {
  --bg: #f7f7f8; --panel: #ffffff; --text: #1d1d1f; --muted: #6b6b73;
  --border: #dcdce0; --link: #0b5cad; --code-bg: #f0f0f3;
  --user: #2f6fd6; --assistant: #2e8b57; --thinking: #9a9aa3; --narration: #b0568f; --tool-call: #7b4fc9;
  --tool-result: #1f8a99; --system: #c58a12; --error: #c62828; --error-bg: #fdecec;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #17171a; --panel: #212125; --text: #e6e6ea; --muted: #9d9da6;
    --border: #3a3a40; --link: #7ab4ff; --code-bg: #2a2a2f;
    --user: #6b9cf0; --assistant: #5cc28a; --thinking: #77777f; --narration: #d98ac0; --tool-call: #a983ec;
    --tool-result: #4fbccb; --system: #e0aa3e; --error: #ff6b6b; --error-bg: #3a1f22;
  }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--text);
  font: 14px/1.45 -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; }
a { color: var(--link); }
.layout { display: flex; align-items: flex-start; }
nav { position: sticky; top: 0; width: 260px; flex: none; height: 100vh; overflow-y: auto;
  padding: 16px; border-right: 1px solid var(--border); background: var(--panel); }
nav ul { list-style: none; margin: 0; padding: 0; }
nav ul ul { padding-left: 14px; }
nav li { margin: 4px 0; overflow-wrap: anywhere; }
main { flex: 1; min-width: 0; padding: 16px 24px 64px; }
h1 { font-size: 22px; margin: 0 0 12px; }
h2 { font-size: 18px; margin: 32px 0 12px; }
h3 { font-size: 16px; margin: 24px 0 8px; }
.cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(170px, 1fr)); gap: 10px; }
.card { background: var(--panel); border: 1px solid var(--border); border-radius: 6px; padding: 10px 12px; }
.card .label { color: var(--muted); font-size: 12px; }
.card .value { font-size: 16px; overflow-wrap: anywhere; }
.card.wide { grid-column: 1 / -1; }
pre, .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 12.5px; }
pre { margin: 6px 0 0; padding: 8px; background: var(--code-bg); border-radius: 4px;
  white-space: pre-wrap; overflow-wrap: anywhere; }
.preview { display: block; white-space: pre-wrap; overflow-wrap: anywhere; padding: 4px 8px;
  background: var(--code-bg); border-radius: 4px; margin-top: 4px; }
details > summary { cursor: pointer; }
.more { color: var(--muted); font-size: 12px; }
.meta { color: var(--muted); font-size: 12px; }
.panel { background: var(--panel); border: 1px solid var(--border); border-radius: 6px; padding: 10px 12px; margin: 8px 0; }
.errors li { margin: 6px 0; }
.excerpt { display: block; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: var(--muted); }
.step { background: var(--panel); border: 1px solid var(--border); border-left: 4px solid var(--border);
  border-radius: 4px; padding: 6px 10px; margin: 6px 0; }
.step-head { font-size: 12px; color: var(--muted); }
.step-head .kind { font-weight: 600; }
.kind-user { border-left-color: var(--user); }
.kind-assistant { border-left-color: var(--assistant); }
.kind-thinking { border-left-color: var(--thinking); }
.kind-narration { border-left-color: var(--narration); }
.kind-tool_call { border-left-color: var(--tool-call); }
.kind-tool_result { border-left-color: var(--tool-result); }
.kind-system { border-left-color: var(--system); }
.step.error { border-left-color: var(--error); background: var(--error-bg); }
.badge { display: inline-block; padding: 0 6px; border-radius: 8px; font-size: 11px; font-weight: 600;
  color: #fff; background: var(--error); }
.transcript { margin-top: 24px; }
@media (max-width: 800px) {
  .layout { display: block; }
  nav { position: static; width: auto; height: auto; border-right: none; border-bottom: 1px solid var(--border); }
  main { padding: 16px; }
}
"""


def escape(text) -> str:
    return html.escape(str(text), quote=True)


def transcript_id(transcript: Transcript) -> str:
    return f"transcript-{transcript.name}"


def parse_timestamp(timestamp: Optional[str]) -> Optional[datetime]:
    if not timestamp:
        return None
    try:
        return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return None


def seconds_between(first: Optional[str], last: Optional[str]) -> Optional[float]:
    start = parse_timestamp(first)
    end = parse_timestamp(last)
    if start is None or end is None:
        return None
    return (end - start).total_seconds()


def format_duration(seconds: Optional[float]) -> str:
    if seconds is None:
        return "n/a"
    seconds = int(round(seconds))
    hours, rest = divmod(seconds, 3600)
    minutes, seconds = divmod(rest, 60)
    if hours:
        return f"{hours}h {minutes}m {seconds}s"
    if minutes:
        return f"{minutes}m {seconds}s"
    return f"{seconds}s"


def format_cost(cost: Optional[float]) -> str:
    return "n/a" if cost is None else f"${cost:.4f}"


def session_transcripts(session: Session) -> List[Transcript]:
    return [session.main] + session.workers


def all_transcripts(task: Task) -> List[Transcript]:
    transcripts = []
    for session in task.sessions:
        transcripts.extend(session_transcripts(session))
    return transcripts


def session_duration(session: Session) -> Optional[float]:
    """Seconds from the first to the last timestamp of the session, workers included."""
    firsts = [t.first_timestamp for t in session_transcripts(session) if t.first_timestamp]
    lasts = [t.last_timestamp for t in session_transcripts(session) if t.last_timestamp]
    if not firsts or not lasts:
        return None
    return seconds_between(min(firsts), max(lasts))


def task_duration(task: Task) -> Optional[float]:
    """Sum of session durations (sessions are separate runs, maybe days apart)."""
    durations = [session_duration(session) for session in task.sessions]
    durations = [d for d in durations if d is not None]
    return sum(durations) if durations else None


def task_cost(task: Task) -> Optional[float]:
    # cost-state in the main transcript already covers the session's workers.
    costs = [s.main.cost_usd for s in task.sessions if s.main.cost_usd is not None]
    return sum(costs) if costs else None


def tokens_line(transcripts: List[Transcript]) -> str:
    input_tokens = sum(t.input_tokens for t in transcripts)
    output_tokens = sum(t.output_tokens for t in transcripts)
    cache_read = sum(t.cache_read_tokens for t in transcripts)
    cache_creation = sum(t.cache_creation_tokens for t in transcripts)
    return (
        f"input {input_tokens:,} · output {output_tokens:,} · "
        f"cache read {cache_read:,} · cache creation {cache_creation:,}"
    )


def models_text(transcripts: List[Transcript]) -> str:
    models = set()
    for transcript in transcripts:
        models.update(transcript.models)
    return ", ".join(sorted(models)) or "n/a"


def thinking_text(transcripts: List[Transcript]) -> str:
    recorded = sum(t.thinking_recorded for t in transcripts)
    total = sum(t.thinking_blocks for t in transcripts)
    return f"thinking recorded: {recorded} of {total} blocks"


def totals_line(transcripts: List[Transcript], duration: Optional[float]) -> str:
    """One escaped line of totals for a transcript or a group of transcripts."""
    tool_calls = sum(t.tool_calls for t in transcripts)
    errors = sum(t.errors for t in transcripts)
    skipped = sum(t.skipped for t in transcripts)
    return escape(
        f"models: {models_text(transcripts)} · tool calls {tool_calls} · errors {errors} · "
        f"{thinking_text(transcripts)} · duration {format_duration(duration)} · tokens: {tokens_line(transcripts)} · "
        f"skipped records {skipped}"
    )


def collapsible_text(text: str, preview_lines: int) -> str:
    """Short text as a <pre>; longer text as <details> whose summary shows the start.

    The summary holds the first preview_lines lines (and at most
    PREVIEW_CHARS_PER_LINE characters per previewed line); the body holds the
    rest, so together they are the whole text and nothing is cut.
    """
    lines = text.split("\n")
    preview = "\n".join(lines[:preview_lines])
    rest = "\n".join(lines[preview_lines:])
    char_limit = preview_lines * PREVIEW_CHARS_PER_LINE
    if len(preview) > char_limit:
        rest = preview[char_limit:] + ("\n" + rest if len(lines) > preview_lines else "")
        preview = preview[:char_limit]
    elif len(lines) <= preview_lines:
        return f"<pre>{escape(text)}</pre>"
    return (
        "<details><summary>"
        f'<span class="mono preview">{escape(preview)}</span>'
        f'<span class="more">show the rest ({len(rest):,} more characters)</span>'
        f"</summary><pre>{escape(rest)}</pre></details>"
    )


# ---------------------------------------------------------- render: sections


def render_sidebar(task: Task) -> str:
    items = [
        '<li><a href="#overview">Overview</a></li>',
        '<li><a href="#errors">Errors</a></li>',
        '<li><a href="#documents">Documents</a></li>',
    ]
    for session in task.sessions:
        worker_items = "".join(
            f'<li><a href="#{escape(transcript_id(worker))}">{escape(worker.actor)}</a></li>'
            for worker in session.workers
        )
        worker_list = f"<ul>{worker_items}</ul>" if worker_items else ""
        items.append(
            f'<li><a href="#{escape(transcript_id(session.main))}">'
            f"Session {escape(session.session_id)}</a>{worker_list}</li>"
        )
    return f'<nav><ul>{"".join(items)}</ul></nav>'


def card(label: str, value: str) -> str:
    return f'<div class="card"><div class="label">{escape(label)}</div><div class="value">{escape(value)}</div></div>'


def render_overview(task: Task, generated: str) -> str:
    transcripts = all_transcripts(task)
    workers = sum(len(session.workers) for session in task.sessions)
    total_tokens = sum(
        t.input_tokens + t.output_tokens + t.cache_read_tokens + t.cache_creation_tokens
        for t in transcripts
    )
    cards = [
        card("Task", task.slug),
        card("Generated", generated),
        card("Sessions", str(len(task.sessions))),
        card("Workers", str(workers)),
        card("Tool calls", str(sum(t.tool_calls for t in transcripts))),
        card("Errors", str(sum(t.errors for t in transcripts))),
        card("Thinking", thinking_text(transcripts)),
        card("Tokens", f"{total_tokens:,}"),
        card("Cost", format_cost(task_cost(task))),
        card("Duration", format_duration(task_duration(task))),
        card("Skipped records", str(task.skipped)),
        f'<div class="card wide"><div class="label">Tokens</div>'
        f'<div class="value">{escape(tokens_line(transcripts))}</div></div>',
    ]
    status_text = dict(task.documents).get("status.md")
    if status_text is not None:
        cards.append(
            f'<div class="card wide"><div class="label">status.md</div><pre>{escape(status_text)}</pre></div>'
        )
    return (
        f'<section id="overview"><h1>poe report: {escape(task.slug)}</h1>'
        f'<div class="cards">{"".join(cards)}</div></section>'
    )


def first_line(text: str) -> str:
    for line in text.split("\n"):
        if line.strip():
            return line.strip()
    return "(no output)"


def render_errors(task: Task) -> str:
    items = []
    for transcript in all_transcripts(task):
        for step in transcript.steps:
            if step.kind != "tool_result" or not (step.is_error or step.is_denied):
                continue
            label = "denied" if step.is_denied else "error"
            items.append(
                f'<li><a href="#{escape(step.anchor)}">{escape(transcript.actor)} · step {step.index}</a> '
                f'<span class="badge">{label}</span> <span class="mono">{escape(step.tool_name or "unknown tool")}</span>'
                f'<span class="mono excerpt">{escape(first_line(step.text))}</span></li>'
            )
    body = f'<ul class="errors">{"".join(items)}</ul>' if items else "<p>No errored or denied tool calls.</p>"
    return f'<section id="errors"><h2>Errors ({len(items)})</h2>{body}</section>'


def render_documents(task: Task) -> str:
    if not task.documents:
        body = "<p>No task documents were found.</p>"
    else:
        body = "".join(
            f'<details class="panel"><summary class="mono">{escape(path)}</summary><pre>{escape(text)}</pre></details>'
            for path, text in task.documents
        )
    return f'<section id="documents"><h2>Documents</h2>{body}</section>'


def render_step(step: Step) -> str:
    is_error = step.is_error or step.is_denied
    classes = f"step kind-{step.kind}" + (" error" if is_error else "")
    head = [
        f'<a href="#{escape(step.anchor)}">#{step.index}</a>',
        escape(step.timestamp or "no time"),
        f'<span class="kind">{escape(KIND_LABELS.get(step.kind, step.kind))}</span>',
    ]
    if step.tool_name:
        head.append(f'<span class="mono">{escape(step.tool_name)}</span>')
    if step.is_denied:
        head.append('<span class="badge">denied</span>')
    elif step.is_error:
        head.append('<span class="badge">error</span>')
    if step.kind == "tool_call" and step.result is not None:
        head.append(f'<a href="#{escape(step.result.anchor)}">result #{step.result.index}</a>')
    if step.worker is not None:
        head.append(
            f'<a href="#{escape(transcript_id(step.worker))}">worker: {escape(step.worker.actor)}</a>'
        )

    if step.kind == "thinking" and not step.text:
        body = '<div class="meta">(thinking text not recorded; see README: Thinking text in the report)</div>'
    elif step.kind in ("tool_call", "tool_result"):
        body = collapsible_text(step.text, TOOL_PREVIEW_LINES)
    else:
        body = collapsible_text(step.text, TEXT_PREVIEW_LINES)

    return (
        f'<div class="{classes}" id="{escape(step.anchor)}">'
        f'<div class="step-head">{" · ".join(head)}</div>{body}</div>'
    )


def render_timeline(transcript: Transcript) -> str:
    if not transcript.steps:
        return '<p class="meta">No steps in this transcript.</p>'
    return "".join(render_step(step) for step in transcript.steps)


def render_worker(worker: Transcript) -> str:
    if worker.parent_step is not None:
        started_by = (
            f'<a href="#{escape(worker.parent_step.anchor)}">'
            f"step #{worker.parent_step.index} ({escape(worker.parent_step.tool_name or 'tool call')})</a>"
        )
    else:
        started_by = "not found"
    duration = seconds_between(worker.first_timestamp, worker.last_timestamp)
    header = (
        f'<div class="panel">'
        f"<div>type: {escape(worker.agent_type or 'unknown')}</div>"
        f"<div>description: {escape(worker.description or 'none')}</div>"
        f"<div>started by: {started_by}</div>"
        f'<div class="meta">{totals_line([worker], duration)}</div></div>'
    )
    return (
        f'<section class="transcript" id="{escape(transcript_id(worker))}">'
        f"<h3>Worker: {escape(worker.actor)} <span class=\"meta mono\">{escape(worker.name)}</span></h3>"
        f"{header}{render_timeline(worker)}</section>"
    )


def render_session(session: Session) -> str:
    main = session.main
    transcripts = session_transcripts(session)
    header = (
        f'<div class="panel">'
        f"<div>first timestamp: {escape(main.first_timestamp or 'n/a')} · "
        f"workers: {len(session.workers)} · cost: {escape(format_cost(main.cost_usd))}</div>"
        f'<div class="meta">session (orchestrator and workers): {totals_line(transcripts, session_duration(session))}</div>'
        f'<div class="meta">orchestrator only: {totals_line([main], seconds_between(main.first_timestamp, main.last_timestamp))}</div>'
        f"</div>"
    )
    workers = "".join(render_worker(worker) for worker in session.workers)
    return (
        f'<section class="transcript" id="{escape(transcript_id(main))}">'
        f"<h2>Session {escape(session.session_id)}</h2>{header}"
        f"<h3>Orchestrator</h3>{render_timeline(main)}</section>{workers}"
    )


def render_sessions(task: Task) -> str:
    if not task.sessions:
        return '<section id="sessions"><h2>Sessions</h2><p>No transcripts were found in logs/.</p></section>'
    return "".join(render_session(session) for session in task.sessions)


def render_report(task: Task, generated: Optional[str] = None) -> str:
    if generated is None:
        generated = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>poe report: {escape(task.slug)}</title>"
        f'<meta name="color-scheme" content="light dark"><style>{CSS}</style></head>'
        f'<body><div class="layout">{render_sidebar(task)}<main>'
        f"{render_overview(task, generated)}{render_errors(task)}"
        f"{render_documents(task)}{render_sessions(task)}"
        "</main></div></body></html>\n"
    )


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Write report.html for a poe task directory.")
    parser.add_argument("task_dir", help="the task directory, e.g. poe/<task-slug>")
    args = parser.parse_args(argv)
    task_dir = Path(args.task_dir)

    try:
        task = load_task(task_dir)
    except OSError as error:
        print(f"poe_report: could not read the task: {error}", file=sys.stderr)
        return 1

    report_path = task_dir / "report.html"
    try:
        report_path.write_text(render_report(task), encoding="utf-8")
    except OSError as error:
        print(f"poe_report: could not write the report: {error}", file=sys.stderr)
        return 1
    print(report_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
