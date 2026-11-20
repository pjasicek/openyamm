"""Fit the off-hand power grip against all four LODs together."""
import json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
source=P/'work/round3_left_before_multilod.json'
if not source.exists():source.write_text((P/'work/round3_left_grip.json').read_text())
g=json.loads(source.read_text());g['handle_centre_hand_local'][1]-=.008;g['handle_centre_hand_local'][2]-=.010
(P/'work/round3_left_multilod_initial.json').write_text(json.dumps(g,indent=2))
s=(P/'scripts/refine_grip.py').read_text().split('# Render isolated')[0]
s=s.replace('rig_weighted.blend','runtime_lod0.blend').replace("['GripRef']","['Attack']").replace('frame_set(8)','frame_set(42)').replace('grip_pose_initial.json','round3_left_multilod_initial.json').replace('grip_pose.json','round3_left_grip.json').replace('grip_refinement.json','round3_multilod_grip.json').replace('B_R_','B_L_').replace('Finger0.001','Finger01').replace('Finger0.002','Finger02').replace('co[:,0]<0','co[:,0]>0').replace('radius=.0157','radius=.012').replace('abs(y[j])>22','abs(y[j])>75')
s=s.replace('np.linspace(-.012,.012,49)','[0.]')
insert="""
arrays=[]
def collect(body):
 me=body.data;me.calc_loop_triangles();c=np.array([tuple(v.co)for v in me.vertices]);l=np.array([d.value for d in me.attributes['finger'].data]);w=np.zeros((len(c),len(bn)))
 for v in me.vertices:
  for gg in v.groups:
   nn=body.vertex_groups[gg.group].name
   if nn in bi:w[v.index,bi[nn]]=gg.weight
 ids=np.where((c[:,0]>0)&((l>0)|(np.linalg.norm(c-np.array(rest['B_L_Hand'].translation),axis=1)<.15)))[0];tr=np.array([list(t.vertices)for t in me.loop_triangles]);tr=tr[np.all(np.isin(tr,ids),axis=1)];mapping=np.full(len(c),-1);mapping[ids]=np.arange(len(ids));arrays.append((c[ids],l[ids],w[ids],mapping[tr]))
collect(body)
for level in [1,2,3]:
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/runtime_lod{level}.blend'));collect(bpy.data.objects['Body'])
bpy.ops.wm.open_mainfile(filepath=str(P/'work/runtime_lod0.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data;bones=list(rig.data.bones)
act=bpy.data.actions['Attack'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];bpy.context.scene.frame_set(42);rig.animation_data.action=None
for n,q in G['finger_local'].items():rig.pose.bones[n].rotation_quaternion=Quaternion(q)
bpy.context.view_layer.update()
offsets=np.cumsum([0]+[len(v[0])for v in arrays]);co=np.concatenate([v[0]for v in arrays]);lab=np.concatenate([v[1]for v in arrays]);weights=np.concatenate([v[2]for v in arrays]);tri=np.concatenate([v[3]+offsets[i]for i,v in enumerate(arrays)])
"""
s=s.replace('ids=np.where((co[:,0]>0)',insert+'\nids=np.where((co[:,0]>0)')
s=s.replace("r=r[np.abs(al)<.064]", "take=np.abs(al)<.064;lid=np.repeat(np.searchsorted(offsets[1:],ftris[:,0]),len(bary))[take];r=r[take]")
s=s.replace("max(0,float(np.min(r))-radius-.0015)**2", "sum(max(0,float(np.min(r[lid==level]))-radius-.0015)**2 for level in range(4)if np.any(lid==level))")
exec(compile(s,str(P/'scripts/refine_grip.py'),'exec'))
