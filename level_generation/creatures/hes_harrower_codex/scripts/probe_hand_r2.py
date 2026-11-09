from pathlib import Path
import bpy,json,numpy as np
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/review_v1/final.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update();R={}
for side in 'LR':
 hand=rig.data.bones[f'B_{side}_Hand'];H=hand.matrix_local.inverted();names=[g.name for g in body.vertex_groups]
 bones=[b for b in rig.data.bones if b.name.startswith(f'B_{side}_Finger')]
 verts=[]
 for v in body.data.vertices:
  w={names[g.group]:g.weight for g in v.groups if g.weight>1e-6}
  if sum(x for n,x in w.items() if n.startswith(f'B_{side}_Finger') or n==hand.name)>.5:verts.append({'index':v.index,'co':list(H@v.co),'weights':w,'normal':list(H.to_3x3()@v.normal)})
 R[side]={'hand':list(map(list,hand.matrix_local)),'bones':{b.name:{'parent':b.parent.name,'matrix':list(map(list,H@b.matrix_local)),'head':list(H@b.head_local),'tail':list(H@b.tail_local)} for b in bones},'vertices':verts}
 print(side,'verts',len(verts),'bones',[(b.name,b.parent.name,sum(any(names[g.group]==b.name and g.weight>.5 for g in v.groups) for v in body.data.vertices)) for b in bones],flush=True)
(P/'work/hand_rest_r2.json').write_text(json.dumps(R)+'\n')
# Compare the actually stored grip with the JSON selected by the first build.
a=bpy.data.actions['Harrower_Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0)
for side in 'LR':
 g=json.loads((P/f'work/grip_pose_{side}.json').read_text())
 print('POSE',side,[(n,round(float(rig.pose.bones[n].rotation_quaternion.angle),3),q) for n,q in g['finger_local'].items()][:3],flush=True)
