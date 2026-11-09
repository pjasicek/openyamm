"""Shared settings for the MM6 desert palm decorations (plain Python: imported by the numpy texture painter, the
Blender build scripts and the post-processing). Atlas cells are (u0, v0, u1, v1) in image space (v down), as painted
by make_textures.py; the Blender side flips v when it writes UVs."""
import os

DESERT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(DESERT, '..', '..', '..', '..'))
TEX = os.path.join(DESERT, 'textures')
MODELS = os.path.join(REPO, 'assets_dev', 'worlds', 'mm6', 'models')
SPRITES = os.path.join(REPO, 'assets_dev', 'engine', 'decorations_x2')
UNITS_PER_METRE = 81.7

# One foliage atlas per plant family, shared by every model that uses it (the engine shares identical images); the
# per-model colour comes from COLOR_0 (occlusion x tint).
ATLAS = {
    'palm': {
        'fanA': (0.0, 0.0, 0.5, 0.5), 'fanB': (0.5, 0.0, 1.0, 0.5), 'fanC': (0.5, 0.5, 1.0, 1.0),
        'skirt': (0.0, 0.5, 0.40, 1.0), 'stalk': (0.42, 0.5, 0.48, 1.0),
    },
    'banana': {
        'leafA': (0.0, 0.0, 0.25, 1.0), 'leafB': (0.25, 0.0, 0.5, 1.0), 'leafC': (0.5, 0.0, 0.75, 1.0),
        'dead': (0.75, 0.0, 1.0, 0.5), 'bunch': (0.75, 0.5, 0.95, 0.85), 'stalk': (0.96, 0.5, 1.0, 1.0),
        'sheath': (0.75, 0.86, 0.95, 1.0),
    },
    'yucca': {
        'sprayA': (0.0, 0.0, 0.5, 0.5), 'sprayB': (0.5, 0.0, 1.0, 0.5), 'dead': (0.0, 0.5, 0.25, 1.0),
        'strands': (0.25, 0.5, 0.5, 1.0), 'bladeA': (0.5, 0.5, 0.625, 1.0), 'bladeB': (0.625, 0.5, 0.75, 1.0),
        'strandsB': (0.75, 0.5, 1.0, 1.0),
    },
}
ATLAS_SIZE = 1024

# Tileable bark maps (512²): u around the stem, v along it.
BARKS = ('palmboot', 'bananastem', 'dragonbark', 'yuccastem')

# id -> (output, sprite file, world height in units, foliage atlas, bark)
MODELS_SPEC = {
    '6tree21': ('mm6_deco_tree21.glb', '6tree21_p140.png', 360, 'palm', 'palmboot'),
    'cac19': ('mm6_deco_cac19.glb', 'cac19_p140.png', 168, 'banana', 'bananastem'),
    'cac18': ('mm6_deco_cac18.glb', 'cac18_p140.png', 255, 'banana', 'bananastem'),
    'cac24': ('mm6_deco_cac24.glb', 'cac24_p144.png', 196, 'yucca', 'dragonbark'),
    'cac17': ('mm6_deco_cac17.glb', 'cac17_p144.png', 218, 'yucca', 'yuccastem'),
    'cac23': ('mm6_deco_cac23.glb', 'cac23_p144.png', 282, 'yucca', 'yuccastem'),
    'cac3': ('mm6_deco_cac3.glb', 'cac3_p144.png', 154, 'yucca', 'yuccastem'),
}
# LOD triangle budgets (LOD0, LOD1, LOD2, impostor: one quad cut to a 6-vertex outline)
BUDGET = {
    '6tree21': (5000, 2000, 600, 4), 'cac19': (3000, 1200, 400, 4), 'cac18': (5000, 2000, 650, 4),
    'cac24': (3000, 1200, 400, 4), 'cac17': (5000, 2000, 800, 4), 'cac23': (4500, 1800, 600, 4),
    'cac3': (1500, 600, 220, 4),
}
WIND = 0.05          # metres at the top, the same on bark and leaves so leaves stay on their stems
TRANSLUCENCY = 0.3
SPECULAR = 0.1


def height_m(sid):
    return MODELS_SPEC[sid][2] / UNITS_PER_METRE


def work(sid):
    path = os.path.join(DESERT, 'work', sid)
    os.makedirs(path, exist_ok=True)
    return path


def review(sid):
    path = os.path.join(DESERT, 'review', sid)
    os.makedirs(path, exist_ok=True)
    return path
