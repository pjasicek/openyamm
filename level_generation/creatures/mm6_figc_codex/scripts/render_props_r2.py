"""Standalone views of the actual exported prop surfaces, with the final tier-A ramp baked."""
import bpy,math,json
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/export_validation.blend'));scene=bpy.context.scene;rig=bpy.data.objects['Rig']
a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];scene.frame_set(0)
lh=rig.pose.bones['B_L_Hand'].matrix.copy();D=rig.data.bones['B_L_Hand'].matrix_local@lh.inverted()
shield_up=(D.to_3x3()@Vector((0,0,1))).normalized();shield_out=(D.to_3x3()@Vector((0,-1,0))).normalized()
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
eq=json.loads((P/'work/equipment.json').read_text());axis=Vector(eq['axe_axis']);edge=Vector(eq['axe_edge']);normal=axis.cross(edge).normalized()
for o in bpy.data.objects:
 if o.type=='MESH':o.hide_render=True
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.threads_mode='FIXED';scene.render.threads=4
scene.render.resolution_x=768;scene.render.resolution_y=1024;scene.render.resolution_percentage=100
scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0;scene.view_settings.gamma=1
scene.world=bpy.data.worlds.new('Prop review neutral world');scene.world.use_nodes=True;bg=scene.world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.20,.20,.20,1);bg.inputs['Strength'].default_value=.65
base=bpy.data.images.load(str(P/'work/tier_figc_a_FighterChainGear_A.png'))
for mat in bpy.data.materials:
 if not mat.use_nodes:continue
 for node in mat.node_tree.nodes:
  if node.type=='TEX_IMAGE' and node.image and 'gear_basecolor' in node.image.name:node.image=base
for name,up,out in [('Axe',axis,-normal),('Shield',shield_up,shield_out)]:
 ob=bpy.data.objects[name];ob.hide_render=False;points=[ob.matrix_world@v.co for v in ob.data.vertices];center=sum(points,Vector())/len(points)
 coords=[v.dot(up) for v in points];center+=up*((max(coords)+min(coords))/2-center.dot(up));height=max(coords)-min(coords)
 for angle,label in [(0,'front'),(32,'quarter')]:
  from mathutils import Quaternion
  direction=Quaternion(up,math.radians(angle))@out;right=up.cross(direction).normalized();camdata=bpy.data.cameras.new('review_camera');camdata.type='ORTHO';camdata.ortho_scale=height*1.16;cam=bpy.data.objects.new('review_camera',camdata);scene.collection.objects.link(cam);cam.location=center+direction*3;cam.rotation_euler=Matrix((right,up,direction)).transposed().to_euler();scene.camera=cam
  ld=bpy.data.lights.new('softbox','AREA');ld.energy=85;ld.shape='DISK';ld.size=2;light=bpy.data.objects.new('softbox',ld);scene.collection.objects.link(light);light.location=center+direction*1.4+up*.7-right*.5;light.rotation_euler=(center-light.location).to_track_quat('-Z','Y').to_euler()
  scene.render.filepath=str(P/f'review/round2/details/{name.lower()}_standalone_{label}.png');bpy.ops.render.render(write_still=True)
  bpy.data.objects.remove(cam,do_unlink=True);bpy.data.objects.remove(light,do_unlink=True)
 ob.hide_render=True
