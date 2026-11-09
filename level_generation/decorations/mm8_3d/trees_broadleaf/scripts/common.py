"""Species configuration and paths shared by every MM8 broadleaf tree script (system Python and Blender's Python).

Adapted from the MM6 species pipeline (../../mm6_new_sorpigal_3d/trees/scripts/common.py). Differences:
 - sprites are the restored MM8 x2 images (assets_dev/engine/decorations_x2/<tex>_p*.png, from ../inventory.json),
   and the tree height defaults to the inventory's binding height / 81.7 units per metre;
 - leaves and bark use SHARED textures (shared/: one 2048 leaf atlas of GRID x GRID cells and one neutral bark set),
   byte-identical in every GLB, so the cooker stores them once. A species picks its atlas cells (leaves.cells) and
   gets its colour through COLOR_0: tint = species target / mean of its cells (leaves) or of the bark texture;
 - install through tools/install_model.py --engine.
A script gets the species id as its first argument after '--' (Blender) or as argv[1] (Python)."""
import copy, json, os, sys

TREES = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(TREES, '..', '..', '..', '..'))
SOURCE = os.path.join(TREES, 'source')
SHARED = os.path.join(TREES, 'shared')
# the restored x2 sprites were retired from assets_dev/engine/decorations_x2 on 2026-10-16 (MM6_2D_RETIREMENT.md)
SPRITES = os.path.join(REPO, 'assets_legacy', 'decorations_x2_mm8_20261016')
INVENTORY = os.path.join(TREES, '..', 'inventory.json')
UNITS_PER_METRE = 81.7
GRID = 4                                # shared leaf atlas: GRID x GRID cells of 512 px (2048 px)

DEFAULTS = {
    'sapling': {"levels": 3, "scale": 8.0, "baseSplits": 0, "splitHeight": 0.42, "shape": "2",
                "branches": [0, 60, 12, 8], "length": [1.0, 0.33, 0.35, 0.3], "downAngle": [90, 55, 45, 45],
                "downAngleV": [0, 20, 10, 10], "segSplits": [0.1, 0.25, 0.3, 0], "splitAngle": [25, 15, 15, 0],
                "baseSize": 0.3, "ratio": 0.03, "curveRes": [8, 4, 3, 1], "resU": 2, "bevelRes": 1,
                "attractUp": [0, 0.5, 0.3, 0], "curve": [0, -15, 0, 0], "seed": 5, "rootFlare": 1.4},
    'seed': 8102,                       # crown rng (clump layout, cards, occlusion rays)
    'clump_seed': 8202, 'lod2_seed': 8203,
    'bark': {'min_thickness': [0.03, 0.06, 0.11], 'budget': [800, 330, 200], 'sides': [0.5, 0.25], 'tile': 0.8,
             'res_big': 1, 'root_mesh': [[4, 3], [4, 2], [4, 2]],
             'roots': 6, 'root_lods': [0, 1],
             'root_reach': 0.3, 'target_srgb': [120, 104, 88], 'occlusion_floor': 0.55},
    'crown': {'canopy_low': 0.3, 'centre': 0.62, 'crown_normal_z': 1.15, 'clumps': 110, 'inner_clumps': 8,
              'outer_radius': [0.6, 0.95], 'inner_radius': [0.55, 0.75], 'gap': 0.8, 'card': [1.15, 1.35],
              'coverage': 0.45, 'tip_thickness': 0.09, 'flatten': 0.75, 'card_up': 0.25, 'shell_radial': 0.75,
              'low_keep': 0.6,
              # inner crown shell (2026-10-16 overdraw pass): star-shaped wrap of the clumps shrunk to `scale`,
              # sphere grid [segments, rings] per LOD
              # mode 'cores' (default since the close-up review): an octahedron at `core` x the clump inside each of
              # the `cores` largest clumps per LOD; mode 'wrap' (the first version) wraps the whole crown
              'shell': {'mode': 'cores', 'core': 0.45, 'cores': [40, 20, 8], 'scale': 0.62,
                        'grid': [[12, 11], [10, 7], [8, 5]], 'value': 0.55, 'ao_floor': 0.5}},
    'occlusion': {'floor': 0.14, 'range': 0.86, 'power': 1.0, 'hue': [1.4, 1.0, 0.9]},
    'lod': {'triangles': [3000, 1300, 500], 'grow': [1.0, 1.35, 1.6], 'outward': [0.0, 0.0, 0.8],
            'tone': [1.0, 0.92, 1.45], 'keep': [1.0, 0.7, 0.6], 'lod2_card_scale': 1.0, 'clump_frame': 4.5},
    'leaves': {'cells': list(range(8)), 'target_srgb': [176, 196, 48],
               # colour lift (2026-10-16): leaf tint +10 % saturation, +5 % value; sunlit outer cards (top 35 % by sky
               # occlusion) ramp toward the sprites' yellow-green highlights
               'lift': {'sat': 1.1, 'val': 1.05, 'highlight': [1.08, 1.06, 0.85], 'top': 0.35}},
    'impostor_tone': [0.86, 0.86, 1.02],
    'impostor_dilate': 5,
    'impostor_edge_fill': True,
    'transparent_bounces': 64,
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


def cell_uv(cell):
    """Lower-left uv corner and size of a shared-atlas cell (row 0 = image top; Blender v up)."""
    row, col = divmod(cell, GRID)
    size = 1.0 / GRID
    return col * size, 1.0 - (row + 1) * size, size


def shared_path(name):
    return os.path.join(SHARED, name)


def lin(c):
    import numpy as np
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def srgb(c):
    import numpy as np
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(np.clip(c, 0, None), 1 / 2.4) - 0.055)


def tints(spec):
    """Linear COLOR_0 tints (leaves, bark): species target / the shared texture's mean over the species' cells."""
    import numpy as np
    meta = json.load(open(shared_path('atlas.json')))
    cells = spec['leaves']['cells']
    weights = np.array([meta['cells'][c]['coverage'] for c in cells])
    mean = np.average([meta['cells'][c]['mean_linear'] for c in cells], axis=0, weights=weights)
    target = np.array(spec['leaves']['target_srgb']) / 255.0
    lift = spec['leaves'].get('lift')
    if lift:                                  # MM8 colour lift: saturation and value of the leaf tint (sRGB HSV)
        import colorsys
        h, sat, val = colorsys.rgb_to_hsv(*target)
        target = np.array(colorsys.hsv_to_rgb(h, min(sat * lift.get('sat', 1.0), 1.0), min(val * lift.get('val', 1.0), 1.0)))
    leaf = lin(target) / mean
    bark = lin(np.array(spec['bark']['target_srgb']) / 255.0) / np.array(meta['bark_mean_linear'])
    return leaf, bark
