"""Way-up columns of the elemental planes (D-58 C5/C7; A6's planes P1-P3): parameters for build_column.py.
The outer haze shells were dropped after the first in-game look (their silhouettes read as hard tube edges).
Units are map units (81.7 per metre). Each shell: radius r0 at the foot to r1 at the top, `height`, `rows` x
`segments`, faded in over `fade_in` (fraction of the height) and out after `full_until`, its texture tiled `u_tiles`
times round and `period` units per tile up, scrolling up `scroll` tiles a second (drifting sideways `drift`).

- P3 the dust shaft (`xeen_wayup_earth`): a column of pale light where dust streams upward out of the bowl, over A6's
  pale stone disc (radius 176) in its ring of standing stones (at 300); the bowl's sky is about 2,400 over the disc.
- P2 the updraft (`xeen_wayup_air`): mist streaming straight up from the ring of white stones (disc radius 176, stones
  at 288), into the open sky.
- P1 the heat column (`xeen_wayup_fire`): heat and embers rising in front of the molten sheet on the gully's back wall
  (A6's exit panel, 268 wide, 900 high): half an ellipse standing against the wall, +z away from it."""

GOLD = (1.0, 0.93, 0.74)

EARTH = {
    'output': 'xeen_deco_wayup_earth.glb',
    'seed': 3,
    'shells': [
        # the light: a soft core, bright at the foot
        {'texture': 'glow', 'r0': 120, 'r1': 135, 'height': 2400, 'rows': 16, 'segments': 24, 'fade_in': 0.03,
         'full_until': 0.45, 'u_tiles': 2.0, 'period': 900.0, 'scroll': 0.05, 'colour': [0.028, 0.026, 0.02, 1.0],
         'emissive': {'factor': [0.012, 0.011, 0.008]}},
        # dust streaming up the column
        {'texture': 'dust', 'r0': 150, 'r1': 175, 'height': 2400, 'rows': 16, 'segments': 28, 'fade_in': 0.02,
         'full_until': 0.55, 'u_tiles': 3.0, 'period': 520.0, 'scroll': 0.42, 'drift': 0.01,
         'colour': [0.05, 0.044, 0.032, 1.0], 'emissive': {'factor': [0.008, 0.007, 0.005]}},
        {'texture': 'motes', 'r0': 110, 'r1': 165, 'height': 2400, 'rows': 16, 'segments': 24, 'fade_in': 0.02,
         'full_until': 0.6, 'u_tiles': 2.0, 'period': 400.0, 'scroll': 0.65, 'drift': -0.02,
         'colour': [0.26, 0.23, 0.17, 1.0], 'emissive': {'factor': [0.07, 0.06, 0.045]}},
    ],
    'textures': {
        'glow': {'size': (256, 512), 'rgb': GOLD, 'rgb_spread': 0.05, 'alpha': 0.8, 'base': 0.35,
                 'weights': (0.20, 0.20, 0.0), 'streak_u': 10.0, 'streak_v': 60.0, 'clump_v': 120.0},
        'dust': {'size': (512, 512), 'rgb': (0.93, 0.84, 0.66), 'rgb_spread': 0.08, 'alpha': 0.85, 'base': 0.08,
                 'weights': (0.40, 0.30, 0.10), 'streak_u': 3.0, 'streak_v': 40.0, 'clump_v': 90.0},
        'motes': {'kind': 'specks', 'size': (256, 256), 'rgb': (1.0, 0.94, 0.78), 'alpha': 1.0, 'blur': 1.3,
                  'stretch': 2.5, 'threshold': 2.4, 'softness': 0.6},
        'haze': {'size': (256, 256), 'rgb': (0.92, 0.86, 0.72), 'rgb_spread': 0.03, 'alpha': 0.6, 'base': 0.5,
                 'weights': (0.30, 0.30, 0.0), 'streak_u': 14.0, 'streak_v': 30.0, 'clump_v': 60.0},
    },
}

AIR = {
    'output': 'xeen_deco_wayup_air.glb',
    'seed': 2,
    'shells': [
        {'texture': 'wisp', 'r0': 140, 'r1': 170, 'height': 2000, 'rows': 16, 'segments': 28, 'fade_in': 0.03,
         'full_until': 0.5, 'u_tiles': 3.0, 'period': 600.0, 'scroll': 0.55, 'drift': 0.04,
         'colour': [0.13, 0.14, 0.15, 1.0], 'emissive': {'factor': [0.02, 0.022, 0.024]}},
        {'texture': 'wisp', 'r0': 90, 'r1': 140, 'height': 2000, 'rows': 16, 'segments': 24, 'fade_in': 0.03,
         'full_until': 0.45, 'u_tiles': 2.0, 'period': 750.0, 'scroll': 0.75, 'drift': -0.05,
         'colour': [0.09, 0.10, 0.11, 1.0]},
    ],
    'textures': {
        'wisp': {'size': (512, 512), 'rgb': (0.92, 0.96, 1.0), 'rgb_spread': 0.04, 'alpha': 0.85, 'base': 0.12,
                 'weights': (0.45, 0.30, 0.05), 'streak_u': 4.0, 'streak_v': 60.0, 'clump_v': 110.0},
        'haze': {'size': (256, 256), 'rgb': (0.92, 0.96, 1.0), 'rgb_spread': 0.03, 'alpha': 0.6, 'base': 0.5,
                 'weights': (0.30, 0.30, 0.0), 'streak_u': 14.0, 'streak_v': 30.0, 'clump_v': 60.0},
    },
}

FIRE = {
    'output': 'xeen_deco_wayup_fire.glb',
    'seed': 1,
    # Session 10 (A6's 21st look): the heat shells' ends showed as a pale grey-olive band over the dark rock: COLOR_0's
    # side fade does not reach the game, and a pale yellow at low strength reads grey there. Now the heat texture
    # carries the side fade itself (u_fade; u_tiles 1, no drift) and is amber, so its faint edge reads warm.
    'shells': [
        # heat rising off the molten sheet: half-ellipses against the wall (+z out), 300 wide
        {'texture': 'heat', 'r0': 250, 'r1': 300, 'wide': 1.0, 'deep': 0.45, 'front_only': True, 'height': 1400,
         'rows': 14, 'segments': 16, 'fade_in': 0.04, 'full_until': 0.5, 'u_tiles': 1.0, 'period': 500.0,
         'scroll': 0.60, 'drift': 0.0, 'colour': [0.22, 0.16, 0.09, 1.0],
         'emissive': {'factor': [0.20, 0.13, 0.07]}},
        {'texture': 'heat', 'r0': 190, 'r1': 250, 'wide': 1.0, 'deep': 0.75, 'front_only': True, 'height': 1400,
         'rows': 14, 'segments': 16, 'fade_in': 0.04, 'full_until': 0.4, 'u_tiles': 1.0, 'period': 650.0,
         'scroll': 0.80, 'drift': 0.0, 'colour': [0.16, 0.115, 0.065, 1.0],
         'emissive': {'factor': [0.14, 0.10, 0.05]}},
        {'texture': 'embers', 'r0': 200, 'r1': 290, 'wide': 1.0, 'deep': 0.6, 'front_only': True, 'height': 1400,
         'rows': 14, 'segments': 16, 'fade_in': 0.02, 'full_until': 0.55, 'u_tiles': 1.5, 'period': 380.0,
         'scroll': 0.95, 'drift': 0.02, 'colour': [1.0, 0.55, 0.20, 1.0],
         'emissive': {'factor': [1.0, 0.6, 0.25], 'strength': 3.0}},
    ],
    'textures': {
        'heat': {'size': (256, 512), 'rgb': (1.0, 0.78, 0.46), 'rgb_spread': 0.08, 'alpha': 0.8, 'base': 0.02,
                 'weights': (0.60, 0.30, 0.05), 'streak_u': 3.0, 'streak_v': 45.0, 'clump_v': 90.0, 'u_fade': 0.25},
        'embers': {'kind': 'specks', 'size': (256, 256), 'rgb': (1.0, 0.82, 0.50), 'alpha': 1.0, 'blur': 1.4,
                   'stretch': 3.0, 'threshold': 2.3, 'softness': 0.5},
    },
}

PRESETS = {'earth': EARTH, 'air': AIR, 'fire': FIRE}
