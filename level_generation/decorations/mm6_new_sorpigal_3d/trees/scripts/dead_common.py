"""Shared settings and paths of the dead-tree builder (6tree27, 6tree28, 6tree29, swptree4, stump5a).
Separate from the living-tree pipeline (common.py, species/): these models are bare wood, so they use their own
procedural branch generator (dead_build.py) instead of Sapling crowns. Work files: work/dead_<id>/, review sheets:
review/dead_<id>/. System Python and Blender's Python both import this module."""
import os, sys

TREES = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(TREES, '..', '..', '..', '..'))
SOURCE = os.path.join(TREES, 'source')
SPRITES = os.path.join(REPO, 'assets_dev', 'engine', 'decorations_x2')
MODELS = os.path.join(REPO, 'assets_dev', 'worlds', 'mm6', 'models')
UNITS_PER_M = 81.7

# Poly Haven CC0 texture sets (dead_fetch.py)
TEXTURE_SETS = ['rough_wood', 'bark_willow_02', 'moss_wood', 'coral_mud_01']

SPECIES = {
    # tall pine snag: straight trunk to a broken top, short drooping branches in whorls, spur twigs
    '6tree28': {
        'kind': 'snag', 'sprite': '6tree28_p140.png', 'output': 'mm6_deco_tree28.glb', 'world_height': 287,
        'bark': {'source': 'rough_wood', 'target_srgb': [118, 118, 108], 'tile': 0.7, 'contrast': 1.7},
        'twig_srgb': [34, 36, 32], 'twig_highlight_srgb': [175, 178, 168], 'tone_by_level': [1.0, 0.5, 0.45],
        'seed': 2801, 'budget': [6400, 2500, 900], 'lod_tone': [1.0, 1.0, 1.05], 'impostor_tone': [1.1, 1.1, 1.12],
    },
    # pine snag with many thin drooping twigs, pointed crown
    '6tree27': {
        'kind': 'snag', 'sprite': '6tree27_p140.png', 'output': 'mm6_deco_tree27.glb', 'world_height': 292,
        'bark': {'source': 'bark_willow_02', 'target_srgb': [132, 132, 122], 'tile': 0.8, 'contrast': 1.3},
        'twig_srgb': [52, 52, 48], 'twig_highlight_srgb': [215, 215, 206], 'tone_by_level': [1.0, 0.72, 0.66],
        'seed': 2701, 'budget': [6800, 2600, 900], 'lod_tone': [1.0, 1.0, 1.08],
    },
    # dark shrub of thin upright stems
    '6tree29': {
        'kind': 'shrub', 'sprite': '6tree29_p140.png', 'output': 'mm6_deco_tree29.glb', 'world_height': 117,
        'bark': {'source': 'rough_wood', 'target_srgb': [74, 78, 80], 'tile': 0.35, 'contrast': 2.3},
        'twig_srgb': [36, 36, 40], 'twig_highlight_srgb': [140, 146, 150],
        'seed': 2901, 'budget': [2400, 900, 320], 'texture_size': 512,
    },
    # gnarled green swamp tree on a mound of roots with hollows
    'swptree4': {
        'kind': 'gnarled', 'sprite': 'swptree4_p120.png', 'output': 'mm6_deco_swptree4.glb', 'world_height': 589,
        # Revision 2 (2026-10-09): pitted, knobby bark (Poly Haven coral_mud_01 as luminance detail, its pits and
        # lumps like the sprite's) in the sprite's light green; the vertex colours carry the native shading
        # (dead_prepare.native_ramp, dead_build.native_colours): dark hollows and crevices, lit tops, moss patches.
        'bark': {'source': 'coral_mud_01', 'target_srgb': [86, 164, 96], 'tile': 0.5, 'contrast': 0.85,
                 'grey': True, 'ao_gain': 2.0, 'height_gain': 0.5},
        'native_shading': {'up': 0.7, 'quantiles': [0.0, 0.93], 'moss': 0.12, 'skirt': 0.3,
                           'chroma': 1.1, 'pit_cups': True},
        'twig_srgb': [36, 104, 34], 'twig_highlight_srgb': [120, 200, 90],
        'seed': 4401, 'budget': [9000, 3400, 1400], 'lod_tone': [1.0, 1.1, 1.14],
        'impostor_tone': [1.12, 1.0, 1.14],
    },
    # cut stump with a stepped top, weathered bark and flared roots
    'stump5a': {
        'kind': 'stump', 'sprite': 'stump5a_p547.png', 'output': 'mm6_deco_stump5a.glb', 'world_height': 72,
        'bark': {'source': 'bark_willow_02', 'target_srgb': [128, 112, 98], 'tile': 0.45, 'contrast': 1.9},
        'seed': 5501, 'budget': [2200, 900, 300, 100], 'lod_tone': [1.0, 0.98, 0.92, 0.84],
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
