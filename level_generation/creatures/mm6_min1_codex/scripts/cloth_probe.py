import bpy,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/gated_master.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];a=bpy.data.actions['Walking'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0);r.animation_data.action=None
cs=[n for n in r.pose.bones.keys() if n.startswith('Skirt_')]
for n in cs:r.pose.bones[n].location=(0,0,0)
bpy.context.view_layer.update()
def pts():
 ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();x=np.array([v.co[:] for v in me.vertices]);ev.to_mesh_clear();return x
base=pts();print('world',list(b.matrix_world),list(r.matrix_world),'mod',[(m.name,m.use_deform_preserve_volume) for m in b.modifiers if m.type=='ARMATURE'])
for n in cs[:6]:
 p=r.data.bones[n].parent.name;pb=r.pose.bones[n];before=pb.matrix.translation.copy();pb.location=r.pose.bones[p].matrix.to_3x3().inverted()@Vector((.02,0,0));bpy.context.view_layer.update();actual=pts()-base;g=b.vertex_groups[n].index;w=np.array([sum(q.weight for q in v.groups if q.group==g) for v in b.data.vertices]);err=np.linalg.norm(actual-w[:,None]*[.02,0,0],axis=1);print('PROBE',n,'parentrel',list(r.data.bones[p].matrix_local.inverted()@r.data.bones[n].matrix_local),'jointshift',list(pb.matrix.translation-before),'maxerror',float(err.max()),'vertex',int(err.argmax()),'w',float(w[err.argmax()]),'actual',actual[err.argmax()].tolist());pb.location=(0,0,0);bpy.context.view_layer.update()
