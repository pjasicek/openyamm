from pathlib import Path
import bpy,numpy as np,json
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/animated_v1.blend'))
rig=bpy.data.objects['Rig'];s=bpy.context.scene;report={}
for clip,frame in [('Death',84),('Dead',0)]:
 a=bpy.data.actions[clip];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];s.frame_set(frame);d=bpy.context.evaluated_depsgraph_get();record={}
 for name in ('Body','Equipment'):
  o=bpy.data.objects[name];e=o.evaluated_get(d);m=e.to_mesh();v=np.array([x.co[:]for x in m.vertices]);names=[g.name for g in o.vertex_groups]
  for region,parts in [('all',None),('horse',('HorsePelvis','HorseSpine','HorseChest')),('bow',('Bow',))]:
   mask=np.ones(len(v),bool) if parts is None else np.array([sum(g.weight for g in vert.groups if names[g.group]in parts)>.75 for vert in o.data.vertices])
   if mask.any():record[name+'_'+region]=float(v[mask,2].min())
  i=int(v[:,2].argmin());record[name+'_lowest']={'rest':list(o.data.vertices[i].co),'pose':v[i].tolist(),'weights':{names[g.group]:g.weight for g in o.data.vertices[i].groups}}
  e.to_mesh_clear()
 assert .0<=record['Body_all']<=.012 and record['Body_horse']<.04 and record['Equipment_bow']>=0,record
 report[clip]=record
print(json.dumps(report,indent=2));(P/'review/corpse_contact.json').write_text(json.dumps(report,indent=2)+'\n')
