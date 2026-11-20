"""MM9's throwing axe PROJECTILES/AXE.abc (what ShowWeapon / HideWeapon put in the hand; DWARFAXE.abc is the scripted miner's pick) in the true-handed bind: vertices posed by the clip given (Scene Root rotation + Bone01), put on the socket RHand1 of the true model. Args: <clip index>. LithTech numbers scaled by 0.0256,
then S = diag(-1,1,1). Writes work/axe_bind.npz: V (bind world, glTF numbers), F, UV, and the socket's local matrix. Project folder. """
import sys, numpy as np
sys.path.insert(0, '../../../tools/mm9_import_discovery')
import convert_abc_model as c
from pathlib import Path
M = '../../../mm9/extracted/MODELS/MODELS/'
d = c.read_abc(Path(M + 'DWARF.abc')); a = c.read_abc(Path(M + 'PROJECTILES/AXE.abc'))
S = np.diag([-1., 1, 1, 1]); K = 0.0256
tr = a.animations[int(sys.argv[1]) if len(sys.argv) > 1 else 0].node_transforms
mr = c.matrix_from_transform(tr[0][0]).astype(float); mb = c.matrix_from_transform(tr[1][0]).astype(float)
bind = a.nodes[1].bind_matrix.astype(float)
pose = mr @ mb @ np.linalg.inv(bind)
lod = a.pieces[0].lods[0]
v = np.array([[*x.position, 1.] for x in lod.vertices])
vp = (pose @ v.T).T[:, :3]
print('AXE posed raw', vp.min(0), vp.max(0))
sk = next(s for s in d.sockets if s.name == 'RHand1')
ms = c.matrix_from_transform(c.Transform(translation=sk.translation, rotation=sk.rotation)).astype(float)
n12 = d.nodes[sk.node_index].bind_matrix.astype(float)
w = n12 @ ms @ np.c_[vp, np.ones(len(vp))].T
w = w.T[:, :3] * K
w[:, 0] *= -1
print('AXE bind true', w.min(0), w.max(0), 'hand node', (n12[:3, 3] * K * [-1, 1, 1]))
pos, uv, f = [], [], []
for fc in lod.faces:
    b = len(pos)
    for fv in fc.vertices:
        pos.append(w[fv.vertex_index]); uv.append(fv.uv)
    f.append((b, b + 2, b + 1))
np.savez('work/axe_bind.npz', V=np.array(pos), F=np.array(f), UV=np.array(uv))
print('AXE faces', len(f))
# axes at MM9's rest in Blender coordinates, true-handed: haft pommel to spike, across toward the edge
import json
Rn = (n12 @ ms)[:3, :3]
Bl = lambda a: [float(-a[0]), float(-a[2]), float(a[1])]
json.dump({'u': Bl(Rn @ [0, 1, 0]), 'a': Bl(Rn @ [0, 0, 1]), 'origin': Bl(n12[:3, 3] * K)}, open('work/axe_axes.json', 'w'))
print('AXES', open('work/axe_axes.json').read())
