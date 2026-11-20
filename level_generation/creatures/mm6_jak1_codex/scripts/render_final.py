import bpy,sys,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(P/'review/viewer/mm6_jak1_a.glb'));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');scene=bpy.context.scene;common.workbench_clay(scene,textured=True)
for mat in bpy.data.materials:
 if mat.node_tree:
  bs=next((n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
  if bs and bs.inputs['Base Color'].links:mat.node_tree.nodes.active=bs.inputs['Base Color'].links[0].from_node
out=P/'review/clips';out.mkdir(exist_ok=True);rows={}
for role in ['Standing','Walking','Cast','Attack','Hit','Death','Dead','Fidget']:
 ac=bpy.data.actions[role];rig.animation_data.action=ac;rig.animation_data.action_slot=ac.slots[0];rows[role]=[]
 for i,f in enumerate(np.linspace(*ac.frame_range,5)):
  scene.frame_set(int(f),subframe=float(f-int(f)))
  for view in ['front','left','three_quarter']:
   path=common.render_views(str(out/f'{role}_{i}'),(.85 if role in ('Death','Dead') else .95),(4.8 if role in ('Death','Dead') else 3.2),views=(view,),resolution=(300,420))[0];rows[role].append({'view':view,'seconds':float(f/scene.render.fps),'path':str(Path(path).relative_to(P))})
(P/'review/clips/frames.json').write_text(json.dumps(rows,indent=2))
