"""MM9's arena monster table (SCRIPTS/PICKMON.inc :PickMonster, :Group1-21) parsed into level groups, each class
resolved to its runtime MM9 monster row (the old importer's replacement table, as the dungeon converter's
content.monster_bases). Used by convert.py; run alone it prints the table and the unresolved classes."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PICKMON = ROOT / "mm9/extracted/SCRIPTS/SCRIPTS/PICKMON.inc"


def parse() -> tuple[list, dict]:
    """(ranges, groups): ranges [(low, high, group)] from :PickMonster (g_ntemp's level); groups {n: [(class, level)]}
    in the order of their getrandomint cases (1..k)."""
    text = PICKMON.read_text(encoding="latin-1").replace("\r", "")
    head, _, rest = text.partition(":Group1\n")
    ranges = []
    for m in re.finditer(r"if \(g_ntemp>=(\d+)\)\s*\n\s*if \(?g_ntemp<=(\d+)\)\s*\n\s*gosub Group(\d+)", head):
        ranges.append((int(m[1]), int(m[2]), int(m[3])))
    for m in re.finditer(r"if \(g_ntemp==(\d+)\)\s*\n\s*gosub Group(\d+)", head):
        ranges.append((int(m[1]), int(m[1]), int(m[2])))
    for m in re.finditer(r"if \(g_ntemp>(\d+)\)\s*\n\s*gosub Group(\d+)", head):
        ranges.append((int(m[1]) + 1, 999, int(m[2])))
    groups = {}
    for m in re.finditer(r":Group(\d+)\n(.*?)(?=\n:Group|\Z)", ":Group1\n" + rest, re.S):
        cases = {}
        for c in re.finditer(r"if \(nMonTemp==(\d+)\)\s*\n\s*set sMonster_Temp (\w+)\s*\n\s*set nMonster_Level (\d+)",
                             m[2]):
            cases[int(c[1])] = (c[2], int(c[3]))
        count = int(re.search(r"getrandomint 1, (\d+) nMonTemp", m[2])[1])
        groups[int(m[1])] = [cases.get(k) for k in range(1, count + 1)]
    return sorted(ranges), groups


def rows(classes) -> dict:
    """MM9 class name -> runtime monster row (or None)."""
    sys.path.insert(0, str(ROOT / "tools/mm9_import_discovery"))
    sys.path.insert(0, str(ROOT / "level_generation/projects/mm9r_common"))
    from dungeon.content import monster_replacements
    from transcode_mm9_dat_to_odm import normalized_binding_name
    replacements = monster_replacements()
    out = {}
    for name in classes:
        candidates = replacements.get(normalized_binding_name(name), [])
        out[name] = min(candidates, key=lambda c: c.source_number).runtime_monster_id if candidates else None
    return out


if __name__ == "__main__":
    ranges, groups = parse()
    print(ranges)
    classes = sorted({c for g in groups.values() for c in g if c} , key=str)
    resolved = rows({c[0] for c in classes})
    for n, g in sorted(groups.items()):
        print(n, [(c[0], c[1], resolved[c[0]]) if c else None for c in g])
    print("unresolved:", sorted(k for k, v in resolved.items() if v is None))
