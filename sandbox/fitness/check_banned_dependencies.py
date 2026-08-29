#!/usr/bin/env python3
"""AST banned dependencies, calls, and in-process state checker for Codebase Cortex.

Parses Python files and dependency manifests in scope and asserts rules defined in fitness_rules.json.
"""

from __future__ import annotations

import ast
import os
import re
import sys
try:
    from . import _fitness_common as fc
except ImportError:
    import _fitness_common as fc


def _check_banned_modules(root, doc, excludes):
    rules = fc.rule_section(doc, "banned_dependencies", "banned_modules")
    results = []
    parse_errors = []

    for rule in rules:
        rule_id = rule["id"]
        adr = rule["adr"]
        banned_mods = rule.get("modules") or []
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
                    matched = fc.module_matches(candidate, banned_mods)
                    if matched:
                        msg = fc.render(msg_template, module=candidate, adr=adr, rule_id=rule_id)
                        violations.append(fc.violation(rel, stmt["line"], msg, rule_id=rule_id))

        results.append(
            fc.result(
                rule_id,
                adr,
                violations,
                check="banned_dependencies:modules",
                files_scanned=scanned_count,
                description=rule.get("description"),
            )
        )

    return results, parse_errors


def _check_banned_calls(root, doc, excludes):
    rules = fc.rule_section(doc, "banned_dependencies", "banned_calls")
    results = []
    parse_errors = []

    for rule in rules:
        rule_id = rule["id"]
        adr = rule["adr"]
        banned_calls_list = rule.get("calls") or []
        msg_template = rule["message"]
        violations = []
        scanned_count = 0

        for abs_path, rel in fc.rule_files(root, rule, excludes):
            tree, err = fc.load_tree(abs_path)
            if err:
                parse_errors.append(fc.violation(rel, 1, err, rule_id=fc.PARSE_CHECK_NAME))
                continue

            scanned_count += 1
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    call_name = fc.dotted_name(node.func)
                    if call_name:
                        matched = fc.call_matches(call_name, banned_calls_list)
                        if matched:
                            msg = fc.render(msg_template, call=call_name, adr=adr, rule_id=rule_id)
                            lineno = getattr(node, "lineno", 1)
                            violations.append(fc.violation(rel, lineno, msg, rule_id=rule_id))

        results.append(
            fc.result(
                rule_id,
                adr,
                violations,
                check="banned_dependencies:calls",
                files_scanned=scanned_count,
                description=rule.get("description"),
            )
        )

    return results, parse_errors


def _is_container_type(node, container_types):
    if node is None:
        return False
    if isinstance(node, (ast.Dict, ast.List, ast.Set)):
        return True
    if isinstance(node, ast.Name) and node.id in container_types:
        return True
    if isinstance(node, ast.Subscript):
        return _is_container_type(node.value, container_types)
    if isinstance(node, ast.Call):
        func_name = fc.dotted_name(node.func)
        if func_name and any(c in func_name for c in container_types):
            return True
    return False


def _check_in_process_state(root, doc, excludes):
    rules = fc.rule_section(doc, "banned_dependencies", "in_process_state")
    results = []
    parse_errors = []

    for rule in rules:
        rule_id = rule["id"]
        adr = rule["adr"]
        name_patterns = [re.compile(p) for p in rule.get("state_name_patterns") or []]
        container_types = set(rule.get("container_types") or [])
        decorators = set(rule.get("memoising_decorators") or [])
        msg_template = rule["message"]
        violations = []
        scanned_count = 0

        for abs_path, rel in fc.rule_files(root, rule, excludes):
            tree, err = fc.load_tree(abs_path)
            if err:
                parse_errors.append(fc.violation(rel, 1, err, rule_id=fc.PARSE_CHECK_NAME))
                continue

            scanned_count += 1
            # Inspect module and class level assignments
            top_level_nodes = []
            for stmt in tree.body:
                if isinstance(stmt, (ast.Assign, ast.AnnAssign)):
                    top_level_nodes.append(stmt)
                elif isinstance(stmt, ast.ClassDef):
                    for class_stmt in stmt.body:
                        if isinstance(class_stmt, (ast.Assign, ast.AnnAssign)):
                            top_level_nodes.append(class_stmt)

            for node in top_level_nodes:
                targets = []
                val_node = None
                annotation_node = None
                lineno = getattr(node, "lineno", 1)

                if isinstance(node, ast.Assign):
                    targets = node.targets
                    val_node = node.value
                elif isinstance(node, ast.AnnAssign):
                    targets = [node.target]
                    val_node = node.value
                    annotation_node = node.annotation

                for target in targets:
                    t_name = fc.dotted_name(target) or getattr(target, "id", None)
                    if not t_name:
                        continue
                    if any(pat.search(t_name) for pat in name_patterns):
                        is_container = _is_container_type(val_node, container_types) or _is_container_type(annotation_node, container_types)
                        if is_container:
                            detail = "in-process dictionary/container state"
                            msg = fc.render(msg_template, name=t_name, detail=detail, adr=adr, rule_id=rule_id)
                            violations.append(fc.violation(rel, lineno, msg, rule_id=rule_id))

                # Check decorated functions
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    f_name = node.name
                    if any(pat.search(f_name) for pat in name_patterns):
                        for dec in node.decorator_list:
                            dec_name = fc.dotted_name(dec) or getattr(dec, "id", None)
                            if dec_name and any(d in dec_name for d in decorators):
                                msg = fc.render(msg_template, name=f_name, detail="memoised cache", adr=adr, rule_id=rule_id)
                                violations.append(fc.violation(rel, lineno, msg, rule_id=rule_id))

        results.append(
            fc.result(
                rule_id,
                adr,
                violations,
                check="banned_dependencies:in_process_state",
                files_scanned=scanned_count,
                description=rule.get("description"),
            )
        )

    return results, parse_errors


def run(root, doc):
    excludes = fc.global_excludes(doc)
    results = []
    all_parse_errors = []

    res, errs = _check_banned_modules(root, doc, excludes)
    results.extend(res)
    all_parse_errors.extend(errs)

    res, errs = _check_banned_calls(root, doc, excludes)
    results.extend(res)
    all_parse_errors.extend(errs)

    res, errs = _check_in_process_state(root, doc, excludes)
    results.extend(res)
    all_parse_errors.extend(errs)

    if all_parse_errors:
        results.insert(0, fc.parse_errors_result(all_parse_errors))

    return results


if __name__ == "__main__":
    sys.exit(fc.standalone_main(run, "Check banned dependencies, calls, and in-process state against architecture rules."))
