import bpy,numpy as np,json
from pathlib import Path
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_weighted_final.blend'))
o=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];m=o.data;a=bpy.data.actions['Attack'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(18)
v=np.array([x.co[:] for x in m.vertices]);e=np.array([x.vertices[:] for x in m.edges]);piece=np.array([x.value for x in m.attributes['piece'].data]);names=[g.name for g in o.vertex_groups]
def report(tag):
 bpy.context.view_layer.update();ob=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ob.to_mesh();posed=np.array([x.co[:] for x in mesh.vertices]);ob.to_mesh_clear()
 ratio=np.linalg.norm(posed[e[:,0]]-posed[e[:,1]],axis=1)/np.maximum(np.linalg.norm(v[e[:,0]]-v[e[:,1]],axis=1),1e-9)
 for index in np.argsort(ratio)[-12:]:
  print(tag,round(ratio[index],2),[(int(i),int(piece[i]),v[i].round(4).tolist(),{names[g.group]:round(g.weight,3) for g in m.vertices[i].groups if g.weight>.01}) for i in e[index]],flush=True)
report('BEFORE')
for side in 'LR':
 g=o.vertex_groups['B_'+side+'_UpperArmTwist'];dest=o.vertex_groups['B_'+side+'_UpperArm']
 for x in m.vertices:
  w=sum(y.weight for y in x.groups if y.group==g.index)
  if w:dest.add([x.index],w,'ADD');g.remove([x.index])
report('NO_UPPER_TWIST')
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_without_upper_twist.blend'))
