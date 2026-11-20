import bpy,numpy as np,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_final.blend'))
body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];sc=bpy.context.scene
copy=body.copy();copy.data=body.data.copy();sc.collection.objects.link(copy)
discard=0
for v in copy.data.vertices:
 weights=sorted([(e.group,e.weight) for e in v.groups if e.weight>0],key=lambda x:-x[1])
 kept=weights[:4];total=sum(w for _,w in kept);discard=max(discard,sum(w for _,w in weights[4:]))
 for g in copy.vertex_groups:g.remove([v.index])
 for group,w in kept:copy.vertex_groups[group].add([v.index],w/total,'REPLACE')
def evaluated(ob):
 ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh()
 co=np.empty(len(m.vertices)*3);m.vertices.foreach_get('co',co);ev.to_mesh_clear();return co.reshape(-1,3)
report={}
for a in bpy.data.actions:
 if not a.use_fake_user:continue
 rig.animation_data.action=a
 if a.slots:rig.animation_data.action_slot=a.slots[0]
 worst=(0,0);p99=0
 for f in np.arange(0,a.frame_range[1]+.01,.5):
  sc.frame_set(int(f),subframe=float(f-int(f)))
  delta=np.linalg.norm(evaluated(body)-evaluated(copy),axis=1)
  p99=max(p99,float(np.percentile(delta,99)))
  if delta.max()>worst[0]:worst=(float(delta.max()),float(f))
 report[a.name]={'max_m':worst[0],'frame':worst[1],'p99_m':p99}
print('FOUR_WEIGHTS',discard,report,flush=True)
(P/'work/four_weights_parity.json').write_text(json.dumps({'max_discarded':discard,'clips':report},indent=2))
assert max(x['max_m'] for x in report.values())<.02
bpy.data.objects.remove(body,do_unlink=True);copy.name='Body'
rig.animation_data.action=None
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_four.blend'))
