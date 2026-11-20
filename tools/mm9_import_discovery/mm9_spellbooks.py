#!/usr/bin/env python3
"""MM9's own spellbooks (user decision 2026-11-08): one book per spell of the merged spell table, drawn as one of four
books by the mastery the spell needs (Normal, Expert, Master, Grandmaster), whatever its school.

MM9 does not import its own spells (MM9_SPELL_MAPPING.md), so its books teach the MM6-MM8 spells. Each MM6-MM8 world
has its own copy of every book (World:mm6, World:mm7, World:mm8); MM9's are World:mm9, so they drop and sell only in
MM9 and the other worlds' books never there. A book copies the same spell's MM8 book (name, price, spell, ground
object), takes its random-treasure weights, and the shop tier of the spell's MM6 book (the tiers MM9's spellbook shops
admitted before, generate_mm9_vendors.py). Ids are 10900 + spell id (10901-10999, the top of MM9's item range).

The art (level_generation/ui/mm9_spellbooks_20261108/, git-ignored) is listed with its hashes in mm9_spellbook_art.yml;
import_mm9_items.py installs the icons as icons_x2/mm9_spellbook_<mastery>.png.
"""
from __future__ import annotations

import hashlib
import re
import shutil
from pathlib import Path

import yaml
from PIL import Image

SPELLBOOK_ID_BASE = 10900
SPELL_COUNT = 99
MASTERIES = {"B": "normal", "E": "expert", "M": "master", "G": "grandmaster"}
MM8_BOOK_IDS = range(400, 800)
MM6_BOOK_IDS = range(1600, 2200)
ART_MANIFEST = Path(__file__).resolve().with_name("mm9_spellbook_art.yml")
# A book's source id is its item id - 10000, except where it stands for an MM9 spellbook that scripts name by its MM9
# id: Eye of the Storm (raw 347) is the Implosion book (import_mm9_items.ENGINE_ITEM_MAPPINGS), and a package's alias
# must match its item's source id.
SOURCE_ITEM_IDS = {20: 347}
# MM9's own spell in a shared slot (world.yml fleetFoot, game/party/WorldSpells.h): Fly's book teaches Fleet Foot in
# MM9 and is named so. Its canonical id keeps the slot's spell name.
WORLD_SPELL_NAMES = {21: "Fleet Foot"}
ICON_SCALE = 2


def spellbook_icon(mastery: str) -> str:
    return f"mm9_spellbook_{mastery}"


def spell_masteries(spell_rows: list[list[str]]) -> dict[int, str]:
    """Spell id 1-99 -> mastery name, from spells.txt's required mastery column (24; empty is Normal)."""
    out = {}
    for row in spell_rows:
        if row and row[0].strip().isdigit() and 1 <= int(row[0]) <= SPELL_COUNT:
            token = row[24].strip().upper() if len(row) > 24 else ""
            out[int(row[0])] = MASTERIES.get(token[:1], "normal")
    missing = sorted(set(range(1, SPELL_COUNT + 1)) - set(out))
    if missing:
        raise ValueError(f"spells.txt lacks spells {missing}")
    return out


def books_by_spell(item_rows: list[list[str]], ids: range) -> dict[int, list[str]]:
    """The first engine book row of each spell (Mod1 "S<id>") among the item ids."""
    out: dict[int, list[str]] = {}
    for row in item_rows:
        if len(row) > 6 and row[0].strip().isdigit() and int(row[0]) in ids and row[4] == "Book":
            match = re.fullmatch(r"S(\d+)", row[6].strip())
            if match:
                out.setdefault(int(match.group(1)), row)
    return out


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.casefold()).strip("_")


def install_icons(output_root: Path, repository_root: Path) -> dict[str, tuple[int, int]]:
    """Copies the four reviewed icons into the world's icons_x2 and returns their logical (x1) sizes."""
    manifest = yaml.safe_load(ART_MANIFEST.read_text(encoding="utf-8"))
    sizes = {}
    for mastery in MASTERIES.values():
        entry = manifest["icons"][mastery]
        source = repository_root / entry["source"]
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        if digest != entry["sha256"]:
            raise ValueError(f"spellbook icon {source} does not match mm9_spellbook_art.yml ({digest})")
        target = output_root / "icons_x2" / f"{spellbook_icon(mastery)}.png"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        with Image.open(source) as image:
            sizes[mastery] = tuple(-(-size // ICON_SCALE) for size in image.size)
    return sizes


def inventory_cells(pixels: int) -> int:
    return max(1, 1 + (max(14, pixels) - 14) // 32)


def unquoted(cell: str) -> str:
    """A cell of a plain-read TSV without its CSV quoting."""
    if len(cell) >= 2 and cell.startswith('"') and cell.endswith('"'):
        return cell[1:-1].replace('""', '"')
    return cell


def spellbook_rows(
    headers: list[str],
    engine_item_rows: list[list[str]],
    engine_random_rows: list[list[str]],
    spell_rows: list[list[str]],
    icon_sizes: dict[str, tuple[int, int]],
) -> tuple[list[list[str]], list[list[str]]]:
    """(items.txt rows, random_items.txt rows) of MM9's spellbooks."""
    columns = {name: index for index, name in enumerate(headers)}
    masteries = spell_masteries(spell_rows)
    mm8_books = books_by_spell(engine_item_rows, MM8_BOOK_IDS)
    mm6_books = books_by_spell(engine_item_rows, MM6_BOOK_IDS)
    weights = {int(row[0]): row[2:8] for row in engine_random_rows if len(row) >= 8 and row[0].strip().isdigit()}
    item_rows, random_rows = [], []
    for spell in range(1, SPELL_COUNT + 1):
        template, shop_template = mm8_books.get(spell), mm6_books.get(spell)
        if template is None or shop_template is None:
            raise ValueError(f"spell {spell} has no MM8 or MM6 book to copy")
        item_id = SPELLBOOK_ID_BASE + spell
        mastery = masteries[spell]
        icon = spellbook_icon(mastery)
        width, height = icon_sizes[mastery]
        canonical = f"mm9:item/spellbook_{slug(template[2])}"
        row = [""] * len(headers)
        # The engine table is read as plain TSV, so a quoted cell keeps its quotes; unquote it, or the writer
        # quotes it again and the description shows in quotes.
        row[:17] = [unquoted(cell) for cell in (template + [""] * 17)[:17]]
        name = WORLD_SPELL_NAMES.get(spell, template[2])
        row[2] = name
        row[columns["Item #"]] = str(item_id)
        row[columns["Pic File"]] = icon
        row[columns["package_id"]] = "mm9"
        row[columns["canonical_id"]] = canonical
        source_id = str(SOURCE_ITEM_IDS.get(spell, item_id - 10000))
        row[columns["source_item_id"]] = source_id
        row[columns["content_flags"]] = "World:mm9"
        row[columns["normalized_tier"]] = str(max(1, min(5, int(shop_template[9] or 1))))
        row[columns["inventory_width"]] = str(inventory_cells(width))
        row[columns["inventory_height"]] = str(inventory_cells(height))
        row[columns["visual_status"]] = "generated_spellbook"
        row[columns["x_mm9_raw_item_id"]] = source_id
        row[columns["x_mm9_canonical_id"]] = canonical
        row[columns["x_mm9_import_status"]] = f"generated_spellbook:{mastery}"
        item_rows.append(row)
        book_weights = weights.get(int(template[0]), ["0"] * 6)
        if any(int(weight or 0) for weight in book_weights):
            random_rows.append([str(item_id), icon, *book_weights, name])
    return item_rows, random_rows


def spellbook_item_id(spell: int) -> int:
    return SPELLBOOK_ID_BASE + spell
