#!/usr/bin/env python3
"""Krohn's glaive (spear piece) and scabbarded sword (sword piece), built from MM9's own piece geometry (no Codex master: the
image tool refused the Guard's weapon prompt, mm9_guard_claude README "Halberd"). Each prop is modelled in the PCA frame of
MM9's piece (axis 0 along the weapon, axis 1 across the blade/guard, axis 2 through it), then written back into MM9's bind
pose (LithTech/glTF coordinates x 0.0256, as convert_abc_model.py) so it sits exactly where MM9's piece sits; the Blender
step (add_props.py) moves it with the fitted Xspear / Xsword joints and weights it rigidly to them.

Spear (MM9: butt -1.724, round guard disc -0.057 r 0.1, glaive blade +0.08..+0.60, 0.17 m wide, a back hook at +0.41):
octagonal-ish 12-sided shaft r 0.027 (dark wood grip with gold bands at the butt, steel-sheathed upper shaft as MM9's skin),
gold butt cap, bronze disc guard with a gold rim, steel socket, double-bevelled steel blade. Sword (MM9: pommel -0.34, grip
to -0.04, cross-guard 0.40 m, scabbard 0.03..1.12): gold pommel, leather grip with gold wire, gold cross-guard with a blue
gem, brown leather scabbard with gold cross-lacing and a gold chape. Procedural PBR paint, one 2048x1024 atlas.
Writes work/props.npz (v, n-less, uv, f, part: 0 spear 1 sword) and textures/props_{basecolor,normal,orm}.png.
Run from the project folder."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / 'tools' / 'mm9_import_discovery'))
import convert_abc_model as abc  # noqa: E402

m = abc.read_abc(REPO / 'mm9/extracted/MODELS/MODELS/KROHN.abc')
frames = {}
for pc in m.pieces:
    if pc.name in ('spear', 'sword'):
        v = np.array([vv.position for vv in pc.lods[0].vertices]) * 0.0256
        c = v.mean(0)
        _, _, vt = np.linalg.svd(v - c)
        P = (v - c) @ vt.T
        # the PCA frame as numpy returns it (the profiles below were measured in exactly this frame: spear butt at
        # -1.724, blade +0.08..+0.60; sword pommel -0.339, scabbard tip +1.119); never flip an axis here
        frames[pc.name] = (c, vt)

W, H = 2048, 1024
V, UV, F, PART = [], [], [], []


def rings(part, profile, sides, uvbox, ang0=0.0, ell=(1.0, 1.0)):
    """Surface of revolution along axis 0: profile [(l, r)], an ellipse (ell scales axis 1, 2). uvbox: (u0, v0, u1, v1) in
    0..1, u along l, v around."""
    b = len(V)
    l0, l1 = profile[0][0], profile[-1][0]
    u0, v0, u1, v1 = uvbox
    for l, r in profile:
        for s in range(sides + 1):
            a = s / sides * 2 * np.pi + ang0
            V.append((l, r * ell[0] * np.cos(a), r * ell[1] * np.sin(a)))
            UV.append((u0 + (l - l0) / (l1 - l0) * (u1 - u0), v0 + s / sides * (v1 - v0)))
            PART.append(part)
    for i in range(len(profile) - 1):
        for s in range(sides):
            p, q = b + i * (sides + 1) + s, b + (i + 1) * (sides + 1) + s
            F.append((p, q + 1, q)); F.append((p, p + 1, q + 1))   # outward (angle runs counter-clockwise about +l)


def inset(poly, d):
    n = len(poly); out = []
    for i in range(n):
        a, b, c = poly[i - 1], poly[i], poly[(i + 1) % n]
        u = (b - a) / np.linalg.norm(b - a); w = (c - b) / np.linalg.norm(c - b)
        nu = np.array([-u[1], u[0]]); nw = np.array([-w[1], w[0]])
        mm = nu + nw; mm /= max(np.linalg.norm(mm), 1e-9)
        out.append(b + mm * d / max(mm @ nu, 0.35))
    return np.array(out)


def area(p):
    return 0.5 * np.sum(p[:, 0] * np.roll(p[:, 1], -1) - np.roll(p[:, 0], -1) * p[:, 1])


def earclip(p):
    idx = list(range(len(p))); tri = []

    def inside(q, a, b, c):
        s = lambda u, v, w: (v[0] - u[0]) * (w[1] - u[1]) - (v[1] - u[1]) * (w[0] - u[0])
        return s(a, b, q) >= 0 and s(b, c, q) >= 0 and s(c, a, q) >= 0
    while len(idx) > 3:
        for k in range(len(idx)):
            i, j, mm = idx[k - 1], idx[k], idx[(k + 1) % len(idx)]
            a, b, c = p[i], p[j], p[mm]
            if (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]) <= 1e-9:
                continue
            if any(inside(p[o], a, b, c) for o in idx if o not in (i, j, mm)):
                continue
            tri.append((i, j, mm)); idx.pop(k); break
        else:
            raise SystemExit('ear clip failed')
    tri.append(tuple(idx))
    return tri


def plate(part, poly, edge_in, thick, uvmap):
    """Double-bevelled plate in the axis 0/1 plane: outline at depth 0 (sharp edge), the inset outline at +-thick."""
    p = poly if area(poly) > 0 else poly[::-1]
    q = inset(p, edge_in)
    n = len(p)
    for s in (1, -1):
        b = len(V)
        for x in p:
            V.append((x[0], x[1], 0.0)); UV.append(uvmap(x)); PART.append(part)
        for x in q:
            V.append((x[0], x[1], s * thick)); UV.append(uvmap(x)); PART.append(part)
        for i in range(n):
            j = (i + 1) % n
            f = [(b + i, b + j, b + n + j), (b + i, b + n + j, b + n + i)]
            F.extend(f if s > 0 else [t[::-1] for t in f])      # outward in the local frame
        for t in earclip(q):
            f = tuple(b + n + k for k in t)
            F.append(f if s > 0 else f[::-1])


def box(part, l0, l1, w, d, uvbox, taper=1.0):
    """A bar along axis 1 (the cross-guard): l along axis 0 (l0..l1), half width w along axis 1, half depth d."""
    u0, v0, u1, v1 = uvbox
    b = len(V)
    pts = []
    for y in (-w, w):
        for l in (l0, l1):
            for z in (-d, d):
                k = taper if abs(y) > 0 else 1
                pts.append((l, y, z * k))
    # 8 corners: index = iy*4 + il*2 + iz
    for i, p in enumerate(pts):
        V.append(p); UV.append((u0 + (p[1] + w) / (2 * w) * (u1 - u0), v0 + ((i % 2) * 0.5 + (i // 2 % 2) * 0.25) * (v1 - v0)))
        PART.append(part)
    quads = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    for a, bb, c, d_ in quads:
        F.append((b + a, b + c, b + bb)); F.append((b + a, b + d_, b + c))   # outward (check_winding)


# ------------------------------------------------------------------ spear (part 0), PCA frame of MM9's spear piece
# atlas: v 0..0.36 shaft strip (u along the shaft), v 0.36..1.0 x u 0..0.55 the blade plate, u 0.55..1 the guard disc
SP_BUTT, SP_GUARD = -1.724, -0.057
RS = 0.027
shaft = [(SP_BUTT - 0.010, 0.002), (SP_BUTT - 0.008, 0.024), (SP_BUTT, 0.032), (SP_BUTT + 0.045, 0.032), (SP_BUTT + 0.052, RS),
         (-1.30, RS), (-1.29, 0.031), (-1.26, 0.031), (-1.25, RS), (-0.98, RS), (-0.97, 0.030), (-0.95, 0.030), (-0.94, RS * 0.95),
         (SP_GUARD - 0.03, RS * 0.95), (SP_GUARD - 0.012, 0.030), (SP_GUARD - 0.010, 0.006)]
rings(0, shaft, 12, (0.005, 0.01, 0.995, 0.35))
# guard disc: a short wide cylinder with a bevelled rim
disc = [(SP_GUARD - 0.011, 0.012), (SP_GUARD - 0.011, 0.090), (SP_GUARD - 0.006, 0.100), (SP_GUARD + 0.006, 0.100),
        (SP_GUARD + 0.011, 0.090), (SP_GUARD + 0.011, 0.012)]
rings(0, disc, 20, (0.56, 0.40, 0.98, 0.98))
socket = [(SP_GUARD + 0.010, 0.030), (SP_GUARD + 0.06, 0.026), (SP_GUARD + 0.10, 0.020), (SP_GUARD + 0.14, 0.012), (SP_GUARD + 0.155, 0.004)]   # runs 2 cm into the blade root (detached audit: an 8 mm gap)
rings(0, socket, 12, (0.56, 0.37, 0.98, 0.39))
BLADE = np.array([(0.075, 0.000), (0.085, 0.075), (0.170, 0.085), (0.257, 0.090), (0.340, 0.088), (0.419, 0.083), (0.470, 0.074),
                  (0.508, 0.062), (0.540, 0.045), (0.570, 0.022), (0.600, -0.008), (0.575, -0.016), (0.540, -0.024),
                  (0.505, -0.031), (0.470, -0.050), (0.451, -0.062), (0.425, -0.098), (0.413, -0.106), (0.395, -0.090),
                  (0.360, -0.071), (0.300, -0.058), (0.258, -0.050), (0.170, -0.042), (0.088, -0.036)])
sp_uv = lambda x: (0.01 + (x[0] - 0.07) / 0.54 * 0.53, 0.38 + (x[1] + 0.115) / 0.215 * 0.60)
plate(0, BLADE, 0.012, 0.0075, sp_uv)
n_spear = len(V)

# ------------------------------------------------------------------ sword (part 1), PCA frame of MM9's sword piece
# atlas: v 0.36..1.0 x u 0.55..1 are the spear's; sword in a second band: we use the lower half of a second atlas row,
# here u is shared: the sword strip lives in v 0..0.35 of the RIGHT half? Keep it simple: the sword gets the region
# u 0..1 x v 0.36.. after the spear? -> one atlas, sword strip below: remap the spear into the top half instead.
for i in range(n_spear):
    u, v = UV[i]
    UV[i] = (u, 0.5 + v * 0.5)           # spear in v 0.5..1
SW_POM, SW_GUARD, SW_TIP = -0.339, -0.03, 1.119
pommel = [(SW_POM - 0.004, 0.004), (SW_POM, 0.018), (SW_POM + 0.012, 0.032), (SW_POM + 0.030, 0.030), (SW_POM + 0.045, 0.018),
          (SW_POM + 0.055, 0.016)]
rings(1, pommel, 12, (0.01, 0.01, 0.10, 0.22))
grip = [(SW_POM + 0.055, 0.016), (SW_POM + 0.065, 0.019), (SW_GUARD - 0.03, 0.021), (SW_GUARD - 0.012, 0.024), (SW_GUARD, 0.024)]
rings(1, grip, 12, (0.11, 0.01, 0.40, 0.22))
box(1, SW_GUARD, SW_GUARD + 0.035, 0.200, 0.018, (0.01, 0.26, 0.40, 0.48), taper=1.0)
scab = [(SW_GUARD + 0.035, 0.002), (SW_GUARD + 0.036, 0.046), (SW_GUARD + 0.07, 0.048), (0.40, 0.046), (0.80, 0.043), (1.02, 0.040),
        (1.06, 0.038), (1.09, 0.030), (1.11, 0.016), (SW_TIP, 0.002)]
rings(1, scab, 14, (0.42, 0.01, 0.99, 0.48), ell=(1.0, 0.42))
for i in range(n_spear, len(V)):
    u, v = UV[i]
    UV[i] = (u, v)                       # sword in v 0..0.5 (its boxes above already use 0..0.48)

V = np.array(V, float); UV = np.array(UV, float); F = np.array(F, int); PART = np.array(PART, int)
# PCA frame -> MM9 model space (glTF numbers)
out = np.zeros_like(V)
for part, name in ((0, 'spear'), (1, 'sword')):
    c, vt = frames[name]
    k = PART == part
    out[k] = c + V[k] @ vt
    if np.linalg.det(vt) < 0:                 # every face above is outward in the local frame; a reflecting PCA frame turns it inside out
        fk = PART[F[:, 0]] == part
        F[fk] = F[fk][:, ::-1]
    print('FRAME', name, 'det %+.0f' % np.linalg.det(vt))
Path('work').mkdir(exist_ok=True)
np.savez('work/props.npz', v=out, local=V, uv=UV, f=F, part=PART)
print('PROPS tris spear', int((PART[F[:, 0]] == 0).sum()), 'sword', int((PART[F[:, 0]] == 1).sum()), 'verts', len(V))

# ------------------------------------------------------------------ paint (procedural PBR)
rng = np.random.default_rng(11)


def noise(sig, sx=1.0):
    n = ndimage.gaussian_filter(rng.normal(size=(H, W)), (sig, sig * sx), mode='wrap')
    return n / n.std()


fine, mid, big = noise(1.2), noise(6), noise(40)
grain = noise(1.0, 14.0)
img = np.zeros((H, W, 3)); rough = np.full((H, W), 0.6); metal = np.zeros((H, W)); hgt = np.zeros((H, W))
rows = np.arange(H)[:, None] * np.ones((1, W)); cols = np.ones((H, 1)) * np.arange(W)[None, :]
U = (cols + 0.5) / W; Vv = 1 - (rows + 0.5) / H
GOLD = np.array([196, 150, 64.]); GOLD_D = np.array([120, 84, 30.])
STEEL = np.array([168, 170, 172.])


def put(mask, col, r, me, h=None):
    img[mask] = col[mask] if col.ndim == 3 else col
    rough[mask] = r[mask] if np.ndim(r) == 2 else r
    metal[mask] = me
    if h is not None:
        hgt[mask] = h[mask] if np.ndim(h) == 2 else h


gold_tex = GOLD[None, None] * (1 + 0.10 * fine[..., None] + 0.12 * mid[..., None]) - 40 * np.clip(noise(2.5) - 1.2, 0, 1)[..., None]
gold_r = 0.32 + 0.06 * fine
# --- spear shaft strip: v 0.5..0.675 (0.01..0.35 scaled), u = length
sv = (Vv - 0.5) / 0.5
shaft_m = (sv >= 0.0) & (sv < 0.36) & (U < 1.0)
l = SP_BUTT - 0.010 + (U - 0.005) / 0.99 * (SP_GUARD - 0.010 - (SP_BUTT - 0.010))
wood = 0.5 + 0.5 * np.sin(sv * 160 + 0.8 * grain + l * 4)
c_wood = np.array([40, 24, 16.]) + wood[..., None] * np.array([26, 15, 9.]) + (grain * 5)[..., None]
c_steel = STEEL[None, None] + (grain * 8 + big * 7)[..., None]
put(shaft_m, c_steel, 0.34 + 0.05 * grain, 1)
put(shaft_m & (l < -1.25), c_wood, 0.62 + 0.04 * grain, 0, 0.3 * wood)
for a, b_ in ((SP_BUTT - 0.02, SP_BUTT + 0.052), (-1.30, -1.25), (-0.98, -0.94), (SP_GUARD - 0.03, SP_GUARD)):
    k = shaft_m & (l >= a) & (l < b_)
    put(k, gold_tex, gold_r, 1, 0.8 + 0.2 * fine)
gem = shaft_m & (np.abs(l + 1.275) < 0.012) & (np.abs(((sv / 0.36 * 4) % 1) - 0.5) < 0.12)
put(gem, np.array([60, 170, 210.])[None, None] * (1 + 0.15 * fine[..., None]), 0.15, 0, 1.0 + 0 * fine)
# --- blade plate: v 0.69..0.99, u 0.01..0.54
blade_m = np.zeros((H, W), bool)
im = Image.new('L', (W, H)); d = ImageDraw.Draw(im)
d.polygon([((sp_uv(x)[0]) * W, (1 - (0.5 + sp_uv(x)[1] * 0.5)) * H) for x in BLADE], fill=255)
blade_m = np.asarray(im) > 0
dist = ndimage.distance_transform_edt(blade_m)
edge = np.clip(1 - dist / 22.0, 0, 1)
c_blade = STEEL[None, None] + (fine * 6 + mid * 8 + big * 9)[..., None] + (grain * 4)[..., None]
c_blade = c_blade * (1 + 0.22 * edge[..., None] ** 2)
put(blade_m, c_blade, 0.30 + 0.06 * noise(3) - 0.12 * edge, 1, 0.8 * np.clip(dist / 22.0, 0, 1))
# engraved gold scroll near the socket end of the blade
scroll = blade_m & (U < 0.12) & (dist > 6) & ((np.sin(U * 900) * np.sin(Vv * 700) + 0.4 * fine) > 0.6)
put(scroll, gold_tex, gold_r, 1)
# --- guard disc + socket: u 0.56..0.98, v 0.685..0.995 (bronze, gold rim)
disc_m = (U > 0.555) & (U < 0.985) & (Vv > 0.5 + 0.40 * 0.5 - 0.004) & (Vv < 0.5 + 0.98 * 0.5 + 0.004)
du = (U - 0.56) / 0.42
c_bronze = np.array([150, 92, 60.])[None, None] * (1 + 0.12 * fine[..., None] + 0.1 * mid[..., None])
put(disc_m, c_bronze, 0.40 + 0.05 * fine, 1, 0.5 + 0.2 * fine)
put(disc_m & ((du < 0.25) | (du > 0.75)), gold_tex, gold_r, 1, 0.9 + 0 * fine)
sock_m = (U > 0.555) & (U < 0.985) & (Vv > 0.5 + 0.37 * 0.5 - 0.004) & (Vv < 0.5 + 0.39 * 0.5 + 0.004)
put(sock_m, c_steel, 0.36, 1)
# --- sword: pommel u .01-.10, grip .11-.40 (v 0.01..0.22), guard .01-.40 v .26-.48, scabbard .42-.99 v .01-.48
pom_m = (U < 0.105) & (Vv < 0.225)
put(pom_m, gold_tex, gold_r, 1, 0.6 + 0.3 * mid)
grip_m = (U >= 0.105) & (U < 0.405) & (Vv < 0.225)
wire = 0.5 + 0.5 * np.sign(np.sin(U * 2 * np.pi * 60 + Vv / 0.22 * 2 * np.pi))
c_grip = np.array([70, 40, 22.])[None, None] * (0.8 + 0.3 * fine[..., None])
put(grip_m, c_grip, 0.7, 0, 0.3)
put(grip_m & (wire > 0.5) & ((U * 60) % 1 < 0.35), gold_tex, gold_r, 1, 0.9 + 0 * fine)
guard_m = (U < 0.405) & (Vv >= 0.255) & (Vv < 0.485)
put(guard_m, gold_tex, gold_r, 1, 0.5 + 0.4 * np.clip(mid, 0, 1))
gu = (U - 0.01) / 0.39
gemg = guard_m & (np.abs(gu - 0.5) < 0.03)
put(gemg, np.array([50, 160, 205.])[None, None] * (1 + 0.15 * fine[..., None]), 0.12, 0, 1.0 + 0 * fine)
scab_m = (U >= 0.415) & (Vv < 0.485)
su = (U - 0.42) / 0.57; sl = SW_GUARD + 0.035 + su * (SW_TIP - SW_GUARD - 0.035); sa = Vv / 0.47
c_leather = np.array([118, 58, 28.])[None, None] * (0.85 + 0.10 * mid[..., None] + 0.08 * fine[..., None]) + (grain * 3)[..., None]
put(scab_m, c_leather, 0.62 + 0.05 * fine, 0, 0.3 + 0.1 * mid)
# gold cross-lacing: X bands every 0.16 m on the front and back faces
ph = (sl / 0.16) % 1
lace = scab_m & (np.minimum(np.abs(ph - sa * 2 % 1), np.abs(ph - (1 - sa * 2 % 1))) < 0.05) & (sl > 0.05) & (sl < 1.0)
put(lace, gold_tex * 1.08, gold_r, 1, 0.9 + 0 * fine)
throat = scab_m & (sl < SW_GUARD + 0.09)
chape = scab_m & (sl > 1.0)
put(throat | chape, gold_tex, gold_r, 1, 0.6 + 0.3 * mid)
img = np.clip(img, 0, 255)
used = shaft_m | blade_m | disc_m | sock_m | pom_m | grip_m | guard_m | scab_m
idx = ndimage.distance_transform_edt(~used, return_distances=False, return_indices=True)
img = img[idx[0], idx[1]]; rough = rough[idx[0], idx[1]]; metal = metal[idx[0], idx[1]]; hgt = hgt[idx[0], idx[1]]
Path('textures').mkdir(exist_ok=True)
Image.fromarray(img.astype(np.uint8)).save('textures/props_basecolor.png')
gy, gx = np.gradient(ndimage.gaussian_filter(hgt, 0.8))
nrm = np.dstack([-gx * 2.2, gy * 2.2, np.ones_like(gx)]); nrm /= np.linalg.norm(nrm, axis=2, keepdims=True)
Image.fromarray(((nrm * 0.5 + 0.5) * 255).astype(np.uint8)).resize((1024, 512), Image.LANCZOS).save('textures/props_normal.png')
orm = np.dstack([np.ones((H, W)), np.clip(rough, 0.05, 1), metal])
Image.fromarray((orm * 255).astype(np.uint8)).resize((1024, 512), Image.LANCZOS).save('textures/props_orm.png')
print('PAINTED')
