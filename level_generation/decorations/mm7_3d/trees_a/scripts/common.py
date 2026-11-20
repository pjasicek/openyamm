"""Species configuration and paths shared by every tree pipeline script (system Python and Blender's Python).
MM7 trees_a copy of the MM6 New Sorpigal pipeline (../../mm6_new_sorpigal_3d/trees/scripts/): the sprite is the
restored x2 frame in assets_dev/engine/decorations_x2/ (inventory.json 'x2'), the CC0 sources are read from the MM6
folder, and post_process.py installs through tools/install_model.py --engine.

A script gets the species id as its first argument after '--' (Blender) or as argv[1] (Python). species/<id>.json
holds every per-tree setting; DEFAULTS are the approved 6tree01 v2 values, so a species file lists only what differs.
Paths: work/<id>/ (generated maps, blends, exports), review/<id>/ (sheets), source/ (CC0 downloads)."""
import copy, json, os, sys

TREES = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(TREES, '..', '..', '..', '..'))
SOURCE = os.path.join(REPO, 'level_generation', 'decorations', 'mm6_new_sorpigal_3d', 'trees', 'source')
SPRITES = os.path.join(REPO, 'assets_legacy', 'decorations_x2_20261016')   # archived from assets_dev/engine/decorations_x2
INVENTORY = os.path.join(TREES, '..', 'inventory.json')

DEFAULTS = {
    'height_m': 6.5,
    'sapling': {"levels": 3, "scale": 4.6, "baseSplits": 2, "splitHeight": 0.42, "shape": "2",
                "branches": [0, 80, 15, 8], "length": [1.0, 0.3, 0.35, 0.3], "downAngle": [90, 50, 45, 45],
                "downAngleV": [0, 25, 10, 10], "segSplits": [0.15, 0.25, 0.3, 0], "splitAngle": [25, 15, 15, 0],
                "baseSize": 0.3, "ratio": 0.035, "curveRes": [6, 4, 3, 1], "resU": 2, "bevelRes": 1,
                "attractUp": [0, 0.6, 0.3, 0], "curve": [0, -20, 0, 0], "seed": 5, "rootFlare": 1.5},
    'seed': 6102,                       # crown rng (clump layout, cards, occlusion rays)
    'clump_seed': 2202, 'lod2_seed': 2203,
    'bark': {'min_thickness': [0.017, 0.035, 0.07], 'budget': [1700, 560, 190], 'tile': 0.8, 'roots': 5,
             'root_reach': 0.42, 'target_srgb': [104, 66, 46], 'occlusion_floor': 0.55},
    'crown': {'canopy_low': 0.36, 'centre': 0.62, 'crown_normal_z': 1.15, 'clumps': 100, 'inner_clumps': 18,
              'outer_radius': [0.42, 0.68], 'inner_radius': [0.4, 0.55], 'gap': 0.72, 'card': [0.36, 0.46],
              'coverage': 0.55, 'tip_thickness': 0.06},
    'occlusion': {'floor': 0.22, 'range': 0.78, 'power': 1.4},
    'lod': {'triangles': [8000, 3000, 1000], 'grow': [1.0, 1.3, 1.6], 'outward': [0.0, 0.0, 0.8],
            'tone': [1.0, 0.92, 1.05], 'keep': [1.0, 0.7, 0.6]},
    'leaves': {'kind': 'leaves', 'target_srgb': [56, 138, 38], 'seeds': [11, 23, 37, 52], 'jitter_red': [0.88, 1.12],
               'jitter_blue': [0.85, 1.1], 'value': [0.78, 1.15]},
    'impostor_tone': [0.94, 0.80, 1.02],
    'fruit': None,                      # {'count', 'radius_m', 'srgb': [..]} on a food tree
    'base': None,                       # a species whose built tree this one reuses (adds only its fruit)
}


def _merge(base, extra):
    for key, value in extra.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _merge(base[key], value)
        else:
            base[key] = value
    return base


def species_id():
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    if not args:
        raise SystemExit('usage: <script> <species id>')
    return args[0]


def extra_args():
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    return args[1:]


def load(sid=None):
    sid = sid or species_id()
    spec = _merge(copy.deepcopy(DEFAULTS), json.load(open(os.path.join(TREES, 'species', f'{sid}.json'))))
    spec['id'] = sid
    spec['work'] = os.path.join(TREES, 'work', sid)
    spec['review'] = os.path.join(TREES, 'review', sid)
    entry = next(e for e in json.load(open(INVENTORY)) if e['name'] == spec['sprite'])
    spec['sprite_path'] = os.path.join(SPRITES, entry['x2'])
    spec['inventory'] = entry
    os.makedirs(spec['work'], exist_ok=True)
    os.makedirs(spec['review'], exist_ok=True)
    return spec


def lin(c):
    import numpy as np
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def srgb(c):
    import numpy as np
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(np.clip(c, 0, None), 1 / 2.4) - 0.055)
