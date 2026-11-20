#!/usr/bin/env python3
"""Gate copy of a Guard body GLB with the halberd back in it (the creature project's grip and blade gates ran on the pre-split
GLB). The attachment's LOD0 (Xbase space, split_attachment.py applied the joint's inverse bind matrix) is mapped back to bind
space by the inverse of that matrix and appended to the LOD0 mesh as a third primitive, skinned fully to Xbase, on the
body material. Usage: merge_halberd.py <body.glb> <halberd.glb> <out.glb>"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import glbpack as G  # noqa: E402

body, hal, out = sys.argv[1:4]
doc, binary = G.read(body); hd, hb = G.read(hal)
hb = bytes(hb)
hm = hd['meshes'][hd['nodes'][0]['mesh']]['primitives'][0]
P = G.acc(hd, hb, hm['attributes']['POSITION']).astype(np.float64)
N = G.acc(hd, hb, hm['attributes']['NORMAL']).astype(np.float64)
UV = G.acc(hd, hb, hm['attributes']['TEXCOORD_0']).astype(np.float32)
T = G.acc(hd, hb, hm['indices']).reshape(-1).astype(np.uint32)
skin = doc['skins'][0]; names = [doc['nodes'][j].get('name') for j in skin['joints']]
slot = names.index('Xbase')
ibm = G.acc(doc, bytes(binary), skin['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1)[slot].astype(np.float64)
bind = np.linalg.inv(ibm)
Pb = (np.c_[P, np.ones(len(P))] @ bind.T)[:, :3].astype(np.float32)
Nb = N @ np.linalg.inv(bind[:3, :3]).T; Nb = (Nb / np.linalg.norm(Nb, axis=1, keepdims=True)).astype(np.float32)
node = next(n for n in doc['nodes'] if n.get('name') == 'Guard' and 'mesh' in n)
mesh = doc['meshes'][node['mesh']]
p0 = mesh['primitives'][0]
jt = doc['accessors'][p0['attributes']['JOINTS_0']]['componentType']
J = np.zeros((len(P), 4), np.uint8 if jt == 5121 else np.uint16); J[:, 0] = slot
W = np.zeros((len(P), 4), np.float32); W[:, 0] = 1
att = {}
att['POSITION'] = G.append(doc, binary, {'componentType': 5126, 'type': 'VEC3'}, Pb); G.set_minmax(doc, binary, att['POSITION'])
att['NORMAL'] = G.append(doc, binary, {'componentType': 5126, 'type': 'VEC3'}, Nb)
att['TEXCOORD_0'] = G.append(doc, binary, {'componentType': 5126, 'type': 'VEC2'}, UV)
att['JOINTS_0'] = G.append(doc, binary, {'componentType': jt, 'type': 'VEC4'}, J)
att['WEIGHTS_0'] = G.append(doc, binary, {'componentType': 5126, 'type': 'VEC4'}, W)
idx = G.append(doc, binary, {'componentType': 5125, 'type': 'SCALAR'}, T.reshape(-1, 1))
mesh['primitives'].append({'attributes': att, 'indices': idx, 'material': p0['material'], 'mode': 4})
G.write(out, doc, binary)
print('MERGED halberd', len(T) // 3, 'tris on Xbase slot', slot, '->', out)
