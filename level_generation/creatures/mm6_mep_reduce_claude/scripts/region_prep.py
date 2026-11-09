"""Inputs for mep_regions.py from the base model (base/mm6_mep.glb) and the dumped mesh (work/mesh_in.npz):
work/basecolor.png and work/inst_{base,mr,normal,mask}.png (LOD0 atlases), work/comp.npy (connected components of the
welded mesh), work/face_skin.npy / face_blue.npy (per-face fraction of skin-mask / pale-blue base colour samples) and work/headset.npy (head texture set: atlas u > 1024/2080). Prints the largest components."""
import io, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P.parent / 'claude_shared')); import region_variants as R  # noqa: E402
doc, b = R.read_glb(P / 'base/mm6_mep.glb'); m = doc['materials'][0]
for k, ti in (('base', m['pbrMetallicRoughness']['baseColorTexture']['index']),
              ('mr', m['pbrMetallicRoughness']['metallicRoughnessTexture']['index']),
              ('normal', m['normalTexture']['index']), ('mask', m['extras']['openyamm_region_mask']['index'])):
    v = doc['bufferViews'][doc['images'][doc['textures'][ti]['source']]['bufferView']]; o = v.get('byteOffset', 0)
    Image.open(io.BytesIO(bytes(b[o:o + v['byteLength']]))).save(P / f'work/inst_{k}.png')
Image.open(P / 'work/inst_base.png').convert('RGB').save(P / 'work/basecolor.png')
d = np.load(P / 'work/mesh_in.npz'); f, nv = d['faces'], len(d['verts'])
A = coo_matrix((np.ones(f.size), (np.repeat(np.arange(len(f)), 3), f.ravel() + len(f))), shape=(len(f) + nv,) * 2)
lab = connected_components(A, directed=False)[1][:len(f)]; lab = np.unique(lab, return_inverse=True)[1]
np.save(P / 'work/comp.npy', lab)
img = np.asarray(Image.open(P / 'work/basecolor.png'), np.float32); H, W = img.shape[:2]
uv = d['wuv'].reshape(-1, 3, 2); B = np.random.default_rng(1).dirichlet((1, 1, 1), 12)
u = np.einsum('sk,fkc->fsc', B, uv)
c = img[np.clip(((1 - u[..., 1] % 1) * H).astype(int), 0, H - 1), np.clip(((u[..., 0] % 1) * W).astype(int), 0, W - 1)]
# skin by the region mask's skin channel (A): the round-2 head paints the face in grey, the tier ramp colours it
mk = np.asarray(Image.open(P / 'work/inst_mask.png').convert('RGBA'), np.float32)
ma = mk[np.clip(((1 - u[..., 1] % 1) * H).astype(int), 0, H - 1), np.clip(((u[..., 0] % 1) * W).astype(int), 0, W - 1), 3]
np.save(P / 'work/face_skin.npy', (ma > 128).mean(1))
np.save(P / 'work/face_blue.npy', ((c[..., 2] - c[..., 0]) > 8).mean(1))
np.save(P / 'work/headset.npy', uv.mean(1)[:, 0] * W / 1024 > 1.0)
cnt = np.bincount(lab); cen = d['verts'][f].mean(1)
for k in np.argsort(-cnt)[:26]:
    print('COMP', k, cnt[k], cen[lab == k].mean(0).round(2))
