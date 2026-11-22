"""Parameters of the water fall built by build_fall.py (a copy of the sand-fall's builder, see its docstring). Every
distance is in map units (81.7 per metre); the GLB is written in metres. The model's origin is the lip: the top of the
notch's edge, at the middle of the fall, with the channel behind it (-out) and the drop in front (+out, glTF +Z:
facing 90 pours toward -X, west), as the sand-fall (level_generation/decorations/xeen_sandfall_claude/README.md).

XD-17 Shangri-La (D-50 Q7): a white fall from a notch 1,728 up the east cliff into the cold pool at -32 (a drop of
1,760), pouring west. The water leaves the lip at about 200 units/s and falls under the game's gravity (9.81 m/s^2 =
800 units/s^2): out = 10.5 x sqrt(drop), 105 out at 100 below the lip, 330 at 1,000, 440 at the pool."""

WATERFALL = {
    'output': 'xeen_deco_waterfall.glb',
    'seed': 50,
    # Centre-line (out, up): a short channel in the notch (220 inland, nearly level), over the edge, then the free-fall
    # parabola out = 10.5 sqrt(drop) down to 100 under the pool's surface (hidden by the water).
    'path': [(-220, -8), (-120, -4), (-40, 0), (10, -3), (44, -18), (74, -50), (105, -100), (148, -200),
             (210, -400), (257, -600), (332, -1000), (378, -1300), (420, -1600), (440, -1760), (453, -1860)],
    # Width at a drop (negative: inland): the notch channel 360, the lip 420, spreading to 660 at the pool.
    'width': [(-220, 360), (-60, 400), (0, 420), (300, 450), (900, 540), (1500, 630), (1860, 680)],
    # The water's hump over the lip, and the channel's sides sunk below it.
    'bulge': [(-220, 4), (-80, 14), (0, 20), (200, 10), (600, 4), (1860, 0)],
    'sink': [(-220, 10), (-40, 10), (120, 0), (1860, 0)],
    'v0': 120.0, 'tongue_accel': 60.0, 'gravity': 800.0,
    'rows': 48,
    # The pool's surface (drop below the lip): the foam and mist stand on it.
    'foot': 1760,
    # Core: blended, lit, a little emissive (aerated water scatters light: keeps it white in the cliff's shade).
    # Nine lanes split between 450 and 800 below the lip into strands; lanes whose end lies below `bottom` stay
    # open under the pool, the others taper to points in the air above it.
    'core': {'texture': 'core', 'scroll': 0.34, 'lanes': 9, 'columns_per_lane': 2,
             'split': (450, 800), 'end': (1500, 2300), 'bottom': 1860,
             'colour': [1.0, 1.0, 1.0, 1.0], 'specular': 0.35, 'translucency': 0.5,
             'emissive': {'factor': [0.16, 0.18, 0.18]}},
    'core_first': True,
    # Spray veils: additive, faded by COLOR_0, just outside the core, building up as the water breaks.
    'haze': [
        {'texture': 'spray', 'scroll': 0.30, 'drift': 0.0, 'gravity': 700.0, 'offset': 22, 'width': 1.15,
         'start': 60, 'fade_in': 900, 'full_until': 1600, 'end': 1860, 'u_tiles': 1.0, 'columns': 8, 'rows': 30,
         'colour': [0.30, 0.32, 0.32, 1.0], 'translucency': 0.3},
        {'texture': 'spray', 'scroll': 0.22, 'drift': 0.01, 'gravity': 600.0, 'offset': 60, 'width': 1.45,
         'start': 500, 'fade_in': 800, 'full_until': 1650, 'end': 1860, 'u_tiles': 1.4, 'columns': 6, 'rows': 22,
         'colour': [0.20, 0.21, 0.21, 1.0], 'translucency': 0.3},
    ],
    # Foam ring on the pool around the foot (additive): radius 40-560, a little longer toward the pool (+out).
    'foam': {'texture': 'foam', 'lift': 4, 'r0': 40, 'r1': 560, 'stretch': 0.25, 'rings': 10, 'segments': 32,
             'fade_in': 0.12, 'full_until': 0.35, 'u_tiles': 6.0, 'period': 420.0, 'scroll': 0.12, 'drift': 0.0,
             'colour': [0.36, 0.38, 0.38, 1.0], 'translucency': 0.2},
    # Mist billowing up from the foot (additive cone shells), centred a little out from the foot, drifting up.
    'mist': [
        {'texture': 'mist', 'lift': -10, 'height': 620, 'r0': 150, 'r1': 420, 'shift': 30, 'rows': 10,
         'segments': 24, 'fade_in': 0.08, 'full_until': 0.25, 'u_tiles': 3.0, 'period': 700.0, 'scroll': 0.10,
         'drift': 0.015, 'colour': [0.26, 0.27, 0.27, 1.0], 'translucency': 0.4},
        {'texture': 'mist', 'lift': -10, 'height': 900, 'r0': 260, 'r1': 600, 'shift': 60, 'rows': 10,
         'segments': 24, 'fade_in': 0.10, 'full_until': 0.2, 'u_tiles': 4.0, 'period': 900.0, 'scroll': 0.07,
         'drift': -0.01, 'colour': [0.14, 0.15, 0.15, 1.0], 'translucency': 0.4},
    ],
    # Sheet normal: mostly outward and up (a cliff-face fall lit from the valley side).
    'normal': (0.55, 0.835),
    'textures': {
        # sRGB white water with a pale blue-green body (aerated streaks, clear gaps between them).
        'core': {'size': (512, 1024), 'rgb': (0.86, 0.94, 0.95), 'rgb_spread': 0.10, 'alpha': 0.92, 'base': 0.62,
                 'weights': (0.34, 0.20, 0.10), 'edge_fade': 0.10, 'streak_u': 2.5, 'streak_v': 70.0,
                 'clump_v': 140.0},
        'spray': {'size': (512, 1024), 'rgb': (0.90, 0.96, 0.97), 'rgb_spread': 0.06, 'alpha': 0.75, 'base': 0.50,
                  'weights': (0.30, 0.28, 0.10), 'streak_u': 4.0, 'streak_v': 50.0, 'clump_v': 110.0},
        'foam': {'size': (512, 512), 'rgb': (0.92, 0.97, 0.97), 'rgb_spread': 0.05, 'alpha': 0.85, 'base': 0.50,
                 'weights': (0.34, 0.26, 0.18), 'streak_u': 5.0, 'streak_v': 8.0, 'clump_v': 30.0},
        'mist': {'size': (512, 512), 'rgb': (0.90, 0.95, 0.96), 'rgb_spread': 0.04, 'alpha': 0.70, 'base': 0.50,
                 'weights': (0.30, 0.30, 0.04), 'streak_u': 14.0, 'streak_v': 18.0, 'clump_v': 40.0},
    },
}

PRESETS = {'waterfall': WATERFALL}


# XD-17 as built (A5's L4, 2026-11-21): the east cliff is no sheer face but a 49-56 degree slope of triangulated rock
# from the notch's crest point (7664, 2815, 1941) through the mid ring (7005, 2573, 906) to the cliff foot
# (6272, 2304, 0), then grass to the pool (surface -40) about 140 further on. The fall is a cascade sliding down that
# slope (normal clearance 26), the rock's profile measured from devdocs/xeen/briefs/xd17/L4/rooms.yml's floor points;
# fit_xd17.py then moves the origin to the foot point and lifts every vertex that sits under the real rock.
_SLOPE = [(-80, -3), (-30, -1), (0, 0), (100, -147), (200, -295), (300, -442), (400, -590), (500, -737), (600, -885),
          (702, -1035), (800, -1149), (900, -1265), (1000, -1381), (1100, -1497), (1200, -1613), (1300, -1729),
          (1400, -1845), (1483, -1937), (1560, -1948), (1620, -1962), (1660, -1990), (1690, -2030)]
WATERFALL_XD17 = dict(WATERFALL)
WATERFALL_XD17.update({
    'output': 'xeen_deco_waterfall.glb',
    'path': _SLOPE,
    # The notch lets out about 300; the sheet spreads to 600 at the foot and 640 into the pool.
    'width': [(-80, 260), (0, 300), (400, 340), (1000, 440), (1600, 560), (2030, 640)],
    'bulge': [(-80, 6), (0, 14), (150, 26), (2030, 26)],
    'sink': [(-80, 4), (0, 0), (150, -12), (2030, -12)],
    'v0': 120.0, 'tongue_accel': 60.0, 'gravity': 800.0,
    'foot': 1981,
    'core': dict(WATERFALL['core'], split=(900, 1400), end=(2100, 2500), bottom=2030),
    'haze': [
        dict(WATERFALL['haze'][0], start=80, fade_in=700, full_until=1700, end=1990, offset=40),
        dict(WATERFALL['haze'][1], start=400, fade_in=700, full_until=1750, end=1990, offset=80),
    ],
    'foam': dict(WATERFALL['foam'], r1=380, stretch=0.1),
    'normal': (0.8, 0.6),
})
PRESETS['waterfall_xd17_s9'] = dict(WATERFALL_XD17)


# Session 10 (A5's placed look, output/studio_cal/xd17/shots/s20_falls/): the game's static shader does not apply
# COLOR_0, so the vertex fades never reached the game: the mist cones' top rims showed as hard lines and bands, the
# veils' sides as edges. Their fades now live in the textures (build_fall.bake_fades): mist and foam map v once over
# their height / radius (`baked`, no v scroll, u drift kept for the swirl); the veils keep their downward scroll with a
# side fade across u. Also: a stream down the gully behind the notch (it wells up out of the ground 760 inland,
# fit_xd17.py BURY_BEYOND), the strands run on over the grass strip and drop over the pool's bank (the edge 140 out
# from the foot), and the veils start lower so their top edges sit inside the white water.
_STREAM = [(-760, 222), (-700, 229), (-600, 197), (-500, 165), (-400, 133), (-300, 102), (-200, 70), (-100, 38),
           (-50, 21), (0, 0)]
_SLOPE10 = _STREAM + [pt for pt in _SLOPE if pt[0] > 0 and pt[0] <= 1483] + [
    (1540, -1935), (1600, -1935), (1620, -1940), (1632, -1962), (1650, -1990), (1690, -2030)]
WATERFALL_XD17 = dict(WATERFALL_XD17)
WATERFALL_XD17.update({
    'path': _SLOPE10,
    'width': [(-760, 110), (-400, 140), (-150, 200), (0, 300), (400, 340), (1000, 440), (1600, 560), (2030, 640)],
    'bulge': [(-760, 4), (-80, 6), (0, 14), (150, 26), (2030, 26)],
    'sink': [(-760, 4), (-80, 4), (0, 0), (150, -12), (2030, -12)],
    'rows': 64,
    'haze': [
        dict(WATERFALL['haze'][0], start=250, fade_in=700, full_until=1700, end=1990, offset=40, u_tiles=1.0,
             drift=0.0),
        dict(WATERFALL['haze'][1], start=500, fade_in=700, full_until=1750, end=1990, offset=80, u_tiles=1.0,
             drift=0.0),
    ],
    'foam': dict(WATERFALL['foam'], r1=380, stretch=0.1, baked=True, texture='foam_baked', scroll=0.0,
                 drift=0.01),
    'mist': [
        dict(WATERFALL['mist'][0], height=520, r1=380, baked=True, texture='mist1', scroll=0.0, u_tiles=2.0,
             drift=0.012, colour=[0.22, 0.23, 0.23, 1.0]),
        dict(WATERFALL['mist'][1], height=700, r1=520, baked=True, texture='mist2', scroll=0.0, u_tiles=3.0,
             drift=-0.008, colour=[0.12, 0.13, 0.13, 1.0]),
    ],
})
WATERFALL_XD17['textures'] = dict(WATERFALL['textures'])
WATERFALL_XD17['textures'].update({
    'spray': dict(WATERFALL['textures']['spray'], u_fade=0.4),
    'foam_baked': dict(WATERFALL['textures']['foam'], v_fade=[0.12, 0.35, 1.4]),
    'mist1': dict(WATERFALL['textures']['mist'], v_fade=[0.10, 0.20, 1.8]),
    'mist2': dict(WATERFALL['textures']['mist'], v_fade=[0.12, 0.18, 1.8]),
})
PRESETS['waterfall_xd17'] = WATERFALL_XD17


# Session 11 (A5's s22 shots, output/studio_cal/xd17/shots/s22_falls/05, 06): from the cliff top the top of the fall
# was a broad pale band, the white core running the whole gully at 200-300 wide, with a ruler-straight brink and its
# sides climbing the gully walls ("ears"). Now:
# - a clear-water `stream` layer (blended, soft sides; ripples smooth across, so no dark stripe runs down it) carries the gully and runs on under the white water to 700 below
#   the brink, narrowing to a quarter;
# - the water goes over the brink clear and glassy; the white core starts below it, each lane at its own drop between
#   20 and 190 (middle lanes first) at 12 % of its width, widening over 220, so the white begins as streaks breaking
#   out of the tongue (tries: lanes starting at the brink as points read as white spikes from the cliff top, at 40 %
#   width as blunt teeth, and the crest itself flashed white);
# - the stream is narrow (40 where it wells up, 110-130 in the gully, 180 at the brink) and follows the gully's
#   measured centre (`shift`, up to 55 to the left of the fall's centre line), so its sides no longer ride the walls.
WATERFALL_XD17_S10 = dict(WATERFALL_XD17)
PRESETS['waterfall_xd17_s10'] = WATERFALL_XD17_S10
WATERFALL_XD17 = dict(WATERFALL_XD17_S10)
WATERFALL_XD17.update({
    'path': [(-760, 200), (-700, 212)] + _SLOPE10[2:],     # the spring's first 60 a little under the gully floor
    'width': [(-760, 10), (-600, 100), (-300, 120), (-100, 120), (-50, 140), (0, 180), (150, 250), (400, 330),
              (1000, 440), (1600, 560), (2030, 640)],
    'shift': [(-760, -40), (-300, -55), (-200, -40), (-100, -22), (-50, -10), (0, 0)],
    'bulge': [(-760, 2), (-80, 4), (0, 10), (150, 24), (2030, 26)],
    'sink': [(-760, 2), (-80, 2), (0, 0), (150, -12), (2030, -12)],
    'core': dict(WATERFALL_XD17_S10['core'], start=(20, 110), start_bias=80.0, grow=220.0, start_width=0.12),
    'stream': {'texture': 'stream', 'start': -760, 'end': 700, 'taper_from': 250, 'rows': 72, 'columns': 6,
               'offset': -4, 'width': 1.0, 'scroll': 0.30, 'colour': [1.0, 1.0, 1.0, 1.0], 'specular': 0.3,
               'translucency': 0.4},
})
WATERFALL_XD17['textures'] = dict(WATERFALL_XD17_S10['textures'])
WATERFALL_XD17['textures']['stream'] = {
    'size': (256, 1024), 'rgb': (0.56, 0.80, 0.84), 'rgb_spread': 0.10, 'alpha': 0.95, 'base': 0.46,
    'weights': (0.16, 0.12, 0.08), 'streak_u': 14.0, 'streak_v': 30.0, 'clump_v': 90.0, 'u_fade': 0.32}
PRESETS['waterfall_xd17'] = WATERFALL_XD17
