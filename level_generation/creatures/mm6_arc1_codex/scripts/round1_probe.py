import bpy,json,math,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'review/round1/baseline/work/rig_equipped.blend'))
r=bpy.data.objects['Rig'];o=bpy.data.objects['Body'];sc=bpy.context.scene
r.animation_data.action=None
for b in r.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update()
report={'rest_joints':{b.name:list(b.head)for b in r.pose.bones},'feet':{},'elbows':{}}
co=np.array([v.co[:]for v in o.data.vertices]);gn={g.index:g.name for g in o.vertex_groups}
for s in 'LR':
 ix=[v.index for v in o.data.vertices if sum(g.weight for g in v.groups if gn[g.group]in[f'B_{s}_Foot',f'B_{s}_Toe0'])>.8]
 report['feet'][s]={'vertices':ix,'bounds':[co[ix].min(0).tolist(),co[ix].max(0).tolist()],'bottom':[(int(i),co[i].tolist())for i in ix if co[i,2]<.04]}
for a in bpy.data.actions:
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];d={s:[999,-999]for s in 'LR'}
 for t in np.linspace(0,a.frame_range[1],int(a.frame_range[1]*48/30)+1):
  sc.frame_set(int(t),subframe=float(t-int(t)))
  for s in 'LR':
   U,F,H=[r.pose.bones[f'B_{s}_'+n]for n in ['UpperArm','Forearm','Hand']]
   ur,fr,hr=[r.data.bones[f'B_{s}_'+n]for n in ['UpperArm','Forearm','Hand']]
   hn=(ur.matrix_local.to_3x3().inverted()@((fr.head_local-ur.head_local).cross(hr.head_local-fr.head_local))).normalized()
   u=(F.head-U.head).normalized();f=(H.head-F.head).normalized();h=U.matrix.to_3x3()@hn
   bend=math.degrees(math.atan2(h.dot(u.cross(f)),u.dot(f)));d[s]=[min(d[s][0],bend),max(d[s][1],bend)]
 report['elbows'][a.name]=d
(P/'review/round1/baseline/probe.json').write_text(json.dumps(report,indent=2))
print('JOINTS', {n:p for n,p in report['rest_joints'].items()if any(t in n for t in ['Pelvis','Foot','Toe','Thigh','Calf','UpperArm','Forearm','Hand'])})
print('FEET', {s:{k:v for k,v in d.items()if k!='vertices'and k!='bottom'}for s,d in report['feet'].items()})
print('ELBOWS',report['elbows'])
