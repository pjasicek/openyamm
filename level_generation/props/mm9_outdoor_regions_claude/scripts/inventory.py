#!/usr/bin/env python3
"""
The props of MM9's outdoor regions as BLVs (devdocs/mm9_rework/DECORATIONS_AND_GRASS.md, step 3): every Prop and
CandleProp of the eleven region DATs, matched by (model, skin) against the prop tables of the 32 MM9 props projects
(their scripts/props_table.py MODELS), which name the installed decoration `mm9_deco_<prop>`.

    python3 level_generation/props/mm9_outdoor_regions_claude/scripts/inventory.py   # -> work/inventory.json, summary
"""
import ast
import collections
import glob
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / 'level_generation/projects/mm9r_common'))
from dungeon.source import read_dat_world  # noqa: E402

REGIONS = ['ISLEOFASHES', 'STURMFORD', 'THJORGARD', 'THRONHEIM', 'DRANGHEIM', 'GUBERLAND', 'FROSGARD', 'LINDISFARNE',
           'YORWICK', 'MOUNTAINPASS', 'BOOTCAMP', 'AFTERWORLD']


# The DAT classes placed as decorations: the props and candles, and (2026-11-05, the props audit) the braziers and
# torches, the chests (kind chest: their loot records and click events are the map's), stat barrels (Barrel:
# dungeon/content.py puts them on the stat barrel rows), bone piles, cauldrons, cook pots, clover, wells and the stat
# stones (no model yet: listed as left out).
CLASSES = {'Prop', 'CandleProp', 'Brazier', 'Torch', 'TreasureChest', 'Barrel', 'BonePile', 'Cauldron', 'Cookpot',
           'Clover', 'WellMMIX', 'StatStone'}


def norm(path) -> str:
    """A DAT path as the props tables key it: forward slashes, lower case, no leading slash; several skins joined by
    ';' without spaces (Afterworld's '/models/props/arrow.abc', the penance stone's 'a; a')."""
    return ';'.join(s.replace('\\', '/').lower().strip().lstrip('/') for s in str(path or '').split(';') if s.strip())


def prop_tables() -> dict:
    """(model, skin) -> (prop, project) from every props project's MODELS literal (the ones it can read)."""
    table = {}
    for f in sorted(glob.glob(str(REPO / 'level_generation/props/mm9_*_claude/scripts/props_table.py'))):
        for node in ast.parse(Path(f).read_text()).body:
            if isinstance(node, ast.Assign) and any(getattr(t, 'id', None) == 'MODELS' for t in node.targets):
                try:
                    models = ast.literal_eval(node.value)
                except ValueError:
                    continue
                for key, prop in models.items():
                    table.setdefault(key, (prop, Path(f).parents[1].name))
    return table


def main() -> int:
    table = prop_tables()
    installed = {Path(f).stem.removeprefix('mm9_deco_') for f in glob.glob(str(REPO / 'assets_source/worlds/mm9/models/mm9_deco_*.glb'))}
    out, have, miss = [], collections.Counter(), collections.Counter()
    for region in REGIONS:
        world = read_dat_world(REPO / f'mm9/extracted/WORLDS/WORLDS/{region}.dat')
        for index, o in enumerate(world.objects):
            p = {q.name: q.value for q in o.properties}
            if o.name not in CLASSES or not p.get('Filename'):
                continue
            key = (norm(p['Filename']), norm(p.get('Skin', '')))
            prop, project = table.get(key, (None, None))
            status = 'installed' if prop in installed else ('known' if prop else 'new')
            (have if status == 'installed' else miss)[key] += 1
            out.append({'region': region.lower(), 'object': index, 'name': str(p.get('Name', '')), 'class': o.name,
                        'model': key[0], 'skin': key[1], 'prop': prop, 'project': project, 'status': status,
                        'scale': p.get('Scale', 1.0), 'script': str(p.get('ScriptName', ''))})
    (HERE / 'work/inventory.json').write_text(json.dumps(out, indent=1) + '\n')
    print(f"placements {len(out)}: with an installed model {sum(have.values())} ({len(have)} model/skin pairs), "
          f"without {sum(miss.values())} ({len(miss)} pairs)")
    for (model, skin), n in miss.most_common(70):
        print(f'  {n:4} {Path(model).stem}  [{Path(skin.split(";")[0]).stem}]')
    return 0


if __name__ == '__main__':
    sys.exit(main())
