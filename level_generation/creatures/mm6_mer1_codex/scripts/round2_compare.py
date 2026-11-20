import bpy,bmesh,sys,json,math,subprocess,runpy,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'));import common,reduction_common as C,reduction_bake as B
W=P/'work/reduction';O=P/'review/reduction';W.mkdir(exist_ok=True);O.mkdir(exist_ok=True)
def render(folder,kind,level,texfolder=None,tiers=None):
 folder.mkdir(parents=True,exist_ok=True);s=bpy.context.scene;common.workbench_clay(s,True);s.display.shading.show_specular_highlight=False;
 s.render.engine='BLENDER_EEVEE';s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.65,.65,.65,1);s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.5
 if hasattr(s,'eevee') and hasattr(s.eevee,'taa_render_samples'):s.eevee.taa_render_samples=16
 for o in list(bpy.data.objects):
  if o.type=='LIGHT':bpy.data.objects.remove(o,do_unlink=True)
 for pos,power in [((4,-4,5),500),((-3,-1,3),300),((0,3,4),400)]:
  data=bpy.data.lights.new('Review softbox','AREA');data.energy=power;data.shape='DISK';data.size=5;light=bpy.data.objects.new('Review softbox',data);s.collection.objects.link(light);light.location=pos;light.rotation_euler=(Vector((0,0,.85))-light.location).to_track_quat('-Z','Y').to_euler()
 s.render.film_transparent=True;s.display.render_aa='16';s.render.resolution_x=820;s.render.resolution_y=820;s.render.resolution_percentage=100
 body=bpy.data.objects['Body'];prop=bpy.data.objects['ClubMesh'];
 for ob in bpy.data.objects:
  if ob.type=='MESH'and ob not in [body,prop]:ob.hide_render=True
 body.hide_render=kind!='body';prop.hide_render=kind!='club';mat=body.data.materials[0];bs=mat.node_tree.nodes.get('Principled BSDF');node=bs.inputs['Base Color'].links[0].from_node;original=node.image
 for m in [*body.data.materials,*prop.data.materials]:
  bs=m.node_tree.nodes.get('Principled BSDF');m.node_tree.nodes.active=bs.inputs['Base Color'].links[0].from_node
 poses=[('Standing',0)]
 scale=1.7*820/700 if level==0 else 1.94*820/[0,550,220,88][level]
 for tier in (tiers or (['a','b','c']if kind=='body'else['a'])):
  if kind=='body':node.image=bpy.data.images.load(str((texfolder if texfolder else P/'textures')/f'mer1_{tier}_preview.png'),check_existing=True)
  for role,t in poses:
   C.activate(role,t)
   for i in range(8):
    angle=i*math.pi/4;target=Vector((0,0,.85));cam=common.ortho_camera('Reduction camera',tuple(target+Vector((math.sin(angle),-math.cos(angle),0))*6),(math.pi/2,0,angle),scale);s.camera=cam;s.render.filepath=str(folder/f'{tier}_{role}_{i}.png');bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)
 node.image=original;body.hide_render=False;prop.hide_render=False
 return {'actor_height_px_lod0':700,'viewport_px':820,'orthographic_scale_m':scale,'switch_pixels':[None,550,220,88][level]}

report={}
for level in range(4):
 for label,blend,tex in [('reference','work/round2/master.blend','textures/round2'),('reduced',f'work/round2/body_lod{level}.blend','work/round2/shared_textures')]:
  bpy.ops.wm.open_mainfile(filepath=str(P/blend));render(P/f'review/round2/reduction/lod{level}/{label}','body',level,P/tex,tiers=['a','b','c'])
