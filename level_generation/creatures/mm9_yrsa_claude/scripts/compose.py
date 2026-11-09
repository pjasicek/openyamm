"""Compose the runtime texture set from the Meshy retexture (our UVs) and the baked AO.

Usage: python3 compose.py <prefix>   (run from the project folder; needs numpy, Pillow, scipy, pygltflib)
Inputs: meshy/retexture_v1/texture_urls_0_*.png, texturing/<prefix>_body_upload.glb (UV triangles),
        textures/<prefix>_ao_2k.png.
Outputs (textures/):
  <prefix>_basecolor.png      2K, Meshy base colour padded into the UV gutters (graded afterwards by
                              ../claude_shared/grade_basecolor.py --ao -> <prefix>_basecolor_graded.png)
  <prefix>_normal_1k.png      Meshy normal, padded (prepare_actor_glb.py converts it to the glTF convention)
  <prefix>_metal_rough_1k.png glTF ORM: R baked AO, G Meshy roughness (floor 0.5), B metallic 0
  <prefix>_material_classes.png 1K labels (CLAUDE_CREATURE_TEXTURES.md): 1 skin (warm hue), 8 cloth/leather,
                              9 metal (Meshy metallic > 0.5), 0 empty
One shared set: these unique NPCs have a single skin, so there are no tiers, masks or ramps.
"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from pygltflib import GLTF2

prefix = sys.argv[1]
HERE = Path.cwd()
M = HERE / 'meshy' / 'retexture_v1'
T = HERE / 'textures'


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
        idx = acc(prim.indices, 1, dt).reshape(-1, 3)
        tris.append(uv[idx])
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


tris = uv_triangles(HERE / 'texturing' / f'{prefix}_body_upload.glb')
c2 = coverage(tris, 2048)
c1 = coverage(tris, 1024)
base = np.asarray(Image.open(M / 'texture_urls_0_base_color.png').convert('RGB').resize((2048, 2048), Image.LANCZOS))
Image.fromarray(pad(base, c2)).save(T / f'{prefix}_basecolor.png')
nrm = np.asarray(Image.open(M / 'texture_urls_0_normal.png').convert('RGB').resize((1024, 1024), Image.LANCZOS))
Image.fromarray(pad(nrm, c1)).save(T / f'{prefix}_normal_1k.png')
rough = np.asarray(Image.open(M / 'texture_urls_0_roughness.png').convert('L').resize((1024, 1024), Image.LANCZOS),
                   np.float32) / 255
metal = np.asarray(Image.open(M / 'texture_urls_0_metallic.png').convert('L').resize((1024, 1024), Image.LANCZOS),
                   np.float32) / 255
rough = pad(np.maximum(rough, 0.5), c1)
ao = np.asarray(Image.open(T / f'{prefix}_ao_2k.png').convert('L').resize((1024, 1024), Image.LANCZOS))
Image.merge('RGB', [Image.fromarray(pad(ao, c1)), Image.fromarray((rough * 255).astype(np.uint8)),
                    Image.new('L', (1024, 1024), 0)]).save(T / f'{prefix}_metal_rough_1k.png')
# material classes
b1 = np.asarray(Image.fromarray(base).resize((1024, 1024), Image.LANCZOS), np.float32) / 255
mx, mn = b1.max(2), b1.min(2)
sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
r, g, b = b1[..., 0], b1[..., 1], b1[..., 2]
hue = np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360
skin = (hue > 5) & (hue < 40) & (sat > 0.2) & (sat < 0.75) & (mx > 0.3)
classes = np.full((1024, 1024), 8, np.uint8)
classes[skin] = 1
classes[metal > 0.5] = 9
classes[~c1] = 0
Image.fromarray(classes).save(T / f'{prefix}_material_classes.png')
print('COMPOSE', prefix, 'coverage %.1f%%' % (100 * c2.mean()), 'classes',
      {int(k): int((classes == k).sum()) for k in np.unique(classes)})
