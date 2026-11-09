#!/usr/bin/env python3
"""Hydra textures for the grafted model (CLAUDE_CREATURE_TEXTURES.md: shared skins + region masks + per-tier ramps,
material classes, AO in R of the metal/roughness maps). Two texture sets (uv_atlas.py layout):
  body 2048x2048: body and necks (part 0), baked from the 20k Meshy model,
  head 1536x1024: one 512x512 tile per head (part k: skull and its neck stub), baked from the head retextures.

`--assemble`: fill texels no bake reached (work/bake_miss_<set>.npy) from the nearest baked texel (padding, so mips
and filtering never pull the background into the islands) and write textures/hyd_<set>_{basecolor,normal,roughness,
ao}.png. Then grade_basecolor.py runs on each base colour with its own AO (see README), then this script without
`--assemble`.

Regions and materials (at most four regions per material):
  'Hydra'   body texture: R body, G N1, B N2, A N3        (body and neck faces)
  'HydraB'  body texture: R N4, G N5, B body             (N4/N5 faces grown by GROW rings)
  'HeadsA'  head texture: R H1, G N1, B H2, A N2         (heads 1-2)
  'HeadsB'  head texture: R H3, G N3, B H5, A N5         (heads 3 and 5)
  'HeadsC'  head texture: R H4, G N4, B F4              (head 4 and its fins)
F4 = head 4's fin membranes (its tan texels): their native colour changes per tier on its own (tan, blue-grey,
green), and sharing H4's ramp turned the red scales tan.
N<k> = neck k (body: the texel's chain from bone weights; head tiles: the stub behind the rigid skull, from the
graft's head_skull flag), H<k> = head k's skull. The neck regions on the head tiles get their own ramps, fitted to the
same native neck colours as the body's, so the colour runs on across the zip.
Out of every region (raw base colour in every tier): ivory (horns, teeth: pale, low saturation, on the head tiles),
eyes (saturated yellow), mouth interiors (saturated deep red, not on the red head 4).
Ramps per tier (palettes 754 A, 755 B, 756 C) from hand-placed rectangles on the native stand frames (necks: front
belly and back-view rectangles; heads: front head rectangles; head 4's fins: its fin rectangles; body: side view):
chroma from the native colours (band-averaged 15th-95th percentile, 15th-85th on heads, by the texel's luminance percentile), luminance from the texel
scaled to the native mean x albedo; heads get more chroma and less lift (the sprites' heads are dark and vivid).
Writes textures/hyd_{body,head}_metal_rough.png (R AO, G roughness, B 0), hyd_<material>_mask.png,
hyd_{body,head}_material_classes.png, hyd_ramps.json, work/face_material.npy (per mesh face 0..4 in the order above)
and review/texture_classes_{body,head}.png."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / 'claude_shared'))
import region_variants as RV
T = ROOT / 'textures'; NATIVE = ROOT.parent / 'mm6_hyd'
PALETTES = {'hyd_a': '754', 'hyd_b': '755', 'hyd_c': '756'}
SETS = {'body': (2048, 2048), 'head': (1536, 1024)}
ALBEDO, HEAD_ALBEDO, HEAD_SAT = 1.35, 1.1, 1.3
GROW = 2
NECK_TRANSFER = True
THROAT_BACK, THROAT_SIDE = 0.4, 0.75
STUB_SIGMA, STUB_DETAIL, STUB_LEAD = 18.0, 0.2, 0.025
PROTRUDE_R = 1.15            # x skull half width from the head axis: horns and spikes
UNDER_FULL = 0.6             # jaw/throat underside: smoothing reaches full strength this far below the axis
TEETH_PX = 10                # texels: pale texels this close to the mouth interior are teeth
SPLIT_BAND = 0.03            # m: head colour blends into neck colour over this arc behind the skull
OPEN_PX, CLOSE_PX = 2, 6                 # ivory/eye masks: drop thin highlight lines, fill shaded specks on horns
W = np.array([0.2126, 0.7152, 0.0722])
NECK_RECTS = {1: [('hydstaa0', 90, 140, 105, 195), ('hydstaa4', 183, 110, 200, 153)],
              2: [('hydstaa0', 110, 95, 127, 170), ('hydstaa4', 162, 67, 183, 147)],
              3: [('hydstaa0', 140, 100, 157, 190), ('hydstaa4', 135, 87, 155, 157)],
              4: [('hydstaa0', 166, 65, 180, 170), ('hydstaa4', 110, 60, 130, 160)],
              5: [('hydstaa0', 185, 150, 200, 205), ('hydstaa4', 97, 110, 107, 180)]}
HEAD_RECTS = {1: [('hydstaa0', 85, 105, 105, 128)], 2: [('hydstaa0', 110, 58, 128, 80)],
              3: [('hydstaa0', 136, 72, 158, 95)],
              4: [('hydstaa0', 167, 30, 182, 48)],
              5: [('hydstaa0', 182, 108, 203, 140)]}
FIN_RECTS = [('hydstaa0', 153, 22, 164, 50), ('hydstaa0', 186, 20, 196, 48)]
BODY_RECTS = [('hydstaa2', 30, 150, 170, 215), ('hydstaa0', 150, 205, 185, 222)]
MATERIALS = [('Hydra', 'body', ['body', 'N1', 'N2', 'N3']), ('HydraB', 'body', ['N4', 'N5', 'body']),
             ('HeadsA', 'head', ['H1', 'N1', 'H2', 'N2']), ('HeadsB', 'head', ['H3', 'N3', 'H5', 'N5']),
             ('HeadsC', 'head', ['H4', 'N4', 'F4'])]
lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
encode = lambda c: np.where(c <= 0.0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)


LOFT_SRC_GAP = 0.01        # m: the loft copies the neck surface starting this far behind its neck ring


def loft_transfer(maps):
    """Body texels of the lofts (graft_heads.py) copy the neck just behind each loft. Each loft texel has its distance
    from the skull ring along the loft (loft_s) and the point of our neck ring at its angle (loft_ref), both from the
    graft; the source is the neck texel at that point's angle round neck k's chain and at its arc plus the gap plus
    loft_s (a copy, not a stretch). Angle and arc measured on the loft itself against the chain smeared the outside
    of tight bends (heads 3 and 5: many texels projected onto one joint; user check 2026-10-09). Baked from the 20k
    model, the lofts picked up the old heads' pale, smeared surface. The normal map is flat there (the tangent frames
    of the two UV islands differ)."""
    data = np.load(ROOT / 'work' / 'uv3d.npz')
    rig = json.load(open(ROOT / 'work' / 'rig.json'))['chains']
    body = np.nonzero(data['part'] == 0)[0]
    tri, bary = rasterise(data['uv'][body], body, SETS['body'])
    valid = tri >= 0; ti = np.maximum(tri, 0)
    xyz = (bary[..., None] * data['xyz'][ti]).sum(-2)
    corner = np.argmax(bary, -1); chain = np.where(valid, data['owner'][ti, corner], -1)
    is_loft = valid & (data['src'][ti] == 2)
    from scipy.spatial import cKDTree
    moved = 0
    for k in range(1, 6):
        J = np.array(rig[k]['joints']); L = np.linalg.norm(np.diff(J, axis=0), axis=1)
        s_tip = np.concatenate([np.cumsum(L[::-1])[::-1], [0]])          # arc from the tip at each joint
        T = np.diff(J, axis=0) / L[:, None]
        U = np.zeros_like(T); up = np.array([0, 0, 1.0]); u = up - (up @ T[-1]) * T[-1]; U[-1] = u / np.linalg.norm(u)
        for i in range(len(T) - 2, -1, -1):
            u = U[i + 1] - (U[i + 1] @ T[i]) * T[i]; U[i] = u / np.linalg.norm(u)

        def tube(P):
            best = np.full(len(P), 1e9); arc = np.zeros(len(P)); th = np.zeros(len(P)); rr = np.zeros(len(P))
            for i in range(len(T)):
                d = J[i + 1] - J[i]; t = np.clip(((P - J[i]) @ d) / (d @ d), 0, 1)
                r = P - (J[i] + t[:, None] * d); dist = np.linalg.norm(r, axis=1)
                m = dist < best
                best[m] = dist[m]; arc[m] = s_tip[i] - t[m] * L[i]
                V = np.cross(T[i], U[i]); th[m] = np.arctan2(r[m] @ V, r[m] @ U[i]); rr[m] = dist[m]
            return arc, th, rr

        lm = is_loft & (chain == k)
        if not lm.any():
            continue
        b = bary[lm]; t_ = ti[lm]
        ls = (b * data['loft_s'][t_]).sum(-1)
        ra, rt, _ = tube((b[..., None] * data['loft_ref'][t_]).sum(-2))
        want = ra + LOFT_SRC_GAP + ls
        nm = valid & ~is_loft & (chain == k)
        ys, xs = np.nonzero(nm); na, nt, nr = tube(xyz[nm])
        sel = (na > want.min() - 0.01) & (na < want.max() + 0.02)
        R = float(np.median(nr[sel]))
        tree = cKDTree(np.stack([np.cos(nt[sel]) * R, np.sin(nt[sel]) * R, na[sel]], 1))
        _, idx = tree.query(np.stack([np.cos(rt) * R, np.sin(rt) * R, want], 1))
        sy, sx = ys[sel][idx], xs[sel][idx]
        ly, lx = np.nonzero(lm)
        for name, a in maps.items():
            if name == 'normal':
                a[ly, lx] = (128, 128, 255)
            else:
                a[ly, lx] = a[sy, sx]
        moved += int(lm.sum())
    print('LOFT texels copied from the necks', moved)


def assemble():
    for name in SETS:
        miss = np.load(ROOT / 'work' / f'bake_miss_{name}.npy')
        _, (iy, ix) = ndimage.distance_transform_edt(miss, return_indices=True)
        maps = {}
        for kind, out, mode in (('base_color', 'basecolor', 'RGB'), ('normal', 'normal', 'RGB'),
                                ('roughness', 'roughness', 'L'), ('ao', 'ao', 'L')):
            maps[out] = np.asarray(Image.open(T / f'{name}_{kind}.png').convert(mode))[iy, ix].copy()
        if name == 'body':
            loft_transfer(maps)

        for out, a in maps.items():
            Image.fromarray(a).save(T / f'hyd_{name}_{out}.png')
        print('ASSEMBLED', name, 'filled texels', int(miss.sum()))




def rasterise(uv, values, size, tol=0.03):
    """Per texel of a (w, h) texture: the value of the triangle covering it and the barycentric weights."""
    w, h = size
    out = np.full((h, w), -1, np.int64); bary = np.zeros((h, w, 3), np.float32)
    for t in range(len(uv)):
        p = uv[t] * (w, h); p[:, 1] = h - p[:, 1]
        x0, y0 = np.floor(p.min(0)).astype(int); x1, y1 = np.ceil(p.max(0)).astype(int)
        x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, w - 1), min(y1, h - 1)
        if x1 < x0 or y1 < y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        a, b, c = p
        d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(d) < 1e-12:
            continue
        w0 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gy - c[1])) / d
        w1 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / d
        w2 = 1 - w0 - w1
        inside = (w0 >= -tol) & (w1 >= -tol) & (w2 >= -tol)
        ys, xs = np.nonzero(inside)
        out[y0 + ys, x0 + xs] = values[t]
        bary[y0 + ys, x0 + xs] = np.stack([w0[inside], w1[inside], w2[inside]], -1)
    return out, bary


if '--assemble' in sys.argv:
    assemble()
    sys.exit(0)


def hsv(rgb):
    im = Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8)).convert('HSV')
    a = np.asarray(im, np.float32) / 255
    return a[..., 0] * 360, a[..., 1], a[..., 2]


data = np.load(ROOT / 'work' / 'uv3d.npz')
tri_part = data['part']; tri_owner = data['owner']; tri_skull = data['skull']; tri_app = data['appendage']
masks = {}; classes = {}; base = {}; soft = {}
for name, size in SETS.items():
    sel = np.nonzero((tri_part == 0) if name == 'body' else (tri_part > 0))[0]
    tri, bary = rasterise(data['uv'][sel], sel, size)
    valid = tri >= 0; ti = np.maximum(tri, 0)
    rgb = np.asarray(Image.open(T / f'hyd_{name}_basecolor.png').convert('RGB'), np.float32) / 255
    base[name] = rgb
    hh, ss, vv = hsv(rgb)
    if name == 'body':
        # chain of the texel: the corner with the largest barycentric weight
        corner = np.argmax(bary, -1)
        chain = np.where(valid, tri_owner[ti, corner], -1)
        names = {'body': valid & (chain == 0)}
        for k in range(1, 6):
            names[f'N{k}'] = valid & (chain == k)
        ivory = np.zeros_like(valid); eyes = ivory.copy(); mouth = ivory.copy()
    else:
        head = np.where(valid, tri_part[ti], 0)
        skull = (bary * tri_skull[ti]).sum(-1) > 0.5
        # opened by OPEN_PX: teeth, horns and eyes are solid blobs; thin pale or yellow highlight lines along the
        # Meshy scale edges (head 4) passed the colour tests and kept their raw colour in every tier
        opening = lambda m: ndimage.binary_opening(m, iterations=OPEN_PX)
        ivory = ndimage.binary_closing(opening(valid & (ss < 0.26) & (vv > 0.52)), iterations=CLOSE_PX) & valid
        eyes = opening(valid & (hh >= 35) & (hh < 70) & (ss > 0.55) & (vv > 0.5) & skull)
        mouth = valid & ((hh < 12) | (hh > 340)) & (ss > 0.55) & (vv < 0.75) & (head != 4) & skull
        # throats: the head retextures paint the underside of the rear skull pale like a belly; as ivory it kept its
        # raw cream in every tier with a ragged edge (user check 2026-10-09, purple head). Pale texels below the skull
        # axis, behind THROAT_BACK of the skull length and within THROAT_SIDE of its half width go to the neck region
        xyz = (bary[..., None] * data['xyz'][ti]).sum(-2)
        chains = json.load(open(ROOT / 'work' / 'rig.json'))['chains']
        throat = np.zeros_like(valid); front = np.zeros(valid.shape, np.float32); underside = np.zeros_like(valid)
        below_w = np.zeros(valid.shape, np.float32); throat_w = np.zeros(valid.shape, np.float32)
        stub_w = np.zeros(valid.shape, np.float32); protrude = np.zeros_like(valid)
        near_mouth = ndimage.binary_dilation(mouth, iterations=TEETH_PX)
        skull_soft = (bary * tri_skull[ti]).sum(-1)
        for k in range(1, 6):
            J = np.array(chains[k]['joints']); tip = J[-1]; T_ = (J[-1] - J[-2]) / np.linalg.norm(J[-1] - J[-2])
            U_ = np.array([0, 0, 1.0]) - T_[2] * T_; U_ /= np.linalg.norm(U_); V_ = np.cross(T_, U_)
            m = valid & (head == k) & skull
            r = xyz - tip; a = -(r @ T_); u = r @ U_; v = r @ V_
            length = np.percentile(a[m], 98); half = np.percentile(np.abs(v[m]), 90)
            # whole head incl. its neck stub: Meshy paints a pale sawtooth fringe where the jaw meets the neck
            # underside weight for the stub smoothing: 0 above the axis, 1 from UNDER_FULL x half width below
            uw = np.clip(-u / (UNDER_FULL * half), 0, 1)
            below_w[valid & (head == k)] = (uw * uw * (3 - 2 * uw))[valid & (head == k)]
            below = valid & (head == k) & ivory & (u < 0.25 * half) & (np.abs(v) < THROAT_SIDE * half) & ~near_mouth
            underside |= below                    # pale jaw/throat scales, not teeth: skin, recoloured
            throat |= below & (a > THROAT_BACK * length)
            # throat zone by geometry (soft): behind THROAT_BACK of the skull and below the axis; built from the pale
            # texels it followed Meshy's painted sawtooth collar
            tb = np.clip((a - THROAT_BACK * length) / (0.25 * length), 0, 1)
            tw = (tb * tb * (3 - 2 * tb)) * uw * (np.abs(v) < THROAT_SIDE * half * 1.3)
            # head-to-neck colour blend: a straight cut across the neck at the skull/stub split (the median arc of
            # texels on the graft's split), blended over SPLIT_BAND; the split by triangles (skull flag) was a jagged
            # line where purple jaw met pale stub (user check 2026-10-09)
            mk = valid & (head == k)
            edge = mk & (np.abs(skull_soft - 0.5) < 0.3)
            a_split = float(np.median(a[edge]))
            t = np.clip((a_split + SPLIT_BAND / 2 - a) / SPLIT_BAND, 0, 1)
            # heads are cut right behind the skull (graft_heads.py CUT_N = SPLIT_N), so the graft's skull flag (which
            # also keeps horns, fins and crests behind the split on the skull) decides head vs neck colours; an arc
            # split gave the crests neck colours
            front[mk] = np.clip(skull_soft, 0, 1)[mk]
            protrude |= mk & (np.hypot(u, v) > PROTRUDE_R * half)
        throat = ndimage.binary_closing(throat, iterations=2) & valid & (head > 0)
        ivory &= ~(throat | underside)

        skin = valid & ~ivory & ~eyes & ~mouth
        # head 4's fin membranes: its tan texels (the skin is red, the eyes more saturated yellow)
        fin = valid & (head == 4) & (hh >= 25) & (hh < 70) & (ss > 0.18) & (vv > 0.35) & ~eyes & ~ivory
        names = {}
        skull = front > 0.5
        for k in range(1, 6):
            names[f'H{k}'] = skin & (head == k) & skull & ~fin
            names[f'N{k}'] = skin & (head == k) & (~skull | throat) & ~fin
            names[f'H{k}'] &= ~throat
        names['F4'] = valid & fin & ~ivory
    cls = np.zeros(valid.shape, np.uint8); cls[valid] = 1; cls[ivory] = 4; cls[eyes] = 6; cls[mouth] = 7
    classes[name] = cls
    # pad the region labels past the island borders (as the base colour's padding): the half-resolution feathered
    # masks otherwise fell off at every island edge, and the raw base colour showed as lines along the head plates
    label = np.full(valid.shape, -1, np.int16)
    for i, m in enumerate(names.values()):
        label[m] = i
    _, (iy, ix) = ndimage.distance_transform_edt(~valid, return_indices=True)
    label = label[iy, ix]
    masks[name] = {n: label == i for i, n in enumerate(names)}
    if name == 'head':
        head_valid, head_front, head_throat, head_of = valid, front, throat, np.where(valid, head, 0)
        keep_detail = ndimage.binary_dilation(mouth | eyes, iterations=TEETH_PX) | (ivory & ~underside)
        head_below = np.where(keep_detail, 0.0, np.maximum(below_w * 0.5, stub_w))
        # soft H/N weights from the blend, padded past the islands like the labels
        f_ = (front * (1 - throat_w))[iy, ix]
        for k in range(1, 6):
            both = masks[name][f'H{k}'] | masks[name][f'N{k}']
            soft[(name, f'H{k}')] = both * f_
            soft[(name, f'N{k}')] = both * (1 - f_)
    print('REGIONS', name, {n: int(m.sum()) for n, m in names.items()}, 'ivory', int(ivory.sum()), 'eyes',
          int(eyes.sum()), 'mouth', int(mouth.sum()), 'throat', int(throat.sum()) if name == 'head' else 0)

# material per face: body faces by neck chain (N4/N5 grown -> HydraB), heads by k
face = data['face']; n_faces = int(face.max()) + 1
face_part = np.zeros(n_faces, int); face_part[face] = tri_part
keys = np.round(data['xyz'] * 1e5).astype(np.int64)
vid = {}; tri_v = np.array([[vid.setdefault(tuple(p), len(vid)) for p in t] for t in keys])
tri_chain = np.array([np.bincount(o, minlength=6).argmax() for o in tri_owner])
grow = np.isin(tri_chain, (4, 5)) & (tri_part == 0)
for _ in range(GROW):
    verts = np.zeros(len(vid), bool); verts[tri_v[grow].ravel()] = True
    grow = verts[tri_v].any(1) & (tri_part == 0)
tri_mat = np.where(grow, 1, 0)
tri_mat = np.where(np.isin(tri_part, (1, 2)), 2, tri_mat)
tri_mat = np.where(np.isin(tri_part, (3, 5)), 3, tri_mat)
tri_mat = np.where(tri_part == 4, 4, tri_mat)
face_mat = np.zeros(n_faces, np.int8); face_mat[face] = tri_mat
np.save(ROOT / 'work' / 'face_material.npy', face_mat)


def feather(m, size):
    im = Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.0))
    return np.asarray(im.resize(size, Image.LANCZOS), np.float32) / 255


HALF = {n: (s[0] // 2, s[1] // 2) for n, s in SETS.items()}
weights = {(tex, n): feather(soft.get((tex, n), m), HALF[tex]) for tex in SETS for n, m in masks[tex].items()}
for mat, tex, names in MATERIALS:
    RV.write_mask([weights[(tex, n)] for n in names], T / f'hyd_{mat}_mask.png', size=HALF[tex])
for tex in SETS:
    Image.fromarray(classes[tex]).resize(HALF[tex], Image.NEAREST).save(T / f'hyd_{tex}_material_classes.png')
    ao = Image.open(T / f'hyd_{tex}_ao.png').convert('L').resize(HALF[tex], Image.LANCZOS)
    rough = Image.open(T / f'hyd_{tex}_roughness.png').convert('L').resize(HALF[tex], Image.LANCZOS)
    Image.merge('RGB', (ao, rough, Image.new('L', HALF[tex], 0))).save(T / f'hyd_{tex}_metal_rough.png')


def native(palette, rects):
    out = []
    for frame, x0, y0, x1, y1 in rects:
        nv = np.asarray(Image.open(NATIVE / 'native_variants' / f'{frame}_{palette}.png').convert('RGBA'),
                        np.float32)[y0:y1, x0:x1] / 255
        out.append(nv[nv[..., 3] > 0.5, :3])
    return lin(np.concatenate(out))


# head neck stubs, throats and jaw undersides: Meshy painted its own neck there (a pale sawtooth fringe where the jaw meets it,
# crumpled spikes); that zone blends into the neck colour, so its brightness is smoothed (masked blur per head, so no
# other island bleeds in), keeping STUB_DETAIL of the original detail. Read from the grade's fresh output
# (*_graded_pre.png, refreshed whenever grade_basecolor.py has rewritten *_graded.png), so reruns do not compound.
pre, out_ = T / 'hyd_head_basecolor_graded_pre.png', T / 'hyd_head_basecolor_graded.png'
if not pre.exists() or out_.stat().st_mtime > pre.stat().st_mtime + 1:
    Image.open(out_).save(pre)
hg = np.asarray(Image.open(pre).convert('RGB'), np.float64) / 255
hlum = hg @ W
zone = np.zeros(head_valid.shape)          # no stub left to flatten (heads cut behind the skull)
zone = ndimage.gaussian_filter(zone, 2.0) * head_valid
smooth_lum = hlum.copy()
for k in range(1, 6):
    mk = (head_of == k).astype(np.float64)
    num = ndimage.gaussian_filter(hlum * mk, STUB_SIGMA); den = ndimage.gaussian_filter(mk, STUB_SIGMA)
    smooth_lum = np.where(head_of == k, num / np.maximum(den, 1e-4), smooth_lum)
target = smooth_lum * (1 - STUB_DETAIL) + hlum * STUB_DETAIL
new_lum = hlum * (1 - zone) + target * zone
hg = np.clip(hg * (new_lum / np.maximum(hlum, 1e-4))[..., None], 0, 1)
Image.fromarray((hg * 255 + 0.5).astype(np.uint8)).save(out_)
import os; os.utime(pre, None)
graded = {tex: RV.load_srgb(T / f'hyd_{tex}_basecolor_graded.png').copy() for tex in SETS}
graded = {tex: np.asarray(Image.fromarray((g * 255 + 0.5).astype(np.uint8)).resize(HALF[tex], Image.LANCZOS),
                          np.float64) / 255 for tex, g in graded.items()}


def fit(tex, weight, rects, albedo, sat, top=0.95):
    g = graded[tex]; core = weight > 0.5
    lum = RV.srgb_to_linear(g[core]) @ W
    rank = (np.argsort(np.argsort(lum)) + 0.5) / lum.size
    targets = {}
    for k, p in PALETTES.items():
        pal = native(p, rects); pal = pal[np.argsort(pal @ W)]
        mid = pal[int(0.15 * len(pal)):int(top * len(pal))]
        band = np.array([(b / np.maximum(b @ W, 1e-3)[:, None]).mean(0) for b in np.array_split(mid, 8)])
        x = rank * (len(band) - 1); i0 = np.minimum(x.astype(int), len(band) - 2); f = (x - i0)[:, None]
        chroma = np.clip(1 + (band[i0] * (1 - f) + band[i0 + 1] * f - 1) * sat, 0, None)
        gain = albedo * float((pal @ W).mean()) / float(lum.mean())
        tgt = g.copy(); tgt[core] = encode(np.clip(chroma * (lum * gain)[:, None], 0, 1))
        targets[k] = tgt
    return RV.fit_ramps(g, targets, weight)


import native_shading as NS
NECK_TRANSFER_GAIN = 1.25


def neck_pixels(name):
    """The native sample pixels of a neck or the body in every palette (sRGB, aligned), as NS.transfer_ramps wants."""
    rects = BODY_RECTS if name == 'body' else NECK_RECTS[int(name[1])]
    out = {}
    for k, p in PALETTES.items():
        px = []
        for frame, x0, y0, x1, y1 in rects:
            ref = np.asarray(Image.open(NATIVE / 'native_variants' / f'{frame}_754.png').convert('RGBA'),
                             np.float64)[y0:y1, x0:x1] / 255
            tier = np.asarray(Image.open(NATIVE / 'native_variants' / f'{frame}_{p}.png').convert('RGB'),
                              np.float64)[y0:y1, x0:x1] / 255
            px.append(tier[ref[..., 3] > 0.5])
        out[f'p{p}'] = np.concatenate(px)
    n = len(out['p754'])
    return dict(out, region=np.zeros(n, int), region_names=np.array([name]))


fitted, report = {}, []
for tex in SETS:
    for n in masks[tex]:
        if NECK_TRANSFER and (n == 'body' or n[0] == 'N') and (weights[(tex, n)] > 0.9).sum() >= 100:
            # necks and body: palette transfer (../NATIVE_SHADING_TRANSFER.md): each ramp stop takes the colour of the
            # native sample pixels nearest in luminance (in palette 754), read in the tier's palette; the chroma-only
            # fit kept the texture's pale grey bellies (user check 2026-10-09: necks paler and greyer than the sprites)
            r = NS.transfer_ramps(graded[tex], {n: weights[(tex, n)]}, neck_pixels(n), {n: n},
                                  {k: int(p) for k, p in PALETTES.items()}, reference=754,
                                  gain={n: NECK_TRANSFER_GAIN})
            fitted[(tex, n)] = {k: v[0] for k, v in r.items()}
            continue
        top = 0.95
        if n == 'body':
            rects, albedo, sat = BODY_RECTS, ALBEDO, 1.0
        elif n == 'F4':
            rects, albedo, sat = FIN_RECTS, HEAD_ALBEDO, HEAD_SAT
        elif n[0] == 'N':
            rects, albedo, sat = NECK_RECTS[int(n[1])], ALBEDO, 1.0
        else:
            # head samples stop at the 85th percentile: the brightest native head pixels are eyes and glints
            rects, albedo, sat, top = HEAD_RECTS[int(n[1])], HEAD_ALBEDO, HEAD_SAT, 0.85
        if (weights[(tex, n)] > 0.9).sum() < 100:
            # a region with (almost) no texels: copy the body texture's ramp of the same name (unused anyway)
            fitted[(tex, n)] = fitted[('body', n)]; continue
        fitted[(tex, n)], rep = fit(tex, weights[(tex, n)], rects, albedo, sat, top)
        report.append({'texture': tex, 'region': n, **{k: v['mean_abs_8bit'] for k, v in rep.items()
                                                        if k.startswith('hyd')}})
json.dump({'variants': list(PALETTES), 'palettes': PALETTES, 'report': report,
           'materials': [{'base': mat, 'prefix': mat, 'mask': f'hyd_{mat}_mask.png',
                          'ramps': {k: [fitted[(tex, n)][k] for n in names] for k in PALETTES}}
                         for mat, tex, names in MATERIALS]},
          open(T / 'hyd_ramps.json', 'w'), indent=1)
COLOURS = {'body': (0.3, 0.5, 0.2), 'N1': (0.6, 0.6, 0.2), 'N2': (0.6, 0.2, 0.7), 'N3': (0.2, 0.8, 0.3),
           'N4': (0.9, 0.2, 0.1), 'N5': (0.2, 0.3, 0.9)}
(ROOT / 'review').mkdir(exist_ok=True)
for tex in SETS:
    preview = base[tex] * 0.3
    for n, m in masks[tex].items():
        preview[m] = (1.0, 0.8, 0.5) if n == 'F4' else COLOURS.get(n) or tuple(min(1.0, x * 1.4 + 0.25)
                                                                               for x in COLOURS['N' + n[1]])
    cls = classes[tex]
    preview[cls == 4] = (1, 1, 0.85); preview[cls == 6] = (1, 0.9, 0); preview[cls == 7] = (0.6, 0, 0)
    Image.fromarray((preview * 255).astype(np.uint8)).save(ROOT / 'review' / f'texture_classes_{tex}.png')
print('COMPOSED', json.dumps(report), 'face materials', np.bincount(face_mat, minlength=5).tolist())
