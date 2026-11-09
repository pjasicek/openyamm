"""Reproducible first rig probes: idle, walk and unarmed strike before the full animation set."""
from pathlib import Path
import sys,os,json,runpy,bpy,numpy as np
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common

def run(name,*args):
 path=p/'scripts'/name;sys.argv=[str(path),'--',*[str(a) for a in args]];runpy.run_path(str(path),run_name='__main__')

bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v1.blend'))
body=bpy.data.objects['Body'];me=body.data
# Hooves are rigid; the two wrist cuffs belong to the forearms and the waistband to the pelvis.
names={g.index:g.name for g in body.vertex_groups}
for v in me.vertices:
 piece=me.attributes['piece'].data[v.index].value
 target='B_Pelvis' if piece==2 else ('B_L_Forearm' if piece==3 else 'B_R_Forearm' if piece==4 else None)
 if piece==0 and v.co.z<.12:target='B_'+('L' if v.co.x>0 else 'R')+'_Foot'
 if piece==1:
  t=float(np.clip((1.16-v.co.z)/.43,0,1));t=t*t*(3-2*t)*.85
  left=float(np.clip(.5+v.co.x/.30,0,1));left=left*left*(3-2*left)
  for g in list(v.groups):body.vertex_groups[g.group].remove([v.index])
  for name,w in [('B_Pelvis',1-t),('B_L_Thigh',t*left),('B_R_Thigh',t*(1-left))]:
   if w:body.vertex_groups[name].add([v.index],w,'REPLACE')
 elif target:
  for g in list(v.groups):body.vertex_groups[g.group].remove([v.index])
  body.vertex_groups[target].add([v.index],1,'REPLACE')
 else:
  for side in ('L','R'):
   toe=body.vertex_groups['B_'+side+'_Toe0'];foot=body.vertex_groups['B_'+side+'_Foot']
   w=sum(g.weight for g in v.groups if g.group==toe.index)
   if w:toe.remove([v.index]);foot.add([v.index],w,'ADD')
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_accessories.blend'))
run('finger_weights.py',p/'work/rig_accessories.blend',p/'work/rig_weighted.blend')
run('retarget.py',p/'work/rig_weighted.blend',p/'work/animation_base.blend','anim_library/humanoid_set/Relax.glb:RelaxIdle:Standing','anim_library/humanoid_set/Unarmed.glb:UnarmedGetHitF1:Hit','anim_library/humanoid_set/Relax.glb:RelaxTalk1:Fidget','anim_library/humanoid_set/Unarmed.glb:UnarmedDeath1:Death')
run('retarget_mixamo.py',p/'work/animation_base.blend',p/'work/animation_base.blend','anim_library/mixamo/Walk.fbx:Walking','anim_library/mixamo/Standard Run.fbx:Running','anim_library/mixamo/Standing Melee Punch.fbx:Attack:plant')
run('aim_strike.py',p/'work/animation_base.blend',p/'work/animation_base.blend')
run('foot_level.py',p/'work/animation_base.blend',p/'work/animation_base.blend','Standing','Walking:const','Attack','Hit','Fidget','Running:const')
run('floor_clips.py',p/'work/animation_base.blend',p/'work/animation_base.blend','Standing','Walking','Attack','Hit','Fidget','Death')
run('run_fit.py',p/'work/animation_base.blend',p/'work/animation_base.blend')
run('clip_timing.py',p/'work/animation_base.blend',p/'work/animation_base.blend')
run('floor_clips.py',p/'work/animation_base.blend',p/'work/animation_base.blend','Attack','Hit','Fidget','Death')
os.environ['FA']='0.6';os.environ['FA_RAMP']='0.15,0.85'
run('twist_bones.py',p/'work/animation_base.blend',p/'work/animated.blend')
# Wrist rings follow the distal forearm twist rigidly; soft skin retains the distributed roll.
body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];me=body.data
for v in me.vertices:
 piece=me.attributes['piece'].data[v.index].value
 if piece not in (3,4):continue
 for g in list(v.groups):body.vertex_groups[g.group].remove([v.index])
 body.vertex_groups['B_'+('L' if piece==3 else 'R')+'_ForearmTwist'].add([v.index],1,'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/animated.blend'))
run('wrap_motion.py',p/'work/animated.blend',p/'work/animated.blend')
body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];me=body.data
# Dense edge screens and representative actual-mesh poses, independent of bone naming.
rest=np.array([v.co[:] for v in me.vertices]);edges=np.array([e.vertices[:] for e in me.edges]);rl=np.linalg.norm(rest[edges[:,0]]-rest[edges[:,1]],axis=1)
pieces=np.array([x.value for x in me.attributes['piece'].data]);skin=(pieces[edges[:,0]]==0)&(pieces[edges[:,1]]==0)
hand=(np.abs(rest[:,0])>.73);arm=(np.abs(rest[:,0])>.23)&(rest[:,2]>1.25)&(rest[:,2]<1.73)
regions={'hands':skin&hand[edges[:,0]]&hand[edges[:,1]],'arms':skin&arm[edges[:,0]]&arm[edges[:,1]],'wrap':pieces[edges[:,0]]==1}
report={};out=p/'review/animation';out.mkdir(parents=True,exist_ok=True)
common.workbench_clay(bpy.context.scene)
for name in ('Standing','Walking','Running','Attack','Hit','Fidget','Death','Dead'):
 act=bpy.data.actions[name];rig.animation_data.action=act
 if act.slots:rig.animation_data.action_slot=act.slots[0]
 f0,f1=act.frame_range;record={r:{'p99':0,'max':0} for r in regions};record['floor_min']=99
 for f in np.arange(f0,f1+.01,.5):
  bpy.context.scene.frame_set(int(f),subframe=float(f%1));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();co=np.array([v.co[:] for v in mesh.vertices]);ev.to_mesh_clear()
  st=np.linalg.norm(co[edges[:,0]]-co[edges[:,1]],axis=1)/np.maximum(rl,1e-7)
  for r,mask in regions.items():
   mx=float(st[mask].max());p99=float(np.percentile(st[mask],99))
   if mx>record[r]['max']:record[r].update(max=mx,frame=float(f),edge=[int(v) for v in edges[mask][np.argmax(st[mask])]])
   record[r]['p99']=max(p99,record[r]['p99'])
  record['floor_min']=min(record['floor_min'],float(co[:,2].min()))
 for i,f in enumerate(np.linspace(f0,f1,5)):
  bpy.context.scene.frame_set(int(f),subframe=float(f%1));common.render_views(str(out/f'{name}_{i:02d}'),1.05,2.5,views=('front','left','three_quarter'),resolution=(640,640))
 report[name]=record
(p/'review/animation/measurements.json').write_text(json.dumps(report,indent=2)+'\n');print('PILOT',json.dumps(report))
