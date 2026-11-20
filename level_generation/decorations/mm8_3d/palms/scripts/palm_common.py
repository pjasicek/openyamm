"""Shared settings for the MM8 palms (plain Python: imported by the numpy texture painter, the Blender build scripts
and the post-processing). Adapted from ../../mm6_new_sorpigal_3d/desert/scripts/desert_common.py.

Atlas cells are (u0, v0, u1, v1) in image space (v down), as painted by make_textures.py; the Blender side flips v
when it writes UVs. Every species shares one foliage atlas ('tropical') and one of two trunk barks, so the engine
holds one copy of each image; per-species colour comes from COLOR_0 (occlusion x tint).

Species geometry is given in fractions of the model height H (measured on the native x2 sprite, x to the right of
the sprite's bounding-box centre, z up from the ground), so a model seen from the front (camera on -Y) reads like the
sprite; lengths in metres are for a 12 m palm and scale with H / 12."""
import os

PALMS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(PALMS, '..', '..', '..', '..'))
TEX = os.path.join(PALMS, 'textures')
# native x2 sprites, archived when the MM8 decoration sprites were retired (2026-10-16)
SPRITES = os.path.join(REPO, 'assets_legacy', 'decorations_x2_mm8_20261016')
UNITS_PER_METRE = 81.7

ATLAS_SIZE = 2048            # basecolour; the normal map is half this
CELL_W = 480 / ATLAS_SIZE
ATLAS = {
    'frondA': (0 * CELL_W, 0.0, 1 * CELL_W, 1.0),      # coconut frond, green
    'frondB': (1 * CELL_W, 0.0, 2 * CELL_W, 1.0),      # coconut frond, yellow / orange leaflet tips
    'frondC': (2 * CELL_W, 0.0, 3 * CELL_W, 1.0),      # date palm frond: stiff, narrow, pale tips
    'frondD': (3 * CELL_W, 0.0, 4 * CELL_W, 1.0),      # coconut frond with strong orange leaflet tips
    'stalk': (1928 / ATLAS_SIZE, 0.0, 2040 / ATLAS_SIZE, 0.5),
    'stalkGold': (1928 / ATLAS_SIZE, 0.5, 2040 / ATLAS_SIZE, 1.0),
}
FRONDS = ('frondA', 'frondB', 'frondC', 'frondD')
ENV = os.path.join(TEX, 'tropical_env.json')      # painted leaflet reach per frond cell along the rachis
BARK_TILE_M = 2.4                                   # trunk height one bark tile covers (u: once round the trunk)
BARKS = ('ringbark', 'bootbark')

WIND = 0.15          # metres at the top of a 12 m palm, the same on every material so fronds stay on the trunk
TRANSLUCENCY = 0.35
SPECULAR = float(os.environ.get('PALM_SPECULAR', 0.15))          # glossy leaflet sheen (with roughness LEAF_ROUGHNESS)
LEAF_ROUGHNESS = float(os.environ.get('PALM_ROUGHNESS', 0.35))
BUDGET = (4000, 1600, 600, 4)      # LOD0, LOD1, LOD2, impostor (one quad cut to a 6-vertex outline)

# ---------------------------------------------------------------------------------------------------- species
# trunk: centreline [(x, z)] in H fractions (base first, the last point is the trunk top);
# diameter: [(z, d)] in H fractions; heart: (x, z) where the fronds spring from (coconut types) or the
# top of the petiole bundle (crownshaft types).
COCONUT = dict(
    bark='ringbark', bark_tint=(0.66, 0.52, 0.34), fronds=24, cells={'frondA': 0.8, 'frondB': 0.2}, dead=0,
    length=(7.0, 8.0), length_age=(1.0, 0.75), width=1.25, petiole=0.55, petiole_cell='stalk', bundle=False,
    elev=(78.0, -20.0), elev_pow=1.2, droop=(80.0, 130.0), fit=True, hang=((16.0, 46.0), (38.0, 82.0)), roll=14.0, edge_shade=0.72,
    sun=((1.12, 1.1, 0.78), (0.72, 0.76, 0.86)),
    highlight=(1.32, 1.36, 0.7),       # sunlit upper/outer fronds (by sky visibility): yellow-green lift
    leaf_tint=(1.0, 1.0, 1.0), dead_tint=(1.0, 1.0, 1.0), value=(0.82, 1.1), heart_bulge=1.3,
    occlusion={'floor': 0.2, 'gamma': 1.3}, inner_floor=0.45, sweep=None, seed=801)

# boot-trunk and crownshaft palms: the heart sits at about half the height and the crown rises well above it, so the
# young fronds stand steeper and more fronds stay high
BOOT = dict(lod2_drop=0.2, elev=(84.0, 35.0), droop=(85.0, 150.0), length=(7.8, 8.6), length_age=(1.0, 0.45), elev_pow=1.5, width=0.9,
            hang=((30.0, 50.0), (66.0, 84.0)), fit=True)

SPECIES = {
    'tree01': dict(COCONUT, sprite='tree01_p337.png', height=980, seed=8101,
                   trunk=[(0.104, 0.0), (0.100, 0.10), (0.087, 0.20), (0.064, 0.30), (0.039, 0.40), (0.016, 0.50),
                          (0.002, 0.58)],
                   diameter=[(0.0, 0.088), (0.02, 0.07), (0.07, 0.058), (0.2, 0.052), (0.4, 0.044), (0.6, 0.037)],
                   heart=(-0.005, 0.605)),
    'tree04': dict(COCONUT, sprite='tree04_p337.png', height=972, seed=8401, fronds=22, elev=(70.0, -15.0), droop=(90.0, 130.0),
                   trunk=[(-0.040, 0.0), (-0.043, 0.10), (-0.034, 0.20), (-0.021, 0.30), (-0.003, 0.40),
                          (0.012, 0.50), (0.018, 0.57)],
                   diameter=[(0.0, 0.07), (0.02, 0.056), (0.07, 0.048), (0.2, 0.044), (0.4, 0.039), (0.6, 0.034)],
                   heart=(0.018, 0.595)),
    'tree08': dict(COCONUT, sprite='tree08_p337.png', height=972, seed=8804, fronds=22, elev=(70.0, -15.0), droop=(90.0, 130.0),
                   cells={'frondA': 0.6, 'frondB': 0.4},
                   trunk=[(-0.042, 0.0), (-0.041, 0.10), (-0.032, 0.20), (-0.017, 0.30), (0.0, 0.40),
                          (0.015, 0.50), (0.02, 0.57)],
                   diameter=[(0.0, 0.07), (0.02, 0.056), (0.07, 0.047), (0.2, 0.042), (0.4, 0.038), (0.6, 0.034)],
                   heart=(0.02, 0.595)),
    'tree09': dict(COCONUT, sprite='tree09_p337.png', height=984, seed=8901, fronds=22, specular=0.06, lod2_drop=0.15,
                   bark_tint=(0.5, 0.44, 0.28),
                   cells={'frondA': 0.3, 'frondB': 0.3, 'frondD': 0.4},
                   trunk=[(-0.227, 0.0), (-0.218, 0.10), (-0.201, 0.20), (-0.165, 0.29), (-0.121, 0.39),
                          (-0.07, 0.46), (-0.02, 0.52)],
                   diameter=[(0.0, 0.07), (0.02, 0.056), (0.07, 0.05), (0.2, 0.05), (0.4, 0.05), (0.6, 0.046)],
                   heart=(0.0, 0.545), sweep=(1.0, 0.0, 0.5)),
    'tree02': dict(COCONUT, sprite='tree02_p337.png', **BOOT, height=944, seed=8201, bark='bootbark', fronds=24, specular=0.1, contrast_max=2.5,
                   petiole=0.9, dead=0, heart_bulge=1.25,
                   trunk=[(0.02, 0.0), (0.017, 0.10), (0.019, 0.20), (0.021, 0.30), (0.02, 0.40), (0.012, 0.44)],
                   diameter=[(0.0, 0.1), (0.03, 0.085), (0.08, 0.075), (0.2, 0.07), (0.33, 0.075), (0.44, 0.085)],
                   heart=(0.005, 0.48)),
    'tree03': dict(COCONUT, sprite='tree03_p337.png', **BOOT, height=924, seed=8301, bark='bootbark', fronds=22,
                   petiole=2.1, bundle=True, dead=0, heart_bulge=1.0,
                   trunk=[(0.008, 0.0), (0.005, 0.10), (0.008, 0.20), (0.01, 0.30), (0.012, 0.36)],
                   diameter=[(0.0, 0.1), (0.03, 0.08), (0.08, 0.066), (0.2, 0.062), (0.36, 0.066)],
                   heart=(0.012, 0.56)),
    'tree06': dict(COCONUT, sprite='tree06_p337.png', **BOOT, height=920, seed=8601, bark='bootbark', fronds=22,
                   cells={'frondA': 0.2, 'frondB': 0.3, 'frondD': 0.5},
                   petiole=2.2, petiole_cell='stalkGold', pet_radius=0.11, contrast_max=2.0, bark_tint=(1.4, 0.98, 0.42), bundle=True, dead=0, heart_bulge=1.0,
                   trunk=[(0.007, 0.0), (0.003, 0.10), (0.004, 0.20), (0.008, 0.30), (0.008, 0.34)],
                   diameter=[(0.0, 0.095), (0.03, 0.075), (0.08, 0.064), (0.2, 0.06), (0.34, 0.066)],
                   heart=(0.01, 0.56)),
    'tree07': dict(COCONUT, sprite='tree07_p337.png', **BOOT, height=936, seed=8701, bark='bootbark', fronds=24,
                   cells={'frondA': 0.6, 'frondB': 0.4},
                   petiole=1.6, bundle=True, dead=0, heart_bulge=1.0,
                   trunk=[(0.016, 0.0), (0.016, 0.10), (0.019, 0.20), (0.021, 0.30), (0.02, 0.37)],
                   diameter=[(0.0, 0.1), (0.03, 0.08), (0.08, 0.068), (0.2, 0.066), (0.37, 0.07)],
                   heart=(0.01, 0.53)),
    'tree05': dict(COCONUT, sprite='tree05_p337.png', height=972, seed=8501, bark='bootbark', fronds=38, bark_tint=(0.86, 0.76, 0.52), specular=0.08, lod2_drop=0.15, contrast_max=2.5,
                   cells={'frondC': 1.0}, dead=0, length=(4.4, 5.0), length_age=(1.0, 0.85), width=1.0, petiole=0.5,
                   heart_bulge=1.15, rows=9, elev=(88.0, -50.0), elev_pow=0.9, droop=(30.0, 80.0),
                   sun=((1.2, 1.15, 0.7), (0.7, 0.75, 0.86)),
                   hang=((26.0, 48.0), (36.0, 64.0)), roll=8.0,
                   trunk=[(0.079, 0.0), (0.076, 0.10), (0.061, 0.20), (0.045, 0.29), (0.03, 0.39), (0.019, 0.47),
                          (0.016, 0.55)],
                   diameter=[(0.0, 0.1), (0.03, 0.09), (0.08, 0.078), (0.2, 0.072), (0.55, 0.068)],
                   heart=(0.018, 0.6)),
}
ORDER = ('tree01', 'tree04', 'tree08', 'tree02', 'tree07', 'tree06', 'tree03', 'tree05', 'tree09')


def output(sid):
    return f'mm8_deco_{sid}.glb'


def height_m(sid):
    return SPECIES[sid]['height'] / UNITS_PER_METRE


def work(sid):
    path = os.path.join(PALMS, 'work', sid)
    os.makedirs(path, exist_ok=True)
    return path


def review(sid):
    path = os.path.join(PALMS, 'review', sid)
    os.makedirs(path, exist_ok=True)
    return path
