"""Full uv npz from the frozen body atlas (work/uv_body_v1.npz, uv_lk.py on asm3) and the current asm4 (asm3 + staff + staff skull; asm3's vertex
and face order are a prefix of asm4's). Materials: 0 'LichKing' body atlas, 1 'LichKingHead' (the skull and the staff skull on the Lich's head set),
2 'LichKingStaff' (shaft, cylindrical UV: u round, v along), 9 the body-atlas skull (Meshy upload occluder only; build drops it).
Args: <asm4 npz> <uv body npz> <lich skull npz> <out npz>"""
import sys, numpy as np
A4, UB, SK, OUT = sys.argv[1:5]
D = np.load(A4); co, tri, comp = D['co'], D['tri'], D['comp']; names = [str(x) for x in D['names']]
U = np.load(UB); fo, cs, lin_f = U['fo'], U['corners'], U['lining']
k = names.index('skull'); k2 = names.index('sskull'); ks = names.index('staff'); fc = comp[tri[:, 0]]
S = np.load(SK); suv = S['uv'] * [1, -1] + [0, 1]                     # glTF v down -> Blender v up
sk_uv = np.zeros((len(co), 2)); sk_uv[np.where(comp == k)[0]] = suv; sk_uv[np.where(comp == k2)[0]] = D['sskull_uv'] * [1, -1] + [0, 1]
V = {}; pos = []; uv = []; orig = []; T = []; mat = []; part = []; lin = []
def emit(vi, m, u, v):
    key = (int(vi), m, round(float(u), 6), round(float(v), 6))
    if key not in V:
        V[key] = len(pos); pos.append(co[vi]); uv.append((u, v)); orig.append(vi); part.append(comp[vi])
    return V[key]
# r7: the crown's brow band ran inside the skull (moved into the crown in r2) and showed as a silver bar through the eye sockets:
# its front arc (|x| < 7 cm, z 1.44-1.515, in front of the head's centre) is dropped; it sat behind the face
cen_ = co[tri].mean(1); kcr = names.index('crown')
band_drop = np.zeros(len(fc), bool) & (fc == kcr)      # r9: tuck_band.py moves the arc inside the skull instead
_unused = (fc == kcr) & (np.abs(cen_[:, 0]) < 0.07) & (cen_[:, 2] > 1.44) & (cen_[:, 2] < 1.515) & (cen_[:, 1] < -0.03)
print('crown band faces dropped', int(band_drop.sum()))
for f, c, l in zip(fo, cs, lin_f):
    if band_drop[f]: continue
    m = 9 if fc[f] == k else 0
    if m == 9: c = [(vi, 0.001, 0.001) for vi, u, v in c]      # occluder only: one free texel (its unwrapped charts spanned the atlas)
    T.append([emit(int(vi), m, u, v) for vi, u, v in c]); mat.append(m); lin.append(bool(l))
for f in np.where(np.isin(fc, [k, k2]))[0]:
    mm_ = 3 if fc[f] == k2 else 1          # r9: the staff's skull on its own material (same head images), tinted MM9's yellow-green by a ramp
    T.append([emit(vi, mm_, *sk_uv[vi]) for vi in tri[f]]); mat.append(mm_); lin.append(False)
# staff: rings of SIDES vertices along the centre line, then two cap centres
nr, sides = [int(x) for x in D['staff_rings']]; s0 = np.where(comp == ks)[0].min()
cl = co[s0:s0 + nr * sides].reshape(nr, sides, 3).mean(1); L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(cl, axis=0), axis=1))]; L /= L[-1]
for f in np.where(fc == ks)[0]:
    vv = tri[f] - s0; row = []
    ring_k = [(v % sides) if v < nr * sides else None for v in vv]
    for vi, v in zip(tri[f], vv):
        if v >= nr * sides:      # cap centre
            row.append(emit(vi, 2, 0.5, 0.0 if v == nr * sides else 1.0)); continue
        r, kk = divmod(v, sides)
        if kk == 0 and any(x is not None and x > sides // 2 for x in ring_k): kk = sides      # seam
        row.append(emit(vi, 2, kk / sides, 0.02 + 0.96 * L[r]))
    T.append(row); mat.append(2); lin.append(False)
# crown cap: the staff material's dark steel strip (v above 0.985), u by angle
if 'cap' in names:
    kc = names.index('cap'); cv = np.where(comp == kc)[0]; cc = co[cv].mean(0)
    for f in np.where(np.isin(fc, [kc, names.index('tubecap')] if 'tubecap' in names else [kc]))[0]:
        T.append([emit(vi, 2, 0.5 + 0.45 * np.cos(np.arctan2(*(co[vi, :2] - cc[:2])[::-1])) * 0.0 + 0.1 + 0.8 * ((np.arctan2(*(co[vi, :2] - cc[:2])[::-1]) + np.pi) / (2 * np.pi)), 0.992) for vi in tri[f]]); mat.append(2); lin.append(False)
np.savez(OUT, co=np.array(pos), tri=np.array(T), uv=np.array(uv), orig=np.array(orig), mat=np.array(mat), comp=np.array(part), names=np.array(names),
         matnames=np.array(['LichKing', 'LichKingHead', 'LichKingStaff', 'LichKingStaffSkull']), lining=np.array(lin))
print('UVASM', len(pos), len(T), 'mats', np.bincount(mat))
