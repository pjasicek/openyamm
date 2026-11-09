from pathlib import Path
import bpy,runpy,sys,json
import numpy as np
p=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(p/'scripts'));import common
for name in ['motion_grip','rig_v5']:
 bpy.ops.wm.open_mainfile(filepath=str(p/'work'/f'{name}.blend'))
 rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];names=[g.name for g in body.vertex_groups]
 rig.animation_data.action=None
 for b in rig.pose.bones:b.matrix_basis.identity()
 print('BODY',name,'groups',names,'modifiers',[(m.name,m.type) for m in body.modifiers])
 print('GROUPSUM',name,[(n,round(sum(e.weight for v in body.data.vertices for e in v.groups if e.group==i),1)) for i,n in enumerate(names) if n in ['B_Head','B_Pelvis','B_Spine','B_Spine1','B_Spine2']])
 for pose in ['rest','Standing']:
  if pose=='Standing':
   a=bpy.data.actions[pose];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0)
  common.workbench_clay(bpy.context.scene)
  common.render_views(str(p/'review'/f'diagnostic_{name}_{pose}'),.85,1.95,views=('three_quarter',),resolution=(650,700))
