#!/usr/bin/env python3
"""v3 runtime maps from the three Meshy retextures (meshy/{body,head}_retexture_v3 and wings_retexture_v3b, 4K, original UVs, the
render-guided masters in references_hd_v3/), per texture set at 2K: AO-graded base colour, tangent normal (glTF +Y
up), specular/roughness (MR red = specular mask, green = roughness), RGBA region mask (R scales, G membranes (head set: iris),
B ventral gold, A spines), material classes; ramps from the MM7 palettes 183/184/185 (colour from the palette, brightness from the texel).

Body/head seam (the user flagged a white patch and a pale stripe at the v2 head/neck seam, then a collar and a
blocky throat patch in v3a): the join (the lofted neck and the faired head stub, scripts/v3/reshape_neck.py) is
painted as a continuation of the cdr1 neck (plates and scales translated by whole plate periods, mirror image for the
first 1.5 cm after the cut, fade into the head paint in front of the stub plane); the head set's hide and gold
luminance are quantile-matched to the body's, and a 4 cm band in front of the stub plane takes the mean colour of the
continuation behind it, so both sets give one colour under every ramp.
Classes by position and colour: spines = the procedural blades (v3part 3) and the yellow head frill; ivory (horns,
teeth, claws, wing spurs, and Meshy's cyan specks on the wing spurs) painted clean enamel; eyes by position (red
iris, slit pupil); mouth interior kept. Wings: membrane faces (baked flag) form the membrane region, bones join the
scale region.
Out: textures/v3/m182v3_{body,head,wings}_{basecolor_2k,normal_2k,metal_rough_2k,region_mask,material_classes,ao}.png,
textures/v3/m182v3_ramps.json (per material name), work/v3/compose_report.json."""
import json, os, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree
P = Path(__file__).resolve().parents[2]; REPO = P.parents[2]; M = P / 'meshy'; BK = P / 'work/v3/bake'
T = P / 'textures/v3'; T.mkdir(parents=True, exist_ok=True); N = 2048
sys.path.insert(0, str(P.parent / 'claude_shared')); import region_variants as R  # noqa: E402
sys.path.insert(0, str(REPO / 'tools')); from normal_map_convention import measure  # noqa: E402
sys.path.insert(0, str(P / 'scripts')); from straighten import straighten  # noqa: E402
Wl = np.array([.2126, .7152, .0722]); lin = R.srgb_to_linear
enc = lambda c: np.where(c <= .0031308, c * 12.92, 1.055 * np.maximum(c, 0) ** (1 / 2.4) - .055)
GAIN = 1.3
VARIANTS = {'m182_a': 183, 'm182_b': 184, 'm182_c': 185}
LABELS = ['body', 'head', 'wings']; MATS = {'body': 'DragonBody', 'head': 'DragonHead', 'wings': 'DragonWings'}


def load(p, mode='RGB'): return np.array(Image.open(p).convert(mode).resize((N, N), Image.Resampling.LANCZOS), float) / 255
def save(a, p): Image.fromarray(np.uint8(np.clip(a, 0, 1) * 255 + .5)).save(p)
def pad(a, cov): return a[tuple(ndimage.distance_transform_edt(~cov, return_distances=False, return_indices=True))]
def hsv(rgb):
    h, s, v = np.moveaxis(np.array(Image.fromarray(np.uint8(np.clip(rgb, 0, 1) * 255)).convert('HSV'), float) / 255, -1, 0)
    return h * 360, s, v
def quantile_match(lum, sel, target):
    q = np.linspace(0, 100, 201); sq = np.maximum.accumulate(np.percentile(lum[sel], q) + np.arange(201) * 1e-9)
    return np.interp(lum, sq, np.percentile(target, q))


D = {}; rep = {}
for label in LABELS:
    src = M / (f'{label}_retexture_v3b' if label == 'wings' else f'{label}_retexture_v3')   # wings: v3b (inner panels as membrane)
    attr = np.load(BK / f'{label}_attr.npy'); cov = attr[..., 2] > .5
    d = {'rgb': load(src / 'texture_urls_0_base_color.png'), 'cov': cov, 'pos': np.load(BK / f'{label}_pos.npy')[..., :3],
         'nrm': np.load(BK / f'{label}_nrm.npy')[..., :3], 'patch': (attr[..., 1] > .5) & (label != 'wings'),
         'hpiece': np.rint(np.floor(attr[..., 0] + 1e-3)).astype(int),
         'part': np.rint((attr[..., 0] - np.floor(attr[..., 0] + 1e-3)) * 4).astype(int),
         'partf': (attr[..., 0] - np.floor(attr[..., 0] + 1e-3)) * 4,
         'memb': attr[..., 1] > .5, 'ao': ndimage.gaussian_filter(load(BK / f'{label}_ao.png', 'L'), 1.0),
         'rough': load(src / 'texture_urls_0_roughness.png', 'L')}
    nm = load(src / 'texture_urls_0_normal.png'); corr = measure(np.uint8(nm * 255 + .5))
    if corr < 0: nm[..., 1] = 1 - nm[..., 1]
    d['normal'] = nm; rep[label] = {'covered': int(cov.sum()), 'meshy_normal_correlation': round(float(corr), 3)}
    D[label] = d

# ---------------- neck continuation (v3b: loft and the faired head stub) ----------------
# The join (the lofted neck in the body set and the head's neck stub in the head set, both refitted by
# scripts/v3/reshape_neck.py) is painted as a continuation of the cdr1 neck: every texel takes the Meshy body paint
# of the cdr1 neck at its own position translated back along the neck by whole plate periods (P = 0.05 m, the
# autocorrelation peak of the ventral plates behind the cut), so plates and scales keep their shape, size and
# spacing up to the chin; over the first 4 cm after the cut Meshy's own continuous paint hands over to it;
# head-stub texels fade to the head's own paint over 2.5 cm in front of the stub plane.
PLATE = .05
g = np.load(P / 'work/v3/graft.npz')
pl = json.loads((P / 'work/v3/cut_plane.json').read_text()); c0 = np.array(pl['centre']); n0 = np.array(pl['normal'])
rs = json.loads((P / 'work/v3b/reshape_report.json').read_text())
Jc = np.array(rs['jaw_hinge']); sax = np.array(rs['skull_axis']); spl = np.array(rs['stub_plane_point'])
u_n = n0 + sax; u_n /= np.linalg.norm(u_n)
b, h_ = D['body'], D['head']
loft = b['cov'] & (b['partf'] > 1.5) & (b['partf'] < 2.5)
targets = {'body': loft | (b['cov'] & b['patch']), 'head': h_['cov'] & h_['patch']}
# neck coordinates: arc s along the neck centreline (the cdr1 centreline behind the cut, then straight on to the
# stub plane) and angle round it in rotation-minimising frames; donors are the cdr1 neck at the same angle and
# s - m * PLATE (angle from the surface normal; m whole periods, landing 1-11 cm behind the cut), so the plates keep their row and spacing even
# where the neck bends.
# (the slab centres of cut_plane.json zigzag by +-4 cm: the cdr1 neck behind the cut is taken as straight along the
# cut normal, then on to the skull-slice centre; the jaw hinge sits low in the head)
cl = np.array([c0 - .25 * n0, c0 - .12 * n0, c0, np.array(rs['neck_end_centre'])])
seg = np.linspace(0, 1, 30)[:, None]
dense = np.vstack([cl[i] + (cl[i + 1] - cl[i]) * seg for i in range(len(cl) - 1)])
arc = np.r_[0, np.cumsum(np.linalg.norm(np.diff(dense, axis=0), axis=1))]; s_cut = arc[np.argmin(np.linalg.norm(dense - c0, axis=1))]
Tg = np.gradient(dense, axis=0); Tg /= np.linalg.norm(Tg, axis=1, keepdims=True)
Uf = [np.array([0, 0, 1.]) - Tg[0] * Tg[0, 2]]; Uf[0] /= np.linalg.norm(Uf[0])
for i in range(1, len(dense)):
    u = Uf[-1] - Tg[i] * (Uf[-1] @ Tg[i]); Uf.append(u / np.linalg.norm(u))
Uf = np.array(Uf); Sf = np.cross(Tg, Uf); ctree = cKDTree(dense)
def neckcoord(p, nrm_):
    # angle round the neck from the surface normal (robust to an off-centre centreline through the faired join)
    k = ctree.query(p)[1]; q = p - dense[k]; return arc[k] + (q * Tg[k]).sum(-1) - s_cut, np.arctan2((nrm_ * Sf[k]).sum(-1), (nrm_ * Uf[k]).sum(-1))
bsel = b['cov'] & (b['part'] == 0) & ~b['patch'] & (np.linalg.norm(b['pos'] - c0, axis=-1) < .45)
bs, bth = neckcoord(b['pos'][bsel], b['nrm'][bsel]); keepd = (bs < -.004) & (bs > -.2)
bidx = np.argwhere(bsel)[keepd]; R_ = .07
emb = lambda s_, th: np.c_[s_, R_ * np.cos(th), R_ * np.sin(th)]    # angle on a circle: no wrap at +-pi
bt = cKDTree(emb(bs[keepd], bth[keepd]))
rep['neck_continuation'] = {'centreline_points': len(cl), 'plate_period_m': PLATE}
for label, tgt in targets.items():
    d = D[label]; p = d['pos'][tgt]; ts_, tth = neckcoord(p, d['nrm'][tgt])
    m = np.maximum(np.ceil((ts_ + .01) / PLATE), 1); qs = ts_ - m * PLATE
    ic = bidx[bt.query(emb(qs, tth))[1]]; col = b['rgb'][ic[:, 0], ic[:, 1]]; nm_ = b['normal'][ic[:, 0], ic[:, 1]]
    # at the cut, Meshy's own paint of the loft is continuous with the cdr1 neck (one paint over both): it hands over
    # to the continuation over the first 4 cm
    w = np.clip(ts_ / .04, 0, 1); w = (w * w * (3 - 2 * w))[:, None]
    col = (1 - w) * d['rgb'][tgt] + w * col; nm_ = (1 - w) * d['normal'][tgt] + w * nm_
    keep = np.ones(len(p))
    if label == 'head':
        behind = (spl - p) @ sax                   # > 0: behind the stub plane (towards the neck)
        ventral = d['nrm'][tgt] @ np.array([0, 0, -1.]) > .35
        reach = np.where(ventral, -.02, 0.)        # the throat plates run 2 cm further, up to the jaw hinge
        keep = np.clip((behind - reach) / .025, 0, 1); keep = keep * keep * (3 - 2 * keep)
    keep = keep[:, None]
    d['rgb'][tgt] = keep * col + (1 - keep) * d['rgb'][tgt]; d['normal'][tgt] = keep * nm_ + (1 - keep) * d['normal'][tgt]
    rep['neck_continuation'][label] = int(tgt.sum())
c1 = spl; n1 = -sax                                 # the head-side seam for the colour band below
# ---------------- classes ----------------
JC = np.array([0, -1.37, .91])
gp = json.loads((P / 'work/v3/graft_params.json').read_text())
V = np.load(P / 'work/v3/v2_master.npz'); Jv = V['heads'][list(V['bones']).index('Jaw')]
def head_xf(p):
    q = p - Jv; k = .004; soft = -k * np.logaddexp(0, -q[:, 1] / k); q[:, 1] = q[:, 1] + (gp['snout_stretch'] - 1) * soft
    A = np.load(P / 'work/v3/src.npz'); jc = A['heads'][list(A['bones']).index('Jaw')]
    return jc + gp['scale'] * q
EYE = head_xf(straighten(np.array([[.0022, -.3525, .4283]])))[0]; EYE[0] = abs(EYE[0])
_a = np.radians(rs['pitch_deg']); _R = np.array([[1, 0, 0], [0, np.cos(_a), -np.sin(_a)], [0, np.sin(_a), np.cos(_a)]])
EYE = Jc + _R @ (EYE - Jc)                     # the v3b head pitch (scripts/v3/reshape_neck.py) turns the eye too
rep['eye_centre'] = EYE.round(4).tolist()
for label in LABELS:
    d = D[label]; rgb, cov, pos, nrm = d['rgb'], d['cov'], d['pos'], d['nrm']; H, S, Vv = hsv(rgb)
    classes = np.zeros((N, N), np.uint8); classes[cov] = 1
    ivory = cov & (S < .26) & (Vv > .55)
    cyan = cov & (H > 165) & (H < 215) & (S > .25) & (label == 'wings')   # Meshy's turquoise specks on the wing spurs
    gold = cov & (H > 35) & (H < 65) & (S > .35) & (Vv > .30)
    eye = np.zeros((N, N), bool); mouth = np.zeros((N, N), bool); spines = np.zeros((N, N), bool); memb = np.zeros((N, N), bool)
    if label == 'body':
        spines = cov & (d['part'] == 3)
        # ivory only on the claws and ankle spurs (low on the legs, off the midline); elsewhere pale texels are the
        # light seams Meshy paints between plates and scales and stay in their region
        ivory &= ~spines & (pos[..., 2] < .45) & (np.abs(pos[..., 0]) > .06); gold &= ~spines
    if label == 'head':
        ex = np.abs(pos[..., 0])
        eye = cov & (np.linalg.norm(np.stack([ex, pos[..., 1], pos[..., 2]], -1) - EYE, axis=-1) < .018)
        mouth = cov & ((H < 22) | (H > 330)) & (S > .35) & (pos[..., 1] < -1.38) & (pos[..., 2] < 1.0) & ~eye
        ventral = nrm[..., 2] < -.3
        teeth = ivory & (d['hpiece'] == 1) & (pos[..., 1] < -1.4) & (pos[..., 2] < 1.0); classes[teeth] = 5
        horn = cov & (d['hpiece'] == 2)
        # the frill: yellow-green and pale spikes of the main surface and the cheek spikes (MM7: yellow frill)
        frill = cov & ~horn & ~teeth & ~mouth & ~eye & (((H > 45) & (H < 110) & (S > .30) & (Vv > .35)) | ((S < .26) & (Vv > .55)) | (d['hpiece'] == 3))
        gold = gold & ventral & ~eye & ~mouth & ~frill
        spines = frill
        ivory = horn | teeth
    if label == 'wings':
        # membrane: wing faces off the wing bone chain (scripts/v3/wing_classes.py, baked per texel)
        memb = cov & d['memb']
        # soft root: within 4 cm of the wing/body junction the membrane share fades to the scale region, so the
        # pale membrane meets the dark hide of the shoulder through a gradient instead of a cut
        pre = np.load(P / 'work/v3b/pre_reshape.npz'); ptri, pmat = pre['tri'], pre['mat']
        jv = np.intersect1d(np.unique(ptri[pmat == 0]), np.unique(ptri[pmat == 2])); jpos = pre['co'][jv]
        djn = np.full((N, N), 9.); djn[cov] = cKDTree(jpos).query(pos[cov])[0]
        root_w = np.clip(djn / .04, 0, 1); root_w = root_w * root_w * (3 - 2 * root_w); d['root_w'] = root_w
        ivory = cov & ~memb & (((S < .2) & (Vv > .62)) | cyan)
        gold &= False
    ivory |= cyan & ~memb
    scales = cov & ~ivory & ~gold & ~spines & ~memb & ~eye & ~mouth
    classes[memb] = 3; classes[ivory & (classes != 5)] = 4; classes[eye] = 6; classes[mouth] = 7
    d.update({'ivory': ivory, 'eye': eye, 'mouth': mouth, 'masks': [scales, memb, gold, spines], 'classes': classes})

# thin pale lines (Meshy paints some UV-seam edges near white): texels much brighter than their 7x7 neighbourhood
# median inside the hide take that median
for label in ('body', 'head'):
    d = D[label]; l_ = d['rgb'] @ Wl; med = np.stack([ndimage.median_filter(d['rgb'][..., c], 7) for c in range(3)], -1)
    surf = d['cov'] if label == 'body' else d['cov'] & (d['hpiece'] == 1)
    hot = surf & (d['masks'][0] | d['masks'][3]) & ~(d['part'] == 3) & (l_ > 1.8 * (med @ Wl) + .04)
    hot = ndimage.binary_dilation(hot) & surf & ~d['ivory'] & ~d['eye']
    d['rgb'][hot] = med[hot]; d['masks'][0] = d['masks'][0] | hot; d['masks'][3] = d['masks'][3] & ~hot
    rep.setdefault('pale_lines_fixed', {})[label] = int(hot.sum())
# pale seams inside the hide and gold regions: luminance above the region's 96th percentile is compressed towards it
# (they would take the ramps' palest stops and read as white lines along the plate edges)
for label in LABELS:
    d = D[label]; out = lin(d['rgb']); l_ = out @ Wl
    for k in (0, 2):
        sel = d['masks'][k]
        if sel.sum() < 100: continue
        cap = np.percentile(l_[sel], 96); over = sel & (l_ > cap)
        tgt = cap + (l_[over] - cap) * .25; out[over] *= (tgt / np.maximum(l_[over], 1e-6))[:, None]
    d['rgb'] = np.clip(enc(np.clip(out, 0, 1)), 0, 1)
# head colour onto the body's: hide and gold luminance quantile-matched (hue and detail kept)
bl = lin(D['body']['rgb']) @ Wl
for k in (0, 2):
    sel_b = D['body']['masks'][k] & ~loft
    hd = D['head']; hl = lin(hd['rgb']) @ Wl; sel = hd['masks'][k] & ~hd['patch']     # the patch is body paint already
    if sel.sum() > 100 and sel_b.sum() > 100:
        m = quantile_match(hl, sel, bl[sel_b]); ratio = np.where(hl > 1e-5, m / np.maximum(hl, 1e-5), 1.)
        out = lin(hd['rgb']); out[sel] *= ratio[sel, None]; hd['rgb'] = np.clip(enc(np.clip(out, 0, 1)), 0, 1)
# wing bones (scale region of the wing set): Meshy painted them darker than the hide they grow out of at the
# shoulder; their luminance is quantile-matched to the body hide so one scales ramp colours both alike
wd = D['wings']; wl = lin(wd['rgb']) @ Wl; sel = wd['masks'][0]
m = quantile_match(wl, sel, bl[D['body']['masks'][0] & ~loft]); ratio = np.where(wl > 1e-5, m / np.maximum(wl, 1e-5), 1.)
out = lin(wd['rgb']); out[sel] *= ratio[sel, None]; wd['rgb'] = np.clip(enc(np.clip(out, 0, 1)), 0, 1)
# seam band: head texels within 6 cm of the ring take the mean colour offset to the loft's last texels
hd = D['head']; near_h = hd['cov'] & ~hd['patch'] & (np.abs((hd['pos'] - c1) @ n1) < .04) & (np.linalg.norm(hd['pos'] - c1, axis=-1) < .25)
last_loft = hd['cov'] & hd['patch'] & (((spl - hd['pos']) @ sax) > .025) & (((spl - hd['pos']) @ sax) < .05)
for k in (0, 2):
    a_ = near_h & hd['masks'][k]; b_ = last_loft & hd['masks'][k]
    if a_.sum() > 50 and b_.sum() > 50:
        off = hd['rgb'][b_].mean(0) - hd['rgb'][a_].mean(0)
        fall = np.clip(1 - np.abs((hd['pos'] - c1) @ n1) / .04, 0, 1)
        hd['rgb'][a_] = np.clip(hd['rgb'][a_] + off * fall[a_, None], 0, 1)
        rep.setdefault('seam_offset', {})[['scales', '', 'gold'][k]] = np.round(off, 3).tolist()

# ---------------- paint, grade, write ----------------
for label in LABELS:
    d = D[label]; rgb = d['rgb']; cov = d['cov']; ao = d['ao']
    l2 = rgb @ Wl
    rgb[d['ivory']] = np.clip((.76 + .20 * l2[d['ivory'], None]) * np.array([1., .98, .87]), 0, 1)
    if d['eye'].any():
        for side in (-1, 1):
            sel = d['eye'] & (np.sign(d['pos'][..., 0]) == side)
            if not sel.any(): continue
            c = d['pos'][sel].mean(0); a = d['nrm'][sel].mean(0); a /= np.linalg.norm(a)
            up = np.array([0, 0, 1.]) - a * a[2]; up /= np.linalg.norm(up); across = np.cross(a, up)
            q = d['pos'][sel] - c; q = q - np.outer(q @ a, a); Rr = np.percentile(np.linalg.norm(q, axis=1), 98)
            r = np.linalg.norm(q, axis=1) / max(Rr, 1e-6); qa = (q @ across) / Rr; qu = (q @ up) / Rr
            col = np.where(r[:, None] < .8, np.array([.95, .16, .08]) * (1.05 - .5 * r[:, None]), np.array([.22, .05, .03]))
            slit = (np.abs(qa) < .12 * np.sqrt(np.clip(1 - (qu / .8) ** 2, 0, 1))) & (r < .8); col[slit] = [.03, .01, .01]
            rgb[sel] = col
            iris = np.zeros_like(sel); iris[sel] = (r < .8) & ~slit; d['masks'][1] = d['masks'][1] | iris   # head G: iris
    rgb = rgb * (.82 + .18 * ao[..., None])
    nm = d['normal']; flat = d['ivory'] | d['eye']; nm[flat] = nm[flat] * .35 + np.array([.5, .5, 1.]) * .65
    rough = np.clip(d['rough'] * .3 + .8 * .7, 0, 1); spec = np.full((N, N), .14)
    for cls, r_, s_ in [(3, .84, .10), (4, .45, .35), (5, .35, .45), (6, .15, .55), (7, .75, .08)]:
        rough[d['classes'] == cls] = r_; spec[d['classes'] == cls] = s_
    spec *= .35 + .65 * ao
    d['rgb'] = rgb
    save(pad(rgb, cov), T / f'm182v3_{label}_basecolor_2k.png'); save(pad(nm, cov), T / f'm182v3_{label}_normal_2k.png')
    save(np.stack([pad(spec, cov), pad(rough, cov), np.zeros_like(spec)], -1), T / f'm182v3_{label}_metal_rough_2k.png')
    save(pad(ao, cov), T / f'm182v3_{label}_ao.png')
    Image.fromarray(pad(d['classes'], cov)).save(T / f'm182v3_{label}_material_classes.png')
    weights = [ndimage.gaussian_filter(pad(m.astype(float), cov), .65) for m in d['masks']]
    if 'root_w' in d:      # wings: membrane weight hands over to the scale ramp at the root
        rw = pad(d['root_w'], cov); mw = weights[1] * rw; weights[0] = np.clip(weights[0] + (weights[1] - mw), 0, 1); weights[1] = mw
    R.write_mask(weights, T / f'm182v3_{label}_region_mask.png', size=N)
    rep[label] |= {'region_texels': [int(m.sum()) for m in d['masks']], 'ivory': int(d['ivory'].sum()), 'eye': int(d['eye'].sum()), 'mouth': int(d['mouth'].sum())}

# ---------------- ramps ----------------
# Each tier's own palette per region (native pixel index sets of the restored package as v2; membranes: only the
# grey-green entries of the side views; spines: the saturated entries of the accent sets). Colour only from the palette, brightness from the texel
# (sea-serpent route, CLAUDE_QUADRUPED_PLAYBOOK "Snakes"): for a ramp stop at texel luminance L the chroma is the
# native colour at the same luminance rank, taken from the palette's 15th-95th percentile and averaged into 8 bands,
# and the brightness is L x ALBEDO x native mean / texel mean. Plain rank matching (v2) mapped Meshy's light scale
# centres onto the sprites' baked white highlights and turned the hide grey and speckled.
ALBEDO = 1.35
# native luminance-rank window per region (chroma bands and brightness): the darkest native pixels are painted
# shadow; gold and spines use their upper ranks (olive shadow entries made the blue tier's belly green)
WINDOW = {0: (.10, .85), 1: (.15, .95), 2: (.35, .98), 3: (.40, .98)}
manifest = json.loads((REPO / 'level_generation/creatures/mm7_m182/manifest.json').read_text())
index_sets = [r['native_indices'] for r in manifest['variants'][0]['regions']] + [list(range(88, 104))]
sprites = REPO / 'assets_dev/engine/sprites'; listing = {e.lower(): e for e in os.listdir(sprites)}
frames = ('sa', 'wa', 'wb', 'wc', 'wd', 'we', 'wf')
ids = np.concatenate([np.asarray(Image.open(sprites / listing[f'm182{a}{v}.bmp'])).ravel() for a in frames for v in range(5)]); ids = ids[ids != 0]
side_ids = np.concatenate([np.asarray(Image.open(sprites / listing[f'm182{a}{v}.bmp'])).ravel() for a in frames for v in (1, 2, 3)]); side_ids = side_ids[side_ids != 0]
pal = {pid: np.frombuffer((REPO / f'assets_dev/worlds/mm7/textures/pal{pid}.act').read_bytes()[:768], np.uint8).reshape(256, 3) / 255 for pid in VARIANTS.values()}
ramps = {f'{MATS[l]}_{v[-1].upper()}': [] for l in LABELS for v in VARIANTS}; ramp_report = []
for region, index_set in enumerate(index_sets):
    lum = np.concatenate([R.luminance(D[l]['rgb'])[D[l]['masks'][region]] for l in LABELS
                          if D[l]['masks'][region].any() and not (region == 1 and l == 'head')])
    values = np.sort(lum); lo, hi = np.percentile(values, [.5, 99.5]); stops_l = np.linspace(lo, hi, 16)
    rank = np.searchsorted(values, stops_l) / len(values)
    native = (side_ids if region == 1 else ids); native = native[np.isin(native, index_set)]
    if region == 1:
        c = pal[183][native]; sat = (c.max(1) - c.min(1)) / np.maximum(c.max(1), 1e-6); native = native[sat < .45]
    if region == 3:      # spines: the saturated (yellow-green in tier A) entries of the spine and accent sets only
        native = ids[np.isin(ids, list(index_sets[1]) + list(range(88, 104)))]
        c = pal[183][native]; sat = (c.max(1) - c.min(1)) / np.maximum(c.max(1), 1e-6); native = native[sat >= .5]
    entry = {'region': ['scales', 'membranes', 'ventral_gold', 'spines'][region], 'texels': int(len(values)), 'range': [float(lo), float(hi)],
             'texel_mean_lum': float(values.mean()), 'native_pixels': int(len(native))}
    for vname, pid in VARIANTS.items():
        cols = R.srgb_to_linear(pal[pid][native]); cols = cols[np.argsort(cols @ Wl)]
        pl, ph = WINDOW[region]; mid = cols[int(pl * len(cols)):int(ph * len(cols))]
        band = np.array([(bb / np.maximum(bb @ Wl, 1e-3)[:, None]).mean(0) for bb in np.array_split(mid, 8)])
        x = np.clip(rank, 0, 1) * (len(band) - 1); i0 = np.minimum(x.astype(int), len(band) - 2); f = (x - i0)[:, None]
        chroma = band[i0] * (1 - f) + band[i0 + 1] * f
        gain = ALBEDO * float((mid @ Wl).mean()) / float(values.mean())
        stops = np.clip(chroma * (stops_l * gain)[:, None], 0, 1)
        for l in LABELS: ramps[f'{MATS[l]}_{vname[-1].upper()}'].append({'range': [float(lo), float(hi)], 'colors': stops.tolist()})
        entry[f'{vname}_gain'] = round(gain, 3); entry[f'{vname}_native_mean_srgb'] = np.round(enc(cols.mean(0)), 3).tolist()
    ramp_report.append(entry)
# head set G channel = the iris: the native eye entries 86 (dark) and 87 (bright) of each palette (183 red,
# 184 green, 185 amber), over the painted iris' luminance range
ilum = R.luminance(D['head']['rgb'])[D['head']['masks'][1]]; ilo, ihi = np.percentile(ilum, [1, 99])
for vname, pid in VARIANTS.items():
    dark, bright = R.srgb_to_linear(pal[pid][86]), R.srgb_to_linear(pal[pid][87])
    stops = [np.clip((dark * (1 - f) + bright * f) * (1.1 if f > .5 else 1.0), 0, 1).tolist() for f in np.linspace(0, 1, 16)]
    ramps[f'DragonHead_{vname[-1].upper()}'][1] = {'range': [float(ilo), float(ihi)], 'colors': stops}
ramp_report.append({'region': 'head iris (head set G)', 'range': [float(ilo), float(ihi)], 'palette_entries': [86, 87]})
(T / 'm182v3_ramps.json').write_text(json.dumps(ramps, indent=1) + '\n')
rep['ramps'] = ramp_report
(P / 'work/v3/compose_report.json').write_text(json.dumps(rep, indent=1) + '\n')
print('COMPOSE', json.dumps({k: v for k, v in rep.items() if k != 'ramps'}))
