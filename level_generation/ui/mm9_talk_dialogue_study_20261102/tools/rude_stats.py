#!/usr/bin/env python3
"""Measure MM9 RUDE dialogue limits: options per node and text lengths.

Reads assets_dev/worlds/mm9/dialogue/rude/NPC*.rude, NPCNAME.rude and TOPBLURB.rude and writes
rude_stats.json next to this study plus a short summary on stdout. Row layout (see
devdocs/mm9/MM9_RUDE_DIALOGUE.md): c01 rude id, c02 node, c03 choice slot, c04 party prompt,
c05 NPC response, c06 next, c07/c09/c11/c13/c15 required keys, c21-c25 forbidden keys.
"""
import csv
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
RUDE_DIR = ROOT / "assets_dev/worlds/mm9/dialogue/rude"
OUT = Path(__file__).resolve().parents[1] / "rude_stats.json"
# Not talk dialogue: 997-999 are the journal's Quest Notes, Auto Notes and Awards lists stored as RUDE files, and
# 400 is the designers' "Keys and Locks!!!!!" key-toggle debug NPC.
EXCLUDED = {400, 997, 998, 999}
SERVICES = {-2: "shop", -3: "training", -4: "skill training", -5: "travel", -6: "bank", -7: "inn", -8: "healer",
            -10: "hire", -11: "dismiss", -13: "item combine", -14: "quest handoff", -15: "town portal",
            -16: "donation"}


def max_compatible(rows):
    """Largest set of a node's rows that can show at once: no row forbids a key another row requires.

    An upper bound on simultaneously visible choices (it ignores that keys are granted in story order)."""
    best = 0
    count = len(rows)
    if count > 20:
        return count
    for mask in range(1, 1 << count):
        chosen = [rows[i] for i in range(count) if mask >> i & 1]
        if len(chosen) <= best:
            continue
        required = set().union(*(set(row["required"]) for row in chosen))
        forbidden = set().union(*(set(row["forbidden"]) for row in chosen))
        if required & forbidden:
            continue
        best = len(chosen)
    return best


def pct(values, p):
    ordered = sorted(values)
    if not ordered:
        return 0
    index = min(len(ordered) - 1, max(0, math.ceil(p / 100.0 * len(ordered)) - 1))
    return ordered[index]


def summary(values):
    return {
        "count": len(values),
        "max": max(values),
        "p99": pct(values, 99),
        "p95": pct(values, 95),
        "p90": pct(values, 90),
        "median": pct(values, 50),
        "mean": round(sum(values) / len(values), 1),
    }


def read_rows(path):
    text = path.read_bytes().decode("cp1252")
    return [r for r in csv.reader(text.splitlines()) if r and r[0].strip()]


def to_int(value):
    try:
        return int(value.strip())
    except ValueError:
        return 0


def main():
    names = {}
    for r in read_rows(RUDE_DIR / "NPCNAME.rude"):
        names[to_int(r[0])] = r[1]
    blurbs = {}
    for r in read_rows(RUDE_DIR / "TOPBLURB.rude"):
        blurbs[to_int(r[0])] = r[2] if len(r) > 2 else ""

    nodes = defaultdict(list)
    kinds = defaultdict(int)
    services = defaultdict(int)
    prompts, responses = [], []
    longest_prompt, longest_response = ("", None), ("", None)
    for path in sorted(RUDE_DIR.glob("NPC*.rude")):
        if path.name in ("NPCNAME.rude",):
            continue
        for r in read_rows(path):
            if len(r) < 6:
                continue
            rude_id, node, slot = to_int(r[0]), to_int(r[1]), to_int(r[2])
            if rude_id in EXCLUDED:
                continue
            prompt, response = r[3], r[4]
            required = [to_int(r[i]) for i in (6, 8, 10, 12, 14) if i < len(r)]
            forbidden = [to_int(r[i]) for i in range(20, 25) if i < len(r)]
            nxt = to_int(r[5])
            kinds["exit" if nxt == -1 else "service" if nxt < -1 else "goto"] += 1
            if nxt < -1:
                services[SERVICES.get(nxt, str(nxt))] += 1
            if any(required):
                kinds["quest_gated"] += 1
            nodes[(rude_id, node)].append(
                {"slot": slot, "prompt": prompt, "response": response, "next": nxt,
                 "required": [k for k in required if k], "forbidden": [k for k in forbidden if k],
                 "file": path.name})
            if prompt:
                prompts.append(len(prompt))
                if len(prompt) > len(longest_prompt[0]):
                    longest_prompt = (prompt, f"{path.name} node {node} slot {slot}")
            if response:
                responses.append(len(response))
                if len(response) > len(longest_response[0]):
                    longest_response = (response, f"{path.name} node {node} slot {slot}")

    rows_per_node = [len(v) for v in nodes.values()]
    slots_per_node = [len({row["slot"] for row in v}) for v in nodes.values()]
    unconditional_per_node = [
        len({row["slot"] for row in v if not row["required"] and not row["forbidden"]}) for v in nodes.values()]
    compatible_per_node = [max_compatible(v) for v in nodes.values()]
    blurb_lengths = [len(b) for k, b in blurbs.items() if b and k not in EXCLUDED]
    name_lengths = [len(n) for k, n in names.items() if n and k not in EXCLUDED]

    widest = sorted(nodes.items(), key=lambda item: len({row["slot"] for row in item[1]}), reverse=True)[:12]
    # Lines in a 480 px wrap at about 6.4 px per RUDE glyph: a rough count of the current panel's lines.
    stats = {
        "source": str(RUDE_DIR.relative_to(ROOT)),
        "npc_files": len(list(RUDE_DIR.glob("NPC*.rude"))) - 1 - len(EXCLUDED),
        "nodes": len(nodes),
        "rows": sum(rows_per_node),
        "rows_per_node": summary(rows_per_node),
        "distinct_choice_slots_per_node": summary(slots_per_node),
        "unconditional_slots_per_node": summary(unconditional_per_node),
        "max_compatible_choices_per_node": summary(compatible_per_node),
        "nodes_with_more_than_3_compatible": sum(1 for s in compatible_per_node if s > 3),
        "nodes_with_more_than_6_compatible": sum(1 for s in compatible_per_node if s > 6),
        "nodes_with_more_than_3_slots": sum(1 for s in slots_per_node if s > 3),
        "nodes_with_more_than_6_slots": sum(1 for s in slots_per_node if s > 6),
        "row_kinds": dict(kinds),
        "service_rows": dict(sorted(services.items(), key=lambda item: -item[1])),
        "nodes_with_an_exit_row": sum(1 for v in nodes.values() if any(row["next"] == -1 for row in v)),
        "non_exit_choices_per_node": summary([sum(1 for row in v if row["next"] != -1) for v in nodes.values()]),
        "prompt_chars": summary(prompts),
        "response_chars": summary(responses),
        "top_blurb_chars": summary(blurb_lengths),
        "npc_name_chars": summary(name_lengths),
        "responses_over_300": sum(1 for n in responses if n > 300),
        "responses_over_600": sum(1 for n in responses if n > 600),
        "prompts_over_60": sum(1 for n in prompts if n > 60),
        "prompts_over_90": sum(1 for n in prompts if n > 90),
        "longest_prompt": {"chars": len(longest_prompt[0]), "where": longest_prompt[1], "text": longest_prompt[0]},
        "longest_response": {"chars": len(longest_response[0]), "where": longest_response[1],
                             "text": longest_response[0]},
        "longest_name": max((n for k, n in names.items() if k not in EXCLUDED), key=len),
        "widest_nodes": [
            {"rude_id": key[0], "node": key[1], "npc": names.get(key[0], ""),
             "rows": len(value), "slots": len({row["slot"] for row in value}),
             "max_compatible": max_compatible(value),
             "prompts": [row["prompt"] for row in sorted(value, key=lambda row: row["slot"])]}
            for key, value in widest],
    }
    OUT.write_text(json.dumps(stats, indent=2, ensure_ascii=False) + "\n")
    for key in ("npc_files", "nodes", "rows", "rows_per_node", "distinct_choice_slots_per_node",
                "row_kinds", "service_rows", "nodes_with_an_exit_row", "non_exit_choices_per_node",
                "unconditional_slots_per_node", "max_compatible_choices_per_node",
                "nodes_with_more_than_3_compatible", "nodes_with_more_than_6_compatible", "nodes_with_more_than_3_slots", "nodes_with_more_than_6_slots",
                "prompt_chars", "response_chars", "top_blurb_chars", "npc_name_chars", "responses_over_300",
                "responses_over_600", "prompts_over_60", "prompts_over_90"):
        print(f"{key}: {stats[key]}")
    print("longest prompt:", stats["longest_prompt"]["chars"], stats["longest_prompt"]["where"])
    print("longest response:", stats["longest_response"]["chars"], stats["longest_response"]["where"])
    for node in stats["widest_nodes"][:6]:
        print("wide:", node["rude_id"], node["node"], node["npc"], node["rows"], node["slots"], node["max_compatible"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
