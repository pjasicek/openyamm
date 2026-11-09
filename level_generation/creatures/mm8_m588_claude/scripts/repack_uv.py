"""Correct excessive Smart UV padding; preserve all geometry, weights and animation samples."""
import bpy,json,math
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig.blend'))
body=bpy.data.objects['Body'];before=np.array([tuple(v.co) for v in body.data.vertices]);bpy.context.view_layer.objects.active=body
for o in bpy.data.objects:o.select_set(o==body)
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.average_islands_scale()
bpy.ops.uv.pack_islands(rotate=True,margin_method='FRACTION',margin=.002,shape_method='CONCAVE')
bpy.ops.object.mode_set(mode='OBJECT')
uvs=np.array([tuple(x.uv) for x in body.data.uv_layers.active.data]);area=0
for f in body.data.polygons:
 a,b,c=uvs[list(f.loop_indices)];area+=abs(np.cross(b-a,c-a))*.5
assert np.array_equal(before,np.array([tuple(v.co) for v in body.data.vertices]))
print('REPACK_COVERAGE',area,flush=True)
assert area>.45,area
for name in ['rig','animated','pilot']:
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/{name}.blend'))
 body=bpy.data.objects['Body'];assert len(body.data.uv_layers.active.data)==len(uvs)
 for dst,value in zip(body.data.uv_layers.active.data,uvs):dst.uv=value
 bpy.ops.wm.save_as_mainfile(filepath=str(P/f'work/{name}.blend'))
(P/'work/uv_repack.json').write_text(json.dumps({'before_coverage':.1611,'after_coverage':float(area),'margin':.002,'geometry_unchanged':True},indent=2)+'\n')
