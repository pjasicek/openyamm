"""Head parts after graft_trell.py's placement: points of the hair and of the face shell, for the head set's region masks. Writes work/hair_pts.npz. Args: <head blend>"""
import bpy, sys
import numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--') + 1])
S, OY, OZ = 0.518, 0.012, 0.905
out = {}
for nm in ('Hair', 'Face'):
    o = bpy.data.objects[nm]; P = np.array([v.co[:] for v in o.data.vertices])
    y = P[:, 1] * S + OY; z = P[:, 2] * S + OZ
    if nm == 'Hair':
        y = np.where(y > 0.06, 0.06 + (y - 0.06) * 0.82, y); z = np.where(z < 0.93, 0.93 + (z - 0.93) * 0.62, z)
    out[nm] = np.c_[P[:, 0] * S, y, z]
np.savez('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm9_trellborg_claude/work/hair_pts.npz', **out)
print('HAIRPTS', {k: len(v) for k, v in out.items()})
