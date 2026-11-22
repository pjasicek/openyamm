#!/usr/bin/env python3
"""MAW in the World of Xeen: check the single source of Xeen's MAW numbers and derive what is made from it.

assets_dev/engine/rulesets/maw/worlds/xeen/balance.yml is the only file edited by hand (devdocs/maw/XEEN_SUPPORT.md).
This tool
  - checks it against Xeen's maps, monsters and quest bits: every Xeen map listed with a band in order, madness
    levels, natives naming Xeen families, story bands on Xeen quest bits, exclusions naming Xeen monsters, and the
    `xeen` columns of rulesets/maw/data/promotions.yml naming Xeen quest bits; and that every pack reserve
    (tools/maw/xeen_pack_reserve.py) was placed against the installed scene;
  - writes beside it item_bases.yml (MAW bases of Xeen's ordinary gear: the gem gear on the base of the MM6-MM8 item
    whose picture it wears) and new_game_continents.yml (Xeen's new-game card with MAW's four new class lines, which
    ruleset.yml puts in place of the world's own card);
  - with --draft FILE writes the suggested bands and madness levels for every map from Xeen's acts (the curve below),
    to compare with or to start balance.yml from;
  - with --review FILE writes a Markdown page for testers: each map's act, Standard party and monster levels, band,
    natives and the families its scene places; the route check (a story map whose natives meet the party lower than
    the story map before it); the D-G rows placed where their stem family is native, with the level each rule gives.

  python3 tools/maw/xeen_balance.py [--check] [--draft FILE] [--review FILE]

--check only checks (and fails when a derived file is not what the sources give).
"""

import argparse
import csv
import re
import statistics
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
MAW = ROOT / "assets_dev/engine/rulesets/maw"
WORLD = ROOT / "assets_dev/worlds/xeen"
BALANCE = MAW / "worlds/xeen/balance.yml"
ITEM_BASES = MAW / "worlds/xeen/item_bases.yml"
CONTINENTS = MAW / "worlds/xeen/new_game_continents.yml"
PROMOTIONS = MAW / "data/promotions.yml"
QBITS = (110000, 119999)
# MAW's four new class lines (Seraphim, Death Knight, Shaman, Elementalist: content/character_selection.yml).
MAW_NEW_CLASSES = [53, 56, 59, 62]
# Xeen's ordinary gear (U-1: no new equipment but the gem gear); artifacts and relics keep their table values.
# Each piece: its tier (source/items.yml `crafted.*.tier`, Xeen's normalized MM6-MM8 tier) and its strength, MM9's
# figures for its strongest pieces: 1.10, 1.15 at the top tier (D-84 MX-6).
GEM_GEAR = {12540: (4, 1.10), 12541: (5, 1.10), 12542: (5, 1.10), 12543: (6, 1.15)}
# MAW's rung by MM6-MM8 tier, as MM9's qualities were put on it (worlds/mm9/balance.yml `rung_by_quality`: tiers 1-4
# and 6 on rungs 1, 2.25, 3.5, 4.75, 6); MM9 has no tier 5, which sits between its neighbours.
RUNG_BY_TIER = {1: 1, 2: 2.25, 3: 3.5, 4: 4.75, 5: 5.375, 6: 6}

# The suggested band's middle by the Standard party level of the map (MAW's MM7 stages as MM9's acts were put on
# them: devdocs/maw/MM9_BALANCE_DESIGN.md section 2; MM9 act 1 at party 6 sits at 6-9, its clans at 33 at 24-36,
# its finale at 64 at 75-95). Linear between the points.
CURVE = [(1, 3), (6, 7), (12, 11), (17, 15), (25, 22), (33, 30), (40, 40), (45, 47), (51, 57), (58, 70), (64, 85),
         (70, 95)]
# The party level of a map Xeen's registry gives none (towns, the finale), by act.
ACT_PARTY = {"I": 3, "II": 13, "III": 24, "IV": 36, "V": 48, "VI": 60, "optional": 63, "any": 30}
START_MAPS = {"xeen_x1.odm", "xeen_xd01.blv"}
HORIZONTAL_STARTERS = {"xeen_x1.odm", "xeen_xd01.blv", "xeen_xd02.blv", "xeen_xd05.blv"}
ARENA = "xeen_xd20.blv"
# Maps whose placed people are peaceful (Bosco's Hall, Shangri-La, the finale): nothing for the Progress tab to count.
PEACEFUL = {"xeen_dd25.blv", "xeen_xd17.blv", "xeen_p5.blv"}


def fail(errors):
    for error in errors:
        print("error: " + error, file=sys.stderr)
    sys.exit(1)


def table_rows(path):
    with open(path, encoding="utf-8", errors="replace") as file:
        return [row for row in csv.reader(file, delimiter="\t") if row and row[0].strip().isdigit()]


def read_monsters():
    return {int(row[0]): {"name": row[1], "picture": row[2].strip(), "level": int(row[3] or 0)}
            for row in table_rows(WORLD / "data_tables/monster_data.txt")}


def family_of(picture):
    return re.sub(r" [A-G]$", "", picture)


def read_world_maps():
    """Xeen's maps from its map table (generated from source/maps.yml): file -> id, name, encounter pictures."""
    maps = {}
    for row in table_rows(WORLD / "data_tables/map_stats.txt"):
        if len(row) > 24:
            pictures = [row[i].strip() for i in (16, 20, 24) if row[i].strip() and row[i].strip() != "0"]
            maps[row[2].strip().lower()] = {"id": int(row[0]), "name": row[1], "pictures": pictures}
    return maps


def read_registry():
    """The orchestrator's map registry (source/maps.yml): file -> key, act, party, levels, role."""
    registry = {}
    for entry in yaml.safe_load((WORLD / "source/maps.yml").read_text())["maps"]:
        registry[entry["stem"].lower()] = entry
    return registry


def party_level(entry):
    numbers = [int(value) for value in re.findall(r"\d+", str(entry.get("party", "")))]
    if numbers:
        return sum(numbers[:2]) / len(numbers[:2])
    return ACT_PARTY.get(str(entry.get("act", "")).split("-")[0], 30)


def curve(level):
    for (low_party, low_mid), (high_party, high_mid) in zip(CURVE, CURVE[1:]):
        if level <= high_party:
            share = max(0.0, (level - low_party) / (high_party - low_party))
            return low_mid + share * (high_mid - low_mid)
    return CURVE[-1][1]


def scene_rows(stem):
    """The monster rows a map's scene places, with their counts."""
    path = WORLD / "maps" / (stem.rsplit(".", 1)[0] + ".scene.yml")
    counts = {}
    if path.exists():
        for value in re.findall(r"^\s+monster_info_id: (\d+)", path.read_text(), re.M):
            counts[int(value)] = counts.get(int(value), 0) + 1
    return counts


def native_levels(pictures, monsters):
    by_picture = {monster["picture"]: monster["level"] for monster in monsters.values()}
    return sorted(by_picture[picture + " B"] for picture in pictures if picture + " B" in by_picture)


def map_natives(name, world_maps, balance):
    """The families MAW pins on a map: balance.yml `natives`, else the map table's encounter pictures."""
    own = ((balance or {}).get("maps") or {}).get(name, {}).get("natives")
    return list(own) if own else list(world_maps.get(name, {}).get("pictures", []))


def suggest(world_maps, registry, monsters, balance=None):
    """Bands and madness levels for every Xeen map from its act's Standard party level (CURVE), keeping the map's own
    native spread: low and high as the natives' highest B level to their lowest, held between 1.3x and 2x (MAW's
    MM6-MM8 bands mostly spread so), 1.4 with fewer than two. The curve gives the level the natives meet (D-84 MX-8):
    MAW pins one native to the band's low, two to its low and high, three to low, mid and high; so with one native
    the low is the curve's value, with two or three the mean of low and high is."""
    suggestions = {}
    for name, world_map in world_maps.items():
        entry = registry.get(name, {})
        level = party_level(entry)
        middle = curve(level)
        natives = native_levels(map_natives(name, world_maps, balance), monsters)
        if name == ARENA:
            band = [1, 1, 1]
        else:
            spread = min(max(natives[-1] / natives[0], 1.3), 2.0) if len(natives) >= 2 and natives[0] > 0 else 1.4
            low = middle if len(natives) == 1 else 2 * middle / (1 + spread)
            band = [low, low * (1 + spread) / 2, low * spread]
        band = [max(1, round(value)) for value in band]
        band[1] = max(band[0], min(band[1], band[2]))
        suggestions[name] = {"band": band, "party": level, "act": str(entry.get("act", "")), "key": entry.get("key", ""),
                             "natives": natives}
    ranked = sorted((name for name in suggestions if name != ARENA and name not in START_MAPS),
                    key=lambda name: (suggestions[name]["party"], name))
    for rank, name in enumerate(ranked, start=1):
        suggestions[name]["madness"] = max(5, round(500 * (rank / len(ranked)) ** 1.2))
    for name in START_MAPS:
        suggestions[name]["madness"] = 4
    suggestions[ARENA]["madness"] = 1
    return suggestions


def draft_text(suggestions, world_maps, registry, monsters):
    lines = ["# Suggested by tools/maw/xeen_balance.py --draft (route order by the Standard party level).", "maps:"]
    for name in sorted(suggestions, key=lambda name: (suggestions[name]["party"], name)):
        suggestion = suggestions[name]
        entry = registry.get(name, {})
        lines.append(f"  # {suggestion['key']} {world_maps[name]['name']}: act {suggestion['act']}, Standard party "
                     f"{entry.get('party', '-')}, monsters {entry.get('levels', '-')}; natives B "
                     f"{suggestion['natives'] or '-'}.")
        fields = [f"band: {suggestion['band']}"]
        if name in HORIZONTAL_STARTERS:
            fields.append("horizontal_starter: true")
        if name in START_MAPS:
            fields.append("madness_start: true")
        fields.append(f"madness_level: {suggestion['madness']}")
        lines.append(f"  {name}: {{{', '.join(fields)}}}")
    return "\n".join(lines) + "\n"


def quest_bits():
    text = (WORLD / "events/common/xeen_quests.lua").read_text()
    return {int(value): name for name, value in re.findall(r'\["([^"]+)"\] = (\d+)', text)}


def excluded(exclusions, monster_id, monster):
    for value in exclusions:
        text = str(value)
        if text.isdigit() and int(text) == monster_id:
            return True
        if text in (monster["name"], monster["picture"], family_of(monster["picture"])):
            return True
    return False


def check(balance, world_maps, monsters):
    errors = []
    maps = {name.lower(): entry for name, entry in (balance.get("maps") or {}).items()}
    for name in sorted(set(world_maps) - set(maps)):
        errors.append(f"{name} is a Xeen map and balance.yml does not list it")
    for name in sorted(set(maps) - set(world_maps)):
        errors.append(f"{name} is listed and is no Xeen map")
    families = {family_of(monster["picture"]) for monster in monsters.values()}
    bits = quest_bits()
    file_exclusions = balance.get("completion_exclude") or []
    for value in file_exclusions:
        if not any(excluded([value], monster_id, monster) for monster_id, monster in monsters.items()):
            errors.append(f"completion_exclude {value!r} names no Xeen monster")
    for name, entry in maps.items():
        band = entry.get("band") or []
        if len(band) != 3 or not band[0] <= band[1] <= band[2] or band[0] < 1:
            errors.append(f"{name}: band {band} must be [low, mid, high], 1 <= low <= mid <= high")
        if name != ARENA and not entry.get("madness_level"):
            errors.append(f"{name}: no madness_level")
        if not entry.get("natives") and not world_maps.get(name, {}).get("pictures") and scene_rows(name) \
                and name != ARENA and name not in PEACEFUL:
            print(f"warning: {name} has monsters and no natives: the Progress tab and `ruleset maplevels` skip it")
        for native in entry.get("natives") or []:
            if native not in families:
                errors.append(f"{name}: native {native!r} is no Xeen family")
        for story in entry.get("story_bands") or []:
            if not QBITS[0] <= story["qbit"] <= QBITS[1] or story["qbit"] not in bits:
                errors.append(f"{name}: story band qbit {story['qbit']} is no Xeen quest bit")
        for value in entry.get("completion_exclude") or []:
            if not any(excluded([value], monster_id, monster) for monster_id, monster in monsters.items()):
                errors.append(f"{name}: completion_exclude {value!r} names no Xeen monster")
    errors += reserve_errors()
    promotions = yaml.safe_load(PROMOTIONS.read_text())["kinds"]
    for kind, entry in promotions.items():
        if not entry.get("xeen"):
            errors.append(f"promotions.yml kind {kind} has no xeen bits")
        for bit in (entry.get("xeen") or []) + [bit for bit in entry.get("mid") or [] if bit >= QBITS[0]]:
            if bit not in bits:
                errors.append(f"promotions.yml kind {kind}: {bit} is no Xeen quest bit")
    return errors


WEAPONS = {"Weapon", "Weapon2", "Weapon1or2", "Missile"}


def item_slot(entry):
    """MAW's armour slot of an item (mm9_balance.py's rule): body armour by its skill, hats apart from helms."""
    equip, skill, kind = entry["Equip Stat"], entry["Skill Group"], entry["Not identified name"]
    if equip == "Armor":
        return skill
    if equip == "Helm":
        return "Hat" if kind in ("Hat", "Crown") else "Helm"
    return equip


def reserve_errors():
    """Pack reserves placed against another scene than the installed one (a map rebuilt since): the game skips them
    until tools/maw/xeen_pack_reserve.py runs again for the map (XEEN_SUPPORT.md section 4)."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from pack_reserve import OVERLAYS, reserve_state
    errors = []
    for path in sorted(OVERLAYS.glob("xeen_*_zz_maw.scene.yml")):
        stem = path.name[:-len("_zz_maw.scene.yml")]
        scene = WORLD / "maps" / f"{stem}.scene.yml"
        if not scene.exists():
            errors.append(f"{path.name}: no Xeen map {stem}")
            continue
        actors = yaml.load(scene.read_text(), Loader=yaml.CSafeLoader)["initial_state"]["actors"]
        state = reserve_state(stem, actors)
        if state is not None and not state["fresh"]:
            errors.append(f"{stem}: its pack reserve was made for another scene (the map was rebuilt): run "
                          f"tools/maw/xeen_pack_reserve.py {stem}")
    return errors


def read_items(path):
    with open(path, encoding="utf-8", errors="replace") as file:
        rows = list(csv.reader(file, delimiter="\t"))
    header_index = next(i for i, row in enumerate(rows) if row and row[0] == "Item #")
    header = rows[header_index]
    return {int(row[0]): dict(zip(header, row)) for row in rows[header_index + 1:] if row and row[0].strip().isdigit()}


def item_bases_text(version):
    """The gem gear's bases (it wears artifacts' pictures, U-1), by MM9's rule for its own gear
    (MM9_BALANCE_DESIGN.md section 5): the rung of its Xeen tier (RUNG_BY_TIER), its own dice, two-handed as it is
    equipped, armour MAW's mean AC of its slot at that rung (between rungs on the line through the neighbours) with the
    slot's reference AC, and its strength (GEM_GEAR)."""
    engine = read_items(ROOT / "assets_dev/engine/data_tables/items.txt")
    bases = yaml.safe_load((MAW / "data/items.yml").read_text())["bases"]
    ladder_values, references = {}, {}
    for item_id, base in bases.items():
        entry = engine.get(item_id)
        if entry is None or entry["Equip Stat"] in WEAPONS:
            continue
        ladder_values.setdefault((item_slot(entry), base[0]), []).append(base[3])
        references.setdefault(item_slot(entry), []).append(base[4])

    def ladder_at(slot_name, rung):
        rungs = sorted(r for (s, r) in ladder_values if s == slot_name)
        mean = {r: statistics.mean(ladder_values[(slot_name, r)]) for r in rungs}
        if rung in mean:
            return round(mean[rung])
        lower = max(r for r in rungs if r < rung)
        upper = min(r for r in rungs if r > rung)
        return round(mean[lower] + (mean[upper] - mean[lower]) * (rung - lower) / (upper - lower))

    lines = [f"# Generated by tools/maw/xeen_balance.py from balance.yml (version {version}); do not edit.",
             "# MAW base items of Xeen's ordinary gear: [rung, dice, two-handed, AC, reference AC, strength].",
             "bases:"]
    errors = []
    items = read_items(WORLD / "data_tables/items.txt")
    for item_id, (tier, strength) in sorted(GEM_GEAR.items()):
        item = items.get(item_id)
        if item is None:
            errors.append(f"gem gear {item_id} is no Xeen item")
            continue
        rung = RUNG_BY_TIER[tier]
        if item["Equip Stat"] in WEAPONS:
            rolled = re.match(r"(\d+)[dD]\d+", item["Mod1"] or "")
            base = [rung, int(rolled.group(1)) if rolled else 0, int(item["Equip Stat"] == "Weapon2"), 0, 0, strength]
            what = f"{item['Skill Group']} {'2H' if base[2] else '1H'}"
        else:
            slot_name = item_slot(item)
            if not any(s == slot_name for (s, _) in ladder_values):
                errors.append(f"item {item_id} {item['Name']}: MAW has no {slot_name} armour")
                continue
            reference = round(statistics.mean(references[slot_name]))
            base = [rung, 0, 0, min(reference, ladder_at(slot_name, rung)), reference, strength]
            what = slot_name
        lines.append(f"  {item_id}: [{', '.join(f'{value:g}' for value in base)}]  # {item['Name']}; tier {tier}, "
                     f"{what}")
    return "\n".join(lines) + "\n", errors


def continents_text():
    """Xeen's new-game card under MAW: the world's own (generated by tools/xeen/build_world.py) with MAW's four new
    class lines added."""
    source = WORLD / "data_tables/new_game_continents.yml"
    data = yaml.safe_load(source.read_text())
    for continent in data["new_game_continents"]:
        continent["available_class_ids"] = sorted(set(continent["available_class_ids"]) | set(MAW_NEW_CLASSES))
    header = ("# Generated by tools/maw/xeen_balance.py from worlds/xeen/data_tables/new_game_continents.yml; do not "
              "edit.\n# Xeen's new-game card under MAW: the world's own with MAW's four new class lines (Seraphim, "
              "Death Knight,\n# Shaman, Elementalist); ruleset.yml puts it in place of the world's card.\n")
    return header + yaml.safe_dump(data, sort_keys=False, width=120)


def review_text(balance, world_maps, registry, monsters):
    lines = [f"# MAW in Xeen: map bands (balance.yml version {balance.get('version')})", "",
             "| Map | Name | Act | Party (Standard) | Monsters (Standard) | Band | Madness | Natives (B) | Placed families |",
             "|---|---|---|---|---|---|--:|---|---|"]
    maps = balance["maps"]
    for name in sorted(maps, key=lambda name: (party_level(registry.get(name, {})), name)):
        entry, registry_entry = maps[name], registry.get(name, {})
        natives = entry.get("natives") or [picture for picture in world_maps.get(name, {}).get("pictures", [])]
        native_text = ", ".join(
            f"{native} {next((m['level'] for m in monsters.values() if m['picture'] == native + ' B'), '?')}"
            for native in natives) or "-"
        placed = {}
        for row, count in scene_rows(name).items():
            monster = monsters.get(row)
            if monster:
                placed[family_of(monster["picture"])] = placed.get(family_of(monster["picture"]), 0) + count
        placed_text = ", ".join(f"{family} x{count}" for family, count in sorted(placed.items(), key=lambda x: -x[1])[:5])
        lines.append(f"| {registry_entry.get('key', '')} | {world_maps.get(name, {}).get('name', name)} | "
                     f"{registry_entry.get('act', '')} | {registry_entry.get('party', '-')} | "
                     f"{registry_entry.get('levels', '-')} | {entry['band']} | {entry.get('madness_level', '-')} | "
                     f"{native_text} | {placed_text or '-'} |")
    lines += route_text(balance, world_maps, registry, monsters) + tier_text(balance, world_maps, monsters)
    return "\n".join(lines) + "\n"


def native_slots(name, balance, world_maps, monsters):
    """Each native family of a map with its B level and the level MAW pins it to (the engine's rule: one native at
    the band's low, two at low and high, three at low, mid and high, sorted by B level)."""
    band = balance["maps"][name]["band"]
    natives = [(level, family) for family in map_natives(name, world_maps, balance)
               for level in [next((m["level"] for m in monsters.values() if m["picture"] == family + " B"), None)]
               if level is not None]
    natives.sort()
    slots = {1: [0], 2: [0, 2], 3: [0, 1, 2]}.get(len(natives), [])
    return {family: (level, band[slot]) for (level, family), slot in zip(natives, slots)}


def meeting_level(name, balance, world_maps, monsters):
    """The level a map's natives meet the party at: its single native's, else the mean of its band's low and high."""
    band = balance["maps"][name]["band"]
    slots = native_slots(name, balance, world_maps, monsters)
    return band[0] if len(slots) == 1 else (band[0] + band[2]) / 2


def route_text(balance, world_maps, registry, monsters):
    """The route check (D-84 MX-8): a story map whose natives meet the party lower than the story map before it."""
    story = [name for name in sorted(balance["maps"], key=lambda name: (party_level(registry.get(name, {})), name))
             if str(registry.get(name, {}).get("act", "")).split("-")[0] in ("I", "II", "III", "IV", "V", "VI")
             and name != ARENA and name not in PEACEFUL and native_slots(name, balance, world_maps, monsters)]
    lines = ["", "## Route check", "",
             "Story maps in route order (Standard party level) whose natives meet the party more than two levels "
             "below the story map before them (one native: the band's low; else the mean of low and high).", ""]
    found = 0
    for before, name in zip(story, story[1:]):
        level, previous = meeting_level(name, balance, world_maps, monsters), meeting_level(
            before, balance, world_maps, monsters)
        if level < previous - 2:
            found += 1
            lines.append(f"- {registry[name].get('key', name)} {world_maps[name]['name']}: {level:g} after "
                         f"{registry[before].get('key', before)} {world_maps[before]['name']} at {previous:g}")
    if not found:
        lines.append("- none")
    return lines


def tier_text(balance, world_maps, monsters):
    """D-84 MX-3: the D-G rows placed where their stem family is native, with the free level each rule gives (no
    party level banked): as a family of its own at tier B (the current rule: its table level pulled halfway into the
    band) and as a member of its stem (its distance above the stem's B row added to the stem's pinned level)."""
    lines = ["", "## D-G rows where their stem is native", "",
             "| Map | Row | Name | Table level | Own family (built) | As its stem's member |", "|---|---|---|--:|--:|--:|"]
    for name in sorted(balance["maps"]):
        band = balance["maps"][name]["band"]
        slots = native_slots(name, balance, world_maps, monsters)
        for row in sorted(scene_rows(name)):
            monster = monsters.get(row)
            if not monster or not re.search(r" [D-G]$", monster["picture"]):
                continue
            stem = family_of(monster["picture"])
            if stem not in slots:
                continue
            level = monster["level"]
            own = level + ((band[0] - level) / 2 if level < band[0] else (band[2] - level) / 2 if level > band[2] else 0)
            stem_level, pinned = slots[stem]
            lines.append(f"| {name} | {row} | {monster['name']} | {level} | {own:g} | {level + pinned - stem_level:g} |")
    return lines


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="only check; fail when a derived file is stale")
    parser.add_argument("--draft", type=Path, help="write the suggested bands and madness levels here")
    parser.add_argument("--review", type=Path, help="write the testers' review page (Markdown) here")
    args = parser.parse_args()

    world_maps = read_world_maps()
    registry = read_registry()
    monsters = read_monsters()
    if args.draft:
        balance = yaml.safe_load(BALANCE.read_text()) if BALANCE.exists() else None
        args.draft.write_text(draft_text(suggest(world_maps, registry, monsters, balance), world_maps, registry,
                                         monsters))
        print(f"wrote {args.draft}")
        return

    balance = yaml.safe_load(BALANCE.read_text())
    errors = check(balance, world_maps, monsters)
    bases, base_errors = item_bases_text(balance.get("version"))
    errors += base_errors
    if errors:
        fail(errors)
    derived = {ITEM_BASES: bases, CONTINENTS: continents_text()}
    stale = [path for path, text in derived.items() if not path.exists() or path.read_text() != text]
    if args.check:
        if stale:
            fail([f"{path.relative_to(ROOT)} is stale: run tools/maw/xeen_balance.py" for path in stale])
    else:
        for path in stale:
            path.write_text(derived[path])
            print(f"wrote {path.relative_to(ROOT)}")
    if args.review:
        args.review.write_text(review_text(balance, world_maps, registry, monsters))
        print(f"wrote {args.review}")
    print(f"balance.yml version {balance.get('version')}: {len(balance['maps'])} maps checked")


if __name__ == "__main__":
    main()
