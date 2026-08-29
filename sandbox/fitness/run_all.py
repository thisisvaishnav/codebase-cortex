#!/usr/bin/env python3
"""Run all AST architectural fitness checks for Codebase Cortex.

Executes import boundary checks and banned dependency/state checks, returning unified JSON.
"""

from __future__ import annotations

import sys
import os
try:
    from . import _fitness_common as fc
    from . import check_import_boundaries
    from . import check_banned_dependencies
except ImportError:
    import _fitness_common as fc
    import check_import_boundaries
    import check_banned_dependencies


def run_all(root, doc):
    results = []
    results.extend(check_import_boundaries.run(root, doc))
    results.extend(check_banned_dependencies.run(root, doc))
    return results


def main():
    parser = fc.build_parser("Run all Codebase Cortex architectural fitness checks.")
    args = parser.parse_args()
    try:
        doc = fc.load_rules(args.rules)
        results = run_all(args.root, doc)
    except fc.FitnessError as exc:
        payload = {
            "passed": False,
            "root": fc.normalise(os.path.abspath(args.root)),
            "rules_file": fc.normalise(os.path.abspath(args.rules)),
            "error": str(exc),
            "checks": [],
        }
        fc.emit(payload, compact=args.compact, quiet=args.quiet)
        sys.exit(2)

    payload = fc.summarise(results, args.root, args.rules)
    fc.emit(payload, compact=args.compact, quiet=args.quiet)
    sys.exit(0 if payload["passed"] else 1)


if __name__ == "__main__":
    main()
