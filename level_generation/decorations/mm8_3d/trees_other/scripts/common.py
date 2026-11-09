"""Species configuration and paths shared by every MM8 trees_other script (system Python and Blender's Python).

Adapted from the MM6 species pipeline (../../../mm6_new_sorpigal_3d/trees/scripts/common.py). Differences:
 - sprites are the restored MM8 x2 images (assets_dev/engine/decorations_x2/<tex>_p*.png, from ../../inventory.json)
   and the tree height defaults to the inventory's binding height / 81.7 units per metre;
 - every species of this batch uses SHARED textures (shared/, scripts/make_shared.py), embedded byte-identical in
   each GLB, so the cooker (keys textures by content) stores them once: one neutral bark set, one needle atlas
   (conifer sprays and pine tufts) and one leaf atlas. A species picks its atlas cells (leaves.cells) and gets its
   colour through COLOR_0: tint = species target / mean of its cells (leaves) or of the bark texture;
 - kinds: 'conifer' (conifer_build.py: whorls of branch-spray cards), 'clump' (the MM6 Sapling + clump pipeline,
   build_tree.py), 'dead' (dead_*.py);
 - install through tools/install_model.py --engine.
A script gets the species id as its first argument after '--' (Blender) or as argv[1] (Python)."""
import copy, json, os, sys

TREES = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(TREES, '..', '..', '..', '..'))
SOURCE = os.path.join(TREES, 'source')
SHARED = os.path.join(TREES, 'shared')
SPRITES = os.path.join(REPO, 'assets_dev', 'engine', 'decorations_x2')
# MM8 x2 sprites were archived after the 3D models were bound (2026-10-16)
if not os.path.exists(os.path.join(SPRITES, 'tree62c_p337.png')):
    SPRITES = os.path.join(REPO, 'assets_legacy', 'decorations_x2_mm8_20261016')
INVENTORY = os.path.join(TREES, '..', 'inventory.json')
UNITS_PER_METRE = 81.7

# Leaf atlases (shared/<atlas>.json lists every cell's uv rectangle, mean linear colour and coverage).
DEFAULTS = {
    'kind': 'clump',
    'atlas': 'leaves',                  # shared atlas of the foliage: 'leaves' or 'needles'
    'sapling': {"levels": 3, "scale": 8.0, "baseSplits": 0, "splitHeight": 0.42, "shape": "2",
                "branches": [0, 60, 12, 8], "length": [1.0, 0.33, 0.35, 0.3], "downAngle": [90, 55, 45, 45],
                "downAngleV": [0, 20, 10, 10], "segSplits": [0.1, 0.25, 0.3, 0], "splitAngle": [25, 15, 15, 0],
                "baseSize": 0.3, "ratio": 0.03, "curveRes": [8, 4, 3, 1], "resU": 2, "bevelRes": 1,
                "attractUp": [0, 0.5, 0.3, 0], "curve": [0, -15, 0, 0], "seed": 5, "rootFlare": 1.4},
    'seed': 8302,                       # crown rng (clump layout, cards, occlusion rays)
    'clump_seed': 8402, 'lod2_seed': 8403,
    'bark': {'min_thickness': [0.03, 0.06, 0.11], 'budget': [1300, 480, 180], 'sides': [0.4, 0.15], 'tile': 1.2,
             'roots': 5, 'root_reach': 0.6, 'target_srgb': [110, 92, 76], 'occlusion_floor': 0.55},
    'crown': {'canopy_low': 0.3, 'centre': 0.62, 'crown_normal_z': 1.15, 'clumps': 70, 'inner_clumps': 12,
              'outer_radius': [0.8, 1.2], 'inner_radius': [0.7, 0.95], 'gap': 0.72, 'card': [1.0, 1.2],
              'coverage': 0.55, 'tip_thickness': 0.09},
    'occlusion': {'floor': 0.22, 'range': 0.78, 'power': 1.4},
    'lod': {'triangles': [6000, 2400, 800], 'grow': [1.0, 1.3, 1.6], 'outward': [0.0, 0.0, 0.8],
            'tone': [1.0, 0.92, 1.05], 'keep': [1.0, 0.7, 0.6]},
    'leaves': {'cells': [0, 1, 2, 3], 'target_srgb': [80, 150, 40]},
    'wind': {'bark': 0.03, 'leaves': 0.12},
    'translucency': 0.35,
    'impostor_tone': [0.94, 0.80, 1.02],
    'fruit': None,
    'base': None,
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


def inventory(name):
    return next(e for e in json.load(open(INVENTORY)) if e['name'] == name)


def load(sid=None):
    sid = sid or species_id()
    spec = _merge(copy.deepcopy(DEFAULTS), json.load(open(os.path.join(TREES, 'species', f'{sid}.json'))))
    spec['id'] = sid
    spec.setdefault('sprite', sid)
    spec.setdefault('output', f'mm8_deco_{sid}.glb')
    entry = inventory(spec['sprite'])
    spec['height_units'] = entry['height']
    spec.setdefault('height_m', round(entry['height'] / UNITS_PER_METRE, 3))
    spec['work'] = os.path.join(TREES, 'work', sid)
    spec['review'] = os.path.join(TREES, 'review', sid)
    spec['sprite_path'] = os.path.join(SPRITES, entry['files'][0])
    os.makedirs(spec['work'], exist_ok=True)
    os.makedirs(spec['review'], exist_ok=True)
    return spec


def shared_path(name):
    return os.path.join(SHARED, name)


def atlas(name):
    return json.load(open(shared_path(f'{name}.json')))


def cell_uv(spec, cell):
    """Lower-left uv corner and size (du, dv) of an atlas cell (Blender v up)."""
    u0, v0, du, dv = atlas(spec['atlas'])['cells'][cell]['uv']
    return u0, v0, du, dv


def lin(c):
    import numpy as np
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def srgb(c):
    import numpy as np
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(np.clip(c, 0, None), 1 / 2.4) - 0.055)


def tints(spec):
    """Linear COLOR_0 tints (leaves, bark): species target / the shared texture's mean over the species' cells."""
    import numpy as np
    meta = atlas(spec['atlas'])
    cells = spec['leaves']['cells']
    weights = np.array([meta['cells'][c]['coverage'] for c in cells])
    mean = np.average([meta['cells'][c]['mean_linear'] for c in cells], axis=0, weights=weights)
    leaf = lin(np.array(spec['leaves']['target_srgb']) / 255.0) / mean
    bark_meta = json.load(open(shared_path(f"{spec.get('bark_set', 'bark')}.json")))
    bark = lin(np.array(spec['bark']['target_srgb']) / 255.0) / np.array(bark_meta['mean_linear'])
    return leaf, bark
