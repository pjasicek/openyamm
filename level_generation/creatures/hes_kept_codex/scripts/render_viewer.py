"""CPU stills of the actual assembled viewer GLBs (same runtime tiers, gear, and clips)."""
import bpy,sys,os
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];ident=sys.argv[sys.argv.index('--')+1];role=os.environ.get('KEPT_ROLE','Standing');seconds=float(os.environ.get('KEPT_SECONDS','0'));focus=os.environ.get('KEPT_FOCUS','body')
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=30;bpy.ops.import_scene.gltf(filepath=str(P/'review/viewer'/f'{ident}.glb'));scene=bpy.context.scene
for o in bpy.data.objects:
 if o.type=='ARMATURE':
  a=next(a for a in bpy.data.actions if a.name==role or a.name.startswith(role+'_'));o.animation_data_create();o.animation_data.action=a;o.animation_data.action_slot=a.slots[0]
scene.render.fps=30;f=seconds*30;scene.frame_set(int(f),subframe=f%1)
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=16;scene.render.threads_mode='FIXED';scene.render.threads=4;scene.world=bpy.data.worlds.new('Review');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.22,.22,.22,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.7
for name,loc,power in [('key',(-2,-3,4),300),('fill',(2,-1,2),90)]:
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.size=3;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
scene.view_settings.view_transform='Standard';scene.view_settings.look='None';sys.path.insert(0,str(P/'scripts'));from kept_review_common import render_views
z,h,xy=(.83,2.0,(-.02,0)) if focus=='body' else (1.55,.45,(-.02,0))
if role=='Attack':z,h,xy=.95,3.5,(-.02,-.4)
if role in ('Death','Dead'):z,h=.6,3.4
if focus=='grip':
 rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');c=rig.matrix_world@rig.pose.bones['B_R_Hand'].head;z,h,xy=c.z,.36,(c.x,c.y)
render_views(str(P/'review'/f'{ident}_{role}_{seconds:g}_{focus}'),z,h,views=('front','three_quarter') if focus in ('head','grip') else ('front','three_quarter','left') if role=='Attack' else ('front','three_quarter','back'),resolution=(480,640) if focus=='body' else (640,640),target=xy)
sys.stdout.flush();sys.stderr.flush();os._exit(0)
