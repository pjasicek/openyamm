import bpy,sys,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(P/'review/viewer/mm6_arc1_a.glb'));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');scene=bpy.context.scene;common.workbench_clay(scene,textured=True)
for mat in bpy.data.materials:
 if mat.node_tree:
  bs=next((n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
  if bs and bs.inputs['Base Color'].links:mat.node_tree.nodes.active=bs.inputs['Base Color'].links[0].from_node
out=P/'review/clips';out.mkdir(exist_ok=True);rows={}
for role in ['Standing','Walking','Cast','Attack','Hit','Death','Dead','Fidget']:
 ac=bpy.data.actions[role];rig.animation_data.action=ac;rig.animation_data.action_slot=ac.slots[0];rows[role]=[]
 for i,f in enumerate((np.array([0,6,12,22,30,36,37,44,52])*scene.render.fps/30 if role in ('Attack','Cast') else np.linspace(*ac.frame_range,7))):
  scene.frame_set(int(f),subframe=float(f-int(f)))
  for view in ['front','left','three_quarter']:
   path=common.render_views(str(out/f'{role}_{i}'),(.85 if role in ('Death','Dead') else .95),(3.4 if role in ('Death','Dead') else 2.6),views=(view,),resolution=(300,420))[0];rows[role].append({'view':view,'seconds':float(f/scene.render.fps),'path':str(Path(path).relative_to(P))})
(P/'review/clips/frames.json').write_text(json.dumps(rows,indent=2))

# Neutral close turnarounds of the head and quiver from the exported tier A.
a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];scene.frame_set(0)
common.render_views(str(P/'review/textured_turnaround'),.91,2.35,views=('front','left','back','right','three_quarter'),resolution=(680,1000))
common.render_views(str(P/'review/head_closeup'),1.56,.52,views=('front','left','back','right','three_quarter'),resolution=(650,650))
