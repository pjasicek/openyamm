"""Shared settings of the MM7 plants batch (plain Python: imported by the texture painter, the Blender builder and the
finishing script). Atlas cells are (u0, v0, u1, v1) in image space (v down)."""
import os

PLANTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(PLANTS, '..', '..', '..', '..'))
TEX = os.path.join(PLANTS, 'textures')
WORK = os.path.join(PLANTS, 'work')
REVIEW = os.path.join(PLANTS, 'review')
SPRITES = os.path.join(REPO, 'assets_legacy', 'decorations_x2_20261016')
UNITS_PER_METRE = 81.7

CELLS = {
    # fronds.png (1024², four 256 x 1024 strips)
    'fern_a': (0.0, 0.0, 0.25, 1.0), 'spray': (0.25, 0.0, 0.5, 1.0), 'palm': (0.5, 0.0, 0.75, 1.0),
    'dry': (0.75, 0.0, 1.0, 1.0),
    # leaves.png (1024²)
    'leaf_var': (0.0, 0.0, 0.25, 0.5), 'leaf_dark': (0.25, 0.0, 0.5, 0.5), 'leaf_green': (0.5, 0.0, 0.75, 0.5),
    'leaf_wilt': (0.75, 0.0, 1.0, 0.5), 'clump': (0.0, 0.5, 0.5, 1.0), 'grass': (0.5, 0.5, 0.955, 1.0),
    'stem_green': (0.962, 0.5, 0.978, 1.0), 'stem_wood': (0.984, 0.5, 1.0, 1.0),
    # joshua.png (1024 x 512)
    'burst': (0.0, 0.0, 0.5, 1.0), 'half': (0.5, 0.0, 1.0, 1.0),
}

# id -> (sprite x2 file, binding height in map units = inventory art_height, LOD triangle budget)
SPECS = {
    'bush03': ('bush03_p120.png', 122, (700, 360, 160)),
    'bush10': ('bush10_p120.png', 163, (1200, 600, 240)),
    'bush11': ('bush11_p120.png', 154, (1500, 700, 260)),
    'bush13': ('bush13_p120.png', 273, (1500, 750, 300)),
    'bush12': ('bush12_p120.png', 256, (2600, 1100, 360)),
    'bush16': ('bush16_p120.png', 129, (2600, 1000, 300)),
    'bush02': ('bush02_p120.png', 190, (1500, 700, 260)),
    'plant01a': ('plant01a_p122.png', 252, (2400, 1100, 360)),
    'plant11a': ('plant11a_p122.png', 256, (2400, 1100, 360)),
    'plant02a': ('plant02a_p122.png', 246, (2400, 1100, 360)),
    'plant01b': ('plant01b_p122.png', 141, (2400, 1100, 360)),
    'plant07b': ('plant07b_p122.png', 170, (2400, 1100, 360)),
    'plant03b': ('plant03b_p122.png', 142, (1800, 900, 300)),
    'plant04b': ('plant04b_p122.png', 158, (2400, 1100, 360)),
}


def height_m(sid):
    return SPECS[sid][1] / UNITS_PER_METRE
