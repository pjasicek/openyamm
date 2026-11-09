"""Per-face weight class of the reduce source (work/face_bone.npy, dump_mesh.py face order; m372's gown is ONE shell with
bodice, bell sleeves and skirt): 1 = robe chains (Robe_* weight >= 0.5 averaged over the corners), 2 = sleeve (Sleeve_*
chains + upper arm / forearm / hand >= 0.5), 0 = the rest (bodice, trunk). Usage: blender -b -P"""
import os, bpy, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = np.load(os.path.join(HERE, 'work', 'mesh_in.npz')); f = d['faces']
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'source.blend'))
b = bpy.data.objects['Body']; names = {g.index: g.name for g in b.vertex_groups}
robe = np.zeros(len(b.data.vertices)); arm = np.zeros(len(b.data.vertices))
for v in b.data.vertices:
    for e in v.groups:
        n = names[e.group]
        if n.startswith('Robe_'):
            robe[v.index] += e.weight
        elif n.startswith('Sleeve_') or any(t in n for t in ('UpperArm', 'Forearm', 'Hand', 'Finger')):
            arm[v.index] += e.weight
fr, fa = robe[f].mean(1), arm[f].mean(1)
lab = np.where(fr >= 0.5, 1, np.where(fa >= 0.5, 2, 0))
np.save(os.path.join(HERE, 'work', 'face_bone.npy'), lab)
print('FACEBONE', {k: int((lab == k).sum()) for k in range(3)})
