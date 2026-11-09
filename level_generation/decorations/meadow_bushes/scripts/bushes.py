"""Settings of the four meadow bushes, shared by the Blender builder and the system-Python scripts.

Model units are metres at 1/100 of the intended game size (a 1.25 m model is meant for a 125-unit bush); the engine
scales a model to its binding height anyway. Origin at the base centre on the ground, Blender +Z up (glTF +Y).

kind     'mound'   clumps spread over an ellipsoid envelope (round, spreading and broadleaf bushes)
         'sapling' a few thin stems with side branches, clumps along their upper part and at the branch tips
envelope [rx, ry, rz, cz]: ellipsoid radii and centre height (mound); under: lowest clump direction z (foliage
         reaching down to the ground)
clumps   number of clumps on the envelope (plus inner_clumps inside it), [min, max] radius (m)
cards    LOD0 leaf cards, shared among the clumps by their cross-section
cells    atlas cell weights (0, 1 small-leaved sprays, 2 broadleaf clump, 3 open medium spray)
card     [min, max] card edge (m); one card shows one whole 512 px atlas cell
card_up  extra +Z on the card normals (broad leaves lie flatter, facing the sky)
budget   maximum triangles per LOD (LOD0, LOD1, LOD2); the target is LOD0 300-800
keep     fraction of the LOD0 cards kept by LOD1 and LOD2 (the most sky-visible, spread out); grow: their scale
wind     openyamm_wind of the leaves (model units at the top); bark sways a quarter of it"""

TILE = 0.5            # bark texture repeat (m): 512 px over 0.5 m, about the leaves' texel density

BUSHES = {
    'meadow_bush01': {
        'note': 'round dense shrub (box, hawthorn)',
        'kind': 'mound', 'seed': 101,
        'height': 1.25,
        'envelope': [0.64, 0.6, 0.6, 0.64], 'under': -0.75,
        'clumps': 24, 'clump_radius': [0.2, 0.3], 'inner_clumps': 4, 'cards': 290,
        'cells': {0: 0.55, 1: 0.45}, 'card': [0.34, 0.42], 'card_up': 0.15,
        'stems': {'count': 5, 'radius': 0.022, 'sides': 4, 'segments': 3, 'spread': 0.08},
        'budget': [800, 400, 200], 'keep': [1.0, 0.48, 0.22], 'grow': [1.0, 1.3, 1.75],
        'wind': 0.025,
    },
    'meadow_bush02': {
        'note': 'wide spreading shrub',
        'kind': 'mound', 'seed': 202,
        'height': 1.05,
        'envelope': [0.92, 0.78, 0.5, 0.54], 'under': -0.7,
        'clumps': 30, 'clump_radius': [0.2, 0.3], 'inner_clumps': 4, 'cards': 300,
        'cells': {0: 0.4, 1: 0.35, 3: 0.25}, 'card': [0.36, 0.44], 'card_up': 0.25,
        'stems': {'count': 6, 'radius': 0.022, 'sides': 4, 'segments': 3, 'spread': 0.12},
        'budget': [800, 400, 200], 'keep': [1.0, 0.48, 0.22], 'grow': [1.0, 1.3, 1.75],
        'wind': 0.02,
    },
    'meadow_bush03': {
        'note': 'young sapling bush: a few thin stems and an open crown',
        'kind': 'sapling', 'seed': 303,
        'height': 1.8,
        'trunks': 3, 'trunk_radius': 0.026, 'lean': [5, 14], 'branches': [2, 3],
        'clump_radius': [0.14, 0.2], 'cards': 175, 'branch_length': [0.36, 0.55],
        'cells': {3: 0.7, 0: 0.3}, 'card': [0.36, 0.44], 'card_up': 0.2,
        'budget': [800, 400, 200], 'keep': [1.0, 0.5, 0.24], 'grow': [1.0, 1.3, 1.7],
        'wind': 0.04,
    },
    'meadow_bush04': {
        'note': 'low broadleaf clump (bramble, elder undergrowth)',
        'kind': 'mound', 'seed': 404,
        'height': 0.78,
        'envelope': [0.58, 0.52, 0.42, 0.34], 'under': -0.6,
        'clumps': 13, 'clump_radius': [0.2, 0.28], 'inner_clumps': 2, 'cards': 200,
        'cells': {2: 1.0}, 'card': [0.42, 0.52], 'card_up': 0.6,
        'stems': {'count': 3, 'radius': 0.014, 'sides': 4, 'segments': 2, 'spread': 0.1},
        'canes': {'count': 3, 'radius': 0.011, 'reach': [0.55, 0.7], 'rise': [0.55, 0.7], 'clumps': 2},
        'budget': [600, 320, 160], 'keep': [1.0, 0.5, 0.25], 'grow': [1.0, 1.3, 1.7],
        'wind': 0.015,
    },
}
