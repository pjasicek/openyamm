"""Paint the Reactor's textures procedurally in the exact UV layout of reactor_geometry.py.

Shell rectangles are painted in world space: every texel row is mapped back to its profile arc length s and radius
r (the same formula as reactor_geometry.lathe), and every column to the angle theta, so rivets and seams are round
and evenly spaced on the model. A height field (seams, rivets, hatches, bezels) gives the normal map (glTF, +Y up)
and a cavity occlusion for the ORM red channel.

Outputs (textures/): rea_metal_basecolor_2k.png, rea_metal_normal_1k.png, rea_metal_orm_1k.png,
rea_material_classes_1k.png, rea_glow_1k.png, rea_glass_512.png. Base colour stays within sRGB 30-243
(GAME_ASSET_MODELLING_GUIDELINES.md section 5); metallic is 1 on steel/chrome and 0 on paint, screens and plastic."""
import math
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'scripts'))
import reactor_layout as L  # noqa: E402
import reactor_geometry as G  # noqa: E402

OUT = os.path.join(HERE, 'textures')
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(6)
S = L.METAL_SIZE

albedo = np.zeros((S, S, 3), np.float32)
height = np.zeros((S, S), np.float32)
rough = np.full((S, S), 0.45, np.float32)
metal = np.zeros((S, S), np.float32)
classes = np.zeros((S, S), np.uint8)
px_w = np.full((S, S), 1.0 / L.DENSITY, np.float32)   # world metres per texel, horizontal
px_h = np.full((S, S), 1.0 / L.DENSITY, np.float32)   # vertical

STEEL = np.array([188, 190, 193], np.float32)
CHROME = np.array([214, 216, 220], np.float32)
COPPER_SEAM = np.array([120, 70, 42], np.float32)
# The metal ships unlit with baked light (see the bake below); ORM/normal maps are kept as records for a lit variant.
METAL_SHELL = 1.0


def blur(a, sx, sy):
    """Gaussian blur with sigma sx along x (columns) and sy along y (rows), wrapping like the panels do."""
    return ndimage.gaussian_filter(a.astype(np.float32), (sy, sx), mode='nearest')


def noise(h, w, sx, sy, amp):
    n = rng.standard_normal((h, w)).astype(np.float32)
    n = blur(n, sx, sy)
    n /= (np.abs(n).max() + 1e-6)
    return n * amp


def lathe_map(rect, pieces):
    """pieces: [(profile, v_span)] as built by reactor_geometry. Returns per-row arrays s (global arc length, metres),
    r, section-start flags and the rectangle's (x, y, w, h)."""
    x, y, w, h = L.METAL_RECTS[rect]
    rows_s = np.full(h, np.nan); rows_r = np.full(h, np.nan); rows_sec = np.full(h, -1); rows_z = np.full(h, np.nan)
    base_s = 0.0
    for profile, v_span in pieces:
        marks, total = L.profile_lengths(profile)
        gaps = G.GAP * (len(profile) - 1) / max(h, 1)
        span = v_span[1] - v_span[0]
        for si, section in enumerate(profile):
            acc = [0.0]
            for (r0, z0), (r1, z1) in zip(section, section[1:]):
                acc.append(acc[-1] + math.hypot(r1 - r0, z1 - z0))
            for k in range(400):
                f = k / 399
                d = f * acc[-1]
                i = min(np.searchsorted(acc, d, side='right') - 1, len(section) - 2)
                tseg = (d - acc[i]) / max(acc[i + 1] - acc[i], 1e-9)
                r = section[i][0] + (section[i + 1][0] - section[i][0]) * tseg
                zz = section[i][1] + (section[i + 1][1] - section[i][1]) * tseg
                t = (marks[si] + d) / total
                tv = (t * (1.0 - gaps) + gaps * si / max(len(profile) - 1, 1)) if len(profile) > 1 else t
                v = v_span[0] + span * (1.0 - tv)
                row = int(min(h - 1, max(0, v * h)))
                rows_s[row] = base_s + marks[si] + d; rows_r[row] = r; rows_sec[row] = si; rows_z[row] = zz
        base_s += total
    # fill gap rows from the nearest painted row (padding)
    idx = np.where(~np.isnan(rows_s))[0]
    for row in range(h):
        if np.isnan(rows_s[row]):
            j = idx[np.argmin(np.abs(idx - row))]
            rows_s[row], rows_r[row], rows_sec[row], rows_z[row] = rows_s[j], rows_r[j], rows_sec[j], rows_z[j]
    lathe_map.z = rows_z
    return rows_s, rows_r, rows_sec, (x, y, w, h)


def paint_shell(rect, pieces, panels, base, rivet_rows=(), seams=True, brushed=True, rivet_seams=True,
                chrome=False, grime_bottom=0.0, mirrored=True):
    s, r, sec, (x, y, w, h) = lathe_map(rect, pieces)
    u = (np.arange(w) + 0.5) / w
    theta = u * math.pi if mirrored else u * 2 * math.pi - math.pi
    TH = np.broadcast_to(theta[None, :], (h, w))
    R = np.broadcast_to(r[:, None], (h, w))
    Sg = np.broadcast_to(s[:, None], (h, w))
    hgt = np.zeros((h, w), np.float32)
    col = np.broadcast_to(base, (h, w, 3)).copy()
    col *= (1.0 + noise(h, w, 18, 1.5, 0.035) if brushed else 1.0 + noise(h, w, 6, 6, 0.02))[..., None]
    if seams and panels:
        step = 2 * math.pi / panels
        k = np.round((TH - step / 2) / step)
        th_seam = step / 2 + k * step
        dist = np.abs(TH - th_seam) * R            # world distance to the nearest seam
        seam = np.clip(1.0 - dist / 0.0055, 0, 1)
        hgt -= 0.0016 * seam
        col = col * (1 - 0.85 * seam[..., None]) + COPPER_SEAM * 0.85 * seam[..., None]
        # rust streak running down from each seam
        streak = np.clip(1.0 - dist / 0.012, 0, 1) * (0.5 + 0.5 * noise(h, w, 1.5, 25, 1.0))
        col = col * (1 - 0.12 * streak[..., None]) + np.array([120, 80, 55]) * 0.12 * streak[..., None]
        if rivet_seams:
            for off in (-0.014, 0.014):
                sk = np.round(Sg / 0.06) * 0.06
                d = np.sqrt(((TH - th_seam) * R - off) ** 2 + (Sg - sk) ** 2)
                riv = np.clip(1.0 - (d / 0.0045) ** 2, 0, 1)
                hgt += 0.0022 * np.sqrt(riv)
                col = col * (1 - 0.25 * (riv > 0)[..., None]) + np.array([205, 205, 205]) * 0.25 * (riv > 0)[..., None]
    for s_row, pitch in rivet_rows:
        ck = np.round(TH * R / pitch) * pitch
        d = np.sqrt((TH * R - ck) ** 2 + (Sg - s_row) ** 2)
        riv = np.clip(1.0 - (d / 0.0045) ** 2, 0, 1)
        hgt += 0.0022 * np.sqrt(riv)
        line = np.clip(1.0 - np.abs(Sg - (s_row + 0.012)) / 0.002, 0, 1)
        hgt -= 0.0008 * line
        col = col * (1 - 0.5 * line[..., None]) + COPPER_SEAM * 0.5 * line[..., None]
    if grime_bottom:
        smax = s.max()
        g = np.clip(1.0 - Sg / (0.35 * smax), 0, 1) * grime_bottom
        col *= (1 - 0.35 * g[..., None])
    # small dents and scratches
    col *= (1.0 + noise(h, w, 40, 40, 0.05))[..., None]
    albedo[y:y + h, x:x + w] = col
    height[y:y + h, x:x + w] = hgt
    rough[y:y + h, x:x + w] = (0.22 if chrome else 0.38) + noise(h, w, 30, 30, 0.06)
    metal[y:y + h, x:x + w] = METAL_SHELL
    classes[y:y + h, x:x + w] = 9
    px_w[y:y + h, x:x + w] = np.maximum(R * (math.pi if mirrored else 2 * math.pi) / w, 1e-4)
    px_h[y:y + h, x:x + w] = max((s.max() - s.min()) / h, 1e-4)
    return s, r, (x, y, w, h), TH, R, Sg


def rect_fill(rect, color, metallic, roughness, cls, grain=0.03):
    x, y, w, h = L.METAL_RECTS[rect]
    col = np.broadcast_to(np.array(color, np.float32), (h, w, 3)).copy()
    col *= (1.0 + noise(h, w, 4, 4, grain))[..., None]
    albedo[y:y + h, x:x + w] = col
    metal[y:y + h, x:x + w] = metallic
    rough[y:y + h, x:x + w] = roughness
    classes[y:y + h, x:x + w] = cls
    return x, y, w, h


# ------------------------------------------------------------------------------------------------ shells
paint_shell('skirt', [(L.SKIRT, (0.0, 1.0))], L.PANELS['skirt'], STEEL, grime_bottom=0.6,
            rivet_rows=[(L.profile_lengths(L.SKIRT)[1] - 0.025, 0.06)])
band_total = L.profile_lengths(L.BAND)[1]
s, r, (x, y, w, h), TH, R, Sg = paint_shell('band', [(L.BAND, (0.0, 1.0))], L.PANELS['band'], STEEL,
                                            rivet_rows=[(0.02, 0.06), (0.255, 0.06)])
# Band screen bezel: a darker recessed frame around the window, rivets at its corners.
rs, half, z0, z1 = L.BAND_SCREEN
sz0, sz1 = z0 - 0.215, z1 - 0.215
inside = (TH < half + 0.03 / rs) & (Sg > sz0 - 0.025) & (Sg < sz1 + 0.025)
window = (TH < half) & (Sg > sz0) & (Sg < sz1)
frame_ = inside & ~window
albedo[y:y + h, x:x + w][frame_] *= 0.62
height[y:y + h, x:x + w][frame_] -= 0.002
albedo[y:y + h, x:x + w][window] = (32, 36, 46)     # behind the screen patch: dark, so no steel shows through

dome_len = L.profile_lengths(L.DOME)[1]; top_len = L.profile_lengths(L.DOME_TOP)[1]
split = top_len / (dome_len + top_len)
s, r, (x, y, w, h), TH, R, Sg = paint_shell('dome', [(L.DOME, (split, 1.0)), (L.DOME_TOP, (0.0, split))],
                                            L.PANELS['dome'], STEEL,
                                            rivet_rows=[(0.02, 0.06), (dome_len - 0.03, 0.06)])
# Back service hatch (HD master 02_back): rectangular groove at the back centre, four screws, a handle.
ZH0, ZH1, HW = 0.17, 0.34, 0.20
c = (math.pi - TH) * R
groove = (np.abs(np.abs(c) - HW / 2) < 0.004) & (Sg > ZH0) & (Sg < ZH1) | \
         ((np.abs(Sg - ZH0) < 0.004) | (np.abs(Sg - ZH1) < 0.004)) & (np.abs(c) < HW / 2 + 0.004)
height[y:y + h, x:x + w][groove] -= 0.003
albedo[y:y + h, x:x + w][groove] *= 0.45
for cx in (-HW / 2 + 0.02, HW / 2 - 0.02):
    for cz in (ZH0 + 0.02, ZH1 - 0.02):
        d = np.sqrt((c - cx) ** 2 + (Sg - cz) ** 2)
        scr = np.clip(1 - (d / 0.008) ** 2, 0, 1)
        height[y:y + h, x:x + w] += 0.002 * np.sqrt(scr)
handle = (np.abs(c) < 0.04) & (np.abs(Sg - (ZH0 + ZH1) / 2) < 0.008)
height[y:y + h, x:x + w][handle] += 0.004
albedo[y:y + h, x:x + w][handle] *= 0.8

paint_shell('cap', [(L.CAP, (0.0, 1.0))], 0, CHROME * 0.82, seams=False, brushed=False, chrome=True)
bl = L.profile_lengths(L.BOWL)[1]; bll = L.profile_lengths(L.BOWL_LOWER)[1]
bsplit = bl / (bl + bll)
s, r, (x, y, w, h), TH, R, Sg = paint_shell('bowl', [(L.BOWL_LOWER, (bsplit, 1.0)), (L.BOWL, (0.0, bsplit))], 0,
                                            CHROME * 0.78, seams=False, brushed=False, chrome=True)
# Grille: radial and ring grooves (visible when the blue glow is off, as in the native hit frames).
grille = (np.abs(((TH * R) % 0.05) - 0.025) > 0.022) | (np.abs((Sg % 0.04) - 0.02) > 0.018)
height[y:y + h, x:x + w][grille] -= 0.0012
albedo[y:y + h, x:x + w][grille] *= 0.55

lid_len = L.profile_lengths(L.LID)[1]
s, r, (x, y, w, h), TH, R, Sg = paint_shell('lid', [(L.LID, (0.0, 1.0))], L.PANELS['lid'], STEEL,
                                            rivet_rows=[(0.05, 0.06), (0.20, 0.06), (0.27, 0.07)])
rs, half, z0, z1 = L.LID_SCREEN
m0 = L.profile_lengths([L.LID[0]])[1]
sz0, sz1 = m0 + (z0 - 3.876), m0 + (z1 - 3.876)
inside = (TH < half + 0.03 / rs) & (Sg > sz0 - 0.022) & (Sg < sz1 + 0.022)
window = (TH < half) & (Sg > sz0) & (Sg < sz1)
frame_ = inside & ~window
albedo[y:y + h, x:x + w][frame_] *= 0.62
height[y:y + h, x:x + w][frame_] -= 0.002
albedo[y:y + h, x:x + w][window] = (32, 36, 46)

# Lid top (planar, seen only from above): plain steel, radial seams, a bolt ring.
x, y, w, h = rect_fill('lidtop', STEEL, 1.0, 0.4, 9)
yy, xx = np.mgrid[0:h, 0:w]
dx, dy = (xx + 0.5) / w - 0.5, (yy + 0.5) / h - 0.5
rad = np.sqrt(dx * dx + dy * dy) * 2 * 0.32
ang = np.arctan2(dy, dx)
radial = np.abs(((ang + math.pi) % (math.pi / 4)) - math.pi / 8) * rad < 0.004
albedo[y:y + h, x:x + w][radial] = COPPER_SEAM
height[y:y + h, x:x + w][radial] -= 0.0015
ring = np.abs(rad - 0.25) < 0.004
height[y:y + h, x:x + w][ring] += 0.0015
px_w[y:y + h, x:x + w] = 0.64 / w; px_h[y:y + h, x:x + w] = 0.64 / h

rect_fill('inner', (46, 46, 50), 1.0, 0.7, 9)
paint_shell('nozzle', [(L.NOZZLE, (0.0, 1.0))], 0, CHROME * 0.85, seams=False, brushed=False, chrome=True)
paint_shell('spire', [(L.SPIRE, (0.0, 1.0))], 0, CHROME * 0.85, seams=False, brushed=False, chrome=True)

# Struts and bowl ring: steel with a rivet line down the middle face.
# Struts (u across the three outer faces, v along): a rivet line down the middle face every 8 cm.
x, y, w, h = rect_fill('strut', STEEL * 0.95, 1.0, 0.35, 9)
yy, xx = np.mgrid[0:h, 0:w]
mpp = 0.75 / h
for k in np.arange(0.04, 0.75, 0.08):
    d = np.sqrt(((xx + 0.5) - w / 2) ** 2 + ((yy + 0.5) - k / mpp) ** 2) * mpp
    height[y:y + h, x:x + w] += 0.0018 * np.sqrt(np.clip(1 - (d / 0.005) ** 2, 0, 1))
px_w[y:y + h, x:x + w] = 0.07 / w; px_h[y:y + h, x:x + w] = mpp
paint_shell('ring', [(L.BOWL_RING, (0.0, 1.0))], 0, STEEL * 0.95, seams=False)

rect_fill('rod', CHROME * 0.9, 1.0, 0.2, 9)
rect_fill('bulb', CHROME, 1.0, 0.18, 9)
rect_fill('tip', STEEL * 0.8, 1.0, 0.35, 9)
for name, color, dot_color in (('hub_black', (36, 36, 40), (150, 150, 150)), ('hub_white', (226, 226, 220), (40, 40, 44))):
    x, y, w, h = rect_fill(name, color, 0.0, 0.45, 11)
    yy, xx = np.mgrid[0:h, 0:w]
    # disc faces use planar UVs over the whole rectangle: a centre dot and a bevel ring (native elbow discs)
    d = np.sqrt((xx + 0.5 - w / 2) ** 2 + (yy + 0.5 - h / 2) ** 2) / (w / 2)
    albedo[y:y + h, x:x + w][d < 0.28] = dot_color
    ring = (d > 0.82) & (d < 0.92)
    albedo[y:y + h, x:x + w][ring] *= 0.75
    height[y:y + h, x:x + w][ring] -= 0.001
# Torn, scorched steel (crown, petals, debris): darker, rough, sooty blotches.
x, y, w, h = rect_fill('debris', STEEL * 0.55, 1.0, 0.7, 9)
albedo[y:y + h, x:x + w] *= (0.55 + 0.45 * np.abs(noise(h, w, 8, 8, 1.0)))[..., None]
rect_fill('hole', (34, 30, 28), 0.0, 0.9, 11)
rect_fill('screen', (32, 36, 46), 0.0, 0.12, 11, grain=0.01)
rect_fill('plain', (176, 178, 176), 0.0, 0.5, 11)

# Control plate (front face; u right, v down): light grey paint, lamp sockets, small gauges, border bevel.
x, y, w, h = rect_fill('plate', (198, 200, 196), 0.0, 0.5, 11)
pw, ph = L.PLATE[2], L.PLATE[3]
yy, xx = np.mgrid[0:h, 0:w]
lx = ((xx + 0.5) / w - 0.5) * pw; ly = (0.5 - (yy + 0.5) / h) * ph
edge = (np.abs(lx) > pw / 2 - 0.012) | (np.abs(ly) > ph / 2 - 0.012)
height[y:y + h, x:x + w][edge] -= 0.002
albedo[y:y + h, x:x + w][edge] *= 0.8
for name, kind, cx, cy, sz in L.LAMPS:
    d = np.maximum(np.abs(lx - cx), np.abs(ly - cy)) if kind == 'green' else np.hypot(lx - cx, ly - cy)
    sock = d < sz * 0.62
    albedo[y:y + h, x:x + w][sock] = (52, 22, 20) if kind == 'red' else (20, 46, 26)
    ring = (d >= sz * 0.62) & (d < sz * 0.8)
    albedo[y:y + h, x:x + w][ring] = (90, 90, 92)
# gauges: two small dark squares with needle lines, a divider line (as on the native plate)
for gx, gy, gs in ((0.12, 0.08, 0.06), (0.03, -0.01, 0.045)):
    g = (np.abs(lx - gx) < gs / 2) & (np.abs(ly - gy) < gs / 2)
    albedo[y:y + h, x:x + w][g] = (70, 72, 74)
    needle = g & (np.abs((lx - gx) - (ly - gy) * 0.6) < 0.0025)
    albedo[y:y + h, x:x + w][needle] = (225, 225, 225)
div = (np.abs(ly + 0.035) < 0.002) & (lx > -0.18) & (lx < 0.2)
albedo[y:y + h, x:x + w][div] = (110, 110, 112)
height[y:y + h, x:x + w][div] -= 0.001
px_w[y:y + h, x:x + w] = pw / w; px_h[y:y + h, x:x + w] = ph / h

# ------------------------------------------------------------------------------------------------ native shading
# The shells are surfaces of revolution measured from the restored front frame, so each front texel (|theta| < 90 deg)
# sees one sprite pixel: x = r sin(theta), height z. The sprite is drawn fullbright ("Lit" frames) with polished
# chrome shading; its masked, low-passed luminance becomes the shells' brightness, times the painted detail
# (seams, rivets, grime) as a high-pass ratio. The back half mirrors the front. The actor always faces the party, so
# the baked front light stays where the sprite had it (NATIVE_SHADING_TRANSFER.md, by direct projection).
SPRITE = np.asarray(Image.open(os.path.join(HERE, '..', 'mm6_rea', 'aligned_2x', 'reasta00.png')).convert('RGBA'),
                    np.float32)
GROUND_ROW, PIVOT_X = 915, 340
sp_rgb = SPRITE[..., :3] / 255.0
sp_lum = sp_rgb @ np.array([0.2126, 0.7152, 0.0722])
mx, mn = sp_rgb.max(-1), sp_rgb.min(-1)
sat = (mx - mn) / np.maximum(mx, 1e-3)
valid = (SPRITE[..., 3] > 200) & (sat < 0.30)          # metal only: no screens, glows, liquid, lamps
valid = ndimage.binary_erosion(valid, iterations=2)
SIG = 5.0                                              # 2.5 cm at 2 px/cm
num = ndimage.gaussian_filter(np.where(valid, sp_lum, 0.0), SIG)
den = ndimage.gaussian_filter(valid.astype(np.float32), SIG)
native_lum = num / np.maximum(den, 1e-3)
native_ok = den > 0.15


def native_level(z0, z1, rmax):
    """Median native metal luminance of the sprite between heights z0..z1, over the central |x| < 0.6 r."""
    vals = []
    for Y in range(int(GROUND_ROW - 200 * z1), int(GROUND_ROW - 200 * z0) + 1):
        x0, x1 = int(PIVOT_X - 120 * rmax), int(PIVOT_X + 120 * rmax) + 1
        ok = valid[Y, x0:x1]
        vals.extend(sp_lum[Y, x0:x1][ok].tolist())
    return float(np.median(vals)) if vals else 0.55


VIEW = np.array([0.0, -0.96, -0.28]) / np.linalg.norm([0.0, -0.96, -0.28])   # toward the party's low eye


def chrome(ndv, nz):
    """Polished chrome seen from the front: bright centre, a darker reflected horizon band, a rim light, brighter
    upward faces (the look of the native pre-rendered metal)."""
    return (0.62 + 0.50 * np.clip((ndv - 0.72) / 0.26, 0, 1) ** 1.5
            - 0.42 * np.exp(-((ndv - 0.45) / 0.15) ** 2)
            + 0.28 * np.exp(-((ndv - 0.14) / 0.08) ** 2)
            + 0.12 * nz)


def native_shade(rect, pieces, level_range, gain=1.0, floor=0.10):
    """Brightness = analytic chrome response (true lathe normals) scaled to the sprite's median metal level over
    level_range (z0, z1), times the painted detail (high-pass ratio)."""
    s_, r_, sec_, (x, y, w, h) = lathe_map(rect, pieces)
    z_ = lathe_map.z
    dr = np.gradient(r_); dz = np.gradient(z_)
    nr, nz = -dz, dr                                   # rows run down the profile: outward normal
    ln = np.maximum(np.hypot(nr, nz), 1e-6); nr, nz = nr / ln, nz / ln
    # smooth like vertex-normal interpolation across the piecewise-linear profile (no banding per segment)
    sig = max(2.0, h / 30.0)
    nr = ndimage.gaussian_filter1d(nr, sig, mode='nearest'); nz = ndimage.gaussian_filter1d(nz, sig, mode='nearest')
    ln = np.maximum(np.hypot(nr, nz), 1e-6); nr, nz = nr / ln, nz / ln
    u = (np.arange(w) + 0.5) / w
    th = u * math.pi
    N = np.stack([nr[:, None] * np.sin(th)[None, :], -nr[:, None] * np.cos(th)[None, :],
                  np.broadcast_to(nz[:, None], (h, w))], -1)
    ndv = np.clip(N @ VIEW, 0, 1)
    shade = chrome(ndv, N[..., 2])
    # chrome parts whose sprite rows are mostly glass or background keep at least a polished-metal level
    level = max(native_level(level_range[0], level_range[1], float(np.nanmax(r_))), 0.40)
    target = shade / max(float(np.median(shade[ndv > 0.3])) if (ndv > 0.3).any() else 1.0, 1e-3) * level
    a = albedo[y:y + h, x:x + w]
    lum = a @ np.array([0.2126, 0.7152, 0.0722]) / 255.0
    detail = lum / np.maximum(ndimage.gaussian_filter(lum, 6.0), 1e-3)
    new_lum = np.clip(target * gain * detail, floor, 0.95)
    albedo[y:y + h, x:x + w] = a * (new_lum / np.maximum(lum, 1e-3))[..., None]
    return level


SHADE_GAIN = 1.1
levels = {
    'skirt': native_shade('skirt', [(L.SKIRT, (0.0, 1.0))], (0.03, 0.20), SHADE_GAIN),
    # the band's own sprite rows are mostly its display; it is the dome's silver in the native frames
    'band': native_shade('band', [(L.BAND, (0.0, 1.0))], (0.50, 0.60), SHADE_GAIN),
    'dome': native_shade('dome', [(L.DOME, (split, 1.0)), (L.DOME_TOP, (0.0, split))], (0.50, 0.60), SHADE_GAIN),
    'lid': native_shade('lid', [(L.LID, (0.0, 1.0))], (4.06, 4.16), SHADE_GAIN),
    'bowl': native_shade('bowl', [(L.BOWL_LOWER, (bsplit, 1.0)), (L.BOWL, (0.0, bsplit))], (3.05, 3.16),
                         SHADE_GAIN * 0.9),
    'nozzle': native_shade('nozzle', [(L.NOZZLE, (0.0, 1.0))], (2.66, 2.80), SHADE_GAIN),
    'spire': native_shade('spire', [(L.SPIRE, (0.0, 1.0))], (1.30, 1.42), SHADE_GAIN),
}
print('native metal levels', {k: round(v, 3) for k, v in levels.items()})

# ------------------------------------------------------------------------------------------------ write metal maps
def dilate_into_gutters(img, mask, iterations=12):
    """Pad colours into the empty gutters so mip levels do not pull in black (guidelines section 4)."""
    out = img.copy(); m = mask.copy()
    for _ in range(iterations):
        grown = m.copy(); acc = np.zeros_like(out); cnt = np.zeros(m.shape, np.float32)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            sm = np.roll(m, (dy, dx), (0, 1)); so = np.roll(out, (dy, dx), (0, 1))
            add = sm & ~m
            acc[add] += so[add]; cnt[add] += 1
            grown |= sm
        new = grown & ~m
        out[new] = acc[new] / np.maximum(cnt[new], 1)[..., None] if out.ndim == 3 else acc[new] / np.maximum(cnt[new], 1)
        m = grown
    return out


used = classes > 0
# Normal map from height (world units per texel per region), glTF convention: +X right, +Y up the image.
hx = (np.roll(height, -1, 1) - np.roll(height, 1, 1)) / (2 * px_w)
hy = (np.roll(height, 1, 0) - np.roll(height, -1, 0)) / (2 * px_h)   # up the image = row - 1
hx = np.clip(hx, -3, 3); hy = np.clip(hy, -3, 3)
n = np.stack([-hx, -hy, np.ones_like(hx)], -1)
n /= np.linalg.norm(n, axis=-1, keepdims=True)

# Baked lighting. The native Reactor frames are fullbright ("Lit"), and the Hive's room light is dim, so the metal is
# an unlit material (fix_gltf.py) whose texture carries the light: the transferred native shading above, the relief
# of seams and rivets lit from above (tangent +Y is up on every part), and chrome-cylinder shading on the round
# small parts (u runs around them: a bright stripe toward the front and back, dark flanks).
relief = np.clip(0.80 + 0.45 * n[..., 1] + 0.25 * (n[..., 2] - 1.0) * 2.0, 0.45, 1.25)
albedo *= relief[..., None]
for name, axis in (('rod', 'u'), ('tip', 'u'), ('strut', 'u')):
    x, y, w, h = L.METAL_RECTS[name]
    u = (np.arange(w) + 0.5) / w
    stripe = 0.35 + 0.75 * np.abs(np.cos(2 * math.pi * u)) ** 0.8 if name != 'strut' else \
        0.55 + 0.5 * np.exp(-((u - 0.5) / 0.25) ** 2)
    albedo[y:y + h, x:x + w] *= stripe[None, :, None]
x, y, w, h = L.METAL_RECTS['bulb']        # spheres: u around (front at 0.5), v from top to bottom
u = (np.arange(w) + 0.5) / w; v = (np.arange(h) + 0.5) / h
front = np.cos(2 * math.pi * (u - 0.5))[None, :] * np.sin(math.pi * v)[:, None]
albedo[y:y + h, x:x + w] *= (0.35 + 0.8 * np.clip(front, 0, 1) ** 0.7 + 0.25 * (1 - v)[:, None])[..., None]

albedo = np.clip(albedo, 30, 243)
alb = dilate_into_gutters(albedo, used)
Image.fromarray(np.clip(alb, 0, 255).astype(np.uint8)).save(os.path.join(OUT, 'rea_metal_basecolor_2k.png'))
nimg = dilate_into_gutters(((n * 0.5 + 0.5) * 255).astype(np.float32), used)
Image.fromarray(nimg.astype(np.uint8)).resize((1024, 1024), Image.LANCZOS).save(
    os.path.join(OUT, 'rea_metal_normal_1k.png'))

# Cavity occlusion from the height field (grooves darker), roughness, metallic: glTF ORM.
cav = height - blur(height, 6, 6)
ao = np.clip(1.0 + cav * 260.0, 0.45, 1.0)
orm = np.stack([ao, np.clip(rough, 0.05, 1.0), metal], -1) * 255
orm = dilate_into_gutters(orm.astype(np.float32), used)
Image.fromarray(orm.astype(np.uint8)).resize((1024, 1024), Image.LANCZOS).save(os.path.join(OUT, 'rea_metal_orm_1k.png'))
Image.fromarray(classes).resize((1024, 1024), Image.NEAREST).save(os.path.join(OUT, 'rea_material_classes_1k.png'))

# ------------------------------------------------------------------------------------------------ glow atlas (unlit)
GS = L.GLOW_SIZE
glow = np.zeros((GS, GS, 3), np.float32)


def grect(name):
    return L.GLOW_RECTS[name]


x, y, w, h = grect('liquid_side')
base = np.array([58, 236, 76], np.float32)
cells = noise(h, w, 6, 6, 1.0) + 0.5 * noise(h, w, 2.5, 2.5, 1.0)
col = base[None, None] * (0.80 + 0.30 * cells)[..., None]
col += np.array([150, 40, 140]) * np.clip(cells - 0.35, 0, 1)[..., None] * 1.6     # pale cell crests
col *= np.linspace(1.08, 0.70, h)[:, None, None]      # darker toward the bottom of the chamber
glow[y:y + h, x:x + w] = col
x, y, w, h = grect('liquid_top')
blobs = noise(h, w, 7, 7, 1.0)
glow[y:y + h, x:x + w] = base[None, None] * (0.95 + 0.25 * blobs)[..., None] + \
    np.array([120, 40, 110]) * np.clip(blobs - 0.4, 0, 1)[..., None]
for name in ('cap_glow', 'bowl_glow'):
    # Dark blue chrome lit from inside: a bright core toward the front, at the cap's top and the bowl's bottom
    # (native reasta frames). Unlit, and the actor faces the party, so the core stays in front like the sprite's.
    x, y, w, h = grect(name)
    yy, xx = np.mgrid[0:h, 0:w]
    u = (xx + 0.5) / w; v = (yy + 0.5) / h
    t = (1.0 - v) if name == 'cap_glow' else v
    core = np.exp(-(u / (0.28 if name == 'cap_glow' else 0.22)) ** 2) * np.exp(-((1.0 - t) / 0.45) ** 2)
    rim = (0.25 + 0.35 * np.exp(-(u / 0.6) ** 2)) * (1.0 if name == 'cap_glow' else 0.55)
    k = np.clip(rim + 1.1 * core, 0, 1.4)
    col = np.stack([18 + 150 * k ** 2.2, 30 + 165 * k ** 1.8, 95 + 150 * k], -1)
    if name == 'bowl_glow':
        grid = (np.abs((xx % 22) - 11) > 9.8) | (np.abs((yy % 16) - 8) > 7.0)
        col[grid] *= 0.7
    glow[y:y + h, x:x + w] = col
for prefix in ('band', 'lid'):
    for k in (1, 2, 3):
        x, y, w, h = grect(f'{prefix}_wave{k}')
        yy, xx = np.mgrid[0:h, 0:w]
        col = np.zeros((h, w, 3), np.float32) + np.array([14, 46, 190])
        col *= (0.75 + 0.35 * np.exp(-(((yy - h / 2) / (h * 0.45)) ** 2)))[..., None]
        trace = np.zeros(w)
        phase = rng.uniform(0, 6)
        for i in range(w):
            f = i / w
            spike = sum(rng.uniform(0.3, 1.0) * math.exp(-((f - c) / 0.012) ** 2) * (1 if j % 2 else -1)
                        for j, c in enumerate(np.linspace(0.2 + 0.05 * k, 0.85, 6)))
            trace[i] = 0.12 * math.sin(f * 40 + phase) + 0.32 * spike
        line_y = h / 2 - trace * h * 0.9
        d = np.abs(yy - line_y[None, :])
        col += np.array([150, 190, 65]) * np.clip(1 - d / 6.0, 0, 1)[..., None]
        col += np.array([60, 60, 20]) * np.clip(1 - d / 2.0, 0, 1)[..., None]
        for ex in (int(w * 0.07), int(w * 0.93)):    # the little end knobs of the native trace
            dd = np.hypot(xx - ex, yy - h / 2)
            col[dd < 6] = (190, 200, 220)
        glow[y:y + h, x:x + w] = col
for name, c in (('lamp_red', (255, 50, 36)), ('lamp_green', (70, 255, 96))):
    x, y, w, h = grect(name)
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.hypot(xx - w * 0.4, yy - h * 0.4) / w
    glow[y:y + h, x:x + w] = np.array(c, np.float32) * 0.85 + np.array([255, 255, 255]) * np.clip(0.4 - d, 0, 1)[..., None] * 0.6
x, y, w, h = grect('arc')
yy, xx = np.mgrid[0:h, 0:w]
core = np.exp(-(((xx + 0.5) / w - 0.5) / 0.3) ** 2)
glow[y:y + h, x:x + w] = np.stack([60 + 190 * core, 110 + 145 * core, 255 + 0 * core], -1)
x, y, w, h = grect('goo')
streak = noise(h, w, 2, 30, 1.0)
glow[y:y + h, x:x + w] = np.array([40, 190, 52]) * (0.85 + 0.3 * streak)[..., None] + \
    np.array([80, 60, 80]) * np.clip(streak - 0.5, 0, 1)[..., None] * 2
gused = glow.max(-1) > 0
glow = dilate_into_gutters(np.clip(glow, 0, 255), gused, 8)
Image.fromarray(glow.astype(np.uint8)).save(os.path.join(OUT, 'rea_glow_1k.png'))

# ------------------------------------------------------------------------------------------------ glass (RGBA)
GSZ = L.GLASS_SIZE
yy, xx = np.mgrid[0:GSZ, 0:GSZ]
u = (xx + 0.5) / GSZ
theta = u * 2 * math.pi - math.pi
a = np.full((GSZ, GSZ), 0.10, np.float32)
c = np.zeros((GSZ, GSZ, 3), np.float32) + np.array([206, 228, 238])
for th0, width, strength in ((-0.42, 0.10, 0.95), (-0.28, 0.03, 0.7), (0.40, 0.07, 0.45)):
    band_ = np.exp(-((theta - th0) / width) ** 2) * strength
    a = np.maximum(a, band_)
    c = c * (1 - band_[..., None]) + np.array([243, 243, 243]) * band_[..., None]
rim = np.exp(-((yy / GSZ) / 0.03) ** 2) + np.exp(-((1 - yy / GSZ) / 0.03) ** 2)
a = np.clip(a + 0.15 * rim, 0, 1)
Image.fromarray(np.dstack([c, a * 255]).astype(np.uint8), 'RGBA').save(os.path.join(OUT, 'rea_glass_512.png'))
print('textures written to', OUT)
