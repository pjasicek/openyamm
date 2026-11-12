"""Shared helpers for the layout research (gutter, seam and packing trials). Plain numpy/PIL/scipy, no Blender.

UVs are glTF convention (v down, image row = v * size), per triangle corner (M x 3 x 2).
"""
import io
import os
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parent
CREATURES = HERE.parents[2]
REPO = CREATURES.parents[1]
sys.path.insert(0, str(CREATURES / 'claude_shared'))
from texture_quality import read_glb, accessor, islands  # noqa: E402

COOK = REPO / 'build/game/openyamm_model_texture_cook'


def lod0_uv(path, image_name=None):
    """Triangles of the first mesh that samples the base-colour image (by name substring, else the first)."""
    doc, binary = read_glb(path)
    target = None
    out_pos, out_uv, mesh_name = [], [], None
    for mesh in doc['meshes']:
        for prim in mesh['primitives']:
            if 'TEXCOORD_0' not in prim['attributes']:
                continue
            image = None
            if 'material' in prim:
                tex = doc['materials'][prim['material']].get('pbrMetallicRoughness', {}).get('baseColorTexture')
                if tex is not None:
                    image = doc['textures'][tex['index']]['source']
            if target is None:
                if image_name and (image is None or image_name not in doc['images'][image].get('name', '')):
                    continue
                target, mesh_name = image, mesh.get('name')
            if image != target or mesh.get('name') != mesh_name:
                continue
            pos = accessor(doc, binary, prim['attributes']['POSITION'])
            uv = accessor(doc, binary, prim['attributes']['TEXCOORD_0'])
            idx = accessor(doc, binary, prim['indices']).astype(np.int64).reshape(-1, 3)
            out_pos.append(pos[idx])
            out_uv.append(uv[idx])
    return np.concatenate(out_pos), np.concatenate(out_uv)


def glb_image(path, name):
    doc, binary = read_glb(path)
    for im in doc['images']:
        if im.get('name') == name:
            view = doc['bufferViews'][im['bufferView']]
            start = view.get('byteOffset', 0)
            return Image.open(io.BytesIO(binary[start:start + view['byteLength']])).convert('RGB')
    raise KeyError(name)


def raster_labels(tri_uv, tri_label, size):
    """Label of the triangle whose interior holds each texel centre (-1: none)."""
    out = -np.ones((size, size), np.int32)
    p = tri_uv * size
    for t, lab in zip(p, tri_label):
        x0, y0 = np.maximum(np.floor(t.min(0)).astype(int), 0)
        x1, y1 = np.minimum(np.ceil(t.max(0)).astype(int) + 1, size)
        if x1 <= x0 or y1 <= y0:
            continue
        gy, gx = np.mgrid[y0:y1, x0:x1] + 0.5
        a, b, c = t
        w0 = (b[0] - a[0]) * (gy - a[1]) - (b[1] - a[1]) * (gx - a[0])
        w1 = (c[0] - b[0]) * (gy - b[1]) - (c[1] - b[1]) * (gx - b[0])
        w2 = (a[0] - c[0]) * (gy - c[1]) - (a[1] - c[1]) * (gx - c[0])
        inside = ((w0 >= 0) & (w1 >= 0) & (w2 >= 0)) | ((w0 <= 0) & (w1 <= 0) & (w2 <= 0))
        out[y0:y1, x0:x1][inside] = lab
    return out


def conservative_labels(tri_uv, tri_label, size):
    """Labels of texels an island's triangles touch at all (texel square overlaps a triangle, approximated by the
    centre test at 4x supersampling): the texels a bilinear lookup inside the island can read."""
    fine = raster_labels(tri_uv, tri_label, size * 4)
    out = -np.ones((size, size), np.int32)
    blocks = fine.reshape(size, 4, size, 4).transpose(0, 2, 1, 3).reshape(size, size, 16)
    has = blocks.max(2)
    out[has >= 0] = has[has >= 0]
    return out


def island_ids(tri_uv, tri_pos):
    isl = islands(tri_uv, tri_pos)
    return np.unique(isl, return_inverse=True)[1]


def voronoi(labels):
    """Each empty texel takes the label of the nearest labelled texel (what Meshy's fill does)."""
    empty = labels < 0
    if not empty.any():
        return labels.copy()
    _, (iy, ix) = ndimage.distance_transform_edt(empty, return_indices=True)
    return labels[iy, ix]


def srgb_to_linear(c):
    c = c / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(c):
    c = np.clip(c, 0, 1)
    return 255.0 * np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def box_mips(img_lin, levels):
    """2x2 box mips (the engine's downsampleMaterialBgra on power-of-two sides), in linear light."""
    chain = [img_lin]
    for _ in range(levels):
        a = chain[-1]
        h, w = a.shape[:2]
        chain.append(a.reshape(h // 2, 2, w // 2, 2, *a.shape[2:]).mean((1, 3)))
    return chain


def push_pull(img, valid):
    """Fill invalid texels by a push-pull pyramid (average of valid texels per level, pulled back up)."""
    img = img.astype(np.float64)
    w = valid.astype(np.float64)
    levels = []
    cur, cw = img * w[..., None], w
    while cur.shape[0] > 1:
        levels.append((cur, cw))
        h, wd = cw.shape
        cur = cur.reshape(h // 2, 2, wd // 2, 2, -1).sum((1, 3))
        cw = cw.reshape(h // 2, 2, wd // 2, 2).sum((1, 3))
    filled = cur / np.maximum(cw, 1e-12)[..., None]
    for cur, cw in reversed(levels):
        up = np.repeat(np.repeat(filled, 2, 0), 2, 1)
        own = cur / np.maximum(cw, 1e-12)[..., None]
        filled = np.where((cw > 0)[..., None], own, up)
    out = img.copy()
    out[~valid] = filled[~valid]
    return out


def cook_mips(png, workdir, levels=6, sharpen=0.75, codec='bc7'):
    """The engine's own cook (box mips in linear sRGB, unsharp mask on mips >= 1, block encode), decoded back.
    Returns [level0, level1, ...] as float sRGB 0-255 arrays."""
    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    out = workdir / (Path(png).stem + f'_{codec}_{sharpen}.oytex')
    jobs = workdir / 'jobs.tsv'
    fields = [str(png), str(out), codec, 'srgb', '0', '1', '2048', '0', '0' * 64, 'model']
    if sharpen > 0:
        fields.append(str(sharpen))
    jobs.write_text('\t'.join(fields) + '\n')
    r = subprocess.run([str(COOK), str(jobs)], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stdout + r.stderr)
    chain = []
    for level in range(levels):
        raw = workdir / 'level.rgba'
        r = subprocess.run([str(COOK), '--preview', str(out), str(raw), str(level)], capture_output=True, text=True)
        if r.returncode:
            raise RuntimeError(r.stdout + r.stderr)
        w, h = map(int, r.stdout.split()[:2])
        data = np.frombuffer(raw.read_bytes(), np.uint8).reshape(h, w, 4)[..., :3].astype(np.float64)
        chain.append(data)
        raw.unlink()
    return chain
