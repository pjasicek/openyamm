"""Wing texture set from the Codex paint: piecewise-affine warp of references_paint/wing_paint.png onto the UV template
(control points paint -> template read by eye on a gridded full-size view), then 2048x1024 base colour, a gentle normal
map from the paint's fine luminance, ORM (R AO 1, G roughness: membrane 0.72, bone 0.5), and the tier region mask
(R membrane, G bone, from the template's white spar lines). Args: none (project folder)."""
import numpy as np
from PIL import Image, ImageFilter
from scipy.spatial import Delaunay
from scipy import ndimage as ndi
P = 'references_paint/'; O = 'textures/'
import os; os.makedirs(O, exist_ok=True)
paint = np.asarray(Image.open(P + 'wing_paint.png').convert('RGB'), np.float64) / 255
tmpl = np.asarray(Image.open(P + 'wing_template.png').convert('L'), np.float64) / 255
H, W = paint.shape[:2]
CP = [  # (paint x, y) -> (template x, y)
    ((292, 205), (287, 234)), ((175, 186), (197, 218)), ((622, 138), (632, 152)), ((968, 222), (988, 244)),
    ((1435, 532), (1445, 536)), ((808, 400), (817, 403)), ((1125, 671), (1133, 676)), ((688, 524), (693, 531)),
    ((930, 720), (939, 723)), ((680, 783), (661, 795)), ((448, 922), (454, 922)), ((318, 563), (322, 569)),
    ((42, 815), (36, 830)),
    ((0, 0), (0, 0)), ((W - 1, 0), (W - 1, 0)), ((0, H - 1), (0, H - 1)), ((W - 1, H - 1), (W - 1, H - 1)),
    ((W // 2, 0), (W // 2, 0)), ((W // 2, H - 1), (W // 2, H - 1)), ((0, H // 2), (0, H // 2)), ((W - 1, H // 2), (W - 1, H // 2))]
src = np.array([c[0] for c in CP], float); dst = np.array([c[1] for c in CP], float)
tri = Delaunay(dst)
yy, xx = np.mgrid[0:H, 0:W]; q = np.c_[xx.ravel(), yy.ravel()].astype(float)
s = tri.find_simplex(q); T = tri.transform[s]
b = np.einsum('nij,nj->ni', T[:, :2], q - T[:, 2]); bc = np.c_[b, 1 - b.sum(1)]
sp = np.einsum('ni,nij->nj', bc, src[tri.simplices[s]])
warped = np.stack([ndi.map_coordinates(paint[..., c], [sp[:, 1], sp[:, 0]], order=1, mode='nearest').reshape(H, W) for c in range(3)], -1)
# keep the red membrane past the outline (bleed), black beyond is fine (never sampled)
inside = tmpl > 0.2
grown = ndi.binary_dilation(inside, iterations=24)
d, (iy, ix) = ndi.distance_transform_edt(~inside, return_indices=True)
bleed = warped.copy(); far = grown & ~inside
bleed[far] = warped[iy[far], ix[far]] * 0.5 + warped[far] * 0.5
base = Image.fromarray((np.clip(bleed, 0, 1) * 255 + 0.5).astype('u1')).resize((2048, 1024), Image.LANCZOS)
base.save(O + 'eb_wing_base.png')
# normal: fine luminance as height
lum = np.asarray(base.convert('L'), np.float64) / 255
hp = lum - ndi.gaussian_filter(lum, 6)
gy, gx = np.gradient(ndi.gaussian_filter(hp, 0.8))
k = 2.2
n = np.dstack([-gx * k, gy * k, np.ones_like(lum)]); n /= np.linalg.norm(n, axis=2, keepdims=True)
Image.fromarray(((n * 0.5 + 0.5) * 255 + 0.5).astype('u1')).resize((1024, 512), Image.LANCZOS).save(O + 'eb_wing_normal.png')
bone = np.asarray(Image.fromarray((tmpl > 0.9).astype('u1') * 255).resize((2048, 1024), Image.BILINEAR), np.float64) / 255
bone = ndi.gaussian_filter(np.clip(ndi.grey_dilation(bone, size=5), 0, 1), 1.5)
memb = np.clip(1 - bone, 0, 1)
orm = np.dstack([np.ones_like(bone), 0.72 * memb + 0.5 * bone, np.zeros_like(bone)])
Image.fromarray((orm * 255 + 0.5).astype('u1')).resize((1024, 512), Image.LANCZOS).save(O + 'eb_wing_orm.png')
np.savez_compressed('work/wing_regions.npz', memb=memb, bone=bone)
print('WING', base.size, 'bone share', round(float(bone.mean()), 3))
