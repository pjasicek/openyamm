#!/usr/bin/env python3
"""Builds the MAW ruleset's table patches from MAW and the MMMerge base it changes.

For each table, rows of MAW's file and of MMMerge's file are matched by key and columns by header name; every cell
MAW changed becomes one line of an override patch against OpenYAMM's engine table (key, column, value), so our own
fixes in cells MAW leaves alone survive. A cell that MAW changed and that OpenYAMM had already changed is a conflict:
it is left out and reported. Rows only MAW has go to an append file, enabled per table once a phase implements what
they need. Whole-file replacements are copied as they are. The result is assets_dev/engine/rulesets/maw/patches/, the
`tables:` list at the end of its ruleset.yml and patches/REPORT.md. See devdocs/maw/HANDOFF.md section 3.4.

Usage: tools/maw/generate_ruleset_patches.py [--maw DIR] [--base DIR]
"""

from __future__ import annotations

import argparse
import csv
import io
import re
import shutil
import struct
import subprocess
import sys
import zlib
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENGINE_TABLES = ROOT / "assets_dev/engine/data_tables"
OUTPUT = ROOT / "assets_dev/engine/rulesets/maw"
MAW_COMMIT = "8967ae88"


@dataclass
class Table:
    """One engine table and the MAW and MMMerge files it is patched from."""

    ours: str  # path below engine/data_tables/
    source: str  # "lod:<name>" inside zMaw.T.lod / mmmerge.T.lod, or "tables:<name>" under Data/Tables
    base_name: str = ""  # MMMerge's name when it differs
    key: object = 0  # our key column index, or "row" for the row number
    header_row: int = 0  # our header row
    source_key: object = None  # the source's key column (default: same as ours)
    source_header_row: object = None  # the source's header row (default: same as ours)
    columns: dict = field(default_factory=dict)  # source header -> our header, for renamed columns
    values: dict = field(default_factory=dict)  # our header -> {source value: our value}
    keys: dict = field(default_factory=dict)  # source key -> our keys, where we split or renamed a row
    fixes: dict = field(default_factory=dict)  # (source header, MAW value) -> value: MAW typos (DEVIATIONS.md)
    spellings: dict = field(default_factory=dict)  # source value -> value: one value spelt two ways, in every column
    ignored_keys: str = ""  # regex of source rows to leave out entirely (unused placeholder rows)
    transposed: bool = False  # source rows are our columns (and the reverse)
    append_rows: bool = False  # write rows only MAW has to an append file that the ruleset loads
    append_columns: bool = False  # write columns only MAW has (new classes) to an appendColumns file
    replace: bool = False  # MAW's file replaces ours
    maw_keys: object = None  # key -> True: MAW's value even where only OpenYAMM changed the cell (Standard rebalances)
    note: str = ""


def is_spellbook(key: str) -> bool:
    """Spellbooks by the engine item table: Standard raised their drop weights, MAW keeps MMMerge's (audit DAT-3)."""
    if not hasattr(is_spellbook, "ids"):
        rows = parse_rows((ENGINE_TABLES / "items.txt").read_bytes())
        is_spellbook.ids = {row[0] for row in rows[2:] if len(row) > 4 and row[4] == "Book"}
    return key in is_spellbook.ids


TABLES = [
    Table("items.txt", "lod:ITEMS.txt", key=0, header_row=1),
    Table("random_items.txt", "lod:rnditems.txt", key=0, header_row=2, maw_keys=is_spellbook,
          note="spellbook weights are MAW's (DAT-3)"),
    Table("monster_data.txt", "lod:MONSTERS.txt", key=0, header_row=1,
          fixes={("Bonus", "Affraid"): "Afraid",
                 ("Treasure", "15%10D40+6"): "15%10D40+L6", ("Treasure", "30%10D40+6"): "30%10D40+L6",
                 ("Treasure", "30%10D40+5"): "30%10D40+L5"},
          note="Fixes MAW's Affraid and item-level typos (DEVIATIONS.md 5 and 6)."),
    Table("map_stats.txt", "lod:mapstats.txt", base_name="MapStats.txt", key=0, header_row=2),
    Table("special_item_enchants.txt", "lod:SPCITEMS.TXT", key="row", header_row=2,
          note="Rows are enchantment ids, so MAW's new ones replace the notes under the table. MAW turns 39 and 40 "
               "(Ogre and Dragon Slaying) into of Ascension and Lichs', which the engine knows by suffix; their "
               "effects are rules code."),
    Table("english/place_mon.txt", "lod:Placemon.txt", key=0, header_row=0,
          note="MAW's new monster names are appended by content/place_mon_names.txt."),
    Table("english/class.txt", "lod:class.txt", key=0, header_row=0, append_rows=True),
    Table("english/potion.txt", "lod:POTION.TXT", replace=True),
    Table("english/potnotes.txt", "lod:POTNOTES.TXT", replace=True),
    Table("class_extra.txt", "tables:Class Extra.txt", key=0, header_row=0, append_rows=True),
    Table("class_multipliers.txt", "tables:Class HP SP.txt", key=0, header_row=0,
          columns={"HPBase": "BaseHP", "HPFactor": "HPPerLevel", "SPBase": "BaseMana", "SPFactor": "ManaPerLevel",
                   "SPStats": "ManaStat"},
          values={"ManaStat": {"I": "Intellect", "P": "Personality", "IP": "Mixed", "-": "None"}},
          append_rows=True),
    # MAW reads its class caps from Class Skillz.txt, which overrides Class Skills.txt (TRAINERS_SKILLS.md §6.1); its
    # rows 50-53 are the four new skills, the other numbered rows unused. Its S (Supreme) reads as Grandmaster: the
    # Knight line's Supreme effects come by class (TRAINERS_SKILLS.md §8).
    Table("class_skills.txt", "tables:Class Skillz.txt", base_name="Class Skills.txt", key=0, header_row=0,
          spellings={"N": "B", "=": "-", "S": "G"}, append_rows=True, append_columns=True,
          ignored_keys=r"Skill(?!5[0-3]$)\d+",
          keys={"Skill50": ["Cover"], "Skill51": ["ManaShield"], "Skill52": ["Enlightenment"],
                "Skill53": ["Retaliation"]}),
    Table("class_starting_skills.txt", "tables:Class Starting Skills.txt", key=0, header_row=0, transposed=True,
          columns={"Leather": "LeatherArmor", "Chain": "ChainArmor", "Plate": "PlateArmor", "Fire": "FireMagic",
                   "Air": "AirMagic", "Water": "WaterMagic", "Earth": "EarthMagic", "Spirit": "SpiritMagic",
                   "Mind": "MindMagic", "Body": "BodyMagic", "Light": "LightMagic", "Dark": "DarkMagic",
                   "Repair": "RepairItem"},
          keys={"High Priest / Master Wizard": ["High Priest", "Master Wizard"]},
          note="The new classes' rows are in content/class_starting_skills_new.txt."),
    Table("class_starting_stats.txt", "tables:Class Starting Stats.txt", key="row", header_row=0),
    Table("complex_item_pictures.txt", "tables:Complex item pictures.txt", key=0, header_row=1),
    Table("potion_settings.txt", "tables:Potion settings.txt", key=1, header_row=0, source_key=1,
          note="MAW's new potions are content/potion_effects.yml."),
    Table("spells.txt", "tables:Spells2.txt", key=2, header_row=0, source_key=0, source_header_row=0,
          columns={"SpellPointsNormal": "Normal Mana", "SpellPointsExpert": "Expert Mana",
                   "SpellPointsMaster": "Master Mana", "SpellPointsGM": "Grandmaster Mana",
                   "DelayNormal": "Normal Recovery", "DelayExpert": "Expert Recovery",
                   "DelayMaster": "Master Recovery", "DelayGM": "Grandmaster Recovery", "DamageAdd": "DamageBase"}),
]

# MAW tables this tool does not generate, and where OpenYAMM has them instead; listed in the report.
NOT_MAPPED = {
    "tables:House rules.txt": "rows repeat their keys by section; the 2 spellbook-shop cells are "
                              "content/house_rules_patch.txt",
    "tables:ObjList.txt": "not ported: MAW's 44 objects are projectile and item sprites; OpenYAMM draws projectiles "
                          "from its own effects",
    "tables:Character portraits.txt": "content/character_data_patch.txt and its append file",
    "tables:SFT.txt": "not ported: the sprite frames of those objects",
    "tables:Class Starting Skillz.txt": "content/class_starting_skills_new.txt and "
                                        "content/class_starting_skills_patch.txt",
    "tables:Extra Skillz.txt": "the four new skills are engine skills; texts in content/skill_des_new.txt",
    "tables:Race Skills.txt": "content/race_skills.yml",
    "tables:Race Skillz.txt": "content/race_skills.yml",
}


def read_lod(path: Path) -> dict[str, bytes]:
    """The files of an MM8 LOD archive: a directory at 0x120 of 76-byte entries, zlib-compressed payloads."""
    data = path.read_bytes()
    base = struct.unpack_from("<I", data, 0x110)[0]
    count = struct.unpack_from("<I", data, 0x11C)[0]
    files = {}
    for index in range(count):
        entry = 0x120 + index * 0x4C
        name = data[entry:entry + 64].split(b"\0")[0].decode("latin-1")
        offset, size = struct.unpack_from("<II", data, entry + 64)
        payload = data[base + offset:base + offset + size][0x60:]
        files[name.lower()] = zlib.decompress(payload) if payload[:1] == b"\x78" else payload
    return files


def parse_rows(text: bytes) -> list[list[str]]:
    reader = csv.reader(io.StringIO(text.decode("latin-1"), newline=""), delimiter="\t")
    return [row for row in reader]


def write_rows(path: Path, rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="latin-1", newline="") as stream:
        writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
        writer.writerows(rows)


def cell(row: list[str], index: int) -> str:
    return row[index].strip() if 0 <= index < len(row) else ""


def header_columns(header: list[str]) -> dict[tuple[str, int], int]:
    """(name, occurrence) -> column, so repeated names such as Monster 'Type' and 'Damage' map by position."""
    seen: dict[str, int] = {}
    columns = {}
    for index, name in enumerate(header):
        name = name.strip()
        if not name:
            continue
        occurrence = seen.get(name, 0)
        seen[name] = occurrence + 1
        columns[(name, occurrence)] = index
    return columns


def keyed_rows(rows: list[list[str]], key, header_row: int) -> dict[str, int]:
    """Key -> row index; keys that repeat are left out (they cannot be patched by key)."""
    if key == "row":
        return {str(index): index for index in range(len(rows)) if index != header_row}
    found: dict[str, int] = {}
    repeated = set()
    for index, row in enumerate(rows):
        value = cell(row, key)
        if index == header_row or not value:
            continue
        if value in found:
            repeated.add(value)
        found[value] = index
    return {value: index for value, index in found.items() if value not in repeated}


def column_label(our_header: list[str], column: int) -> str:
    """The patch's column: the header name when it is unique, else '#<index>'."""
    name = cell(our_header, column)
    unique = name and sum(1 for other in our_header if other.strip() == name) == 1
    return name if unique else f"#{column}"


def transpose(rows: list[list[str]]) -> list[list[str]]:
    width = max((len(row) for row in rows), default=0)
    return [[row[column] if column < len(row) else "" for row in rows] for column in range(width)]


@dataclass
class Result:
    patch: list[list[str]] = field(default_factory=list)
    appended: list[list[str]] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    skipped_rows: list[str] = field(default_factory=list)
    unmapped_columns: set = field(default_factory=set)
    fixes: list = field(default_factory=list)
    columns: list = field(default_factory=list)  # appended columns: header row, then one row per key


def diff_table(table: Table, maw: list[list[str]], base: list[list[str]], ours: list[list[str]]) -> Result:
    result = Result()
    if table.transposed:
        maw, base = transpose(maw), transpose(base)
    source_key = table.key if table.source_key is None else table.source_key
    source_header_row = table.header_row if table.source_header_row is None else table.source_header_row
    our_header = ours[table.header_row]
    our_columns = header_columns(our_header)
    source_columns = header_columns(base[source_header_row])
    maw_columns = header_columns(maw[source_header_row])
    our_rows = keyed_rows(ours, table.key, table.header_row)
    base_rows = keyed_rows(base, source_key, source_header_row)

    for key, maw_index in keyed_rows(maw, source_key, source_header_row).items():
        if table.ignored_keys and re.fullmatch(table.ignored_keys, key):
            continue
        maw_row = maw[maw_index]
        base_row = base[base_rows[key]] if key in base_rows else []
        forced = table.maw_keys is not None and table.maw_keys(key)
        changes = []
        for (name, occurrence), source_column in maw_columns.items():
            maw_value = table.spellings.get(cell(maw_row, source_column), cell(maw_row, source_column))
            base_column = source_columns.get((name, occurrence))
            base_value = cell(base_row, base_column) if base_column is not None else ""
            base_value = table.spellings.get(base_value, base_value)
            if maw_value != base_value or (forced and source_column != source_key):
                fixed = table.fixes.get((name, maw_value))
                if fixed is not None:
                    result.fixes.append(f"{key} / {name}: MAW '{maw_value}', patched '{fixed}'")
                changes.append((name, occurrence, base_value, fixed if fixed is not None else maw_value))
        if not changes:
            continue
        if key not in base_rows and table.key != "row":
            if table.append_rows:
                for our_key in table.keys.get(key, [key]):
                    row = map_row(table, maw_row, maw_columns, our_columns, len(our_header))
                    row[table.key] = our_key
                    result.appended.append(row)
                    if table.append_columns:
                        result.columns.append([our_key] + new_column_values(table, maw_row, maw_columns, our_columns))
            else:
                result.skipped_rows.append(key)
            continue
        for our_key in table.keys.get(key, [key]):
            if table.append_columns:
                result.columns.append([our_key] + new_column_values(table, maw_row, maw_columns, our_columns))
            if table.key == "row" and our_key not in our_rows:
                our_row = []  # Row-numbered tables grow by patching rows past the end.
            elif our_key in our_rows:
                our_row = ours[our_rows[our_key]]
            else:
                result.skipped_rows.append(f"{our_key} (no such row in {table.ours})")
                continue
            for name, occurrence, base_value, maw_value in changes:
                our_name = table.columns.get(name, name)
                our_column = our_columns.get((our_name, occurrence))
                if our_column is None:
                    result.unmapped_columns.add(name)
                    continue
                if our_column == table.key:
                    result.conflicts.append(f"{our_key}: the key changes from '{base_value}' to '{maw_value}'")
                    continue
                mapping = table.values.get(our_name, {})
                our_value = mapping.get(maw_value, maw_value)
                if our_row and not forced and cell(our_row, our_column) != mapping.get(base_value, base_value):
                    result.conflicts.append(
                        f"{our_key} / {our_name}: ours '{cell(our_row, our_column)}', MMMerge '{base_value}', "
                        f"MAW '{maw_value}'")
                    continue
                if our_row and cell(our_row, our_column) == our_value:
                    continue
                result.patch.append([our_key, column_label(our_header, our_column), our_value])
    if table.append_columns:
        names = [name for (name, occurrence), _ in maw_columns.items()
                 if (table.columns.get(name, name), occurrence) not in our_columns]
        result.columns.insert(0, [cell(our_header, table.key)] + names)
        result.unmapped_columns -= set(names)
    return result


def new_column_values(table: Table, maw_row, maw_columns, our_columns) -> list[str]:
    """The cells of a MAW row in the columns OpenYAMM's table does not have."""
    return [table.spellings.get(cell(maw_row, column), cell(maw_row, column))
            for (name, occurrence), column in maw_columns.items()
            if (table.columns.get(name, name), occurrence) not in our_columns]


def map_row(table: Table, maw_row, maw_columns, our_columns, width: int) -> list[str]:
    row = [""] * width
    for (name, occurrence), source_column in maw_columns.items():
        our_name = table.columns.get(name, name)
        our_column = our_columns.get((our_name, occurrence))
        if our_column is not None:
            value = table.spellings.get(cell(maw_row, source_column), cell(maw_row, source_column))
            row[our_column] = table.values.get(our_name, {}).get(value, value)
    return row


def table_rows(source: str, maw_lod: dict, base_lod: dict, maw_root: Path, base_root: Path, base_name: str):
    kind, name = source.split(":", 1)
    if kind == "lod":
        return parse_rows(maw_lod[name.lower()]), parse_rows(base_lod_file(base_root, base_name or name))
    return (parse_rows((maw_root / "Data/Tables" / name).read_bytes()),
            parse_rows((base_root / "Data/Tables" / (base_name or name)).read_bytes()))


def base_lod_file(base_root: Path, name: str) -> bytes:
    # The MMMerge base LOD is kept extracted in reference/mmerge_data_forus.
    for candidate in (base_root / "Data/mmmerge.T.lod").iterdir():
        if candidate.name.lower() == name.lower():
            return candidate.read_bytes()
    raise FileNotFoundError(name)


# Contributions written by hand in content/ follow the generated ones in ruleset.yml, below this comment, and are kept.
HAND_WRITTEN_MARKER = "\n  # Written by hand in content/"


def update_ruleset_tables(entries: list[str]) -> None:
    path = OUTPUT / "ruleset.yml"
    text = path.read_text()
    start = text.index("\ntables:")
    hand_written = text[text.index(HAND_WRITTEN_MARKER):] if HAND_WRITTEN_MARKER in text else "\n"
    block = "\ntables:" + ("\n" + "\n".join(entries) if entries else " []")
    path.write_text(text[:start] + block + hand_written)


# Spells whose numbers MAW sets in Lua rather than in Spells2.txt.
SPELL_POWERS_LUA = "Scripts/General/zzMaw-Spells.lua"
# Mass Distortion takes a share of the target's HP: its spellPowers dice are unused, its cost is not (COMBAT_SPEC.md
# §6.7).
SPELL_POWERS_SKIPPED = {44}
# MAW scales these spells by mastery in events.CalcSpellDamage: Fire Spike x8/6 and x10/6 at Master and Grandmaster.
SPELL_MASTERY_PERCENTS = {7: ["100", "100", "133", "167"]}


def spell_power_patch(maw_root: Path, ours: list[list[str]]) -> list[list[str]]:
    """spells.txt cells for the dice MAW rolls and the mana it charges: spellPowers {dmgAdd, diceMin, diceMax, cost}
    per spell id (since 8967ae88 the cost there sets the spell's mana by mastery, over Spells2.txt)."""
    text = (maw_root / SPELL_POWERS_LUA).read_text(encoding="latin-1")
    block = text[text.index("spellPowers ="):]
    block = block[:block.index("\n\t\t}")]
    pattern = re.compile(r"\[(\d+)\]\s*=\s*\{dmgAdd\s*=\s*([\d.]+),\s*diceMin\s*=\s*([\d.]+),\s*diceMax\s*=\s*([\d.]+),"
                         r"\s*(?:cost\s*=\s*\{([\d,\s]+)\})?")
    names = {row[0]: row[2] for row in ours[1:] if len(row) > 2 and row[0].isdigit()}
    patch = []
    for spell_id, add, dice_min, dice_max, cost in pattern.findall(block):
        if spell_id not in names:
            continue
        name = names[spell_id]
        costs = [value.strip() for value in cost.split(",")] if cost else []
        for mastery, value in zip(("Normal", "Expert", "Master", "Grandmaster"), costs):
            patch.append([name, f"{mastery} Mana", value])
        if int(spell_id) in SPELL_POWERS_SKIPPED:
            continue
        patch += [[name, "DamageBase", add], [name, "DamageDiceMin", dice_min], [name, "DamageDiceSides", dice_max]]
        for mastery, percent in zip(("Normal", "Expert", "Master", "Grandmaster"),
                                    SPELL_MASTERY_PERCENTS.get(int(spell_id), [])):
            patch.append([name, f"{mastery} Damage %", percent])
    return patch


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--maw", type=Path, default=Path.home() / "github/Maw-Mod-MMMerge")
    parser.add_argument("--base", type=Path, default=ROOT / "reference/mmerge_data_forus")
    args = parser.parse_args()

    commit = subprocess.run(["git", "-C", str(args.maw), "rev-parse", "--short=8", "HEAD"],
                            capture_output=True, text=True).stdout.strip()
    if commit != MAW_COMMIT:
        print(f"MAW checkout is at {commit or 'unknown'}, expected {MAW_COMMIT}", file=sys.stderr)
        return 1

    maw_lod = read_lod(args.maw / "Data/zMaw.T.lod")
    patches = OUTPUT / "patches"
    tables = OUTPUT / "tables"
    for folder in (patches, tables):
        if folder.exists():
            shutil.rmtree(folder)

    entries = []
    report = ["# MAW table patches", "",
              f"Generated by `tools/maw/generate_ruleset_patches.py` from MAW `{MAW_COMMIT}` against the MMMerge "
              "base in `reference/mmerge_data_forus`. Do not edit by hand; rerun the tool.", "",
              "| Table | Patched cells | Appended rows | Rows left out | Conflicts kept as ours | Note |",
              "|---|---|---|---|---|---|"]
    details = []
    for table in TABLES:
        maw, base = table_rows(table.source, maw_lod, {}, args.maw, args.base, table.base_name)
        if table.replace:
            write_rows(tables / table.ours, maw)
            entries.append(f"  - table: {table.ours}\n    mode: replace\n    path: tables/{table.ours}")
            report.append(f"| `{table.ours}` | replaced | | | | MAW's whole file |")
            continue
        ours = parse_rows((ENGINE_TABLES / table.ours).read_bytes())
        result = diff_table(table, maw, base, ours)
        if table.ours == "spells.txt":
            powers = spell_power_patch(args.maw, ours)
            replaced = {(key, column) for key, column, _ in powers}
            result.patch = [cell for cell in result.patch if (cell[0], cell[1]) not in replaced] + powers
        line = f"  - table: {table.ours}\n    mode: override\n    path: patches/{table.ours}"
        if result.patch or result.appended or len(result.columns) > 1:
            write_rows(patches / table.ours, [["key", "column", "value"]] + result.patch)
        if result.appended:
            append_path = Path(table.ours).with_suffix(".append" + Path(table.ours).suffix)
            write_rows(patches / append_path, result.appended)
            line += f"\n    append: patches/{append_path}"
        if len(result.columns) > 1 and len(result.columns[0]) > 1:
            columns_path = Path(table.ours).with_suffix(".columns" + Path(table.ours).suffix)
            write_rows(patches / columns_path, result.columns)
            line += f"\n    appendColumns: patches/{columns_path}"
        if result.patch or result.appended or len(result.columns) > 1:
            key = '"row"' if table.key == "row" else table.key
            entries.append(line + f"\n    keyColumn: {key}\n    headerRow: {table.header_row}")
        report.append(f"| `{table.ours}` | {len(result.patch)} | {len(result.appended)} | "
                      f"{len(result.skipped_rows)} | {len(result.conflicts)} | {table.note} |")
        if result.conflicts or result.skipped_rows or result.unmapped_columns or result.fixes:
            details += ["", f"## {table.ours}", ""]
            if result.unmapped_columns:
                details.append("Columns without a counterpart: " + ", ".join(sorted(result.unmapped_columns)) + ".")
            if result.skipped_rows:
                details.append("Rows left out (new in MAW): " + ", ".join(result.skipped_rows) + ".")
            if result.fixes:
                details += ["", "MAW typos fixed:", ""] + [f"- {fix}" for fix in result.fixes]
            if result.conflicts:
                details += ["", "Cells OpenYAMM already changed, kept as ours:", ""]
                details += [f"- {conflict}" for conflict in result.conflicts]

    report += ["", "Not generated here:", ""]
    report += [f"- `{source.split(':', 1)[1]}`: {why}" for source, why in NOT_MAPPED.items()]
    (OUTPUT / "patches").mkdir(parents=True, exist_ok=True)
    (OUTPUT / "patches/REPORT.md").write_text("\n".join(report + details) + "\n")
    update_ruleset_tables(entries)
    print("\n".join(report[6:6 + len(TABLES)]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
