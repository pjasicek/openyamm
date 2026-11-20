"""Verify the eight-weight export limit on sampled posed surfaces before reducing geometry."""
import bpy,sys,json
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/motion_timed.blend'))
body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];sc=bpy.context.scene
samples=[]
def vertices(a,f):
 rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];sc.frame_set(int(f),subframe=f-int(f))
 ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();v=np.empty(len(me.vertices)*3);me.vertices.foreach_get('co',v);ev.to_mesh_clear();return v.reshape(-1,3)
for a in bpy.data.actions:
 for f in np.linspace(*a.frame_range,17):samples.append((a,float(f),vertices(a,float(f))))
before=max(sum(g.weight>1e-6 for g in v.groups) for v in body.data.vertices)
for o in bpy.data.objects:o.select_set(o==body)
bpy.context.view_layer.objects.active=body
bpy.ops.object.vertex_group_limit_total(limit=8);bpy.ops.object.vertex_group_normalize_all(lock_active=False)
errors=[]
for a,f,v in samples:errors.append((float(np.linalg.norm(vertices(a,f)-v,axis=1).max()),a.name,f))
worst=max(errors);assert worst[0]<.01,('Eight weights move the skin too far',worst)
assert max(sum(g.weight>1e-6 for g in v.groups) for v in body.data.vertices)<=8
(P/'work/influence_limit.json').write_text(json.dumps({'before':before,'after':8,'worst_displacement_m':worst[0],'action':worst[1],'frame':worst[2],'samples':len(samples),'four_weight_trial_max_displacement_m':0.01622449494053818,'reason':'Four influences visibly move the late death shoulder; current engine supports eight.'},indent=2))
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/motion_limited.blend'))
print('EIGHT WEIGHTS',before,'->8; worst',worst,flush=True)
