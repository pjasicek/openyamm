"""Shared geometry and texture layout of the MM6 Reactor (plain Python, used by Blender and the texture painter).

Units are metres with one native logical pixel = 1 cm, measured from the side silhouette of the restored front frame
(mm6_rea/aligned_2x/reasta00.png): radius = half-width per row, height above the sprite's ground row. Front = -Y.
A profile is a list of sections; a section is a list of (r, z) points, smooth inside, hard at section joins.
Profiles run from the bottom/inside along the visible surface: the face normal is (dz, -dr) in the (r, z) plane.
"""
import math

# Segments by silhouette size (guidelines section 1): large shells, the bowl and cup, small turned parts, thin rods.
# Quality budget (user, 2026-10-13): the Reactor is alone in its room with at most a few Kreegans, so silhouettes
# get more segments than a crowd creature would.
SEG = 48
SEG_MID = 32
SEG_SMALL = 16
SEG_ROD = 8
METAL_SIZE = 2048
GLOW_SIZE = 1024
GLASS_SIZE = 512

# ---------------------------------------------------------------- lathe parts (r, z)
# Guidelines (level_generation/GAME_ASSET_MODELLING_GUIDELINES.md): straight walls carry only their end rings; thin
# lips that would be long slivers on a 32-segment ring (band lip, lid rim, spire collar) are normal-map detail;
# faces hidden under other parts (the skirt's top under the band) are not modelled.
SKIRT = [[(1.00, 0.0), (1.00, 0.025)], [(1.00, 0.025), (0.848, 0.215)]]
BAND = [[(0.845, 0.215), (0.845, 0.488)], [(0.845, 0.488), (0.79, 0.488)]]
# The dome is split at z 1.025: its top ring (DomeTop) is replaced by the torn crown in the wreck.
DOME = [[(0.80, 0.488), (0.797, 0.56), (0.785, 0.64), (0.758, 0.72), (0.718, 0.80), (0.665, 0.88),
         (0.605, 0.955), (0.54, 1.025)]]
DOME_TOP = [[(0.54, 1.025), (0.475, 1.095), (0.462, 1.115)]]
CAP = [[(0.462, 1.115), (0.43, 1.165), (0.37, 1.215), (0.29, 1.258), (0.205, 1.285)]]
SPIRE = [[(0.205, 1.285), (0.15, 1.32), (0.10, 1.365), (0.068, 1.41), (0.05, 1.45), (0.024, 1.48)]]
SPIRE_ROD = ((0.0, 0.0, 1.475), (0.0, 0.0, 1.80), 0.024)   # thin rods: separate 6-sided tubes
LOWER_BALL = ((0.0, 0.0, 1.835), 0.045)
UPPER_BALL = ((0.0, 0.0, 2.22), 0.045)
ARC_BOTTOM, ARC_TOP = 1.876, 2.178
ARC_CENTRE = (0.0, 0.0, 2.03)

NOZZLE_ROD = ((0.0, 0.0, 2.255), (0.0, 0.0, 2.525), 0.024)
NOZZLE = [[(0.024, 2.52), (0.036, 2.52)], [(0.036, 2.52), (0.06, 2.54)],
          [(0.06, 2.54), (0.06, 2.60)], [(0.06, 2.60), (0.08, 2.62)],
          [(0.08, 2.62), (0.10, 2.67), (0.14, 2.72), (0.20, 2.76), (0.27, 2.79), (0.36, 2.83), (0.41, 2.865)]]
# The bowl is split at z 3.00: its lower part (BowlLower) is replaced by torn petals in the wreck.
BOWL_LOWER = [[(0.41, 2.865), (0.46, 2.895), (0.52, 2.945), (0.57, 3.00)]]
BOWL = [[(0.57, 3.00), (0.61, 3.06), (0.64, 3.12), (0.655, 3.17)]]
BOWL_RING = [[(0.655, 3.17), (0.672, 3.185), (0.672, 3.205), (0.648, 3.218)]]
GLASS = [(0.65, 3.218), (0.675, 3.26), (0.698, 3.33), (0.715, 3.42), (0.728, 3.52), (0.738, 3.62),
         (0.752, 3.72), (0.762, 3.80), (0.765, 3.858)]
# Lid: band with the display, flared rim, then the top (seen only from above: two rings and a strip-triangulated
# centre cap, no 32-spoke fan).
LID = [[(0.765, 3.858), (0.80, 3.876)], [(0.80, 3.876), (0.80, 4.06)], [(0.80, 4.06), (0.90, 4.18)],
       [(0.90, 4.18), (0.62, 4.23), (0.32, 4.262)]]
LID_CAP_Z = 4.262
CHAMBER_PIVOT = (0.0, 0.0, 4.30)
LIQUID_BASE = 3.205
LIQUID_LEVELS = {'Liq100': 3.76, 'Liq60': 3.50, 'Liq25': 3.31}


def glass_radius(z):
    pts = GLASS
    if z <= pts[0][1]:
        return pts[0][0]
    for (r0, z0), (r1, z1) in zip(pts, pts[1:]):
        if z <= z1:
            return r0 + (r1 - r0) * (z - z0) / (z1 - z0)
    return pts[-1][0]


# Screens (front, theta 0): band window and lid window, as (radius, half angle, z0, z1).
BAND_SCREEN = (0.853, 0.54, 0.255, 0.43)
LID_SCREEN = (0.808, 0.50, 3.905, 4.035)

# Control plate on the dome front (centre x, centre z, width, height); flat, tangent to the dome there.
PLATE = (0.04, 0.80, 0.46, 0.36)
# Lamps in plate coordinates (x right, y up, metres from the plate centre): kind, x, y, size.
LAMPS = [('LampRed', 'red', -0.12, 0.08, 0.032), ('LampG1', 'green', -0.12, -0.10, 0.03),
         ('LampG2', 'green', 0.12, -0.085, 0.03)]

# Arms: shoulder (x, z) of the image-left (-X) arm; segment lengths; the +X arm mirrors x.
LOWER_SHOULDER = (-0.66, 0.83)
LOWER_LENGTHS = (0.55, 0.56, 0.50)
UPPER_SHOULDER = (-0.43, 2.90)
UPPER_LENGTHS = (0.50, 0.40, 0.22)

# ---------------------------------------------------------------- texture atlas rectangles (x, y, w, h)
# Image coordinates, origin top-left. Lathe strips map the part's top to the rectangle's top row; u runs from the
# front centre (u = 0) to the back (u = 1) on both sides (mirrored), except the glass (full circle).
# Metal atlas: every rectangle sized from the part's real dimensions (metres, at the strip's reference radius) and
# one shared texel density, scaled up until the shelf packing fills the 2K atlas (guidelines section 4). Parts seen
# rarely carry a lower factor (lid top, inner liner); the control plate a higher one (read up close).
METAL_SPECS = {  # name: (width m, height m, density factor)
    'skirt': (math.pi * 0.93, 0.25, 1.0), 'band': (math.pi * 0.845, 0.33, 1.0), 'dome': (math.pi * 0.70, 0.73, 1.0),
    'cap': (math.pi * 0.35, 0.29, 1.0), 'bowl': (math.pi * 0.55, 0.41, 1.0), 'lid': (math.pi * 0.85, 0.96, 0.8),
    'lidtop': (0.64, 0.64, 0.5), 'inner': (math.pi * 0.65, 0.95, 0.3), 'nozzle': (math.pi * 0.15, 0.40, 1.0),
    'spire': (math.pi * 0.10, 0.29, 1.0), 'plate': (0.46, 0.36, 2.0), 'plain': (0.15, 0.15, 1.0),
    'screen': (0.30, 0.08, 1.0), 'strut': (0.07, 0.75, 1.0), 'ring': (math.pi * 0.66, 0.07, 1.0),
    'rod': (0.13, 0.60, 1.0), 'hub_black': (0.20, 0.20, 1.0), 'hub_white': (0.20, 0.20, 1.0),
    'bulb': (0.20, 0.20, 1.0), 'tip': (0.12, 0.20, 1.0), 'debris': (0.30, 0.30, 1.0), 'hole': (0.30, 0.20, 1.0),
}
PACK_GAP = 8


def pack(specs, size, density):
    """Shelf packing, tallest first; returns {name: (x, y, w, h)} or None when it does not fit."""
    items = sorted(((max(16, int(math.ceil(w * density * f))), max(16, int(math.ceil(h * density * f))), n)
                    for n, (w, h, f) in specs.items()), key=lambda t: (-t[1], -t[0]))
    rects = {}; x = y = 0; shelf = 0
    for w, h, n in items:
        if w > size:
            return None
        if x + w > size:
            x = 0; y += shelf + PACK_GAP; shelf = 0
        if y + h > size:
            return None
        rects[n] = (x, y, w, h); x += w + PACK_GAP; shelf = max(shelf, h)
    return rects


def _fit(specs, size):
    lo, hi = 100.0, 2000.0
    for _ in range(40):
        mid = (lo + hi) / 2
        if pack(specs, size, mid): lo = mid
        else: hi = mid
    return lo, pack(specs, size, lo)


DENSITY, METAL_RECTS = _fit(METAL_SPECS, METAL_SIZE)
GLOW_RECTS = {
    'liquid_side': (0, 0, 512, 256),
    'liquid_top':  (512, 0, 256, 256),
    'cap_glow':    (768, 0, 256, 128),
    'bowl_glow':   (768, 128, 256, 128),
    'band_wave1':  (0, 256, 512, 96), 'band_wave2': (0, 352, 512, 96), 'band_wave3': (0, 448, 512, 96),
    'lid_wave1':   (512, 256, 512, 96), 'lid_wave2': (512, 352, 512, 96), 'lid_wave3': (512, 448, 512, 96),
    'lamp_red':    (0, 560, 64, 64),
    'lamp_green':  (64, 560, 64, 64),
    'arc':         (128, 560, 128, 64),
    'goo':         (256, 560, 256, 256),
}

# Panels around each shell (seams between panels, a panel centred on the front).
PANELS = {'skirt': 24, 'band': 16, 'dome': 12, 'cap': 8, 'lid': 16, 'bowl': 12}


def profile_lengths(profile):
    """Cumulative arc length at every section boundary, and the total."""
    marks = [0.0]
    total = 0.0
    for section in profile:
        for (r0, z0), (r1, z1) in zip(section, section[1:]):
            total += math.hypot(r1 - r0, z1 - z0)
        marks.append(total)
    return marks, total
