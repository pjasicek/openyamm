"""Rest vertex positions and StalkEye membership of work/uv_master.blend -> work/master_co.npz (for piece_map.py)."""
import bpy, os
import numpy as np
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(P, 'work/uv_master.blend'))
mesh = bpy.data.objects['Beholder']; g = mesh.vertex_groups['StalkEye'].index
co = np.array([tuple(v.co) for v in mesh.data.vertices])
eye = np.array([any(x.group == g and x.weight > .5 for x in v.groups) for v in mesh.data.vertices])
np.savez(os.path.join(P, 'work/master_co.npz'), co=co, stalk_eye=eye)
print('DUMPED', len(co))
