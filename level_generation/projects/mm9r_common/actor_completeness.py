#!/usr/bin/env python3
"""
The MM9 actor completeness audit (devdocs/mm9_rework/MM9_ACTOR_COMPLETENESS.md): every character-like DAT object of
the 44 rebuilt maps against what the rework places, and every RUDE dialogue against what opens it.

    python3 level_generation/projects/mm9r_common/actor_completeness.py            # summary, MISSING list, RUDE gaps
    python3 level_generation/projects/mm9r_common/actor_completeness.py --json out.json

Check 1 (objects): a DAT object is a character when it has MM9 AI properties (SightDistance/HearingDistance), is a
RUDEProp or carries RUDENPCId/NPCNbr/DoRude, is a Spawner, or is a prop drawn with a character model (a posed figure).
Its status: PLACED_ACTOR (its anchor in the project's work/content.json actors), PLACED_PROP (work/props.json or a
content.json decoration), else the reasoned rule in RULES (SCRIPTED, EXCLUDED, MISSING, or PLACED_ACTOR still pending
the next conversion); an object no rule covers is UNRESOLVED. A pending PLACED_ACTOR is a rule written before the final
rebuild: once the map is reconverted the object must be in content.json, or the audit reports it.
Check 2 (dialogues): every assets_dev/worlds/mm9/dialogue/rude/NPC<id>.rude against the installed scenes'
mm9_rude_id, the map Lua's MM9.openRude / evt.OpenMm9Rude and hirelings.txt; and each DAT host's own id (DoRude with
NPCnnn.scr, NPC_nnn.wav or NPCNbr; RUDENPCId; DoRude.scr) against its placed actor's mm9_rude_id or the map Lua.
Nothing is written into assets_dev.
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import struct
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
PROJECTS = ROOT / "level_generation/projects"
RAW = ROOT / "assets_editor_dev/worlds/mm9/maps"
WORLD = ROOT / "assets_dev/worlds/mm9"
SCRIPTS = ROOT / "mm9/extracted/SCRIPTS/SCRIPTS"
# models that a character class also uses but that are not characters (CommonerHuman2MaleA's tree04 placeholder)
NOT_FIGURES = {"tree04.abc", ""}
EXTRA_FIGURES = {"njam.abc", "fre.abc", "wyrd_old.abc", "wyrd_mature.abc", "wyrd_young.abc", "mummyew.abc"}
# RUDE files that are not dialogues: the journal's quest notes, autonotes and awards (generate_mm9_quest_interactions)
JOURNAL_RUDE = {997, 998, 999}

# (map stem, DAT name pattern, status, reason) for the objects the last conversion does not place; the reasons are
# checked against MM9's scripts (MM9_ACTOR_COMPLETENESS.md). PENDING = PLACED_ACTOR at the next conversion.
PENDING = "PLACED_ACTOR_PENDING"
RULES = [
    ("1000terrors", r"SquareObj\d+", "EXCLUDED", "ChessSquare.scr square (Fish class, Visible 0): an invisible script "
     "holder; the map Lua carries the 64 squares as the boxes the pieces attack (CHESS)"),
    ("1000terrors", r"Spawner\d+", "SCRIPTED", "Spawner DefaultSpawn: the map Lua's SPAWNS, send(target, 'spawn')"),
    ("1000terrors", r"LeverHand", "EXCLUDED", "WG_hand.scr :Init clears Visible; :OnPlay (the win cinema) never sets it "
     "again (its SetFlag is commented out): never seen in MM9"),
    ("anskramkeep", r"ImpGateSpawner\d", "SCRIPTED", "AK_ImpGate.scr holder (Fish class, Visible 0): the map Lua's imp "
     "gates send its five Imps"),
    ("beethoven", r"LobberPod[AB]0", "SCRIPTED", "CacheOnly template of the Lobbers' pods: the engine's pod launch"),
    ("bootcamp", r"(Goat|Cow|BrownCow)\d", PENDING, "monster_classes (M19), npc_rows rows 9268 / 9267 / 9297"),
    ("bootcamp", r".*CACHEONLY", "SCRIPTED", "CacheOnly template of BC_Manager.scr (Switch0/1 'fight' / 'open'): "
     "regionlua.py museum_lines spawns the demonstration fight and the chest-opening monk (M22)"),
    ("chasmofthedead", r"GhostSpawner", "SCRIPTED", "Chasm_GhostSpawner.scr holder (Visible 0): spawnGhost()"),
    ("chasmofthedead", r"ApparitionCACHE_ONLY", "SCRIPTED", "CacheOnly template of spawnGhost()'s row 9139"),
    ("dragonstadium", r"WingedMutantCache", "SCRIPTED", "CacheOnly template of Dragon.scr :SpawnMutants"),
    ("drangheimprison", r"DwarvenSmith1", "EXCLUDED", "DrangheimSmith.scr :Main p0 0: RemoveObject at once"),
    ("frosgard", r"IceLobbercicle0", "SCRIPTED", "CacheOnly template of the Ice Lobbers' pods: the engine's pod launch"),
    ("guberland", r"AtliGuard", PENDING, "outdoor.people with the Guard row 9111; regionlua.py hides him at key 197"),
    ("hallofthegods", r"DragonAzure\d", "EXCLUDED", "models\\DragonAzure.abc is not in MM9's MODELS and the class has "
     "no MONSTERS.txt row: MM9 has nothing to show"),
    ("tasaracademy", r"Dagrell0", "SCRIPTED", "CacheOnly template; the crate's SpawnObject Dagrell is placed hidden"),
    ("templeofhonk", r"BigHonk[01]", PENDING, "Goose row 9293 (M19)"),
    ("templeofhonk", r"Fish\d", PENDING, "Fish row 9227 (M19)"),
    ("templeofhonk", r"Skeleton1[01]", "EXCLUDED", "CacheOnly 1 and no script of the map spawns Honk or Honk2"),
    ("thjorgard", r"ShopkeeperElfFemaleB8", "EXCLUDED", "Hjarrand, parked about 28 000 units outside the region with "
     "no MM9 polygon under him; RUDE 7 is reached in Thjorgard City and Thjorad Mine"),
    ("thronheimcity", r"GuardSpawn1", "SCRIPTED", "Thronheimcity_BadAss.scr :GetExtraGuard: the hidden ExtraGuard"),
    ("thronheimcity", r"GuardSpawn0", "SCRIPTED", "ThronheimCity_Guard.scr :OnDeath: each dead breakout guard sends a "
     "new one from here while the Terror lives (citylua.py kill hook, at most GUARDS_SENT_CAP; M23)"),
    ("thronheimcity", r"(Kira|Bjarni|Sigmund|Forad|Tryygva|Markel|Sven)", "EXCLUDED", "the Argument cinema's cast "
     "(ARG_*.scr) on its stage under the city, not built; the council is the six posed RUDEProps"),
    ("wizardslab", r"GreaterDemonCACHEONLY", "SCRIPTED", "CacheOnly template of WizardMaster.scr's summon (9242)"),
    ("yanmirsfort", r"IceLobbercicle8", "SCRIPTED", "CacheOnly template: YanmirFort_BugSpawn.scr respawns, pods"),
    ("yanmirsfort", r"Spawner\d", "SCRIPTED", "Spawner DefaultSpawn Yeti/Thrall: convert.py SPAWNERS"),
    ("yorwick", r"Ewe0", PENDING, "Ewe row 9272 (M19); MarySheep.scr's following is not carried"),
    ("yorwick", r"(Kira0?|Sven\d*|Tryygva|guard)", "EXCLUDED", "battlefield figure: SvenShowTake.inc :RemoveAll hides "
     "it on every load but during the battlefield cutscene (cutscene work)"),
]


def load_objects(path: Path) -> list[dict]:
    """A raw_objects.yml (mm9_raw_world_objects) as [{index, class, properties}], read line by line (fast)."""
    objects, current, name = [], None, None
    for line in path.open(encoding="utf-8"):
        if line.startswith("  - object_index: "):
            current = {"index": int(line.split(":")[1]), "class": None, "properties": {}}
            objects.append(current)
            name = None
        elif current is not None and current["class"] is None and line.startswith("    name: "):
            current["class"] = json.loads(line[len("    name: "):])
        else:
            stripped = line.strip()
            if stripped.startswith('- name: "'):
                name = stripped[len('- name: "'):-1]
            elif stripped.startswith("value_json: ") and current is not None and name is not None:
                try:
                    current["properties"].setdefault(name, json.loads(json.loads(stripped[len("value_json: "):])))
                except json.JSONDecodeError:
                    pass
                name = None
    return objects


def model(p: dict) -> str:
    return str(p.get("Filename", "")).replace("\\", "/").lower().split("/")[-1]


def script(p: dict) -> str:
    return str(p.get("ScriptName") or "").replace("\\", "/").split("/")[-1].lower()


def float_id(value) -> int:
    """MM9 stores NPCNbr / RUDENPCId as a float's bits."""
    if isinstance(value, int) and 0 <= value <= 0xFFFFFFFF:
        decoded = struct.unpack("<f", struct.pack("<I", value))[0]
        if decoded.is_integer() and 0 < decoded < 10000:
            return int(decoded)
    return 0


def projects() -> dict[str, Path]:
    out = {}
    for directory in sorted(PROJECTS.glob("mm9r_*")):
        overrides = directory / "overrides.yml"
        if overrides.exists() and (directory / "work/content.json").exists():
            out[yaml.safe_load(overrides.read_text())["map"]["stem"]] = directory
    return out


def kind(o: dict, figures: set) -> str | None:
    p = o["properties"]
    if "SightDistance" in p or "HearingDistance" in p:
        return "ai"
    if o["class"] == "RUDEProp" or "RUDENPCId" in p:
        return "rudeprop"
    if "NPCNbr" in p or "DoRude" in p:
        return "npc"
    if o["class"] == "Spawner" or "DefaultSpawn" in p:
        return "spawner"
    if model(p) in figures:
        return "figure"
    return None


def check_objects(maps: dict[str, list], stems: dict[str, Path]) -> list[dict]:
    figures = {model(o["properties"]) for objects in maps.values() for o in objects
               if "SightDistance" in o["properties"] or o["class"] == "RUDEProp"} - NOT_FIGURES | EXTRA_FIGURES
    rows = []
    for stem, directory in stems.items():
        content = json.loads((directory / "work/content.json").read_text())
        anchors = {a["anchor"] for a in content["actors"]}
        decorations = {d["anchor"] for d in content["decorations"]}
        props = json.loads((directory / "work/props.json").read_text()) if (directory / "work/props.json").exists() \
            else []
        prop_objects = {p.get("source_object") for p in props}
        prop_names = {p.get("source_name") for p in props}
        for o in maps[stem]:
            what = kind(o, figures)
            if what is None:
                continue
            name = str(o["properties"].get("Name", ""))
            row = {"map": stem, "index": o["index"], "class": o["class"], "name": name, "kind": what}
            if name in anchors:
                row["status"], row["reason"] = "PLACED_ACTOR", "content.json"
            elif o["index"] in prop_objects or {name, "obj_" + name} & (prop_names | decorations):
                row["status"], row["reason"] = "PLACED_PROP", "props.json / decoration"
            else:
                rule = next((r for r in RULES if r[0] == stem and re.fullmatch(r[1], name)), None)
                row["status"], row["reason"] = (rule[2], rule[3]) if rule else ("UNRESOLVED", "no rule")
            rows.append(row)
    return rows


def script_text() -> dict[str, str]:
    return {f.name.lower(): f.read_text(errors="replace") for f in SCRIPTS.iterdir()}


def includes(texts: dict, name: str, seen: set | None = None) -> set:
    seen = set() if seen is None else seen
    for match in re.finditer(r'#include\s+"?([\w.]+)"?', texts.get(name, ""), re.IGNORECASE):
        if match.group(1).lower() not in seen:
            seen.add(match.group(1).lower())
            includes(texts, match.group(1).lower(), seen)
    return seen


def check_dialogues(maps: dict[str, list], stems: dict[str, Path]) -> dict:
    texts = script_text()
    files = sorted(int(m.group(1)) for f in (WORLD / "dialogue/rude").iterdir()
                   if (m := re.match(r"NPC(\d+)\.rude$", f.name)))
    hosts = collections.defaultdict(list)          # rude id -> [(map, DAT name)]
    for stem, objects in maps.items():
        for o in objects:
            p, name, ids = o["properties"], str(o["properties"].get("Name", "")), set()
            if p.get("DoRude"):
                if m := re.match(r"npc(\d+)\.scr$", script(p)):
                    ids.add(int(m.group(1)))
                if m := re.search(r"NPC_(\d+)\.wav$", str(p.get("GreetingSound") or ""), re.IGNORECASE):
                    ids.add(int(m.group(1)))
                ids.add(float_id(p.get("NPCNbr")))
            ids.add(float_id(p.get("RUDENPCId")))
            words = str(p.get("ScriptParams") or "").split()
            if script(p) == "dorude.scr" and words and words[0].isdigit():
                ids.add(int(words[0]))
            for source in {script(p)} | includes(texts, script(p)) if script(p) else ():
                ids |= {int(m.group(1)) for m in re.finditer(r"^\s*DoRude\s+(\d+)\s*$", texts.get(source, ""),
                                                             re.MULTILINE | re.IGNORECASE)}
            for rude in ids - {0}:
                hosts[rude].append((stem, name))
    reached = collections.defaultdict(set)
    lua_rudes = collections.defaultdict(set)
    for scene in (WORLD / "maps").glob("*.scene.yml"):
        for m in re.finditer(r'mm9_rude_id"?\s*:\s*(-?\d+)', scene.read_text()):
            reached[int(m.group(1))].add("actor:" + scene.name.split(".")[0])
    for lua in list((WORLD / "events").rglob("*.lua")) + list((WORLD / "behaviors").glob("*.lua")):
        for m in re.finditer(r"(?:openRude|OpenMm9Rude)\(\s*(\d+)\s*\)", lua.read_text()):
            reached[int(m.group(1))].add("lua:" + lua.stem)
            lua_rudes[lua.stem].add(int(m.group(1)))
    for line in (WORLD / "data_tables/hirelings.txt").read_text().splitlines()[1:]:
        if line.strip():
            reached[int(line.split("\t")[0])].add("hireling")
    unreachable = [{"rude": r, "hosts": hosts.get(r, []), "journal": r in JOURNAL_RUDE} for r in files
                   if r not in reached]
    # each placed host shows its own id (or the map Lua opens it)
    host_ids = collections.defaultdict(set)        # (map, DAT name) -> its RUDE ids
    for rude, where in hosts.items():
        for host in where:
            host_ids[host].add(rude)
    wrong = []
    for stem, directory in stems.items():
        content = json.loads((directory / "work/content.json").read_text())
        scene = yaml.load((WORLD / f"maps/{stem}.scene.yml").read_text(), Loader=yaml.CSafeLoader)
        actors = scene["initial_state"].get("actors", [])
        for a in content["actors"]:
            ids = host_ids.get((stem, a["anchor"]))
            if not ids or ids & lua_rudes.get(stem, set()):
                continue
            shown = actors[a["actor_index"]].get("mm9_rude_id") if a["actor_index"] < len(actors) else None
            if shown not in ids:
                wrong.append({"map": stem, "name": a["anchor"], "rude": sorted(ids), "scene": shown})
    return {"files": len(files), "reached": sum(1 for r in files if r in reached), "unreachable": unreachable,
            "wrong_host": wrong}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--json", type=Path, help="write the full report here")
    args = parser.parse_args()
    stems = projects()
    maps = {stem: load_objects(RAW / f"{stem}.raw_objects.yml") for stem in stems}
    rows = check_objects(maps, stems)
    dialogues = check_dialogues(maps, stems)
    totals = collections.Counter(r["status"] for r in rows)
    print(f"{len(stems)} maps, {len(rows)} character objects:", dict(sorted(totals.items())))
    per_map = collections.defaultdict(collections.Counter)
    for r in rows:
        per_map[r["map"]][r["status"]] += 1
    for stem in sorted(per_map):
        print(f"  {stem:22}", dict(sorted(per_map[stem].items())))
    for r in rows:
        if r["status"] in ("MISSING", "UNRESOLVED", PENDING):
            print(f"{r['status']}: {r['map']} {r['name']} ({r['class']}): {r['reason']}")
    print(f"RUDE: {dialogues['files']} dialogues, {dialogues['reached']} reachable")
    for u in dialogues["unreachable"]:
        print(f"  unreachable {u['rude']}: " + ("journal table" if u["journal"] else
                                               (", ".join(f"{m} {n}" for m, n in u["hosts"]) or "no MM9 host")))
    for w in dialogues["wrong_host"]:
        print(f"  host {w['map']} {w['name']}: MM9 RUDE {w['rude']}, scene {w['scene']}")
    if args.json:
        args.json.write_text(json.dumps({"objects": rows, "dialogues": dialogues}, indent=1))
    return 1 if totals.get("UNRESOLVED") else 0


if __name__ == "__main__":
    raise SystemExit(main())
