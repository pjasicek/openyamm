import bpy,sys,json
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/motion_native.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
contacts=json.loads((P/'work/contacts.json').read_text())
for action in ('Attack','Death'):
 for label,e in contacts[action]['contacts'].items():
  if 'point' not in e:continue
  a=bpy.data.actions[action];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];f=e['frame'];sc.frame_set(int(f),subframe=f-int(f))
  ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();xyz=np.array([v.co[:] for v in me.vertices]);ev.to_mesh_clear()
  i=int(np.argmin(np.linalg.norm(xyz-np.array(e['point']),axis=1)));v=body.data.vertices[i]
  print('CONTACT DETAIL',action,label,'vertex',i,'rest',list(v.co),'weights',[(body.vertex_groups[g.group].name,round(g.weight,3)) for g in v.groups if g.weight>.01],flush=True)
  common.workbench_clay(sc)
  common.render_views(str(P/f'review/contact_{action}_{label}'),.85,1.2,('front','left','three_quarter'),resolution=(640,700))
