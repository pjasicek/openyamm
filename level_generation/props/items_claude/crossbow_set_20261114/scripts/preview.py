#!/usr/bin/env python3
"""Offline preview of the crossbow clips (README.md "Gates"): the skinned arms and the crossbow template on the right
hand's Weapon node, drawn from Camera01 as the engine draws the view model (the eye at Camera01's position looking
along glTF -Z, 60 degree vertical field, 16:9), with a crosshair. A z-buffered software raster of both meshes with
their base colour textures and one light: quick enough to tune poses between in-game captures.

    preview.py <arms.glb> <crossbow.glb> <out.png> <clip>@<seconds>[@side] [...]

Several poses are tiled two to a row; @side views the pose from the right (70 units right of the eye and 20 ahead,
looking left) to check the hands on the stock, @close from 30 units right at the idle's right hand. numpy and Pillow
only.
"""
import io
import json
import os
import struct
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'dual_wield_20261114', 'scripts'))
from bake_dual_clips import Arms, load_glb  # noqa: E402

WIDTH, HEIGHT = 640, 360
FOV_Y = 60.0
NEAR = 1.0
TYPES = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}
COUNTS = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


def accessor(j, blob, index):
    acc = j['accessors'][index]
    view = j['bufferViews'][acc['bufferView']]
    n = COUNTS[acc['type']]
    start = view.get('byteOffset', 0) + acc.get('byteOffset', 0)
    out = np.frombuffer(bytes(blob), TYPES[acc['componentType']], acc['count'] * n, start).astype(np.float64)
    if acc.get('normalized'):
        out = out / float(np.iinfo(TYPES[acc['componentType']]).max)
    return out.reshape(acc['count'], n) if n > 1 else out


def image_of(j, blob, material):
    texture = j['materials'][material].get('pbrMetallicRoughness', {}).get('baseColorTexture')
    if texture is None:
        return None
    image = j['images'][j['textures'][texture['index']]['source']]
    view = j['bufferViews'][image['bufferView']]
    start = view.get('byteOffset', 0)
    data = bytes(blob[start:start + view['byteLength']])
    return np.asarray(Image.open(io.BytesIO(data)).convert('RGB').resize((256, 256)), np.float64) / 255


def vertex_colours(j, blob, primitive):
    count = j['accessors'][primitive['attributes']['POSITION']]['count']
    texture = image_of(j, blob, primitive['material']) if 'material' in primitive else None
    if texture is None or 'TEXCOORD_0' not in primitive['attributes']:
        return np.full((count, 3), 0.7)
    uv = accessor(j, blob, primitive['attributes']['TEXCOORD_0'])
    x = np.clip((uv[:, 0] % 1.0) * 255, 0, 255).astype(int)
    y = np.clip((uv[:, 1] % 1.0) * 255, 0, 255).astype(int)
    return texture[y, x]


class Scene:
    def __init__(self, arms_path, crossbow_path):
        j, blob = load_glb(arms_path)
        self.arms = Arms(j, blob)
        self.skinned = []
        for node in j['nodes']:
            if 'mesh' not in node or 'skin' not in node:
                continue
            skin = j['skins'][node['skin']]
            inverse = accessor(j, blob, skin['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1)
            for primitive in j['meshes'][node['mesh']]['primitives']:
                a = primitive['attributes']
                faces = accessor(j, blob, primitive['indices']).astype(int).reshape(-1, 3)
                self.skinned.append((accessor(j, blob, a['POSITION']), accessor(j, blob, a['JOINTS_0']).astype(int),
                                     accessor(j, blob, a['WEIGHTS_0']), faces, vertex_colours(j, blob, primitive),
                                     skin['joints'], inverse))
        cj, cblob = load_glb(crossbow_path)
        primitive = cj['meshes'][0]['primitives'][0]
        self.crossbow = (accessor(cj, cblob, primitive['attributes']['POSITION']),
                         accessor(cj, cblob, primitive['indices']).astype(int).reshape(-1, 3),
                         vertex_colours(cj, cblob, primitive))

    def triangles(self, clip, seconds):
        arms = self.arms
        world = arms.world(arms.local(clip, seconds))
        eye = world[arms.index['Camera01']][:3, 3]
        out = []
        for positions, joints, weights, faces, colours, skin_joints, inverse in self.skinned:
            mats = np.array([world[n] for n in skin_joints]) @ inverse
            blended = np.einsum('vk,vkij->vij', weights, mats[joints])
            p = np.einsum('vij,vj->vi', blended[:, :3, :3], positions) + blended[:, :3, 3]
            out.append((p - eye, faces, colours))
        weapon = world[arms.index['Weapon']]
        positions, faces, colours = self.crossbow
        out.append((positions @ weapon[:3, :3].T + weapon[:3, 3] - eye, faces, colours))
        return out


# The side view: a camera right of the eye and ahead of it, looking left (its right is the eye's back).
SIDE_FROM = np.array([70.0, -5.0, -20.0])
# @close: the same direction from nearer, at the height and depth of the idle's right hand.
CLOSE_FROM = np.array([30.0, -9.5, -19.0])
SIDE_AXES = np.array([[0.0, 0.0, 1.0], [0.0, 1.0, 0.0], [1.0, 0.0, 0.0]])


def render(scene, clip, seconds, side=None):
    tan = np.tan(np.radians(FOV_Y / 2))
    aspect = WIDTH / HEIGHT
    image = np.zeros((HEIGHT, WIDTH, 3)) + np.array([0.55, 0.62, 0.7])
    depth = np.full((HEIGHT, WIDTH), np.inf)
    light = np.array([-0.4, 0.75, 0.55])
    light /= np.linalg.norm(light)
    for points, faces, colours in scene.triangles(clip, seconds):
        if side:
            points = (points - (CLOSE_FROM if side == 'close' else SIDE_FROM)) @ SIDE_AXES.T
        tri = points[faces]
        normal = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        normal /= np.maximum(np.linalg.norm(normal, axis=1, keepdims=True), 1e-9)
        shade = 0.45 + 0.55 * np.abs(normal @ light)
        colour = colours[faces].mean(axis=1) * shade[:, None]
        z = -tri[..., 2]
        visible = (z > NEAR).all(axis=1)
        sx = (tri[..., 0] / np.maximum(z, 1e-6) / (tan * aspect) * 0.5 + 0.5) * WIDTH
        sy = (0.5 - tri[..., 1] / np.maximum(z, 1e-6) / tan * 0.5) * HEIGHT
        for k in np.nonzero(visible)[0]:
            x0, x1 = int(max(np.floor(sx[k].min()), 0)), int(min(np.ceil(sx[k].max()), WIDTH - 1))
            y0, y1 = int(max(np.floor(sy[k].min()), 0)), int(min(np.ceil(sy[k].max()), HEIGHT - 1))
            if x0 > x1 or y0 > y1:
                continue
            xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
            (ax, bx, cx), (ay, by, cy) = sx[k], sy[k]
            area = (bx - ax) * (cy - ay) - (cx - ax) * (by - ay)
            if abs(area) < 1e-9:
                continue
            w0 = ((bx - xs) * (cy - ys) - (cx - xs) * (by - ys)) / area
            w1 = ((cx - xs) * (ay - ys) - (ax - xs) * (cy - ys)) / area
            w2 = 1 - w0 - w1
            inside = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
            if not inside.any():
                continue
            inv = w0 / z[k, 0] + w1 / z[k, 1] + w2 / z[k, 2]
            d = 1 / np.maximum(inv, 1e-9)
            region = depth[y0:y1 + 1, x0:x1 + 1]
            take = inside & (d < region)
            region[take] = d[take]
            image[y0:y1 + 1, x0:x1 + 1][take] = colour[k]
    picture = Image.fromarray((np.clip(image, 0, 1) * 255).astype(np.uint8))
    draw = ImageDraw.Draw(picture)
    draw.line([(WIDTH / 2 - 8, HEIGHT / 2), (WIDTH / 2 + 8, HEIGHT / 2)], fill=(255, 40, 40))
    draw.line([(WIDTH / 2, HEIGHT / 2 - 8), (WIDTH / 2, HEIGHT / 2 + 8)], fill=(255, 40, 40))
    draw.text((6, 4), f'{clip} {seconds:.2f}{" " + side if side else ""}', fill=(0, 0, 0))
    return picture


def main():
    if len(sys.argv) < 5:
        print(__doc__)
        return 2
    scene = Scene(sys.argv[1], sys.argv[2])
    poses = [p.split('@') for p in sys.argv[4:]]
    pictures = [render(scene, p[0], float(p[1]), p[2] if len(p) > 2 else None) for p in poses]
    columns = min(2, len(pictures))
    rows = (len(pictures) + columns - 1) // columns
    sheet = Image.new('RGB', (WIDTH * columns, HEIGHT * rows), (0, 0, 0))
    for index, picture in enumerate(pictures):
        sheet.paste(picture, ((index % columns) * WIDTH, (index // columns) * HEIGHT))
    sheet.save(sys.argv[3])
    print('wrote', sys.argv[3])
    return 0


if __name__ == '__main__':
    sys.exit(main())
