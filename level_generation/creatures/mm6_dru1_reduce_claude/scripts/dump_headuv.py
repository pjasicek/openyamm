"""Head faces of work/head_uv.blend -> work/headuv.npz (per head face: part (hpart), uvpart, HeadUV corners, atlas UVMap corners,
rest-pose corner positions and vertex normals). Usage: blender -b -P dump_headuv.py"""
import os, bpy, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'head_uv.blend'))
me = bpy.data.objects[os.environ.get('REA_CAND', 'Cand_66')].data
hp = np.zeros(len(me.polygons), np.int32); me.attributes['hpart'].data.foreach_get('value', hp)
up = np.zeros(len(me.polygons), np.int32); me.attributes['uvpart'].data.foreach_get('value', up)
h, a = me.uv_layers['HeadUV'].data, me.uv_layers['UVMap'].data
sel = [p for p in me.polygons if hp[p.index] > 0]
np.savez(os.path.join(HERE, 'work', 'headuv.npz'), part=np.array([hp[p.index] for p in sel]), uvpart=np.array([up[p.index] for p in sel]), face=np.array([p.index for p in sel]),
         huv=np.array([[h[l].uv[:] for l in p.loop_indices] for p in sel]), auv=np.array([[a[l].uv[:] for l in p.loop_indices] for p in sel]),
         pos=np.array([[me.vertices[v].co[:] for v in p.vertices] for p in sel]),
         nrm=np.array([[me.vertices[v].normal[:] for v in p.vertices] for p in sel]))
print('DUMPED', len(sel))
