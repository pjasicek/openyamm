import bpy,sys,json
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
args=sys.argv[sys.argv.index('--')+1:];src,tag=args[:2];roles=args[2:] or ['Standing','Walking','Attack','Cast','Hit','Death','Dead','Fidget']
bpy.ops.wm.open_mainfile(filepath=str(p/src));rig=bpy.data.objects['Rig'];scene=bpy.context.scene
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
  common.render_views(str(out/f'{role}_{i}'),.65 if role in ['Death','Dead'] else .85,3.4 if role in ['Death','Dead'] else 2.1,views=('front','left','three_quarter'),resolution=(300,420))
  meta.append({'role':role,'i':i,'frame':f})
(out/'frames.json').write_text(json.dumps(meta,indent=2))

rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];scene.frame_set(0)
print('JOINTS',json.dumps({n:list(rig.pose.bones[n].head) for n in ['B_Pelvis','B_Spine2','B_L_UpperArm','B_L_Forearm','B_L_Hand','B_R_UpperArm','B_R_Forearm','B_R_Hand','B_L_Foot','B_R_Foot']}))
common.render_views(str(out/'collar'),1.42,.55,views=('front','left','three_quarter'),resolution=(700,700))
body=bpy.data.objects['Body'];me=body.data
mesh={'vertices':[list(v.co) for v in me.vertices], 'piece':[a.value for a in me.attributes['piece'].data], 'faces':[list(f.vertices) for f in me.polygons], 'uv':[[list(me.uv_layers.active.data[i].uv) for i in f.loop_indices] for f in me.polygons], 'head':[v.value for v in me.attributes['head'].data]}
(p/'work/round1_mesh.json').write_text(json.dumps(mesh))
