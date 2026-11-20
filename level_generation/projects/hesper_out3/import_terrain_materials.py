"""Pack the Brood Spires' two new library materials (creep_wet, brood_membrane) from their CC0 downloads.

    python3 level_generation/projects/hesper_out3/import_terrain_materials.py

tools/terrain_materials.py prepare packs assets_source/engine/terrain_materials/<id> (sources.yml) into
albedo_height.png and normal_ao_rough.png, and records the material in the runtime library, which is assets_dev's:
Hesper is staged, never installed, so the library is redirected here (work/terrain_library_prepared.yml) and the
entries are printed in the form of the stage's terrain_library.yml (its mean colours set the map's tints).
"""
import sys
from pathlib import Path

import yaml

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
import terrain_materials  # noqa: E402

IDS = ['creep_wet', 'brood_membrane']
library = PROJECT / 'work/terrain_library_prepared.yml'
library.parent.mkdir(exist_ok=True)
terrain_materials.LIBRARY = library
terrain_materials.prepare(IDS)
entries = yaml.safe_load(library.read_text())['materials']
print(yaml.safe_dump({k: entries[k] for k in IDS}, sort_keys=False))
