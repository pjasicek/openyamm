import bpy,sys,runpy
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
def lighting(sc,textured=True):
 sc.render.engine='BLENDER_EEVEE';sc.view_settings.view_transform='Standard'
 sc.world=bpy.data.worlds.new('Neutral');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.2,.2,.2,1);sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.35
 for name,loc,power,size in [('Key',(-2,-3,3),250,3),('Fill',(2,-1,2),150,3),('Rim',(0,3,3),180,2)]:
  d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);sc.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
common.workbench_clay=lighting
sys.argv=['hands','--',str(p/'export/mm6_nobl_runtime_lod0.glb'),str(p/'review/lit_hand'),'Standing:0','Attack:.683']
runpy.run_path(str(p/'scripts/glb_hand_closeups.py'),run_name='__main__')
a=bpy.data.actions['Standing'];r=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0)
common.render_views(str(p/'review/lit_chest'),1.2,.8,views=('front','three_quarter','back'),resolution=(700,700))
