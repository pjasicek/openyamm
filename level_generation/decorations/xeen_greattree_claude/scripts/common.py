"""Configuration and paths shared by every script of the Xeen great-tree crown (system Python and Blender's Python).

Adapted from the MM8 broadleaf batch (../../mm8_3d/trees_broadleaf/scripts/common.py, copied, not edited). Differences:
 - no sprite inventory: the crown envelope is a procedurally drawn silhouette (make_envelope.py ->
   source/crown_silhouette.png) and the model height comes from the species file (`height_m`, metres; 81.7 units/m);
 - own shared textures (make_shared.py -> shared/): a 2048 leaf atlas of GRID x GRID = 2 x 2 cells of 1024 px, each a
   spray cluster of MM8 maple sprays (the MM8 batch's leaf atlas bytes, copied into source/) recoloured to a cool deep
   green, for ~2.4 m cards with ~20 cm leaves; the bark is the Xeen trunk texture xdbark (a copy of
   assets_source/worlds/xeen/textures_x4/xdbark.png) plus a normal map derived from it;
 - the bark keeps the trunk's texture colour (tint 1), so the limbs meet A6's xdbark trunk;
 - install through tools/install_model.py --world xeen.
A script gets the species id as its first argument after '--' (Blender) or as argv[1] (Python)."""
import copy, json, os, sys

TREES = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(TREES, '..', '..', '..'))
SOURCE = os.path.join(TREES, 'source')
SHARED = os.path.join(TREES, 'shared')
# lane S: one Blender at a time (the wrapper waits for the lane lock); never /snap/bin/blender directly
BLENDER = os.path.join(REPO, 'level_generation', 'creatures', 'xeen_tiers_claude', 'bin', 'blender')
UNITS_PER_METRE = 81.7
GRID = 2                                # leaf atlas: GRID x GRID cells of 1024 px (2048 px)
XDBARK = os.path.join(REPO, 'assets_source', 'worlds', 'xeen', 'textures_x4', 'xdbark.png')
# xdbark on A6's trunk: one tile covers 128 units around x 256 units along
BARK_TILE_M = (128 / UNITS_PER_METRE, 256 / UNITS_PER_METRE)

DEFAULTS = {
    'seed': 8102, 'clump_seed': 8202, 'lod2_seed': 8203,
    'bark': {'budget': [3600, 1600, 800], 'occlusion_floor': 0.5, 'base_fade': [3.0, 9.0], 'wind': 0.05},
    'crown': {'canopy_low': 0.3, 'centre': 0.62, 'crown_normal_z': 1.15, 'clumps': 110, 'inner_clumps': 8,
              'outer_radius': [0.6, 0.95], 'inner_radius': [0.55, 0.75], 'gap': 0.8, 'card': [1.15, 1.35],
              'coverage': 0.45, 'flatten': 0.75, 'card_up': 0.25, 'shell_radial': 0.75, 'low_keep': 0.6,
              'shell': {'mode': 'cores', 'core': 0.45, 'cores': [40, 20, 8], 'value': 0.55, 'ao_floor': 0.5}},
    'occlusion': {'floor': 0.14, 'range': 0.86, 'power': 1.0, 'hue': [1.4, 1.0, 0.9], 'rays': 32},
    'lod': {'triangles': [15000, 7500, 3750], 'grow': [1.0, 1.3, 1.6], 'outward': [0.0, 0.0, 0.8],
            'tone': [1.0, 0.92, 1.45], 'keep': [1.0, 0.7, 0.6], 'lod2_card_scale': 1.0, 'clump_frame': 4.5},
    'leaves': {'cells': [0, 1, 2, 3], 'target_srgb': [34, 92, 58], 'wind': 0.3},
    'impostor_tone': [0.86, 0.86, 1.02],
    'impostor_dilate': 5,
    'impostor_edge_fill': True,
    'transparent_bounces': 64,
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
    spec.setdefault('output', f'xeen_deco_{sid}.glb')
    spec['height_units'] = spec['height_m'] * UNITS_PER_METRE
    spec['work'] = os.path.join(TREES, 'work', sid)
    spec['review'] = os.path.join(TREES, 'review', sid)
    spec['sprite_path'] = os.path.join(SOURCE, spec.get('silhouette', 'crown_silhouette.png'))
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
    """Linear COLOR_0 tints (leaves, bark): leaves = species target / the atlas mean over the species' cells; bark 1
    (the trunk's own xdbark colour)."""
    import numpy as np
    meta = json.load(open(shared_path('atlas.json')))
    cells = spec['leaves']['cells']
    weights = np.array([meta['cells'][c]['coverage'] for c in cells])
    mean = np.average([meta['cells'][c]['mean_linear'] for c in cells], axis=0, weights=weights)
    target = np.array(spec['leaves']['target_srgb']) / 255.0
    leaf = lin(target) / mean
    return leaf, np.ones(3)
