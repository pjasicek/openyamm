"""Per-model specs (inside Blender). Sizes are relative to the sprite height H unless a group says rel=False;
tints are linear multipliers on the atlas colour (COLOR_0 = tint x occlusion)."""
import clump

G = (1.0, 1.0, 1.0)
STEM = {'r': 0.008, 'in': 0.45, 'colour': 'green', 'tint': (0.8, 0.85, 0.8)}

def shell(cell, n, size, tint, z=(0.05, 0.85), depth=(0.6, 0.85), **kw):
    return dict(cell=cell, n=n, size=size, tint=tint, z=z, depth=depth, **kw)


def heads(cell, n, r, profile, z=(0.2, 1.0), depth=(0.85, 1.02), rise=(20, 60), stem=0.006, **kw):
    d = dict(cell=cell, n=n, r=r, profile=profile, tint=kw.pop('tint', G), z=z, depth=depth, rise=rise,
             segments=kw.pop('segments', 8), spacing=kw.pop('spacing', 0.72))
    if stem:
        d['stem'] = dict(STEM, r=stem, len=kw.pop('stem_len', 0.25), colour=kw.pop('stem_colour', 'green'))
    d.update(kw)
    return d


SPECS = {
    'plant16': {'atlas': 'flowers', 'seed': 1601,
                'shell': [shell('s_ground', 22, 0.36, (0.8, 1.0, 0.7), z=(0.05, 0.75))],
                'leaves': [{'cell': 'l_lance_serrate', 'n': 13, 'from': 'whorl', 'k': 6, 'len': (0.13, 0.3),
                            'elev': (5, 50), 'z': (0.2, 0.85), 'depth': (0.35, 0.75), 'droop': (0.2, 0.6),
                            'tint': (0.9, 1.0, 0.75), 'stem': {'r': 0.01, 'in': 0.6}, 'roll': 0.7, 'width': 1.35,
                            'segs': 2, 'margin': 1.05},
                           {'cell': 'l_lance_serrate', 'n': 12, 'from': 'base', 'len': (0.2, 0.4), 'elev': (5, 45),
                            'root_r': 0.15, 'droop': (0.3, 0.7), 'tint': (0.75, 0.85, 0.65), 'roll': 0.7,
                            'width': 1.3}],
                'heads': [heads('h_lotus', 16, (0.14, 0.19), 'dish', rise=(15, 50), depth=(0.85, 1.0),
                                stem=0.007, spacing=0.7)],
                'lod_plan': clump.plan(leaf2=0.4)},
    'plant17': {'atlas': 'flowers', 'seed': 1701,
                'shell': [shell('s_ground', 12, 0.36, (0.6, 0.75, 0.6), z=(0.0, 0.45))],
                'leaves': [{'cell': 'l_tulip', 'n': 18, 'from': 'base', 'len': (0.35, 0.65), 'elev': (40, 80),
                            'root_r': 0.25, 'droop': (0.4, 1.0), 'tint': (0.9, 1.0, 0.85), 'roll': 0.6,
                            'width': 1.2},
                           {'cell': 'l_tulip', 'n': 14, 'from': 'volume', 'len': (0.18, 0.32), 'elev': (15, 55),
                            'z': (0.1, 0.6), 'depth': (0.3, 0.8), 'tint': (0.8, 0.9, 0.75), 'roll': 0.6,
                            'width': 1.2}],
                'heads': [heads('h_tulip', 18, (0.09, 0.11), 'goblet', z=(0.3, 1.0), depth=(0.4, 0.95),
                                rise=(55, 85), top_clear=1.7, stem=0.008, stem_len=0.45, spacing=0.85)]},
    'plant19': {'atlas': 'flowers', 'seed': 1901,
                'shell': [shell('s_ground', 34, 0.36, (0.42, 0.55, 0.38), z=(0.03, 0.8), depth=(0.3, 0.85))],
                'heads': [heads('h_startulip', 30, (0.12, 0.15), 'cup', depth=(0.85, 1.0), rise=(25, 65),
                                spacing=0.65)]},
    'plant20': {'atlas': 'flowers', 'seed': 2001,
                'shell': [shell('s_ground', 14, 0.34, (0.45, 0.62, 0.38), z=(0.2, 0.8), depth=(0.4, 0.7))],
                'leaves': [{'cell': 'l_hosta', 'n': 18, 'from': 'base', 'len': (0.3, 0.58), 'elev': (10, 55),
                            'root_r': 0.12, 'droop': (0.3, 0.8), 'tint': (0.95, 1.0, 0.85), 'roll': 0.5,
                            'width': 1.0}],
                'heads': [heads('h_petunia', 24, (0.09, 0.115), 'trumpet', z=(0.3, 1.0), rise=(25, 65))]},
    'plant21': {'atlas': 'flowers', 'seed': 2101,
                'shell': [shell('s_ground', 24, 0.36, (0.62, 0.66, 0.3), z=(0.03, 0.8))],
                'leaves': [{'cell': 'l_hosta', 'n': 6, 'from': 'base', 'len': (0.3, 0.5), 'elev': (30, 60),
                            'tint': (1.0, 1.0, 0.7), 'roll': 0.5, 'root_r': 0.2},
                           {'cell': 'l_broad_lance', 'n': 10, 'from': 'base', 'len': (0.3, 0.6), 'elev': (40, 75),
                            'tint': (0.8, 0.9, 0.4), 'roll': 0.5, 'root_r': 0.2}],
                'heads': [heads('h_trumpet', 15, (0.12, 0.15), 'trumpet', z=(0.3, 1.0), stem=0.007)]},
    'plant22': {'atlas': 'flowers', 'seed': 2201,
                'shell': [shell('s_ground', 10, 0.32, (0.45, 0.6, 0.45), z=(0.0, 0.4))],
                'leaves': [{'cell': 'l_broad_lance', 'n': 18, 'from': 'base', 'len': (0.35, 0.7), 'elev': (35, 75),
                            'root_r': 0.1, 'droop': (0.3, 0.8), 'tint': (0.9, 0.95, 0.85), 'roll': 0.5,
                            'width': 1.25}],
                'heads': [heads('h_florets', 22, (0.11, 0.14), 'dome', z=(0.15, 1.0), depth=(0.7, 1.0),
                                rise=(30, 75), stem=0.008, stem_colour='brown', stem_len=0.25, spacing=0.6,
                                tint=(1.0, 0.9, 0.85))]},
    'plant23': {'atlas': 'flowers', 'seed': 2301,
                'shell': [shell('s_strap', 10, 0.5, (0.72, 0.66, 0.36), z=(0.0, 0.5), depth=(0.3, 0.6))],
                'leaves': [{'cell': 'l_strap', 'n': 26, 'from': 'base', 'len': (0.4, 0.85), 'elev': (35, 80),
                            'root_r': 0.2, 'droop': (0.5, 1.2), 'tint': (0.75, 0.7, 0.35), 'roll': 0.5,
                            'width': 0.8, 'segs': 4}],
                'heads': [heads('h_lily', 28, (0.13, 0.16), 'dish', z=(0.15, 1.0), depth=(0.85, 1.0),
                                spacing=0.6)]},
    'plant24': {'atlas': 'flowers', 'seed': 2401, 'radius_scale': 0.85,
                'leaves': [{'cell': 'l_strap', 'n': 40, 'from': 'base', 'len': (0.5, 1.0), 'elev': (45, 88),
                            'root_r': 0.3, 'droop': (0.3, 1.1), 'tint': (0.62, 0.95, 0.65), 'roll': 0.5,
                            'width': 0.45, 'segs': 3},
                           {'cell': 'l_broad_lance', 'n': 4, 'from': 'base', 'len': (0.7, 1.0), 'elev': (55, 80),
                            'root_r': 0.2, 'droop': (0.2, 0.5), 'tint': (0.7, 1.0, 0.7), 'roll': 0.4, 'width': 0.9}],
                'heads': [heads('h_daisy', 6, (0.1, 0.12), 'flat', z=(0.3, 0.8), depth=(0.7, 0.95),
                                rise=(25, 55), segments=10, stem=0.008, stem_len=0.5, tint=(1.0, 0.72, 0.45))]},
    'plant25': {'atlas': 'flowers', 'seed': 2501,
                'shell': [shell('s_ground', 22, 0.36, (0.5, 0.58, 0.3), z=(0.0, 0.6), depth=(0.2, 0.8))],
                'leaves': [{'cell': 'l_red', 'n': 15, 'from': 'whorl', 'k': 4, 'len': (0.13, 0.28),
                            'elev': (5, 55), 'z': (0.35, 1.0), 'depth': (0.3, 0.85), 'tint': (1.0, 1.0, 1.0),
                            'roll': 0.7, 'width': 1.1, 'segs': 2}],
                'heads': [heads('h_impatiens', 14, (0.09, 0.12), 'dish', z=(0.0, 0.75), stem=0)]},
    'plant26': {'atlas': 'flowers', 'seed': 2601,
                'shell': [shell('s_ground', 14, 0.3, (0.55, 0.75, 0.5), z=(0.25, 0.85), depth=(0.3, 0.7))],
                'leaves': [{'cell': 'l_lance_dark', 'n': 19, 'from': 'whorl', 'k': 6, 'len': (0.14, 0.3),
                            'elev': (-5, 45), 'z': (0.15, 0.85), 'depth': (0.3, 0.85), 'droop': (0.3, 0.7),
                            'tint': (0.95, 1.0, 0.9), 'roll': 0.6, 'width': 1.6, 'segs': 2,
                            'stem': {'r': 0.012, 'in': 0.3, 'colour': 'brown'}}],
                'heads': [heads('h_star', 26, (0.09, 0.115), 'star', z=(0.35, 1.0), depth=(0.82, 1.0),
                                stem=0.005, spacing=0.65, segments=6)]},
    'plant27': {'atlas': 'flowers', 'seed': 2701, 'radius_scale': 1.12,
                'shell': [shell('s_ground', 12, 0.4, (0.42, 0.5, 0.32), z=(0.0, 0.55), depth=(0.2, 0.7))],
                'leaves': [{'cell': 'l_serrate_ovate', 'n': 44, 'from': 'volume', 'len': (0.15, 0.32),
                            'elev': (0, 45), 'z': (0.05, 0.75), 'depth': (0.3, 0.85), 'droop': (0.2, 0.6),
                            'tint': (0.9, 0.95, 0.75), 'roll': 0.7, 'width': 1.0, 'segs': 2},
                           {'cell': 'l_serrate_ovate', 'n': 10, 'from': 'base', 'len': (0.3, 0.5), 'elev': (5, 30),
                            'root_r': 0.2, 'tint': (0.75, 0.8, 0.6), 'roll': 0.7, 'segs': 2}],
                'heads': [heads('h_blossom', 6, (0.2, 0.25), 'dish', z=(0.3, 0.95), depth=(0.75, 0.95),
                                rise=(25, 55), segments=10, top_clear=0.5, stem=0, spacing=0.7)]},
    # ---------------------------------------------------------------- leafy plants (atlas 'leafy')
    'plant02': {'atlas': 'leafy', 'seed': 201, 'wind': 0.03,
                'stalks': [{'pts': [(0, 0, 0), (0.02, 0.01, 0.2), (0.0, 0.03, 0.4)], 'r': 0.022, 'colour': 'green',
                            'tint': (0.6, 0.65, 0.55), 'sides': 5}],
                'leaves': [{'cell': 'l_schefflera', 'n': 16, 'from': 'whorl', 'k': 8, 'len': (0.14, 0.24),
                            'elev': (-25, 30), 'z': (0.3, 0.95), 'depth': (0.15, 0.75), 'droop': (0.2, 0.6),
                            'tint': (0.95, 1.0, 0.85), 'roll': 0.5, 'width': 1.7, 'segs': 2, 'margin': 1.1,
                            'stem': {'r': 0.012, 'in': 0.05, 'from_z': 0.3, 'tint': (0.6, 0.65, 0.55)}}],
                'cards': [{'cell': 's_ground', 'n': 4, 'size': 0.16, 'r': 0.06, 'tint': (0.55, 0.62, 0.45)}],
                'lod_plan': clump.plan(leaf1=0.6, leaf2=0.35)},
    'plant03': {'atlas': 'leafy', 'seed': 301,
                'leaves': [{'cell': 'l_spot', 'n': 80, 'from': 'base', 'len': (0.25, 1.1), 'elev': (30, 75),
                            'root_r': 0.35, 'droop': (0.3, 0.8), 'tint': (0.95, 1.0, 0.9), 'roll': 0.5,
                            'width': 1.0, 'segs': 2, 'margin': 1.08}]},
    'plant04': {'atlas': 'leafy', 'seed': 401,
                'cards': [{'cell': 's_tuft', 'n': 9, 'size': 0.95, 'r': 0.16, 'tint': (0.72, 0.7, 0.62),
                           'aspect': 1.4, 'lean': (0, 20)}],
                'leaves': [{'cell': 'l_blade', 'n': 70, 'from': 'base', 'len': (0.6, 1.0), 'elev': (25, 75),
                            'root_r': 0.35, 'droop': (0.5, 1.3), 'tint': (0.72, 0.68, 0.62), 'roll': 0.5,
                            'width': 0.7, 'segs': 3, 'fit': False}]},
    'plant05': {'atlas': 'leafy', 'seed': 501, 'wind': 0.04,
                'leaves': [{'cell': 'l_fern', 'n': 16, 'from': 'base', 'len': (0.65, 1.0), 'elev': (45, 82),
                            'root_r': 0.08, 'droop': (0.3, 0.8), 'tint': (0.85, 1.0, 0.75), 'roll': 0.25,
                            'width': 1.0, 'segs': 4, 'fold': 0.15, 'margin': 1.05},
                           {'cell': 'l_fern', 'n': 6, 'from': 'base', 'len': (0.4, 0.6), 'elev': (20, 45),
                            'root_r': 0.05, 'droop': (0.4, 0.9), 'tint': (0.7, 0.8, 0.6), 'roll': 0.25,
                            'segs': 3, 'fit': False}],
                'lod_plan': clump.plan(leaf1=0.6, leaf2=0.4)},
    'plant09': {'atlas': 'leafy', 'seed': 901,
                'shell': [shell('s_pothos', 24, 0.34, (0.75, 0.85, 0.65), z=(0.05, 0.9), depth=(0.15, 0.7),
                                tilt=0.5)],
                'leaves': [{'cell': 'l_heart', 'n': 64, 'from': 'volume', 'len': (0.2, 0.3), 'elev': (-15, 50),
                            'z': (0.03, 0.95), 'depth': (0.7, 1.0), 'tint': (0.92, 1.0, 0.85), 'roll': 0.8,
                            'width': 1.0, 'segs': 2, 'fit': False},
                           {'cell': 'l_heart', 'n': 18, 'from': 'volume', 'len': (0.2, 0.28), 'elev': (25, 75),
                            'z': (0.75, 1.0), 'depth': (0.0, 0.8), 'tint': (0.95, 1.0, 0.85), 'roll': 0.8,
                            'width': 1.0, 'segs': 2, 'fit': False}]},
    'plant10': {'atlas': 'leafy', 'seed': 1001, 'wind': 0.03,
                'stalks': [{'pts': [(0, 0, 0), (0.04, 0.0, 0.2), (-0.02, 0.02, 0.42), (0.05, -0.01, 0.62),
                                    (0.02, 0.0, 0.8)], 'r': 0.045, 'colour': 'brown', 'tint': (0.95, 0.85, 0.75),
                            'sides': 5}],
                'cards': [{'cell': 's_tuft', 'n': 3, 'size': 0.16, 'r': 0.05, 'tint': (0.6, 0.75, 0.6)}],
                'leaves': [{'cell': 'l_broad', 'n': 13, 'from': 'whorl', 'k': 4, 'len': (0.11, 0.18),
                            'elev': (-15, 40), 'z': (0.3, 1.0), 'depth': (0.35, 0.9), 'droop': (0.2, 0.6),
                            'tint': (0.95, 1.0, 0.9), 'roll': 0.6, 'width': 1.2, 'segs': 2,
                            'stem': {'r': 0.012, 'in': 0.12, 'from_z': 0.65, 'colour': 'brown',
                                     'tint': (0.9, 0.8, 0.7)}}]},
    'plant11': {'atlas': 'leafy', 'seed': 1101,
                'leaves': [{'cell': 'l_sword', 'n': 24, 'from': 'base', 'len': (0.6, 1.0), 'elev': (62, 88),
                            'root_r': 0.25, 'droop': (0.0, 0.35), 'tint': (0.9, 0.95, 0.85), 'roll': 0.35,
                            'width': 1.4, 'segs': 3, 'fold': 0.35, 'margin': 1.05}]},
    'plant13': {'atlas': 'leafy', 'seed': 1301,
                'leaves': [{'cell': 'l_blade', 'n': 50, 'from': 'base', 'len': (0.6, 1.0), 'elev': (55, 88),
                            'root_r': 0.3, 'droop': (0.1, 0.8), 'tint': (0.8, 1.0, 0.8), 'roll': 0.4,
                            'width': 1.1, 'segs': 3, 'fold': 0.3, 'margin': 1.1}]},
    'plant15': {'atlas': 'leafy', 'seed': 1501,
                'stalks': [{'pts': [(0.0, 0.0, 0.0), (0.0, 0.0, 0.62)], 'r': 0.022, 'colour': 'brown',
                            'tint': (1.0, 0.75, 0.65)},
                           {'pts': [(0.05, 0.02, 0.0), (0.04, 0.03, 0.56)], 'r': 0.02, 'colour': 'brown',
                            'tint': (1.0, 0.75, 0.65)},
                           {'pts': [(-0.04, 0.03, 0.0), (-0.03, 0.02, 0.5)], 'r': 0.018, 'colour': 'brown',
                            'tint': (1.0, 0.75, 0.65)}],
                'leaves': [{'cell': 'l_lance', 'n': 18, 'from': 'stalk', 'z': (0.36, 0.62), 'len': (0.5, 0.85),
                            'elev': (-5, 45), 'droop': (0.3, 0.7), 'tint': (0.9, 0.95, 0.9), 'roll': 0.3,
                            'width': 1.5, 'segs': 3, 'fit': False},
                           {'cell': 'l_broad', 'n': 1, 'from': 'stalk', 'z': (0.6, 0.62), 'len': (0.35, 0.4),
                            'elev': (60, 70), 'droop': (0.2, 0.3), 'tint': (0.7, 0.8, 0.7), 'width': 1.4,
                            'segs': 2, 'fit': False, 'priority': 1.0},
                           {'cell': 'h_bud', 'n': 2, 'from': 'stalk', 'z': (0.45, 0.55), 'len': (0.2, 0.24),
                            'elev': (-50, -35), 'droop': (0.0, 0.1), 'tint': G, 'roll': 0.3, 'width': 1.6,
                            'segs': 2, 'fit': False, 'fold': 0.6, 'priority': 1.0}]},
    'plant34': {'atlas': 'leafy', 'seed': 3401, 'wind': 0.05,
                'stalks': [{'pts': [(0, 0, 0), (0.0, 0.01, 0.35), (0.01, 0.0, 0.7), (0.0, 0.0, 0.93)],
                            'r': 0.012, 'colour': 'green', 'tint': (0.95, 1.0, 0.6), 'sides': 5}],
                'leaves': [{'cell': 'l_corn', 'n': 13, 'from': 'stalk', 'z': (0.08, 0.86), 'len': (0.3, 0.42),
                            'elev': (25, 60), 'droop': (1.0, 1.8), 'tint': (1.0, 1.0, 0.65), 'roll': 0.3,
                            'width': 1.8, 'segs': 4, 'fit': False, 'fold': 0.3},
                           {'cell': 'l_corn', 'n': 2, 'from': 'stalk', 'z': (0.9, 0.96), 'len': (0.12, 0.16),
                            'elev': (70, 85), 'droop': (0.2, 0.5), 'tint': (0.95, 1.0, 0.7), 'width': 1.2,
                            'segs': 2, 'fit': False, 'priority': 1.0}],
                'lod_plan': clump.plan(leaf1=0.7, leaf2=0.5)},
    'plant01': {'atlas': 'leafy', 'seed': 101,
                'shell': [shell('s_pothos', 10, 0.3, (0.6, 0.7, 0.5), z=(0.02, 0.45), depth=(0.4, 0.9), tilt=0.5)],
                'leaves': [{'cell': 'l_dieff', 'n': 9, 'from': 'base', 'len': (0.5, 0.9), 'elev': (45, 80),
                            'root_r': 0.15, 'droop': (0.4, 1.0), 'tint': (0.75, 0.85, 0.55), 'roll': 0.5,
                            'width': 0.95, 'segs': 3},
                           {'cell': 'l_spot', 'n': 12, 'from': 'base', 'len': (0.3, 0.5), 'elev': (20, 55),
                            'root_r': 0.35, 'droop': (0.4, 1.0), 'tint': (1.0, 0.95, 0.45), 'roll': 0.5,
                            'width': 1.2, 'segs': 2},
                           {'cell': 'l_spot', 'n': 10, 'from': 'base', 'len': (0.35, 0.6), 'elev': (35, 70),
                            'root_r': 0.25, 'droop': (0.4, 1.0), 'tint': (0.7, 0.8, 0.65), 'roll': 0.5,
                            'width': 1.2, 'segs': 2},
                           {'cell': 'l_blade', 'n': 14, 'from': 'base', 'len': (0.5, 0.9), 'elev': (50, 85),
                            'root_r': 0.3, 'droop': (0.3, 1.0), 'tint': (0.55, 0.62, 0.4), 'roll': 0.4,
                            'width': 0.6, 'segs': 3}],
                'heads': [heads('h_violets', 4, (0.1, 0.13), 'dish', z=(0.05, 0.3), depth=(0.6, 0.9),
                                rise=(40, 80), stem=0, spacing=0.9)]},
    'plant28': {'atlas': 'flowers', 'seed': 2801, 'wind': 0.03,
                'clump': {'cz': 0.72, 'rz': 0.3, 'floor': 0.3},
                'trunk': {'top': 0.42, 'scale': 0.92, 'lobes': 7, 'flare': 0.22, 'tint': (0.78, 0.66, 0.5),
                          'crown_shade': 0.55},
                'shell': [shell('s_shrub', 110, 0.22, (0.85, 0.95, 0.62), z=(0.42, 1.0), depth=(0.62, 1.0),
                                tilt=0.5),
                          shell('s_shrub', 20, 0.26, (0.4, 0.45, 0.3), z=(0.45, 0.85), depth=(0.25, 0.55),
                                tilt=0.6)],
                'lod_plan': clump.plan(card1=0.55, card2=0.3)},
    'plant30': {'atlas': 'flowers', 'seed': 3001, 'wind': 0.03,
                'clump': {'cz': 0.62, 'rz': 0.4, 'floor': 0.3},
                'branches': {'n': 7, 'r': 0.022, 'z': (0.3, 0.6), 'depth': (0.25, 0.55), 'foot': 0.06,
                             'tint': (0.62, 0.48, 0.36)},
                'shell': [shell('s_shrub', 120, 0.21, (0.8, 0.9, 0.5), z=(0.3, 1.0), depth=(0.62, 1.0), tilt=0.5),
                          shell('s_shrub', 20, 0.25, (0.4, 0.42, 0.25), z=(0.3, 0.8), depth=(0.2, 0.55),
                                tilt=0.6)],
                'lod_plan': clump.plan(card1=0.55, card2=0.3)},
    'plant32': {'atlas': 'flowers', 'seed': 3201, 'wind': 0.03,
                'clump': {'cz': 0.55, 'rz': 0.48, 'floor': 0.3},
                'branches': {'n': 9, 'r': 0.014, 'z': (0.2, 0.55), 'depth': (0.2, 0.5), 'foot': 0.03,
                             'tint': (0.62, 0.5, 0.4)},
                'shell': [shell('s_box', 170, 0.17, (0.85, 0.95, 0.7), z=(0.12, 1.0), depth=(0.64, 1.0),
                                tilt=0.5),
                          shell('s_box', 24, 0.22, (0.4, 0.45, 0.3), z=(0.2, 0.85), depth=(0.25, 0.55), tilt=0.6)],
                'lod_plan': clump.plan(card1=0.5, card2=0.28)},
    'plant42': {'atlas': 'flowers', 'seed': 4201, 'wind': 0.03,
                'clump': {'cz': 0.6, 'rz': 0.42, 'floor': 0.3},
                'trunk': {'top': 0.3, 'scale': 0.55, 'lobes': 6, 'flare': 0.2, 'tint': (0.8, 0.68, 0.52),
                          'crown_shade': 0.3, 'min_r': 0.06},
                'branches': {'n': 11, 'r': 0.02, 'z': (0.35, 0.9), 'depth': (0.5, 0.9), 'foot': 0.05,
                             'tint': (0.78, 0.66, 0.5)},
                'shell': [shell('s_box', 100, 0.18, (0.85, 0.95, 0.65), z=(0.15, 1.0), depth=(0.65, 1.0),
                                tilt=0.5)],
                'lod_plan': clump.plan(card1=0.5, card2=0.28)},
    # ---------------------------------------------------------------- dry and mixed (atlas 'leafy')
    'plant48': {'atlas': 'leafy', 'seed': 4801, 'wind': 0.02,
                'clump': {'cz': 0.55, 'rz': 0.5, 'floor': 0.35},
                'branches': {'n': 12, 'r': 0.03, 'z': (0.35, 0.65), 'depth': (0.35, 0.6), 'foot': 0.05,
                             'tint': (0.95, 0.85, 0.65), 'sides': 5, 'forks': 3},
                'shell': [shell('s_twigs', 24, 0.3, (0.85, 0.78, 0.62), z=(0.4, 1.0), depth=(0.7, 1.0),
                                weights='flower')],
                'lod_plan': clump.plan(card1=0.6, card2=0.35)},
    'plant49': {'atlas': 'leafy', 'seed': 4901, 'wind': 0.02,
                'clump': {'cz': 0.5, 'rz': 0.5, 'floor': 0.35, 'ground': 0.5},
                'shell': [shell('s_twigs', 46, 0.5, (0.85, 0.75, 0.6), z=(0.05, 0.95), depth=(0.55, 0.92),
                                weights='flower'),
                          shell('s_twigs', 14, 0.55, (0.55, 0.48, 0.38), z=(0.2, 0.8), depth=(0.15, 0.45),
                                weights='flower')],
                'lod_plan': clump.plan(card1=0.6, card2=0.4)},
    'plant56': {'atlas': 'leafy', 'seed': 5601,
                'leaves': [{'cell': 'l_sword', 'n': 30, 'from': 'base', 'len': (0.55, 0.95), 'elev': (62, 88),
                            'root_r': 0.05, 'root_c': [(-0.05, 0.05), (0.22, -0.08), (-0.3, -0.05), (0.32, 0.1)],
                            'droop': (0.0, 0.4), 'tint': (0.75, 0.8, 0.65), 'roll': 0.35, 'width': 1.3, 'segs': 3,
                            'fit': False},
                           {'cell': 'l_blade', 'n': 30, 'from': 'base', 'len': (0.15, 0.3), 'elev': (35, 80),
                            'root_r': 0.4, 'droop': (0.4, 1.0), 'tint': (0.8, 0.8, 0.6), 'roll': 0.4,
                            'width': 0.7, 'segs': 2, 'fit': False}],
                'shell': [shell('s_ground', 26, 0.22, (0.55, 0.62, 0.42), z=(0.0, 0.12), depth=(0.2, 0.9))],
                'heads': [heads('h_waterlily', 16, (0.045, 0.06), 'dish', z=(0.0, 0.12), depth=(0.3, 0.95),
                                rise=(55, 85), stem=0, spacing=0.9)]},
}


def pads(sid):
    """Lily pads lying flat on the water: plant37 one olive pad, plant38 three pink pads round a closed bud."""
    import math
    import plant_lib as pl
    from mathutils import Vector
    sp = clump.Sprite(sid)
    atlas = pl.Atlas('leafy')
    mat = pl.material('Foliage', 'leafy', cutout=True, roughness=0.55,
                      extras={'openyamm_wind': 0.01, 'openyamm_specular': 0.25, 'openyamm_translucency': 0.2})
    if sid == 'plant37':
        layout = [((0.0, 0.0, 0.0), sp.W * 0.5, 0.4, 'p_green', (0.95, 0.95, 0.9))]
        bud = None
    else:
        r = sp.W * 0.25
        layout = [((math.cos(a) * r * 0.95, math.sin(a) * r * 0.95, 0.004 * i), r, a + math.pi, 'p_pink',
                   (0.9, 0.85, 0.88)) for i, a in enumerate((0.3, 2.4, 4.4))]
        bud = 0.26
    objects = []
    for lod, (segs, rim) in enumerate(((16, True), (10, True), (6, False))):
        g = pl.Geo()
        for centre, radius, turn, cell, tint in layout:
            prof = [(0.0, 0.0), (0.75, 0.0), (1.0, 0.07)] if rim else [(0.0, 0.0), (1.0, 0.03)]
            pl.head(g, atlas, cell, Vector(centre), Vector((0, 0, 1)), radius, None, tint, profile=prof,
                    segments=segs, turn=turn, open_normals=0.0)
        if bud:
            h = bud
            for k in range(2 if lod < 2 else 1):
                a = k * math.pi / 2 + 0.3
                right = Vector((math.cos(a), math.sin(a), 0)) * h * 0.55
                pl.card(g, atlas, 'h_bud', Vector((0, 0, 0)), right, Vector((0, 0, h)), None, (1.0, 0.55, 0.8))
        objects.append(g.to_object(('Plant', 'Plant_LOD1', 'Plant_LOD2')[lod], [mat]))
    return objects


# flowering shrubs: the same shrub with hibiscus heads (tinted per model)
SPECS['plant29'] = dict(SPECS['plant28'], seed=2801, heads=[heads('h_hibiscus', 18, (0.085, 0.105), 'dish',
                        z=(0.45, 1.0), depth=(0.9, 1.02), rise=(15, 55), stem=0, tint=(0.95, 0.93, 0.8))])
SPECS['plant31'] = dict(SPECS['plant30'], seed=3101, heads=[heads('h_hibiscus', 16, (0.11, 0.135), 'dish',
                        z=(0.3, 1.0), depth=(0.92, 1.03), rise=(15, 55), stem=0, tint=(0.95, 0.13, 0.02))])
SPECS['plant33'] = dict(SPECS['plant32'], seed=3301, heads=[heads('h_hibiscus', 32, (0.065, 0.08), 'dish',
                        z=(0.15, 1.0), depth=(0.94, 1.03), rise=(10, 50), stem=0, tint=(0.9, 0.62, 0.04))])


def build(sid):
    if sid in ('plant48', 'plant49'):
        import woody
        return woody.build(sid)
    if sid in ('plant43', 'plant44', 'plant46', 'plant47'):
        import stump
        return stump.build(sid)
    if sid in ('plant50', 'plant51', 'plant52', 'plant53', 'plant54'):
        import cactus
        return cactus.build(sid)
    if sid in ('plant37', 'plant38'):
        return pads(sid)
    spec = SPECS[sid]
    return clump.build(sid, spec, spec['seed'])
