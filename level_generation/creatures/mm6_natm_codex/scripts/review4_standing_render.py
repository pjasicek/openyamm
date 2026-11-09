"""Render the actual packed runtime assets, including folded corpse feathers and shared UV maps."""
import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
info=json.loads((P/'export/export_info.json').read_text());folder=P/'review/final';folder.mkdir(exist_ok=True)
def load(file):
 bpy.ops.wm.read_factory_settings(use_empty=True);sc=bpy.context.scene;sc.render.fps=48;sc.render.fps_base=1;bpy.ops.import_scene.gltf(filepath=str(file));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');meshes=[o for o in bpy.data.objects if o.type=='MESH']
 for track in rig.animation_data.nla_tracks:track.mute=True
 sc.render.engine='BLENDER_EEVEE';sc.world=bpy.data.worlds.new('World');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.18,.18,.18,1);sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.5;sc.view_settings.view_transform='Standard';sc.view_settings.look='None'
 for pos,power in [((4,-4,5),500),((-3,-1,3),300),((0,3,4),400)]:
  data=bpy.data.lights.new('Softbox','AREA');data.energy=power;data.size=5;ob=bpy.data.objects.new('Softbox',data);sc.collection.objects.link(ob);ob.location=pos;ob.rotation_euler=(Vector((0,0,.85))-ob.location).to_track_quat('-Z','Y').to_euler()
 return sc,rig,meshes

def activate(rig,role,t=0):
 a=next(a for a in bpy.data.actions if a.name==role or a.name.endswith('|'+role));rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];frame=t*48;bpy.context.scene.frame_set(int(frame),subframe=frame%1)


sc,r,meshes=load(P/'review/viewer/mm6_natm_a.glb');sc.render.film_transparent=True;activate(r,'Standing',0)
common.render_views(str(folder/'round4_standing_00'),.90,4.0,views=('front','left','three_quarter'),resolution=(750,900),target=(0,-.60))
