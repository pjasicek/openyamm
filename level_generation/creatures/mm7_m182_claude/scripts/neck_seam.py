"""Head/body seam match for the v2 compose (system Python, called by scripts/compose_v2.py).

The head set is the Meshy head retexture, the body set the Meshy body retexture; they meet on a UV seam around the
upper neck. Texels of either set within 15 mm (3D) of the other set's texels form the seam band. The head set is
matched to the body there: per channel, the mean colour of the head band is scaled to the body band's, with the
correction fading out over 40 mm into the head (the face keeps its own paint). Throat texels (already continuous
across the seam) are left alone. Returns the measured band means and the applied gain."""
import numpy as np
from scipy.spatial import cKDTree


def match(D):
    h, b = D['head'], D['body']
    hp = h['pos'][h['cov']]; bp = b['pos'][b['cov']]
    sub = bp[::7]; db, _ = cKDTree(sub).query(hp)          # head texel -> nearest body texel distance
    hm = np.zeros(h['cov'].shape); hm[h['cov']] = db
    hsub = hp[::7]; dh, _ = cKDTree(hsub).query(bp); bm = np.zeros(b['cov'].shape); bm[b['cov']] = dh
    keep_h = h['cov'] & ~h.get('throat', np.zeros_like(h['cov'])); keep_b = b['cov'] & ~b.get('throat', np.zeros_like(b['cov']))
    band_h = keep_h & (hm < .015); band_b = keep_b & (bm < .015)
    if band_h.sum() < 100 or band_b.sum() < 100: return {'band_texels': [int(band_h.sum()), int(band_b.sum())]}
    mh = h['rgb'][band_h].mean(0); mb = b['rgb'][band_b].mean(0); gain = np.clip(mb / np.maximum(mh, 1e-4), .6, 1.6)
    w = np.clip(1 - (hm - .015) / .04, 0, 1) * keep_h
    h['rgb'] = np.clip(h['rgb'] * (1 + (gain - 1) * w[..., None]), 0, 1)
    return {'band_texels': [int(band_h.sum()), int(band_b.sum())], 'head_band_mean': mh.round(4).tolist(), 'body_band_mean': mb.round(4).tolist(),
            'gain': gain.round(4).tolist()}
