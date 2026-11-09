"""Species configuration and paths shared by every tree pipeline script (system Python and Blender's Python).
MM7 seasonal trees: a copy of the MM6 New Sorpigal tree pipeline (../../mm6_new_sorpigal_3d/trees/scripts/common.py)
with this batch's paths. Sources (bark, leaves) are read from the MM6 folder; sprites are the restored x2 frames in
assets_dev/engine/decorations_x2/. A seasonal variant names its family's summer species in "family": it takes that
species' settings (skeleton, crown, envelope), so its trunk, branches and clumps are identical, and overrides only
what its season changes (leaf colours; "season": "bare" builds the leafless tree with bare_build.py).

A script gets the species id as its first argument after '--' (Blender) or as argv[1] (Python). species/<id>.json
holds every per-tree setting; DEFAULTS are the approved 6tree01 v2 values, so a species file lists only what differs.
Paths: work/<id>/ (generated maps, blends, exports), review/<id>/ (sheets), source/ (CC0 downloads)."""
import copy, json, os, sys

TREES = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(TREES, '..', '..', '..', '..'))
SOURCE = os.path.join(REPO, 'level_generation', 'decorations', 'mm6_new_sorpigal_3d', 'trees', 'source')
SPRITES = os.path.join(REPO, 'assets_legacy', 'decorations_x2_20261016')   # the x2 frames moved here on 2026-10-16
UNITS_PER_M = 81.7

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
    'season': 'leaves',                 # 'bare': the family's skeleton without leaves (bare_build.py)
    'bare': None,                       # bare-tree settings (bare_build.py, bare_prepare.py)
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


def raw(sid):
    """Species file merged over its family's summer species (seasonal variants), not yet over DEFAULTS."""
    own = json.load(open(os.path.join(TREES, 'species', f'{sid}.json')))
    if own.get('family'):
        family = raw(own['family'])
        own.setdefault('envelope_sprite', family.get('envelope_sprite', family['sprite']))
        for key in ('sprite', 'output', 'note'):
            family.pop(key)
        return _merge(family, own)
    return own


def load(sid=None):
    sid = sid or species_id()
    spec = _merge(copy.deepcopy(DEFAULTS), raw(sid))
    spec['id'] = sid
    spec.setdefault('family', None)
    # the crown envelope (profile.json) comes from the family's summer sprite, so every season fits one crown
    spec['envelope_path'] = os.path.join(SPRITES, f"{spec.get('envelope_sprite', spec['sprite'])}.png")
    spec['work'] = os.path.join(TREES, 'work', sid)
    spec['review'] = os.path.join(TREES, 'review', sid)
    spec['sprite_path'] = os.path.join(SPRITES, f"{spec['sprite']}.png")
    os.makedirs(spec['work'], exist_ok=True)
    os.makedirs(spec['review'], exist_ok=True)
    return spec


def lin(c):
    import numpy as np
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def srgb(c):
    import numpy as np
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(np.clip(c, 0, None), 1 / 2.4) - 0.055)


def review_env(min_free_mb=2500):
    """Environment for a review render (render_review.py): Eevee needs the GPU; when other sessions fill its memory
    (Eevee then segfaults), the render runs on Cycles CPU instead. Decided before Blender starts."""
    import subprocess
    env = dict(os.environ)
    try:
        out = subprocess.run(['nvidia-smi', '--query-gpu=memory.used,memory.total', '--format=csv,noheader,nounits'],
                             capture_output=True, text=True, timeout=20).stdout.split(',')
        free = float(out[1]) - float(out[0])
    except (OSError, ValueError, IndexError, subprocess.SubprocessError):
        free = 0.0
    if free < min_free_mb:
        env['TREES_REVIEW_CPU'] = '1'
    return env
