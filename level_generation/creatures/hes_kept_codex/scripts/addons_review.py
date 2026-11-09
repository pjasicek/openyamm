"""Review the equipped final source with CPU lights and the runtime normal convention."""
import bpy,sys,os,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];kind=os.environ.get('KEPT_BODY','male');style=os.environ.get('KEPT_STYLE','ragged');tier=os.environ.get('KEPT_TIER','c');action=os.environ.get('KEPT_ACTION','Kept_ArmedStanding' if style=='ragged' and tier!='a' else 'Kept_Standing');frame=float(os.environ.get('KEPT_FRAME','0'))
bpy.ops.wm.open_mainfile(filepath=str(P/'work/addons_v2/equipped.blend'));scene=bpy.context.scene;rig=bpy.data.objects['Rig'];rig.animation_data.action=bpy.data.actions[action];rig.animation_data.action_slot=rig.animation_data.action.slots[0];scene.frame_set(int(frame),subframe=frame%1)
keep={'Kept','Rig'}
if style=='ragged':keep.add('hes_kept_collar');keep.update({'b':{'hes_kept_pick'},'c':{'hes_kept_club','hes_kept_plate'},'a':set()}[tier])
for o in bpy.data.objects:o.hide_render=o.name not in keep
# Meshy normals use +Y down; the runtime prepare step flips them. Mirror that for this source preview.
for im in bpy.data.images:
 if 'normal_1k' in im.name:
  import numpy as np
  a=np.array(im.pixels[:],dtype=np.float32).reshape(-1,4);a[:,1]=1-a[:,1];im.pixels.foreach_set(a.ravel())
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=24;scene.render.threads_mode='FIXED';scene.render.threads=4
scene.world=bpy.data.worlds.new('Preview');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.22,.22,.22,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.7
for name,loc,power,size in [('key',(-2,-3,4),350,3),('fill',(2,-1,2),80,2)]:
 data=bpy.data.lights.new(name,'AREA');data.energy=power;data.size=size;o=bpy.data.objects.new(name,data);scene.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
scene.view_settings.view_transform='Standard';scene.view_settings.look='None';sys.path.insert(0,str(P/'scripts'));from kept_review_common import render_views
focus=os.environ.get('KEPT_FOCUS','body');target=(-.02,0);z,h=(1.53,.45) if focus=='head' else (.9,2.5)
if focus=='head':
 c=rig.matrix_world@rig.pose.bones['B_Head'].head;z=c.z+.06;target=(c.x,c.y)
render_views(str(P/'review/addons_v2'/f'{tier}_{action}_{frame:g}_{focus}'),z,h,views=('front','three_quarter','back') if focus=='body' else ('front','three_quarter'),resolution=(640,768) if focus=='body' else (640,640),target=target)
sys.stdout.flush();sys.stderr.flush();os._exit(0)
