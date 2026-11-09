import bpy,numpy as np
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_final_motion.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body']
names=[b.name for b in rig.data.bones if b.name.startswith('Robe_')];bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for n in names:rig.data.edit_bones[n].use_connect=False
bpy.ops.object.mode_set(mode='OBJECT');act=bpy.data.actions['Death'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];bpy.context.scene.frame_set(24)
def coords():
 ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();out=np.array([v.co[:] for v in me.vertices]);ev.to_mesh_clear();return out
v0=coords();raw={n:rig.pose.bones[n].matrix.copy() for n in names};w=np.array([sum(g.weight for g in v.groups if body.vertex_groups[g.group].name in names) for v in body.data.vertices]);print('ORDER',names);print('MATRICES',rig.matrix_world,body.matrix_world)
for n in names:
 M=raw[n].copy();M.translation+=Vector((0,0,.1));rig.pose.bones[n].matrix=M;bpy.context.view_layer.update()
v1=coords();err=v1-v0-np.outer(w,[0,0,.1]);ix=np.argmax(np.linalg.norm(err,axis=1));print('LINEAR_ERROR',np.linalg.norm(err,axis=1).max(),ix,'DELTA',v1[ix]-v0[ix],'WEIGHT',w[ix])
for n in names:
 error=rig.pose.bones[n].matrix.translation-raw[n].translation-Vector((0,0,.1))
 if error.length>.00001:print('BONE_ERROR',n,list(error))
print('MAX_TRANSLATIONS',open(p/'work/cloth_contacts.json').read())
