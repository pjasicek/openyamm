"""Compile the pickups test room and assemble its scene and Lua into runtime/worlds/hesper, the tree the shared Hesper
stage installs (level_generation/projects/hesper_stage/stage.py; assets_dev is never modified).

    blender --background --factory-startup --python level_generation/projects/hesper_pickups_test/author_pickups_test_blender.py
    python3 level_generation/projects/hesper_pickups_test/build_pickups_test.py
    python3 level_generation/projects/hesper_stage/stage.py
"""
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / 'hesper_stage'))
from blv_build import build  # noqa: E402

build(PROJECT, 'hes_pickups_test.blv', {}, arrival='start')
