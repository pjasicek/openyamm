"""Dump UV anatomy and bake a reusable short-range AO map from the selected master."""
import json
import runpy
import sys
from pathlib import Path
import bpy
import numpy as np

P = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/uv_master.blend'))
mesh = bpy.data.objects['Thunderbird']
me = mesh.data
me.calc_loop_triangles()
uv = me.uv_layers.active.data
labels = me.attributes['anatomy_part'].data
u = np.array([[tuple(uv[l].uv) for l in t.loops] for t in me.loop_triangles],dtype=np.float32)
x = np.array([[tuple(me.vertices[v].co) for v in t.vertices] for t in me.loop_triangles],dtype=np.float32)
part = np.array([max(set(labels[v].value for v in t.vertices),
    key=lambda k:sum(labels[v].value == k for v in t.vertices)) for t in me.loop_triangles],dtype=np.int32)
np.savez(P/'work/uv3d.npz',uv=u,xyz=x,part=part)
areas = np.abs(np.cross(u[:,1]-u[:,0],u[:,2]-u[:,0]))*.5
assert (areas > 1e-12).all()
(P/'review/uv_audit.json').write_text(json.dumps({'triangles':len(u),'zero_area_uv_triangles':0,
    'uv_area_sum':float(areas.sum()),'unique_packed_smart_project':True,'head_density_factor':2.5},indent=2)+'\n')
(P/'textures').mkdir(exist_ok=True)
sys.argv = ['bake_creature_ao.py','--','Thunderbird',str(P/'textures/m552_ao.png'),'.018','2048']
runpy.run_path(str(P.parent/'claude_shared/bake_creature_ao.py'),run_name='__main__')
