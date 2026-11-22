"""Parameters of the falls built by build_fall.py (one entry per installed model). Every distance is in map units
(81.7 per metre); the GLB is written in metres. The model's origin is the lip: the rim edge's top, at the middle of
the fall, with the land behind it (-out) and the drop in front (+out, glTF +Z: facing 90 pours toward -X, west).

A new fall (X7's lava falls) is a new entry: its colours, textures, scroll and shape. Additive layers can fade to
nothing through COLOR_0 (the engine multiplies the base colour by it but never its alpha), so the haze sheets carry
the bottom fade; the blended core cannot, and frays into tapering strands instead (README, "Why strands")."""

SANDFALL = {
    'output': 'xeen_deco_sandfall.glb',
    'seed': 31,
    # Centre-line of the core (out, up) from the buried inland end of the tongue over the edge (0, 0) down the drop.
    # Its run of about 0.55 per unit of drop keeps ~100 units clear of a rim cell's terrain slope (one 512 cell down
    # from 1,024 in X5, 0.5; X6's 1,300-1,700 lips are steeper), then it turns vertical below the rim's foot.
    'path': [(-450, -28), (-300, -18), (-150, -8), (-40, 0), (40, -12), (110, -50), (170, -120), (240, -250),
             (330, -430), (430, -630), (530, -820), (630, -1010), (720, -1200), (800, -1400), (870, -1620),
             (920, -1850), (950, -2080), (965, -2300)],
    # Width (side to side) at a drop (negative: the tongue's distance inland).
    'width': [(-450, 560), (-200, 720), (0, 800), (300, 730), (900, 800), (1600, 900), (2300, 980)],
    # Tongue crest above the centre-line (along the sheet normal) and the sides sunk below it, by drop.
    'bulge': [(-450, 0), (-330, 34), (-120, 58), (0, 60), (200, 46), (600, 30), (2300, 20)],
    'sink': [(-450, 20), (-60, 20), (120, 0), (2300, 0)],
    # Flow speed (units per second) along the path: v0 at the tongue's inland end, the tongue's own acceleration,
    # then gravity (scaled: sand streams look slower than a free fall) along the drop.
    'v0': 45.0, 'tongue_accel': 22.0, 'gravity': 520.0,
    'rows': 46,                    # core rows along the path (denser near the lip)
    # Core: blended, lit. Lanes across the texture (their borders are transparent) end as strands between these drops.
    'core': {'texture': 'core', 'scroll': 0.30, 'lanes': 7, 'columns_per_lane': 2,
             'split': (450, 650), 'end': (800, 1250),
             'colour': [1.0, 1.0, 1.0, 1.0], 'specular': 0.05, 'translucency': 0.45},
    # Haze sheets: additive, faded by COLOR_0; offset outward from the core, wider, slower, ending in nothing.
    'haze': [
        {'texture': 'haze', 'scroll': 0.22, 'drift': 0.0, 'gravity': 380.0, 'offset': 40, 'width': 1.12,
         'start': -20, 'fade_in': 260, 'full_until': 650, 'end': 2250, 'u_tiles': 1.0, 'columns': 8, 'rows': 34,
         'colour': [0.32, 0.32, 0.32, 1.0], 'translucency': 0.15},
        {'texture': 'haze', 'scroll': 0.15, 'drift': 0.012, 'gravity': 300.0, 'offset': 95, 'width': 1.38,
         'start': 120, 'fade_in': 520, 'full_until': 900, 'end': 2300, 'u_tiles': 1.6, 'columns': 6, 'rows': 26,
         'colour': [0.16, 0.16, 0.16, 1.0], 'translucency': 0.15},
    ],
    # Dust lifting off the lip (additive), built when the key is 'plume'. Off: over a bright sky an additive plume can
    # only lighten, and read as white spray in X5 (review/ingame1).
    # Dust lifting off the lip (additive): its curve (out, up) from just behind the edge, width by fraction of its
    # length, faded in over 'foot' and out after 'full_until'; V is distance over 'period', so the drift up it is
    # scroll x period units per second (72 here).
    'plume_off': {'path': [(-80, -10), (40, 60), (160, 170), (320, 290), (520, 400), (760, 470)],
              'width': [(0.0, 760), (1.0, 1350)], 'foot': 0.14, 'full_until': 0.22, 'rows': 16, 'columns': 8,
              'period': 600.0, 'scroll': 0.12, 'drift': 0.02, 'u_tiles': 1.3,
              'colour': [0.22, 0.22, 0.22, 1.0], 'translucency': 0.4},
    # Sheet normal for lighting: mostly up, a little outward, for every vertex (both sides of a veil of falling
    # grains light alike; the shader does not flip normals on back faces).
    'normal': (0.35, 0.94),
    'textures': {
        # sRGB sand: X6's desert terrain (engine sand_ripples mean colour 0.76 0.63 0.47), a touch paler in the air.
        'core': {'size': (512, 1024), 'rgb': (0.80, 0.67, 0.49), 'rgb_spread': 0.16, 'alpha': 0.95, 'base': 0.80,
                 'weights': (0.24, 0.22, 0.12), 'edge_fade': 0.14, 'streak_u': 3.5, 'streak_v': 60.0, 'clump_v': 120.0},
        # The haze is added to what is behind it: a darker, more saturated sand keeps it from reading as white spray.
        'haze': {'size': (512, 1024), 'rgb': (0.74, 0.58, 0.38), 'rgb_spread': 0.10, 'alpha': 0.70, 'base': 0.55,
                 'weights': (0.30, 0.26, 0.08), 'streak_u': 6.0, 'streak_v': 80.0, 'clump_v': 160.0},
    },
}

# X7's lava falls (D-40): three on the lava cove's south wall (lip about 2,350 high, the world rim below), pouring
# north, faces toward the signature camera on the cove's west lip. The sand-fall's shape with a shorter tongue; viscous:
# slower flow and scroll, three wide lanes that stay an unbroken sheet far down before they fray; the core glows (its
# own streak texture as the emission map, dark crust streaks in it), the haze sheets are additive heat glow.
LAVAFALL = dict(SANDFALL)
LAVAFALL.update({
    'output': 'xeen_deco_lavafall.glb',
    'seed': 40,
    'path': [(-300, -18), (-150, -8), (-40, 0), (40, -12), (110, -50), (170, -120), (240, -250),
             (330, -430), (430, -630), (530, -820), (630, -1010), (720, -1200), (800, -1400), (870, -1620),
             (920, -1850), (950, -2080), (965, -2300)],
    'width': [(-300, 520), (-120, 640), (0, 700), (300, 660), (900, 700), (1600, 760), (2300, 820)],
    'bulge': [(-300, 0), (-200, 30), (-80, 50), (0, 52), (200, 40), (600, 26), (2300, 18)],
    'sink': [(-300, 18), (-60, 18), (120, 0), (2300, 0)],
    'v0': 30.0, 'tongue_accel': 14.0, 'gravity': 300.0,
    'core': {'texture': 'core', 'scroll': 0.16, 'lanes': 3, 'columns_per_lane': 3,
             'split': (900, 1200), 'end': (1500, 2100),
             'colour': [0.55, 0.22, 0.10, 1.0], 'specular': 0.15, 'translucency': 0.2,
             'emissive': {'factor': [1.0, 0.42, 0.10], 'strength': 1.6}},
    'haze': [
        {'texture': 'haze', 'scroll': 0.10, 'drift': 0.0, 'gravity': 240.0, 'offset': 40, 'width': 1.15,
         'start': -20, 'fade_in': 200, 'full_until': 900, 'end': 2250, 'u_tiles': 1.0, 'columns': 8, 'rows': 34,
         'colour': [0.42, 0.13, 0.03, 1.0], 'translucency': 0.1},
        {'texture': 'haze', 'scroll': 0.07, 'drift': 0.01, 'gravity': 200.0, 'offset': 95, 'width': 1.45,
         'start': 100, 'fade_in': 450, 'full_until': 1100, 'end': 2300, 'u_tiles': 1.6, 'columns': 6, 'rows': 26,
         'colour': [0.22, 0.06, 0.01, 1.0], 'translucency': 0.1},
    ],
    'textures': {
        # sRGB molten rock: yellow-orange, darker crust streaks through it (a wide spread of the streak noise).
        'core': {'size': (512, 1024), 'rgb': (1.0, 0.50, 0.12), 'rgb_spread': 0.55, 'alpha': 0.98, 'base': 0.88,
                 'weights': (0.18, 0.16, 0.08), 'edge_fade': 0.10, 'streak_u': 5.0, 'streak_v': 90.0,
                 'clump_v': 180.0},
        'haze': {'size': (512, 1024), 'rgb': (1.0, 0.42, 0.10), 'rgb_spread': 0.10, 'alpha': 0.70, 'base': 0.55,
                 'weights': (0.30, 0.26, 0.08), 'streak_u': 6.0, 'streak_v': 80.0, 'clump_v': 160.0},
    },
})

PRESETS = {'sandfall': SANDFALL, 'lavafall': LAVAFALL}
