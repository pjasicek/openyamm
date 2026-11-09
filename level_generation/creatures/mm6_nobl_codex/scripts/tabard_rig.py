"""Give the front tabard its own belt-mounted cloth chains."""
import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v7.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
pv=np.zeros(len(me.vertices),np.int32);me.attributes['piece'].data.foreach_get('value',pv)
ids=np.where(pv==9)[0];assert len(ids)>40
co=np.array([tuple(v.co) for v in me.vertices]);chains=[]
for side,x in [('L',.055),('R',-.055)]:
 points=[(x,-.152,z) for z in [1.015,.9025,.79,.6775,.565]]
 chains.append({'deg':160 if side=='L' else -160,'pts':points,'parent':'B_Pelvis','bones':[]})
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for c in chains:
 parent=rig.data.edit_bones[c['parent']]
 for k in range(4):
  b=rig.data.edit_bones.new(f"Tabard_{'L' if c['deg']>0 else 'R'}_{k}")
  b.head=c['pts'][k];b.tail=c['pts'][k+1];b.parent=parent;b.use_connect=False
  parent=b;c['bones'].append(b.name)
bpy.ops.object.mode_set(mode='OBJECT')
for c in chains:
 for n in c['bones']:body.vertex_groups.new(name=n)
for i in ids:
 for g in body.vertex_groups:g.remove([int(i)])
 x,y,z=co[i];left=float(np.clip((x+.055)/.11,0,1))
 t=float(np.clip((1.015-z)/.1125-.5,0,3));a=int(t);b=min(a+1,3);f=t-a
 for c,sidew in zip(chains,[left,1-left]):
  w={a:1-f};w[b]=w.get(b,0)+f
  for k,v in w.items():
   if v*sidew>1e-5:body.vertex_groups[c['bones'][k]].add([int(i)],v*sidew,'REPLACE')
bpy.context.scene['nobl_tabard']=json.dumps(chains)
back=[]
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for side,x in [('L',.10),('R',-.10)]:
 c={'deg':20 if side=='L' else -20,'pts':[(x,.073,z) for z in [1.00,.8975,.795,.6925,.59]],'parent':'B_Pelvis','bones':[]}
 parent=rig.data.edit_bones['B_Pelvis']
 for k in range(4):
  b=rig.data.edit_bones.new(f'BackTabard_{side}_{k}');b.head=c['pts'][k];b.tail=c['pts'][k+1];b.parent=parent;b.use_connect=False
  parent=b;c['bones'].append(b.name)
 back.append(c)
bpy.ops.object.mode_set(mode='OBJECT')
for c in back:
 for n in c['bones']:body.vertex_groups.new(name=n)
for i in np.where(pv==8)[0]:
 for g in body.vertex_groups:g.remove([int(i)])
 x,y,z=co[i];left=float(np.clip((x+.10)/.20,0,1));t=float(np.clip((1.-z)/.1025-.5,0,3));a=int(t);b=min(a+1,3);f=t-a
 for c,sidew in zip(back,[left,1-left]):
  w={a:1-f};w[b]=w.get(b,0)+f
  for k,v in w.items():
   if v*sidew>1e-5:body.vertex_groups[c['bones'][k]].add([int(i)],v*sidew,'REPLACE')
bpy.context.scene['nobl_skirt_back']=json.dumps(back)
assert len(rig.data.bones)==140,len(rig.data.bones)
bpy.ops.wm.save_mainfile()
