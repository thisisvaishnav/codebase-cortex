#!/usr/bin/env python3
"""Shared helpers for the Codebase Cortex architectural fitness checks.

Design constraints (do not break these):

* **Standard library only.** These scripts execute inside the agent's sandbox
  (Daytona, or TrueForge's local sandbox fallback). Nothing may be pip-installed
  there, so `ast`, `re`, `json`, `fnmatch` and friends are all we get.
* **Data-driven.** No repository-specific rule lives in code. Every layer rule,
  banned module and name pattern comes from ``fitness_rules.json`` so a new
  architectural invariant is a config edit, not a code change.
* **Machine-readable first.** Checks write JSON to stdout and prose to stderr,
  so `cortex-detect` can pipe stdout straight into its ``fitness_checks`` field.

Every rule carries the id of the ADR it enforces, so a violation can be traced
back to the decision (and therefore to the maintainer who owns it).
"""

from __future__ import annotations

import argparse
import ast
import fnmatch
import json
import os
import re
import sys

FITNESS_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_RULES_PATH = os.path.join(FITNESS_DIR, "fitness_rules.json")

PARSE_CHECK_NAME = "parse-python-sources"


class FitnessError(Exception):
    """Something stopped the checks from running at all (exit code 2)."""


class RuleConfigError(FitnessError):
    """``fitness_rules.json`` is missing, malformed, or incomplete."""


# --------------------------------------------------------------------------- #
# rule configuration
# --------------------------------------------------------------------------- #


def load_rules(path=None):
    """Load and shallow-validate the rule config."""
    path = os.path.abspath(path or DEFAULT_RULES_PATH)
    try:
        with open(path, "r", encoding="utf-8") as handle:
            doc = json.load(handle)
    except FileNotFoundError:
        raise RuleConfigError("rule config not found: %s" % path)
    except json.JSONDecodeError as exc:
        raise RuleConfigError("rule config is not valid JSON (%s): %s" % (path, exc))
    if not isinstance(doc, dict):
        raise RuleConfigError("rule config must be a JSON object: %s" % path)
    if not isinstance(doc.get("checks"), dict):
        raise RuleConfigError('rule config must contain a "checks" object: %s' % path)
    doc.setdefault("settings", {})
    doc["_path"] = path
    return doc


def global_excludes(doc):
    settings = doc.get("settings") or {}
    return list(settings.get("exclude_paths") or [])


def rule_section(doc, check_name, section):
    """Return the list of rules at ``checks.<check_name>.<section>``."""
    check = (doc.get("checks") or {}).get(check_name) or {}
    rules = check.get(section) or []
    if not isinstance(rules, list):
        raise RuleConfigError(
            "checks.%s.%s must be a list of rule objects" % (check_name, section)
        )
    for index, rule in enumerate(rules):
        if not isinstance(rule, dict):
            raise RuleConfigError(
                "checks.%s.%s[%d] must be an object" % (check_name, section, index)
            )
        for required in ("id", "adr", "scope", "message"):
            if not rule.get(required):
                raise RuleConfigError(
                    "checks.%s.%s[%d] (%s) is missing required key %r"
                    % (check_name, section, index, rule.get("id", "<unnamed>"), required)
                )
    return rules


# --------------------------------------------------------------------------- #
# path handling
# --------------------------------------------------------------------------- #


def normalise(path):
    """Normalise to forward slashes with no leading ``./``."""
    path = str(path).replace(os.sep, "/")
    while path.startswith("./"):
        path = path[2:]
    return path


def _is_glob(pattern):
    return any(ch in pattern for ch in "*?[")


def path_matches(rel_path, patterns):
    """True if ``rel_path`` is inside any of ``patterns``.

    A pattern containing ``*``, ``?`` or ``[`` is treated as an fnmatch glob
    (``*`` also spans ``/``). Anything else is a literal path prefix, so
    ``src/core/`` matches ``src/core/anything/deep.py``. ``.`` / ``**`` / ``""``
    match everything.
    """
    rel_path = normalise(rel_path)
    for pattern in patterns:
        pattern = normalise(pattern)
        if pattern in ("", ".", "./", "**", "*"):
            return True
        if _is_glob(pattern):
            if fnmatch.fnmatchcase(rel_path, pattern):
                return True
        else:
            pattern = pattern.rstrip("/")
            if rel_path == pattern or rel_path.startswith(pattern + "/"):
                return True
    return False


def is_excluded(rel_path, patterns):
    """True if ``rel_path`` is excluded.

    A pattern with no ``/`` matches any single path segment (so ``__pycache__``
    excludes it at any depth); one with a ``/`` is a path prefix; globs use
    fnmatch against both the whole path and each segment.
    """
    rel_path = normalise(rel_path)
    segments = [seg for seg in rel_path.split("/") if seg]
    for pattern in patterns:
        pattern = normalise(pattern).rstrip("/")
        if not pattern:
            continue
        if _is_glob(pattern):
            if fnmatch.fnmatchcase(rel_path, pattern):
                return True
            if any(fnmatch.fnmatchcase(seg, pattern) for seg in segments):
                return True
        elif "/" in pattern:
            if rel_path == pattern or rel_path.startswith(pattern + "/"):
                return True
        elif pattern in segments:
            return True
    return False


def iter_python_files(root, excludes):
    """Yield ``(abs_path, rel_posix_path)`` for every .py file under ``root``."""
    root = os.path.abspath(root)
    if not os.path.isdir(root):
        raise FitnessError("scan root is not a directory: %s" % root)
    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = normalise(os.path.relpath(dirpath, root))
        if rel_dir == ".":
            rel_dir = ""
        keep = []
        for name in sorted(dirnames):
            candidate = "%s/%s" % (rel_dir, name) if rel_dir else name
            if not is_excluded(candidate, excludes):
                keep.append(name)
        dirnames[:] = keep
        for name in sorted(filenames):
            if not name.endswith(".py"):
                continue
            rel = "%s/%s" % (rel_dir, name) if rel_dir else name
            if is_excluded(rel, excludes):
                continue
            yield os.path.join(dirpath, name), rel


def rule_files(root, rule, excludes):
    """Yield the files a single rule applies to, honouring scope and excludes."""
    scope = rule.get("scope") or ["."]
    rule_excludes = list(rule.get("exclude") or [])
    for abs_path, rel in iter_python_files(root, excludes):
        if not path_matches(rel, scope):
            continue
        if rule_excludes and is_excluded(rel, rule_excludes):
            continue
        yield abs_path, rel


# --------------------------------------------------------------------------- #
# AST helpers
# --------------------------------------------------------------------------- #

_TREE_CACHE = {}


def load_tree(abs_path):
    """Parse a source file into an AST. Returns ``(tree, error_message)``.

    Memoised on (path, mtime, size) so two checks scanning the same tree parse
    each file once. This is a build-time tool, not a request path - the cache is
    process-local on purpose and is discarded when the run ends.
    """
    try:
        stat = os.stat(abs_path)
    except OSError as exc:
        return None, "cannot stat file: %s" % exc
    key = (abs_path, stat.st_mtime_ns, stat.st_size)
    if key in _TREE_CACHE:
        return _TREE_CACHE[key]
    try:
        with open(abs_path, "r", encoding="utf-8") as handle:
            source = handle.read()
    except (OSError, UnicodeDecodeError) as exc:
        result = (None, "cannot read file: %s" % exc)
    else:
        try:
            result = (ast.parse(source, filename=abs_path), None)
        except SyntaxError as exc:
            result = (None, "syntax error: %s (line %s)" % (exc.msg, exc.lineno))
    _TREE_CACHE[key] = result
    return result


def package_parts(rel_path):
    """Directory components of a file, used to resolve relative imports."""
    parts = [p for p in normalise(rel_path).split("/")[:-1] if p]
    return parts


def resolve_relative_import(rel_path, module, level):
    """Resolve ``from ..x import y`` to an absolute dotted module name."""
    parts = package_parts(rel_path)
    climb = max(level - 1, 0)
    base = parts[: len(parts) - climb] if climb <= len(parts) else []
    if module:
        base = base + module.split(".")
    return ".".join(part for part in base if part)


def import_statements(tree, rel_path):
    """Flatten a module's imports into candidate dotted module names.

    Each entry is ``{"line", "raw", "candidates"}``. ``candidates`` is ordered
    broadest-first so a rule that forbids ``src.api`` reports the package once
    rather than also reporting every symbol pulled out of it.
    """
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                out.append(
                    {
                        "line": node.lineno,
                        "raw": "import %s" % alias.name,
                        "candidates": [alias.name],
                    }
                )
        elif isinstance(node, ast.ImportFrom):
            level = node.level or 0
            if level:
                base = resolve_relative_import(rel_path, node.module, level)
                shown = "from %s%s import ..." % ("." * level, node.module or "")
            else:
                base = node.module or ""
                shown = "from %s import ..." % base
            if not base:
                continue
            candidates = [base]
            for alias in node.names:
                if alias.name != "*":
                    candidates.append("%s.%s" % (base, alias.name))
            out.append({"line": node.lineno, "raw": shown, "candidates": candidates})
    out.sort(key=lambda entry: entry["line"])
    return out


def module_matches(dotted, patterns):
    """Match a dotted module name against module patterns.

    ``src.api`` matches ``src.api`` and ``src.api.routes``. A pattern with a
    glob character is fnmatched instead.
    """
    for pattern in patterns:
        if _is_glob(pattern):
            if fnmatch.fnmatchcase(dotted, pattern):
                return pattern
        elif dotted == pattern or dotted.startswith(pattern + "."):
            return pattern
    return None


def dotted_name(node):
    """Best-effort dotted name for a Name/Attribute chain, else None."""
    parts = []
    current = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
        return ".".join(reversed(parts))
    return None


def call_matches(dotted, patterns):
    for pattern in patterns:
        if _is_glob(pattern):
            if fnmatch.fnmatchcase(dotted, pattern):
                return pattern
        elif dotted == pattern:
            return pattern
    return None


# --------------------------------------------------------------------------- #
# results
# --------------------------------------------------------------------------- #


class _SafeDict(dict):
    def __missing__(self, key):
        return "{%s}" % key


def render(template, **values):
    try:
        return str(template).format_map(_SafeDict(values))
    except (IndexError, ValueError):
        return str(template)


def violation(rel_path, line, message, rule_id=None):
    entry = {"file": normalise(rel_path), "line": int(line), "message": message}
    if rule_id:
        entry["rule"] = rule_id
    return entry


def result(name, adr, violations, check=None, files_scanned=0, description=None):
    ordered = sorted(violations, key=lambda v: (v["file"], v["line"], v["message"]))
    entry = {
        "name": name,
        "adr": adr,
        "passed": not ordered,
        "violations": ordered,
    }
    if check:
        entry["check"] = check
    if description:
        entry["description"] = description
    entry["files_scanned"] = files_scanned
    return entry


def compile_patterns(rule, key):
    """Compile a rule's regex list, reporting bad patterns as config errors."""
    compiled = []
    for raw in rule.get(key) or []:
        try:
            compiled.append((raw, re.compile(raw)))
        except re.error as exc:
            raise RuleConfigError(
                "rule %r has an invalid regex in %s: %r (%s)"
                % (rule.get("id"), key, raw, exc)
            )
    return compiled


def parse_errors_result(errors):
    """Unparseable sources are a hard failure: we cannot vouch for what we
    could not read."""
    return result(
        PARSE_CHECK_NAME,
        "N/A",
        errors,
        check="harness",
        files_scanned=len(errors),
        description="Every Python source in scope must parse, or the checks below are blind to it.",
    )


def summarise(results, root, rules_path):
    return {
        "passed": all(item["passed"] for item in results),
        "root": normalise(os.path.abspath(root)),
        "rules_file": normalise(os.path.abspath(rules_path)),
        "checks": results,
    }


# --------------------------------------------------------------------------- #
# CLI plumbing shared by every check script
# --------------------------------------------------------------------------- #


def build_parser(description):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--root",
        default=os.getcwd(),
        help="directory to scan (default: current working directory)",
    )
    parser.add_argument(
        "--rules",
        default=DEFAULT_RULES_PATH,
        help="path to fitness_rules.json (default: alongside this script)",
    )
    parser.add_argument(
        "--compact", action="store_true", help="emit single-line JSON on stdout"
    )
    parser.add_argument(
        "--quiet", action="store_true", help="suppress the human summary on stderr"
    )
    return parser


def print_human_summary(payload, stream=sys.stderr):
    stream.write("root:  %s\n" % payload["root"])
    stream.write("rules: %s\n" % payload["rules_file"])
    for item in payload["checks"]:
        status = "PASS" if item["passed"] else "FAIL"
        stream.write(
            "[%s] %-52s %-8s files=%d violations=%d\n"
            % (
                status,
                item["name"],
                item.get("adr", "-"),
                item.get("files_scanned", 0),
                len(item["violations"]),
            )
        )
        for entry in item["violations"]:
            stream.write("       %s:%d  %s\n" % (entry["file"], entry["line"], entry["message"]))
    stream.write("overall: %s\n" % ("PASS" if payload["passed"] else "FAIL"))
    stream.flush()


def emit(payload, compact=False, quiet=False):
    text = json.dumps(payload) if compact else json.dumps(payload, indent=2)
    sys.stdout.write(text + "\n")
    sys.stdout.flush()
    if not quiet:
        print_human_summary(payload)


def standalone_main(run_check, description, argv=None):
    """Run one check script as a standalone program."""
    args = build_parser(description).parse_args(argv)
    try:
        doc = load_rules(args.rules)
        results = run_check(args.root, doc)
    except FitnessError as exc:
        payload = {
            "passed": False,
            "root": normalise(os.path.abspath(args.root)),
            "rules_file": normalise(os.path.abspath(args.rules)),
            "error": str(exc),
            "checks": [],
        }
        emit(payload, compact=args.compact, quiet=args.quiet)
        return 2
    payload = summarise(results, args.root, args.rules)
    emit(payload, compact=args.compact, quiet=args.quiet)
    return 0 if payload["passed"] else 1
