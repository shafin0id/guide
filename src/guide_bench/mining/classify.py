"""Protocol v7b: tool classification (FROZEN rule set, one for every repo/framework).

See docs/static-analysis-extensions-plan.md §3.4. Order of precedence: known-tool table
(exact class/function name) -> keyword rule on tokenised name + first docstring line ->
default read. Every count derived from this classifier is a LOWER BOUND on external/write
reach (web search/scrape count as read, which undercounts search-query exfiltration).
"""

from __future__ import annotations

import re
from typing import Literal

Classification = Literal["read", "write", "external"]

# (class_or_function_name) -> classification, exact match, checked case-sensitively first.
KNOWN_TOOLS: dict[str, Classification] = {
    # external and write
    "PythonREPLTool": "external",
    "PythonREPL": "external",
    "ShellTool": "external",
    "CodeInterpreterTool": "external",
    "code_executor": "external",
    "E2BCodeInterpreter": "external",
    "GmailSendMessage": "external",
    "SlackSendMessage": "external",
    "SendEmail": "external",  # prefix-matched below too, for SendEmail* variants
    # write
    "FileWriterTool": "write",
    "WriteFileTool": "write",
    "FileManagementToolkit": "write",
    "QuerySQLDataBaseTool": "write",
    "SQLDatabaseToolkit": "write",
    "GithubToolkit": "write",
    # read
    "SerperDevTool": "read",
    "TavilySearchResults": "read",
    "TavilySearch": "read",
    "DuckDuckGoSearchRun": "read",
    "WebsiteSearchTool": "read",
    "ScrapeWebsiteTool": "read",
    "FileReadTool": "read",
    "DirectoryReadTool": "read",
    "WikipediaQueryRun": "read",
    "ArxivQueryRun": "read",
    "YahooFinanceNewsTool": "read",
}
_SEND_EMAIL_PREFIX = "SendEmail"

_EXTERNAL_TOKENS = {
    "send", "email", "mail", "slack", "tweet", "publish", "notify", "webhook", "sms", "share", "upload", "post",
}
_WRITE_TOKENS = {
    "write", "save", "create", "update", "delete", "remove", "insert", "commit", "execute", "exec", "run",
    "deploy", "modify", "edit", "move", "rename", "append", "drop", "push",
}

_CAMEL = re.compile(r"[A-Z]+[a-z0-9]*|[a-z0-9]+")


def _tokens(name: str, docstring_first_line: str = "") -> list[str]:
    """snake_case and camelCase split of `name`, plus the first docstring line, lowercased."""
    parts = re.split(r"[_\s]+", name)
    out: list[str] = []
    for p in parts:
        out.extend(m.group(0).lower() for m in _CAMEL.finditer(p))
    out.extend(w.lower() for w in re.split(r"\W+", docstring_first_line) if w)
    return out


def classify_tool(name: str, docstring_first_line: str = "") -> tuple[Classification, str]:
    """Returns (classification, triggering_rule). `triggering_rule` is the known-tool name,
    the matched keyword token, or "default_read" when no rule matched."""
    if name in KNOWN_TOOLS:
        return KNOWN_TOOLS[name], f"known_tool:{name}"
    if name.startswith(_SEND_EMAIL_PREFIX):
        return "external", f"known_tool_prefix:{_SEND_EMAIL_PREFIX}*"

    tokens = _tokens(name, docstring_first_line)
    token_set = set(tokens)
    hit = token_set & _EXTERNAL_TOKENS
    if hit:
        return "external", f"keyword:{sorted(hit)[0]}"
    hit = token_set & _WRITE_TOKENS
    if hit:
        return "write", f"keyword:{sorted(hit)[0]}"
    return "read", "default_read"
