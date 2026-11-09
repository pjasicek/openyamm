import bpy,json
from pathlib import Path
from mathutils import Matrix
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'rig_pilots_v1.blend'))
rig=bpy.data.objects['Lizardman_Rig'];body=bpy.data.objects['Lizardman_Body']
for state in ('standing','rest'):
    if state=='rest':
        rig.animation_data.action=None
        for t in rig.animation_data.nla_tracks:t.mute=True
        for b in rig.pose.bones:b.matrix_basis=Matrix.Identity(4)
        bpy.context.view_layer.update()
    deps=bpy.context.evaluated_depsgraph_get();evaluated=body.evaluated_get(deps);mesh=evaluated.to_mesh()
    records=[]
    for v in mesh.vertices:
        original=body.data.vertices[v.index].co
        if abs(original.x)>40 and original.z<100 and original.z>65:
            records.append(((v.co-original).length,v.index,list(original),list(v.co),[(body.vertex_groups[g.group].name,g.weight) for g in body.data.vertices[v.index].groups]))
    print(state,sorted(records,reverse=True)[:10],flush=True)
    print('bones',[(b.name,list(b.head),list(b.location),list(b.rotation_quaternion),list(b.scale)) for b in rig.pose.bones if 'Digit' in b.name or 'Thumb' in b.name],flush=True)
    evaluated.to_mesh_clear()
