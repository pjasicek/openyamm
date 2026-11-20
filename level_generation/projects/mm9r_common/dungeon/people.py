"""The names MM9 gives its people, for every MM9 map's actors (dungeon/build.py).

A placement with its own RUDE dialogue is the person NPCNAME.rude names (the name its dialogue shows: Ludwig Van,
Brother Kennet, The Dook). Most converters already name it so; some placements kept their DAT object name
(PoorTownGuard10, ForadDarre, TronPlayer) or their body row's name (Lindisfarne's Monk and Initiate rows, the Baron).
Those take the dialogue's name. A real name the converter chose (Sven Forkbeard on the Arena's generic Peasant
dialogue) stays. The engine shows an MM9 dialogue actor's own name over its row's (game/data/ActorNameResolver.cpp).
"""

from __future__ import annotations

import re
from pathlib import Path

from .source import ROOT

NPC_NAMES = ROOT / "mm9/extracted/RUDE/RUDE/NPCNAME.rude"
ROW_TABLES = (ROOT / "assets_dev/worlds/mm9/data_tables/monster_data.txt",
              ROOT / "assets_dev/engine/data_tables/monster_data.txt")


def _tables() -> tuple[dict, dict]:
    if not hasattr(_tables, "cache"):
        from transcode_mm9_dat_to_odm import read_mm9_npc_names, read_numeric_tsv_rows
        rows = {}
        for path in reversed(ROW_TABLES):
            rows.update({row_id: cells[1].strip() for row_id, cells in read_numeric_tsv_rows(Path(path)).items()
                         if len(cells) > 1})
        _tables.cache = read_mm9_npc_names(NPC_NAMES), rows
    return _tables.cache


def dat_like(name: str) -> bool:
    """A DAT object name rather than a person's: one word with a trailing number or an inner capital."""
    return " " not in name and re.search(r"\d$|[a-z][A-Z]", name) is not None


def name_people(actors: list) -> list:
    """Names each actor with a RUDE dialogue by NPCNAME.rude where its name is a DAT object name or its row's name.
    Returns the changes, (actor index, old name, new name)."""
    npc_names, row_names = _tables()
    changes = []
    for actor in actors:
        name = npc_names.get(int(actor.get("mm9_rude_id") or 0), "")
        old = actor.get("name", "")
        if name and name != old and (old == row_names.get(actor["monster_info_id"]) or dat_like(old)):
            actor["name"] = name
            changes.append((actor["actor_index"], old, name))
    return changes
