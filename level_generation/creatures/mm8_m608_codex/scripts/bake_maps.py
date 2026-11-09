"""Retain semantic UV triangles and short-range occlusion for the two texture sets."""
import bpy,sys,runpy,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_uv.blend'))
for part in ['body','head']:
 o=bpy.data.objects[part.title()];me=o.data;me.calc_loop_triangles();uv=me.uv_layers.active.data
 labels=np.array([int(me.attributes['band'].data[t.polygon_index].value) if part=='body' else 0 for t in me.loop_triangles],dtype=np.int32)
 np.savez(P/f'work/{part}_uv3d.npz',uv=np.array([[uv[i].uv[:] for i in t.loops] for t in me.loop_triangles]),xyz=np.array([[me.vertices[i].co[:] for i in t.vertices] for t in me.loop_triangles]),part=labels)
 sys.argv=['bake','--',o.name,str(P/f'textures/{part}_ao.png'),'.035','1024']
 runpy.run_path(str(P.parent/'claude_shared/bake_creature_ao.py'),run_name='__main__')
print('BAKED_MAPS',flush=True)
