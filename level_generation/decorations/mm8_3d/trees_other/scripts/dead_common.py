"""Shared settings and paths of the dead-tree builder, copied from the MM6 trees (6tree27, 6tree28, 6tree29, swptree4,
stump5a: their kinds stay in dead_build.py) and used here for MM8 tree28 (kind 'broad').
Separate from the living-tree pipeline (common.py, species/): these models are bare wood, so they use their own
procedural branch generator (dead_build.py) instead of Sapling crowns. Work files: work/dead_<id>/, review sheets:
review/dead_<id>/. System Python and Blender's Python both import this module."""
import os, sys

TREES = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(TREES, '..', '..', '..', '..'))
SOURCE = os.path.join(TREES, 'source')
SPRITES = os.path.join(REPO, 'assets_dev', 'engine', 'decorations_x2')
# MM8 x2 sprites were archived after the 3D models were bound (2026-10-16)
if not os.path.exists(os.path.join(SPRITES, 'tree62c_p337.png')):
    SPRITES = os.path.join(REPO, 'assets_legacy', 'decorations_x2_mm8_20261016')
UNITS_PER_M = 81.7

# Poly Haven CC0 texture sets (dead_fetch.py)
TEXTURE_SETS = ['rough_wood', 'bark_willow_02', 'moss_wood', 'coral_mud_01']

SPECIES = {
    # MM8 tree28: large bare deciduous tree, a central leader with twisted ridged bark, limbs from about 30 % of the
    # height arching outward and forking into dense fine twigs, a few low sprouts (Shadowspire out06, Ravage Roaming)
    'tree28': {
        'kind': 'broad', 'sprite': 'tree28_p337.png', 'output': 'mm8_deco_tree28.glb', 'world_height': 1008,
        'bark': {'source': 'bark_willow_02', 'target_srgb': [138, 108, 72], 'tile': 1.1, 'contrast': 2.4},
        'twig_srgb': [82, 66, 52], 'twig_highlight_srgb': [204, 182, 144], 'twig_width': 1.5, 'twig_depth': 0,
        'buds': {'fraction': 0.5, 'radius': [2.2, 3.4], 'srgb': [[170, 116, 112], [128, 146, 92], [190, 150, 120]]},
        'tone_by_level': [1.0, 0.95, 0.88, 0.8, 0.74, 0.7],
        'broad': {'trunk_radius': 0.56, 'knob': 0.1, 'leader_top': 0.9, 'limbs': 10, 'limbs_z': [0.24, 0.8],
                  'elevation': [28, 60], 'limb_radius': 0.42, 'r_min': 0.045, 'card': [1.3, 2.0],
                  'fork_length': [0.58, 0.72], 'side_shoots': 1.5, 'limb_cards': 1.2, 'tip_cards': [1, 3],
                  'sprouts': 6, 'roots': 6, 'root_reach': 0.8, 'reach': 1.0, 'slack': 1.04},
        'occ': [0.4, 0.6], 'card_keep': [1.0, 0.85, 0.5], 'card_grow': [1.0, 1.25, 1.8],
        'proxy_grow': [1.0, 1.2, 1.5],
        'seed': 2808, 'budget': [5000, 2000, 900], 'lod_tone': [1.0, 1.07, 1.06], 'impostor_tone': [1.0, 1.0, 1.0],
    },
}


def species_id():
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    if not args:
        raise SystemExit('usage: <script> <id>')
    return args[0]


def load(sid=None):
    sid = sid or species_id()
    spec = dict(SPECIES[sid])
    spec['id'] = sid
    spec['height_m'] = spec['world_height'] / UNITS_PER_M
    spec['work'] = os.path.join(TREES, 'work', f'dead_{sid}')
    spec['review'] = os.path.join(TREES, 'review', f'dead_{sid}')
    spec['sprite_path'] = os.path.join(SPRITES, spec['sprite'])
    os.makedirs(spec['work'], exist_ok=True)
    os.makedirs(spec['review'], exist_ok=True)
    return spec


def lin(c):
    import numpy as np
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def srgb(c):
    import numpy as np
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(np.clip(c, 0, None), 1 / 2.4) - 0.055)
