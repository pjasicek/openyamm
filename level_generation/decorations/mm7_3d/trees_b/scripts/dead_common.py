"""Shared settings and paths of the MM7 bare-tree builder (tree41, tree42, 7tree06), adapted from the MM6 dead-tree
builder (level_generation/decorations/mm6_new_sorpigal_3d/trees/scripts/dead_common.py).

MM7's bare trees are gnarled hardwoods whose every limb is drawn in the sprite, so their skeleton is traced from the
sprite (trace_skeleton.py: thinning, branch graph, axes with radii from the distance transform) and lifted into 3D in
dead_build.py (kind 'traced'); the rest (tubes, LODs, occlusion, twig atlas, impostor, export, validation) is the MM6
dead-tree code. Work files: work/dead_<id>/, review sheets: review/dead_<id>/. Textures are read from the MM6 tree
project's source/ (Poly Haven CC0 sets, never written here). System Python and Blender's Python import this module."""
import os, sys

TREES = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(TREES, '..', '..', '..', '..'))
SOURCE = os.path.join(REPO, 'level_generation', 'decorations', 'mm6_new_sorpigal_3d', 'trees', 'source')
SPRITES = os.path.join(REPO, 'assets_legacy', 'decorations_x2_20261016')
UNITS_PER_M = 81.7

# Poly Haven CC0 texture sets (present in the MM6 project's source/)
TEXTURE_SETS = ['rough_wood', 'bark_willow_02', 'moss_wood', 'coral_mud_01']

SPECIES = {
    # gnarled leaning dead tree: twisted trunk forking low into two or three crooked limbs with antler-like tips
    'tree41': {
        'kind': 'traced', 'sprite': 'tree41_p121.png', 'output': 'mm7_deco_tree41.glb', 'world_height': 1132,
        'bark': {'source': 'coral_mud_01', 'target_srgb': [104, 62, 46], 'tile': 2.2, 'contrast': 2.0,
                 'grey': True, 'ao_gain': 2.0, 'height_gain': 0.5},
        'native_shading': {'up': 0.6, 'quantiles': [0.35, 1.0], 'moss': 0.0, 'chroma': 1.15, 'height_strength': 0.0},
        'twig_srgb': [52, 30, 22], 'twig_highlight_srgb': [150, 98, 80], 'tone_by_level': [1.0, 0.95, 0.9],
        'seed': 4101, 'budget': [6000, 2400, 800], 'lod_tone': [1.0, 1.05, 1.06], 'impostor_tone': [1.0, 1.0, 1.0],
        'trace': {'depth': [0.5, 1.05], 'knob': 0.16, 'knob_freq': 1.6, 'ring': 2.0, 'seg': 0.2},
    },
    # broad dead oak: thick trunk splitting at 40 % into a tangle of crooked limbs and fine twigs, a hollow at the fork
    'tree42': {
        'kind': 'traced', 'sprite': 'tree42_p121.png', 'output': 'mm7_deco_tree42.glb', 'world_height': 1280,
        'bark': {'source': 'coral_mud_01', 'target_srgb': [116, 76, 56], 'tile': 2.2, 'contrast': 2.0,
                 'grey': True, 'ao_gain': 2.0, 'height_gain': 0.5},
        'native_shading': {'up': 0.6, 'quantiles': [0.35, 1.0], 'moss': 0.0, 'chroma': 1.15, 'height_strength': 0.0},
        'twig_srgb': [58, 34, 24], 'twig_highlight_srgb': [160, 108, 86], 'tone_by_level': [1.0, 0.95, 0.9],
        'seed': 4201, 'budget': [6000, 2400, 800], 'lod_tone': [1.0, 1.0, 1.04], 'impostor_tone': [1.0, 1.0, 1.0],
        'trace': {'depth': [0.5, 1.1], 'knob': 0.16, 'knob_freq': 1.6, 'ring': 2.5, 'seg': 0.36,
                  'radius_scale': 1.1, 'limb_scale': [1.3, 1.25, 1.12],
                  # the dark hollow at the fork: sprite (236.7, 308.8) px, 64 x 61 px of near-black
                  'hollow': [0.09, 6.19, 0.75, 0.85]},
    },
    # slim bare tree: one trunk dividing at a fifth of the height into a vase of thin upright stems
    '7tree06': {
        'kind': 'traced', 'sprite': '7tree06_p121.png', 'output': 'mm7_deco_7tree06.glb', 'world_height': 1190,
        'bark': {'source': 'bark_willow_02', 'target_srgb': [126, 88, 70], 'tile': 1.0, 'contrast': 1.3},
        'native_shading': {'up': 0.6, 'quantiles': [0.22, 1.0], 'moss': 0.0, 'chroma': 1.1, 'height_strength': 0.0},
        'twig_srgb': [60, 40, 30], 'twig_highlight_srgb': [160, 116, 96], 'tone_by_level': [1.0, 0.97, 0.94],
        'seed': 6061, 'budget': [7000, 2600, 900], 'lod_tone': [1.0, 1.0, 1.04], 'impostor_tone': [1.0, 1.0, 1.0],
        'trace': {'depth': [0.3, 0.75], 'knob': 0.05, 'radius_scale': 1.0, 'ring': 2.5, 'seg': 0.25},
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
