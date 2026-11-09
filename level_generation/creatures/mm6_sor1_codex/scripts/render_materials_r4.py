"""Fixed-light texture comparison and explicit full/quarter-resolution material close-ups."""
import bpy,sys,math
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
args=sys.argv[sys.argv.index('--')+1:];label=args[0];tier=args[1] if len(args)>1 else 'c';mip=args[2] if len(args)>2 else '1';old=label=='accepted'
bpy.ops.wm.open_mainfile(filepath=str(p/'work'/('round3_lod0.blend' if old else 'round4_lod0.blend')));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];scene=bpy.context.scene
for o in bpy.data.objects:
 if o.type=='MESH':o.hide_render=o.name not in ['Body','Staff']
for i,m in enumerate(body.data.materials):
 for n in m.node_tree.nodes:
  if n.type=='TEX_IMAGE' and n.image:
   channel='basecolor' if 'basecolor' in n.image.name else 'normal' if 'normal' in n.image.name else 'orm' if '_orm' in n.image.name or 'metal_rough' in n.image.name else None
   if channel=='basecolor' and (not old or i==0):
    name=p/'work'/f'reduction_candidate0_{tier}.png' if old else p/'textures/round4'/f'review_{tier}{"_mip4" if mip=="4" else ""}.png';n.image=bpy.data.images.load(str(name),check_existing=True)
   elif not old and mip=='4' and channel in ['normal','orm']:n.image=bpy.data.images.load(str(p/'textures/round4'/f'sor1_{channel}_mip4.png'),check_existing=True);n.image.colorspace_settings.name='Non-Color'
  if n.type=='BSDF_PRINCIPLED':n.inputs['Specular IOR Level'].default_value=0;n.inputs['Metallic'].default_value=0
rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=bpy.data.actions['Standing'].slots[0];scene.frame_set(0)
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=16;scene.cycles.use_denoising=True;scene.cycles.seed=42;scene.render.threads_mode='FIXED';scene.render.threads=4;scene.render.film_transparent=True;scene.view_settings.view_transform='Standard';scene.view_settings.look='None'
if scene.world is None:scene.world=bpy.data.worlds.new('World')
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.7,.7,.7,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.65
for loc,energy,size in [((-3,-4,5),350,5),((4,2,3),200,4)]:
 d=bpy.data.lights.new('Softbox','AREA');d.energy=energy;d.shape='DISK';d.size=size;o=bpy.data.objects.new('Softbox',d);bpy.context.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
cam=common.ortho_camera('MaterialCamera',(0,-6,.90),(math.pi/2,0,0),2.02);scene.camera=cam;out=p/'review/round4/renders';out.mkdir(exist_ok=True)
if mip=='1':
 scene.render.resolution_x=scene.render.resolution_y=832;scene.render.resolution_percentage=100
 for i in (range(8) if tier=='c' else [0]):
  a=i*math.pi/4;cam.location=(6*math.sin(a),-6*math.cos(a),.90);cam.rotation_euler=(math.pi/2,0,a);scene.render.filepath=str(out/f'{label}_{tier}_{i}.png');bpy.ops.render.render(write_still=True)
if not old and tier=='c':
 for name,z,height,res in [('collar',1.43,.64,272),('robe',.70,.75,256),('hem',.22,.52,176)]:
  cam.location=(0,-6,z);cam.rotation_euler=(math.pi/2,0,0);cam.data.ortho_scale=height;scene.render.resolution_x=scene.render.resolution_y=res;scene.render.filepath=str(out/f'{name}_mip{mip}.png');bpy.ops.render.render(write_still=True)
