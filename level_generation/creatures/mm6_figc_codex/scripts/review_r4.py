"""Fixed before/after review and editable snapshot of this one-pass revision."""
import bpy,math,sys,runpy,json
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];R=P/'review/round4';sys.path.insert(0,str(P/'scripts'));import common
for folder in ['axe','body','lower']:(R/folder).mkdir(exist_ok=True)
def load(path):
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=30;bpy.ops.import_scene.gltf(filepath=str(path));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];bpy.context.scene.frame_set(0);bpy.context.view_layer.update();return rig

def camera(center,direction,up,scale,res,path):
 scene=bpy.context.scene;right=up.cross(direction).normalized();data=bpy.data.cameras.new('ReviewCamera');data.type='ORTHO';data.ortho_scale=scale;cam=bpy.data.objects.new('ReviewCamera',data);scene.collection.objects.link(cam);cam.location=center+direction*4;cam.rotation_euler=Matrix((right,up,direction)).transposed().to_euler();scene.camera=cam;scene.render.resolution_x=res;scene.render.resolution_y=res;scene.render.resolution_percentage=100;scene.render.filepath=str(path);bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)

for label,path in [('accepted',R/'accepted_combined.glb'),('reduced',P/'review/viewer/mm6_figc_a.glb')]:
 load(path);scene=bpy.context.scene;common.workbench_clay(scene,textured=True);scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
 for i in range(8):
  a=i*math.pi/4;direction=Vector((math.sin(a),-math.cos(a),.08)).normalized();up=direction.cross(Vector((math.cos(a),math.sin(a),0))).normalized();camera(Vector((0,0,.90)),direction,up,1.763883397*768/700,768,R/'body'/f'{label}_{i}.png')
 axe=next(o for o in bpy.data.objects if o.type=='MESH' and 'Axe_visual' in o.name)
 for o in bpy.data.objects:
  if o.type=='MESH':o.hide_render=o!=axe
 scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=4
 scene.world=bpy.data.worlds.new('Neutral world');scene.world.use_nodes=True;bg=scene.world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.20,.20,.20,1);bg.inputs['Strength'].default_value=.65
 up=(axe.matrix_world.to_3x3()@Vector((0,0,1))).normalized();out=(axe.matrix_world.to_3x3()@Vector((.3626246,-.9319353,0))).normalized();center=axe.matrix_world@Vector((0,0,(.46959427-.116)/2))
 for angle,name in [(0,'front'),(32,'quarter')]:
  direction=Quaternion(up,math.radians(angle))@out;right=up.cross(direction).normalized();ld=bpy.data.lights.new('Softbox','AREA');ld.energy=85;ld.size=2;light=bpy.data.objects.new('Softbox',ld);scene.collection.objects.link(light);light.location=center+direction*1.4+up*.7-right*.5;light.rotation_euler=(center-light.location).to_track_quat('-Z','Y').to_euler();camera(center,direction,up,.68,640,R/'axe'/f'{label}_{name}.png')
  if name=='front':camera(center,direction,up,1.763883397*288/700,288,R/'axe'/f'{label}_ingame.png')
  bpy.data.objects.remove(light,do_unlink=True)
for label,level in [('accepted',1),('reduced',1),('reduced',2),('reduced',3)]:
 load(R/f'{label}_lod{level}.glb');scene=bpy.context.scene;common.workbench_clay(scene,textured=True);scene.view_settings.view_transform='Standard';scene.view_settings.look='None';res=[0,768,384,192][level];pixels=[0,550,220,88][level]
 for angle,name in [(0,'front'),(35,'quarter')]:
  a=math.radians(angle);direction=Vector((math.sin(a),-math.cos(a),.08)).normalized();up=direction.cross(Vector((math.cos(a),math.sin(a),0))).normalized();camera(Vector((0,0,.90)),direction,up,1.763883397*res/pixels,res,R/'lower'/f'{label}_lod{level}_{name}.png')
# Canonical snapshot retains un-ramped materials and the unchanged runtime animations.
load(R/'combined_unbaked.glb')
for folder in [P/'textures/round4_body',P/'textures/round4_axe']:
 for name in ['basecolor','metal_rough','normal','region_mask']:
  image=bpy.data.images.load(str(folder/f'{name}.png'),check_existing=True);image.pack()
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/mm6_figc_authoring.blend'))
# The established clip-sheet script uses the current combined viewer model.
runpy.run_path(str(P/'scripts/render_final.py'),run_name='__main__')
