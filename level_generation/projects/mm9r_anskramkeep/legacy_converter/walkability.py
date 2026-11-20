#!/usr/bin/env python3
"""The shared walkability audit (../hesper_stage/check_walkability.py: steps, flights, unreachable regions, pits,
movers, actors) on the built keep (work/runtime/anskramkeep.blv and its scene), with the MM9 world's monster table for
the flyers; findings in work/walkability.json. Usage: walkability.py"""
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
sys.path.insert(0, str(PROJECT.parent / "hesper_stage"))
import check_walkability as walk  # noqa: E402

walk.MONSTER_TABLES = [ROOT / "assets_dev/worlds/mm9/data_tables/monster_data.txt"] + list(walk.MONSTER_TABLES)
walk.audit([PROJECT / "work/runtime/anskramkeep.blv"], {"__none__"}, PROJECT / "work/walkability.json", workers=1)
