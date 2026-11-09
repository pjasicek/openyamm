from pathlib import Path
import bpy,sys,runpy,json,numpy as np
p=Path(__file__).resolve().parents[1]
# Read the actual export through the existing source-speed gate.
lib=p.parents[2]/'anim_library/humanoid_set'
roles={'Standing':('Armed','ArmedIdle'),'Walking':('Armed','ArmedWalk'),'Running':('Armed','ArmedRunForward'),'Attack':('1Hand','SwordAttackR3'),'Hit':('Armed','ArmedGetHitF1'),'Death':('Armed','ArmedKnockdown1')}
sys.argv=[str(p/'scripts/trace_export.py'),'--',str(p/'export/mm6_fgt_runtime_lod0.glb')]+[f'{r}={lib/(st+".glb")}:{c}' for r,(st,c) in roles.items()]
runpy.run_path(sys.argv[0],run_name='__main__')
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_revision2.blend'));r=bpy.data.objects['Rig'];result={}
for role,frame in [('Standing',0),('Attack',21),('Death',16),('Dead',0)]:
 r.animation_data.action=bpy.data.actions[role];r.animation_data.action_slot=r.animation_data.action.slots[0];bpy.context.scene.frame_set(frame)
 result[role]={}
 for name in ['Body','Mace']:
  o=bpy.data.objects[name];ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();co=np.array([[v.co.x,v.co.z,-v.co.y] for v in m.vertices]);ev.to_mesh_clear()
  result[role][name]={'min':co.min(0).tolist(),'max':co.max(0).tolist(),'center':((co.min(0)+co.max(0))/2).tolist()}
  if name=='Mace' and role=='Dead':assert co[:,1].min()>-.001,'Dropped mace below floor'
(p/'review/revision2/posed_bounds.json').write_text(json.dumps(result,indent=2))
runpy.run_path(str(p/'scripts/pack_authoring.py'),run_name='__main__')
