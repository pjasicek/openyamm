import bpy,sys,json
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
args=sys.argv[sys.argv.index('--')+1:];src,tag=args[:2];roles=args[2:] or ['Standing','Walking','Attack','Cast','Hit','Death','Dead','Fidget']
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(p/src));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');scene=bpy.context.scene
common.workbench_clay(scene,textured=True)
out=p/'review'/tag;out.mkdir(exist_ok=True,parents=True)
meta=[]
for role in roles:
 rig.animation_data_create();rig.animation_data.action=None
 for pb in rig.pose.bones:pb.matrix_basis.identity()
 act=bpy.data.actions[role];rig.animation_data.action=act
 if act.slots:rig.animation_data.action_slot=act.slots[0]
 f0,f1=act.frame_range
 for i in range(5):
  f=round(f0+(f1-f0)*i/4);scene.frame_set(f)
  target=(0.0,0.0)
  if role=='Attack':
   lo,hi=common.world_bounds([o for o in bpy.data.objects if o.type=='MESH' and o.name!='Icosphere'])
   center=(lo+hi)/2;target=(center.x,center.y)
  common.render_views(str(out/f'{role}_{i}'),.65 if role in ['Death','Dead'] else .85,3.4 if role in ['Death','Dead'] else (2.9 if role in ['Attack','Cast'] else 2.1),views=('front','left','three_quarter'),resolution=(300,420),target=target)
  meta.append({'role':role,'i':i,'frame':f})
(out/'frames.json').write_text(json.dumps(meta,indent=2))
