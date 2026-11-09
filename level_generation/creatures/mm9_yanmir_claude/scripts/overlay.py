"""Meshy vertices (scaled to MM9's height) with MM9's joints, front and side, to place the joint estimates. Args: <meshy glb> <out png>"""
import sys, json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from pygltflib import GLTF2
sys.path.insert(0, '../claude_shared/floor')
from glb_pose import Glb, Model
g = GLTF2().load(sys.argv[1]); p = g.meshes[0].primitives[0]; a = g.accessors[p.attributes.POSITION]; bv = g.bufferViews[a.bufferView]
blob = g.binary_blob(); V = np.frombuffer(blob, 'f4', a.count * 3, (bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(-1, 3)
print('glTF', V.min(0), V.max(0), g.nodes[0].matrix if hasattr(g.nodes[0], 'matrix') else None, g.nodes[0].rotation, g.nodes[0].scale)
B = np.c_[V[:, 0], -V[:, 2], V[:, 1]]
print('blender', B.min(0).round(3), B.max(0).round(3))
np.save('work/meshy_body_verts.npy', B)
sc = 2.563; Q = B * sc + np.array([0, -0.27, -1.418 + 0.5 * sc])
m = Model(Glb('source/true/bigfoot1_true.glb')); nm = [n.get('name') for n in m.glb.json['nodes']]; w = m.world({})
J = {nm[i]: np.array([w[i][0, 3], -w[i][2, 3], w[i][1, 3]]) for i in range(len(nm)) if nm[i].startswith('Bip')}
S = 330; H = 1000; im = Image.new('RGB', (1400, H), (40, 40, 44)); d = ImageDraw.Draw(im)
def px(x, z, cx): return cx + x * S, H - (z + 1.5) * S
for x, y, z in Q: d.point(px(x, z, 400), (200, 200, 200)); d.point(px(y, z, 1150), (200, 200, 200))
for k, q in J.items():
    x, y = px(q[0], q[2], 400); d.ellipse((x - 3, y - 3, x + 3, y + 3), fill=(255, 40, 40)); x, y = px(q[1], q[2], 1150); d.ellipse((x - 3, y - 3, x + 3, y + 3), fill=(255, 40, 40))
for k in range(-14, 13):
    z = k / 10 * 1; _, y = px(0, z, 0); d.line((0, y, 12, y), fill=(255, 255, 0)); d.text((14, y - 5), f'{z:.1f}', fill=(255, 255, 0))
im.save(sys.argv[2])
