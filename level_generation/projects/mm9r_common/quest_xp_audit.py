#!/usr/bin/env python3
"""The rework's quest XP sites against the MM9 quest XP profile (devdocs/mm9_rework/BALANCE_PLAN.md section 3.1).

Reads every `mm9r_*/*.py` converter statically (no conversion runs): each `balanced_experience(...)` or
`experience_lua(...)` call (quest_xp.py) is a site; its arguments are resolved from literals, module constants, the
enclosing function's local unpacking, a `for` loop over a literal table, or the enclosing function's call sites. Writes
`quest_xp_audit.json` beside this file: every site (map, key, original, balanced), and every profile entry either with
the sites that pay it or as unmatched with the reason.

    python3 level_generation/projects/mm9r_common/quest_xp_audit.py
"""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

COMMON = Path(__file__).resolve().parent
PROJECTS = COMMON.parent
sys.path.insert(0, str(COMMON))
from quest_xp import PROFILE_PATH, ROOT, balanced_experience  # noqa: E402

OUTPUT = COMMON / "quest_xp_audit.json"
SITE_FUNCTIONS = {"balanced_experience", "experience_lua"}
PARAMETERS = ("original", "key", "script", "routine")

# Profile entries no rework site pays, by (script, routine, original), and why.
UNMATCHED_REASONS = {
    ("forad.scr", "OnDeath", 194000): "not carried: the rework's Frosgard City turns Forad Darre hostile in the "
                                      "battle but has no Forad.scr :OnDeath handler (key 494), so his death pays "
                                      "nothing yet",
}


class Unresolved(Exception):
    pass


def module_constants(tree: ast.Module) -> dict:
    """Module-level `NAME = literal` and `A, B = literal, literal` assignments."""
    found: dict = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                bind(target, node.value, found, found)
    return found


def bind(target: ast.AST, value: ast.AST, out: dict, names: dict) -> None:
    try:
        resolved = evaluate(value, names)
    except Unresolved:
        return
    assign(target, resolved, out)


def assign(target: ast.AST, value, out: dict) -> None:
    if isinstance(target, ast.Name):
        out[target.id] = value
    elif isinstance(target, (ast.Tuple, ast.List)) and isinstance(value, (tuple, list)) \
            and len(value) == len(target.elts):
        for element, item in zip(target.elts, value):
            assign(element, item, out)


def evaluate(node: ast.AST, names: dict):
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        if node.id in names:
            return names[node.id]
        raise Unresolved(node.id)
    if isinstance(node, (ast.Tuple, ast.List)):
        return tuple(evaluate(element, names) for element in node.elts)
    if isinstance(node, ast.Subscript):
        return evaluate(node.value, names)[evaluate(node.slice, names)]
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return evaluate(node.left, names) + evaluate(node.right, names)
    raise Unresolved(ast.unparse(node))


def parents(tree: ast.AST) -> dict:
    found = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            found[child] = node
    return found


def environments(call: ast.Call, tree: ast.Module, up: dict, constants: dict) -> list[dict]:
    """The name bindings the call can see: one per enclosing loop item and per call of its enclosing function."""
    chain = []
    node = call
    while node in up:
        node = up[node]
        chain.append(node)
    envs = [dict(constants)]
    for scope in reversed(chain):
        if isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef)):
            envs = [env for base in envs for env in function_bindings(scope, tree, base)]
            for statement in ast.walk(scope):
                if isinstance(statement, ast.Assign):
                    for env in envs:
                        for target in statement.targets:
                            bind(target, statement.value, env, env)
        elif isinstance(scope, ast.For):
            expanded = []
            for env in envs:
                try:
                    items = evaluate(scope.iter, env)
                except Unresolved:
                    expanded.append(env)
                    continue
                for item in items:
                    bound = dict(env)
                    assign(scope.target, item, bound)
                    expanded.append(bound)
            envs = expanded
    return envs


def function_bindings(function: ast.FunctionDef, tree: ast.Module, base: dict) -> list[dict]:
    """The enclosing function's parameters, one binding per literal call of it in the module (else none)."""
    params = [a.arg for a in function.args.args]
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
             and ((isinstance(node.func, ast.Name) and node.func.id == function.name)
                  or (isinstance(node.func, ast.Attribute) and node.func.attr == function.name))]
    if not calls or params[:1] == ["self"]:
        return [dict(base)]
    found = []
    for call in calls:
        env = dict(base)
        for name, value in zip(params, call.args):
            bind(ast.Name(id=name), value, env, base)
        for keyword in call.keywords:
            if keyword.arg:
                bind(ast.Name(id=keyword.arg), keyword.value, env, base)
        found.append(env)
    return found


def call_arguments(call: ast.Call, env: dict) -> dict:
    nodes = dict(zip(PARAMETERS, call.args))
    nodes.update({k.arg: k.value for k in call.keywords if k.arg in PARAMETERS})
    values = {}
    for name in PARAMETERS:
        if name not in nodes:
            values[name] = None
            continue
        try:
            values[name] = evaluate(nodes[name], env)
        except Unresolved:
            values[name] = f"<{ast.unparse(nodes[name])}>"
    return values


def map_name(project: str) -> str:
    stem = project.removeprefix("mm9r_")
    return stem.removesuffix("_blv")


def scan_sites() -> list[dict]:
    sites = []
    for path in sorted(PROJECTS.glob("mm9r_*/*.py")):
        if path.parent == COMMON or path.name.startswith("test_"):
            continue
        text = path.read_text(encoding="utf-8")
        if not any(name in text for name in SITE_FUNCTIONS):
            continue
        tree = ast.parse(text, filename=str(path))
        up = parents(tree)
        constants = module_constants(tree)
        for call in ast.walk(tree):
            if not (isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
                    and call.func.id in SITE_FUNCTIONS):
                continue
            seen = set()
            for env in environments(call, tree, up, constants):
                args = call_arguments(call, env)
                signature = tuple(args.values())
                if signature in seen:
                    continue
                seen.add(signature)
                site = {"map": map_name(path.parent.name), "file": str(path.relative_to(ROOT)),
                        "line": call.lineno, **args}
                if isinstance(args["original"], int):
                    plain = {k: (v if not (isinstance(v, str) and v.startswith("<")) else None)
                             for k, v in args.items()}
                    site["balanced"] = balanced_experience(**plain)
                else:
                    site["balanced"] = None
                sites.append(site)
    return sites


def profile_entries() -> list[dict]:
    """The profile's awards with the map from each entry's comment line."""
    import yaml
    text = PROFILE_PATH.read_text(encoding="utf-8")
    awards = (yaml.safe_load(text) or {}).get("awards") or []
    comments = re.findall(r"^  # ([^,\n]+),", text, flags=re.M)
    if len(comments) != len(awards):
        comments = [None] * len(awards)
    return [{"script": a["script"], "routine": a["routine"], "original": int(a["original"]), "xp": int(a["xp"]),
             "key": a.get("key"), "map": m} for a, m in zip(awards, comments)]


def matches(entry: dict, site: dict) -> bool:
    if site["original"] != entry["original"]:
        return False
    if entry["key"] is not None and site["key"] == entry["key"]:
        return True
    script, routine = site["script"], site["routine"]
    return (isinstance(script, str) and isinstance(routine, str) and script.lower() == entry["script"].lower()
            and routine.lower() == entry["routine"].lower())


def main() -> int:
    sites = scan_sites()
    entries = profile_entries()
    unresolved = [s for s in sites if not isinstance(s["original"], int)]
    matched, unmatched = [], []
    for entry in entries:
        paying = [f"{s['map']} ({s['file']}:{s['line']}, key {s['key']})" for s in sites if matches(entry, s)]
        if paying:
            matched.append({**entry, "sites": paying})
        else:
            reason = UNMATCHED_REASONS.get((entry["script"], entry["routine"], entry["original"]),
                                           "no rework site found")
            unmatched.append({**entry, "reason": reason})
    for site in sites:
        site["profile"] = [f"{e['script']}:{e['routine']}" for e in entries if matches(e, site)] or None
    report = {
        "about": "MM9 quest XP caps in the rework converters (devdocs/mm9_rework/BALANCE_PLAN.md 3.1); generated by "
                 "level_generation/projects/mm9r_common/quest_xp_audit.py from the converters' sources",
        "profile": str(PROFILE_PATH.relative_to(ROOT)),
        "summary": {
            "sites": len(sites),
            "capped_sites": sum(1 for s in sites if s["balanced"] is not None and s["balanced"] != s["original"]),
            "unresolved_sites": len(unresolved),
            "profile_entries": len(entries),
            "matched_entries": len(matched),
            "unmatched_entries": len(unmatched),
        },
        "sites": sites,
        "matched": matched,
        "unmatched": unmatched,
    }
    OUTPUT.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"]))
    for entry in unmatched:
        print(f"unmatched: {entry['map']} {entry['script']} {entry['routine']} {entry['original']}: {entry['reason']}")
    for site in unresolved:
        print(f"unresolved: {site['file']}:{site['line']} {site}")
    return 1 if unresolved else 0


if __name__ == "__main__":
    sys.exit(main())
