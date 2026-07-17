#!/usr/bin/env python3
"""Path-discipline checker.

Scans backend/app/**/*.py and frontend/src/**/*.{js,jsx} for hardcoded,
platform-specific filesystem path strings — the kind that work on Ubuntu
and silently break on Windows. Everything is stdlib-only so this runs
with any Python 3.8+ interpreter, no venv or install required.

Scope: only string literals that are *arguments to a function call* are
considered (file I/O is inherently call-based: open(...), pd.read_csv(...),
Path(...), fs.readFileSync(...)). Plain string literals sitting in dict
values, return payloads, or docstrings are left alone on purpose.

Exemptions (not flagged even though they contain '/'):
  - URLs (http://, https://, ws://, ...)
  - FastAPI route registration: router.get/post/put/delete/patch/...(...),
    APIRouter(...), and any `prefix=` keyword argument
  - JS/JSX `import ... from '...'`, `export ... from '...'`, `require(...)`
  - JS/JSX axios/fetch-style HTTP calls: `.get("/api/...")`, `.post(...)`, etc.

Usage:
    python scripts/check_paths.py

Exit code 0 = clean, 1 = at least one hardcoded path found.
"""

from __future__ import annotations

import ast
import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_APP_DIR = REPO_ROOT / "backend" / "app"
FRONTEND_SRC_DIR = REPO_ROOT / "frontend" / "src"

URL_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*://")

FILE_EXTENSIONS = {
    ".csv", ".json", ".db", ".sqlite", ".sqlite3", ".xlsx", ".xls",
    ".txt", ".log", ".yaml", ".yml", ".parquet", ".pkl", ".png",
    ".jpg", ".jpeg", ".pdf", ".ini", ".cfg", ".env", ".toml", ".zip",
}

# Call names whose string arguments are route templates, not file paths.
ROUTE_CALL_NAMES = {
    "get", "post", "put", "delete", "patch", "options", "head",
    "websocket", "route", "add_api_route", "APIRouter",
}


@dataclass
class Finding:
    file: Path
    line: int
    snippet: str
    reason: str

    def format(self, root: Path) -> str:
        try:
            rel = self.file.relative_to(root)
        except ValueError:
            rel = self.file
        return f"{rel}:{self.line}: {self.reason} -> {self.snippet!r}"


# type/subtype content-type strings ("application/json", "text/csv", ...) —
# same shape as a path with a "file extension" segment, but not a path.
MIME_TYPE_PATTERN = re.compile(
    r"^(application|text|image|audio|video|multipart|font|message)/[\w.+-]+$"
)

# Tailwind's opacity-modifier syntax ("bg-green-900/30", "text-white/50").
TAILWIND_FRACTION_PATTERN = re.compile(r"^[\w:-]+/\d+$")


def looks_like_path(value: str) -> bool:
    """Heuristic: does this string look like a hardcoded local filesystem path?"""
    if not value:
        return False
    if URL_PATTERN.match(value):
        return False
    if MIME_TYPE_PATTERN.match(value):
        return False
    if TAILWIND_FRACTION_PATTERN.match(value):
        return False

    has_slash = "/" in value or "\\" in value
    if not has_slash:
        return False

    suffix = Path(value.replace("\\", "/")).suffix.lower()
    if suffix in FILE_EXTENSIONS:
        return True

    segments = [s for s in re.split(r"[/\\]", value) if s]
    meaningful_segments = [s for s in segments if len(s) >= 2]
    return len(meaningful_segments) >= 2


# --------------------------------------------------------------------------
# Python scanner (AST-based)
# --------------------------------------------------------------------------

def _call_name(func: ast.AST) -> str:
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return ""


def _iter_call_arg_exprs(call: ast.Call):
    for arg in call.args:
        yield arg
    for kw in call.keywords:
        if kw.arg == "prefix":
            continue
        if kw.value is not None:
            yield kw.value


def _scan_expr_for_paths(expr: ast.AST, path: Path, findings: list, seen_ids: set) -> None:
    joinedstr_child_ids = {
        id(c)
        for node in ast.walk(expr)
        if isinstance(node, ast.JoinedStr)
        for c in node.values
        if isinstance(c, ast.Constant)
    }

    for node in ast.walk(expr):
        if isinstance(node, ast.JoinedStr):
            static_parts = [
                c.value for c in node.values
                if isinstance(c, ast.Constant) and isinstance(c.value, str)
            ]
            joined = "".join(static_parts)
            if id(node) not in seen_ids and looks_like_path(joined):
                findings.append(Finding(path, node.lineno, joined, "hardcoded filesystem path (f-string)"))
                seen_ids.add(id(node))
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            if id(node) in joinedstr_child_ids or id(node) in seen_ids:
                continue
            if looks_like_path(node.value):
                findings.append(Finding(path, node.lineno, node.value, "hardcoded filesystem path"))
                seen_ids.add(id(node))


def scan_python_file(path: Path) -> list:
    findings: list = []
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except (SyntaxError, UnicodeDecodeError) as exc:
        return [Finding(path, 0, str(exc), "could not parse file")]

    seen_ids: set = set()

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if _call_name(node.func) in ROUTE_CALL_NAMES:
            continue
        for arg_expr in _iter_call_arg_exprs(node):
            _scan_expr_for_paths(arg_expr, path, findings, seen_ids)

    return findings


# --------------------------------------------------------------------------
# JS / JSX scanner (regex-based — no external JS parser dependency)
# --------------------------------------------------------------------------

JS_IMPORT_OR_EXPORT_LINE = re.compile(r"^\s*(import\b.*|export\s+.*\bfrom\b.*)$")
JS_REQUIRE_CALL = re.compile(r"\brequire\(\s*['\"][^'\"]*['\"]\s*\)")
JS_STRING_LITERAL = re.compile(r"""(['"`])((?:\\.|(?!\1).)*)\1""")
JS_HTTP_METHOD_CALL_PREFIX = re.compile(r"\.(get|post|put|delete|patch|head|options)\s*\(\s*$")


def scan_js_file(path: Path) -> list:
    findings: list = []
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        return [Finding(path, 0, str(exc), "could not read file")]

    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("//") or stripped.startswith("*"):
            continue
        if JS_IMPORT_OR_EXPORT_LINE.match(stripped):
            continue

        cleaned = JS_REQUIRE_CALL.sub("", line)

        for match in JS_STRING_LITERAL.finditer(cleaned):
            quote, value = match.group(1), match.group(2)
            if quote == "`" and "${" in value:
                # Template literal with interpolation — the raw text can contain
                # arbitrary JS (e.g. division operators), not a static string.
                # Too unreliable to path-check without a real JS parser.
                continue
            prefix = cleaned[: match.start()]
            if JS_HTTP_METHOD_CALL_PREFIX.search(prefix):
                continue
            if looks_like_path(value):
                findings.append(Finding(path, lineno, value, "hardcoded filesystem path"))

    return findings


# --------------------------------------------------------------------------
# Runner
# --------------------------------------------------------------------------

def main() -> int:
    all_findings: list = []
    files_scanned = 0

    if BACKEND_APP_DIR.is_dir():
        for py_file in sorted(BACKEND_APP_DIR.rglob("*.py")):
            files_scanned += 1
            all_findings.extend(scan_python_file(py_file))
    else:
        print(f"[warn] {BACKEND_APP_DIR} not found — skipping backend scan")

    if FRONTEND_SRC_DIR.is_dir():
        js_files = sorted(FRONTEND_SRC_DIR.rglob("*.js")) + sorted(FRONTEND_SRC_DIR.rglob("*.jsx"))
        for js_file in js_files:
            files_scanned += 1
            all_findings.extend(scan_js_file(js_file))
    else:
        print(f"[warn] {FRONTEND_SRC_DIR} not found — skipping frontend scan")

    print(f"Path-discipline check: scanned {files_scanned} files "
          f"({BACKEND_APP_DIR.relative_to(REPO_ROOT)}, {FRONTEND_SRC_DIR.relative_to(REPO_ROOT)})")

    if not all_findings:
        print("PASS — no hardcoded filesystem paths found.")
        return 0

    print(f"FAIL — {len(all_findings)} hardcoded path(s) found:\n")
    for finding in sorted(all_findings, key=lambda f: (str(f.file), f.line)):
        print(f"  {finding.format(REPO_ROOT)}")
    print("\nUse pathlib.Path / os.path.join (or Path-based constants) instead of raw path strings.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
