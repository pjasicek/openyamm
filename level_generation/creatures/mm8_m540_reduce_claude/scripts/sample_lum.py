"""Base colour luminance per rest face (centroid UV) from the installed GLB's first image -> work/face_lum.npy,
work/basecolor.png."""
import io, json, struct, numpy as np
from PIL import Image
d = open('work/mm8_m540_source_pre_reduce.glb', 'rb').read()
n = struct.unpack_from('<I', d, 12)[0]; j = json.loads(d[20:20 + n]); b0 = 20 + n + 8
bv = j['bufferViews'][j['images'][0]['bufferView']]; o = b0 + bv.get('byteOffset', 0)
img = Image.open(io.BytesIO(d[o:o + bv['byteLength']])).convert('RGB'); img.save('work/basecolor.png')
a = np.asarray(img, np.float32) / 255; H, W = a.shape[:2]
uv = np.load('work/mesh_in.npz')['wuv'].reshape(-1, 3, 2).mean(1)
lum = a[np.clip(((1 - uv[:, 1]) * H).astype(int), 0, H - 1), np.clip((uv[:, 0] * W).astype(int), 0, W - 1)].mean(1)
np.save('work/face_lum.npy', lum); print('LUM', len(lum))
