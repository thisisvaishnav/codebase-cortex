#!/usr/bin/env python3
"""AST import boundary checker for Codebase Cortex.

Parses Python files in scope and asserts layering rules defined in fitness_rules.json.
"""

from __future__ import annotations

import sys
try:
    from . import _fitness_common as fc
except ImportError:
    import _fitness_common as fc


def run(root, doc):
    excludes = fc.global_excludes(doc)
    rules = fc.rule_section(doc, "import_boundaries", "layer_rules")
    results = []
    parse_errors = []

    for rule in rules:
        rule_id = rule["id"]
        adr = rule["adr"]
        forbid = rule.get("forbid") or []
        allow = rule.get("allow") or []
        msg_template = rule["message"]
        violations = []
        scanned_count = 0

        for abs_path, rel in fc.rule_files(root, rule, excludes):
            tree, err = fc.load_tree(abs_path)
            if err:
                parse_errors.append(fc.violation(rel, 1, err, rule_id=fc.PARSE_CHECK_NAME))
                continue

            scanned_count += 1
            imports = fc.import_statements(tree, rel)
            for stmt in imports:
                for candidate in stmt["candidates"]:
                    if allow and fc.module_matches(candidate, allow):
                        continue
                    matched = fc.module_matches(candidate, forbid)
                    if matched:
                        msg = fc.render(msg_template, module=candidate, adr=adr, rule_id=rule_id)
                        violations.append(fc.violation(rel, stmt["line"], msg, rule_id=rule_id))

        results.append(
            fc.result(
                rule_id,
                adr,
                violations,
                check="import_boundaries",
                files_scanned=scanned_count,
                description=rule.get("description"),
            )
        )

    if parse_errors:
        results.insert(0, fc.parse_errors_result(parse_errors))

    return results


if __name__ == "__main__":
    sys.exit(fc.standalone_main(run, "Check import boundaries against architecture rules."))
