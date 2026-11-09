"""Paint fixes on the body pages, before the masks. Meshy painted the throat, its red-brown corners and the neckline trim onto the top of the chest plate shell (part 11): that zone takes the plate's own paint, reflected across a line just under the trim, so the skin ends at the plate's top edge.
The torso's top beside the neck (paint pulled in by the join, Meshy's filler) takes the mail and plate from lower on the chest. Colours are copied from a front splat of the same page paint; relief of the zones is faded to flat."""
import numpy as np
from scipy import ndimage as ndi
K = 1400.
def ss(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
def grid(body, Pp, sel):
    W, H = int(.36 * K), int(.72 * K); c = np.zeros((H, W, 3), np.float32); z = np.full((H, W), -9., np.float32)
    for p in range(2):
        s = sel[p]; q = Pp[p][s]; ix = (np.abs(q[:, 0]) * K).astype(int); iy = (q[:, 1] * K).astype(int); k = (ix < W) & (iy >= 0) & (iy < H)
        ix, iy, cc, zz = ix[k], iy[k], body[p][s][k], q[k, 2]
        o = np.argsort(zz); c[iy[o], ix[o]] = cc[o]; z[iy[o], ix[o]] = zz[o]
    m = z > -8; _, (a, b) = ndi.distance_transform_edt(~m, return_indices=True); return c[a, b]
def look(g, x, y):
    co = [y * K, np.abs(x) * K]; return np.stack([ndi.map_coordinates(g[..., i], co, order=1, mode='nearest') for i in range(3)], -1)
def apply(body, Pp, Mp, Fp, fid, ob, part):
    fm = [(part[ob[fid[p]]].max(1)) for p in range(2)]
    tex = [np.where(Mp[p], 0, -1) for p in range(2)]
    pv = []
    for p in range(2):
        a = np.full(Mp[p].shape, -1, np.int32); a[Mp[p]] = fm[p][Fp[p][Mp[p]]]; pv.append(a)
    gs = grid(body, Pp, [pv[p] == 11 for p in range(2)]); gm = grid(body, Pp, [pv[p] == 0 for p in range(2)])
    W = []
    n1 = n2 = 0
    for p in range(2):
        w0 = np.zeros(Mp[p].shape, np.float32)
        s = pv[p] == 11; q = Pp[p][s]; ax = np.abs(q[:, 0]); yl = .455 + .55 * ax; d = q[:, 1] - yl
        w = ss(d, -.004, .004); ys = yl - np.maximum(d, 0) - .006
        c = look(gs, ax, ys); body[p][s] = body[p][s] * (1 - w[:, None]) + c * w[:, None]; w0[s] = w; n1 += int((w > .5).sum())
        s = (pv[p] == 0) & (Pp[p][..., 1] > .575) & (Pp[p][..., 1] < .70) & (np.abs(Pp[p][..., 0]) > .082) & (np.abs(Pp[p][..., 0]) < .22) & (Pp[p][..., 2] > -.02)
        q = Pp[p][s]; ax = np.abs(q[:, 0])
        w = ss(q[:, 1], .578, .600) * ss(ax, .082, .095) * (1 - ss(ax, .205, .22)) * ss(q[:, 2], -.02, .01)
        tri = lambda v, L: np.abs(((v / L + 1) % 2) - 1) * L        # a plain 4 cm patch of plate, mirror-tiled: no ridge or rim comes across
        c = look(gm, .12 + tri(ax, .04), .50 + tri(q[:, 1], .045)); body[p][s] = body[p][s] * (1 - w[:, None]) + c * w[:, None]; w0[s] = np.maximum(w0[s], w); n2 += int((w > .5).sum())
        W.append(w0)
    print('plate zone texels', n1, 'neck side texels', n2)
    # run 2: the shell's top edge (a plain cut) takes a leather trim that continues the trim Meshy painted down the throat's sides (x ~.06):
    # the band's texels copy that trim, along its length by |x| and across it by height, so grain and edge lines carry over
    from classes import classes
    gt = grid(body, Pp, [(pv[p] >= 0) & (pv[p] != 11) & (Pp[p][..., 2] > 0) for p in range(2)])      # the throat and its trim (not part 0)
    lea = classes(gt)[2]; ys = np.arange(.53, .605, .005); cen = []; hw = []
    for y_ in ys:
        r = int(y_ * K); xs = np.arange(int(.045 * K), int(.078 * K)); m_ = lea[r, xs]
        if m_.sum() < 3: cen.append(np.nan); hw.append(np.nan); continue
        cen.append(xs[m_].mean() / K); hw.append(max((xs[m_].max() - xs[m_].min()) / K / 2, .003))
    cen = np.interp(ys, ys[~np.isnan(cen)], np.array(cen)[~np.isnan(cen)]); hw = float(np.nanmedian(hw))
    TOP, BW = .5195, .013      # shell top at .52; band 1.3 cm
    n3 = 0
    for p in range(2):
        s = pv[p] == 11; q = Pp[p][s]; ax = np.abs(q[:, 0]); u = (TOP - q[:, 1]) / BW      # 0 at the top edge, 1 at the band's foot
        w = 1 - ss(u, .9, 1.08)
        ysrc = .535 + np.clip(ax / .078, 0, 1) * .06; xc = np.interp(ysrc, ys, cen); xsrc = xc + (np.clip(u, 0, 1) * 2 - 1) * hw
        c = look(gt, xsrc, ysrc); body[p][s] = body[p][s] * (1 - w[:, None]) + c * w[:, None]; W[p][s] = np.maximum(W[p][s], w); n3 += int((w > .5).sum())
    # orange flecks where the chest mail meets the armpit hide (x .19-.25, y .36-.47): made grey
    from classes import hsv
    n4 = 0
    for p in range(2):
        hh, sa, va = hsv(body[p]); P_ = Pp[p]; ax = np.abs(P_[..., 0])
        o = (pv[p] == 0) & (ax > .19) & (ax < .25) & (P_[..., 1] > .36) & (P_[..., 1] < .47) & (P_[..., 2] > -.06) & (hh > 8) & (hh < 45) & (sa > .38) & (va > .25)
        o = ndi.binary_dilation(o, iterations=2) & (pv[p] == 0) & ~((hh > 45) & (hh < 150) & (sa > .3))
        L_ = body[p][o] @ np.array([.2126, .7152, .0722]); body[p][o] = np.clip(L_[:, None] * np.array([1., 1., 1.02]) * .9, 0, 1); n4 += int(o.sum())     # grey at the same luminance: the mail's own pattern stays
    print('trim texels', n3, 'trim source half width cm', round(hw * 100, 2), 'mail fleck texels', n4)
    return W
