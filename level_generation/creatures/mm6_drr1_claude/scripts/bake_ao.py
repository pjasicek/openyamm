"""Rest-pose triangles (UV, 3D position) of the rat mesh -> work/uv3d.npz."""
import bpy, os, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE,'work/anim_v1.blend'))
rig = bpy.data.objects['Wyrm_Rig']; rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
me = bpy.data.objects['Wyrm'].data; me.calc_loop_triangles(); uv = me.uv_layers.active.data
U = np.array([[tuple(uv[l].uv) for l in t.loops] for t in me.loop_triangles], dtype=np.float32)
Xs = np.array([[tuple(me.vertices[v].co) for v in t.vertices] for t in me.loop_triangles], dtype=np.float32)
np.savez(os.path.join(HERE, 'work', 'uv3d.npz'), uv=U, xyz=Xs, part=np.array([me.attributes['part'].data[t.vertices[0]].value for t in me.loop_triangles],dtype=np.int32))
print('DUMPED', len(U))

import runpy,sys
sys.argv=["bake_creature_ao.py","--","Wyrm",os.path.join(HERE,"textures/wyrm_ao_2k.png"),".02","2048"]
runpy.run_path(os.path.join(HERE,"../claude_shared/bake_creature_ao.py"),run_name="__main__")
