import bpy,json,math
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(P.parents[2]/'assets_dev/worlds/mm6/models/mm6_drag.glb'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');body=next(o for o in bpy.data.objects if o.type=='MESH');sc=bpy.context.scene;sc.render.fps=24;rig.animation_data_create()
expected={'Standing','Walking','Running','Fidget','Attack','Cast','Hit','Death','Dead'}
clips={a.name.split('_Rig')[0]:a for a in bpy.data.actions};report={'actions':list(clips),'bones':len(rig.data.bones),'samples':{}}
assert len(bpy.data.actions)>=9
for name in expected:
 action=next(a for a in bpy.data.actions if a.name==name or a.name.startswith(name+'_'));rig.animation_data.action=action
 if hasattr(action,'slots') and action.slots:rig.animation_data.action_slot=action.slots[0]
 values=[]
 for fraction in [0,.25,.5,.75,1]:
  a,b=action.frame_range;t=a+(b-a)*fraction;sc.frame_set(int(t),subframe=t%1);ob=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ob.to_mesh();coords=[ob.matrix_world@v.co for v in mesh.vertices];assert all(math.isfinite(x) for v in coords for x in v);values.append({'frame':t,'min_z':min(v.z for v in coords),'max_z':max(v.z for v in coords)});ob.to_mesh_clear()
 report['samples'][name]=values
assert all(n in rig.data.bones for n in ['LThigh','RThigh','Tail8','Jaw','Socket_Mouth'])
(P/'review/delivered_reimport.json').write_text(json.dumps(report,indent=2));print('DELIVERED REIMPORT PASS',len(report['samples']),'clips')
