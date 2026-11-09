#!/usr/bin/env python3
"""Body texture set from the texture-pass retexture (TEXTURE_QUALITY_PASS.md step 4, 2026-10-30), as ../../scripts/
compose.py did for the v1 retexture, from Meshy's 4K maps on our UVs: colour downsampled once to 2K (Lanczos), normal,
roughness and metallic to 1K, each padded into the UV gutters from the upload's own UV triangles; never a re-bake.

Usage (from the project folder): compose_texpass.py <out prefix> <meshy job dir> <upload glb> <ao png>
Writes textures/<out>_basecolor.png (2K; graded afterwards by ../claude_shared/grade_basecolor.py),
<out>_normal_1k.png, <out>_metal_rough_1k.png (R baked AO, G roughness floor 0.5, B metallic 0) and
<out>_material_classes.png (1K: 1 skin, 8 cloth/leather, 9 metal, 0 empty), as compose.py.
"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from pygltflib import GLTF2

out, job, upload, aopath = sys.argv[1:5]
M, T = Path(job), Path.cwd() / 'textures'


def uv_triangles(path):
    g = GLTF2().load(str(path))
    blob = g.binary_blob()

    def acc(i, n, dt):
        a = g.accessors[i]
        bv = g.bufferViews[a.bufferView]
        off = (bv.byteOffset or 0) + (a.byteOffset or 0)
        return np.frombuffer(blob, dtype=dt, count=a.count * n, offset=off).reshape(a.count, n)
    tris = []
    for prim in g.meshes[0].primitives:
        uv = acc(prim.attributes.TEXCOORD_0, 2, np.float32)
        ia = g.accessors[prim.indices]
        dt = {5121: np.uint8, 5123: np.uint16, 5125: np.uint32}[ia.componentType]
        tris.append(uv[acc(prim.indices, 1, dt).reshape(-1, 3)])
    return np.concatenate(tris)


def coverage(tris, size):
    im = Image.new('L', (size, size), 0)
    d = ImageDraw.Draw(im)
    for t in tris:
        d.polygon([(float(u * size), float(v * size)) for u, v in t], fill=255)
    return np.asarray(im) > 0


def pad(img, covered):
    _, (iy, ix) = ndimage.distance_transform_edt(~covered, return_indices=True)
    return img[iy, ix]


def load(name, mode, size):
    im = Image.open(M / f'texture_urls_0_{name}.png').convert(mode)
    return im.resize((size, size), Image.LANCZOS) if im.size != (size, size) else im


tris = uv_triangles(upload)
c2, c1 = coverage(tris, 2048), coverage(tris, 1024)
base = np.asarray(load('base_color', 'RGB', 2048))
Image.fromarray(pad(base, c2)).save(T / f'{out}_basecolor.png')
Image.fromarray(pad(np.asarray(load('normal', 'RGB', 1024)), c1)).save(T / f'{out}_normal_1k.png')
rough = np.asarray(load('roughness', 'L', 1024), np.float32) / 255
metal = np.asarray(load('metallic', 'L', 1024), np.float32) / 255
rough = pad(np.maximum(rough, 0.5), c1)
ao = np.asarray(Image.open(aopath).convert('L').resize((1024, 1024), Image.LANCZOS))
Image.merge('RGB', [Image.fromarray(pad(ao, c1)), Image.fromarray((rough * 255).astype(np.uint8)),
                    Image.new('L', (1024, 1024), 0)]).save(T / f'{out}_metal_rough_1k.png')
b1 = np.asarray(Image.fromarray(base).resize((1024, 1024), Image.LANCZOS), np.float32) / 255
mx, mn = b1.max(2), b1.min(2)
sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
r, g, b = b1[..., 0], b1[..., 1], b1[..., 2]
hue = np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360
classes = np.full((1024, 1024), 8, np.uint8)
# mm9_peasantm1: the body set holds no skin (head, neck and hands are in the head set); the hue rule took the brown
# boots and the olive jacket for skin, so every painted body texel is cloth/leather unless Meshy marked it metal
classes[metal > 0.5] = 9
classes[~c1] = 0
Image.fromarray(classes).save(T / f'{out}_material_classes.png')
print('COMPOSE_TEXPASS', out, 'coverage %.1f%%' % (100 * c2.mean()),
      {int(k): int((classes == k).sum()) for k in np.unique(classes)})
