"""Per vertex of work/source.blend: summed weight of the vertex groups whose names contain any of BONES (comma list)
-> work/share_<label>.npy. Usage: blender -b -P bone_share.py -- <label> <Digit,...>"""
import os, sys, bpy
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
label, bones = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'source.blend'))
body = bpy.data.objects['Body']; idx = {g.index for g in body.vertex_groups if any(b in g.name for b in bones.split(','))}
share = np.array([sum(g.weight for g in v.groups if g.group in idx) for v in body.data.vertices])
np.save(os.path.join(HERE, 'work', f'share_{label}.npy'), share); print('SHARE', label, int((share > .5).sum()), 'vertices over 0.5')
