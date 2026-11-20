"""Transport the sculpted elbow normals back to bind space for glTF skinning."""
import bpy,json,runpy
from pathlib import Path
from mathutils import Matrix,Vector
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/animation_finish.blend'))
b=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];me=b.data
r.animation_data.action=bpy.data.actions['Standing'];r.animation_data.action_slot=r.animation_data.action.slots[0];bpy.context.scene.frame_set(0)
ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh()
# Geometric normals from the deformed, welded surface, independent of stored/custom loop normals.
normal=[Vector() for v in em.vertices]
for f in em.polygons:
 for i in f.vertices:normal[i]+=f.normal*f.area
normal=[n.normalized() for n in normal];ev.to_mesh_clear()
selected=set(i for f in me.polygons if me.attributes['cuff'].data[f.index].value==3 for i in f.vertices)
matrices={g.index:(r.pose.bones[g.name].matrix@r.data.bones[g.name].matrix_local.inverted()).to_3x3() for g in b.vertex_groups if g.name in r.data.bones}
rest=[v.normal.copy() for v in me.vertices];maxerror=0
for i in selected:
 v=me.vertices[i];M=sum((matrices[g.group]*g.weight for g in v.groups),Matrix(((0,0,0),)*3));rest[i]=(M.inverted()@normal[i]).normalized();maxerror=max(maxerror,(M@rest[i]).normalized().angle(normal[i]))
me.normals_split_custom_set_from_vertices(rest);me.update()
assert maxerror<.002,maxerror
(p/'work/review2_normals.json').write_text(json.dumps({'elbow_vertices':len(selected),'max_skin_normal_roundtrip_angle_rad':maxerror,'method':'Area-weighted geometric normals in Standing, transported through inverse weighted bone rotation to bind space; positions, UVs, weights and actions unchanged.'},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/animation_finish.blend'))
