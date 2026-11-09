import runpy,sys,bpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
sys.argv=['contacts','--',str(P/'work/production_body.blend'),'Standing','Walking','Attack','Cast','Hit','Death','Dead','Fidget'];runpy.run_path(str(P/'scripts/g6_contacts.py'),run_name='__main__')
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(P/'review/viewer/mm6_jak1_a.glb'));rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');sc=bpy.context.scene;common.workbench_clay(sc,textured=True)
for mat in bpy.data.materials:
 if mat.node_tree:
  bs=mat.node_tree.nodes.get('Principled BSDF')
  if bs and bs.inputs['Base Color'].links:mat.node_tree.nodes.active=bs.inputs['Base Color'].links[0].from_node
for n,t in [('Fidget',2.9),('Attack',4/30)]:
 rig.animation_data.action=bpy.data.actions[n];rig.animation_data.action_slot=rig.animation_data.action.slots[0];f=t*sc.render.fps;sc.frame_set(int(f),subframe=f-int(f));common.render_views(str(P/f'review/body_contact_{n}'),1.15,1.2,views=['front','right','three_quarter'],target=(-.2,0),resolution=(650,800))
