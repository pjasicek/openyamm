"""Actual tier colours and tangent normals in neutral Cycles lighting, 700-pixel actor."""
import bpy,sys,math,numpy as np
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
args=sys.argv[sys.argv.index('--')+1:];label=args[0];tier=args[1] if len(args)>1 else 'c';level=int(args[2]) if len(args)>2 else 0
bpy.ops.wm.open_mainfile(filepath=str(p/'work'/('round3_motion.blend' if label=='reference' else f'round3_lod{level}.blend')));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];scene=bpy.context.scene
for o in bpy.data.objects:
 if o.type=='MESH':o.hide_render=o!=body
if label=='reference':
 for im in bpy.data.images:
  if im.name in ['sor1_normal_1k.png','sor1_head_normal_1k.png']:
   a=np.array(im.pixels[:],np.float32).reshape(-1,4);a[:,1]=1-a[:,1];im.pixels.foreach_set(a.ravel());im.update()
for i,m in enumerate(body.data.materials):
 for n in m.node_tree.nodes:
  if n.type=='TEX_IMAGE' and n.image and 'basecolor' in n.image.name and i==0:n.image=bpy.data.images.load(str(p/'work'/f'reduction_{label}{level}_{tier}.png'))
  if n.type=='BSDF_PRINCIPLED':n.inputs['Specular IOR Level'].default_value=0;n.inputs['Metallic'].default_value=0
rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=bpy.data.actions['Standing'].slots[0];scene.frame_set(0)
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=16;scene.cycles.use_denoising=True;scene.cycles.seed=42;scene.render.threads_mode='FIXED';scene.render.threads=4;scene.render.film_transparent=True;scene.view_settings.view_transform='Standard';scene.view_settings.look='None'
if scene.world is None:scene.world=bpy.data.worlds.new('World')
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.7,.7,.7,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.65
for loc,energy,size in [((-3,-4,5),350,5),((4,2,3),200,4)]:
 d=bpy.data.lights.new('Softbox','AREA');d.energy=energy;d.shape='DISK';d.size=size;o=bpy.data.objects.new('Softbox',d);bpy.context.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
height=[700,550,220,88][level];res=int(round(height*1.86/1.7));scene.render.resolution_x=scene.render.resolution_y=res;scene.render.resolution_percentage=100;cam=common.ortho_camera('ReductionCamera',(0,-6,.85),(math.pi/2,0,0),1.86);scene.camera=cam
out=p/'review/round3/reduction';
for i in range(8):
 a=i*math.pi/4;cam.location=(6*math.sin(a),-6*math.cos(a),.85);cam.rotation_euler=(math.pi/2,0,a);scene.render.filepath=str(out/f'pbr_{label}{level}_{tier}_{i}.png');bpy.ops.render.render(write_still=True)
