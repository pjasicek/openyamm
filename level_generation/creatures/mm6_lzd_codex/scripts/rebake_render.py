"""Eight-view shaded comparisons at the required actor pixel heights."""
import bpy,bmesh,sys,json,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'));import common
def keep(ob,part):
 if part=='actor':return
 bm=bmesh.new();bm.from_mesh(ob.data);la=bm.verts.layers.int['piece'];bmesh.ops.delete(bm,geom=[f for f in bm.faces if all(v[la]==201 for v in f.verts)!=(part=='bow')],context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(ob.data);bm.free()
def render(path,tag,level,reference=False,views=8,parts=('body','bow'),palette=None,samples=16,camera_path=None,box_filter=False):
 bpy.ops.wm.open_mainfile(filepath=str(path));sc=bpy.context.scene;rig=bpy.data.objects['Rig'];a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];sc.frame_set(0)
 ob=bpy.data.objects['BakeSource' if reference else 'Body'];ob.hide_viewport=False
 for o in bpy.data.objects:
  if o.type=='MESH':o.hide_render=o!=ob
 bpy.context.view_layer.update();lo,hi=common.world_bounds([ob])
 camera=Path(camera_path)if camera_path else P/'review/rebake/camera.json'
 if not camera.exists():camera.write_text(json.dumps({'center':list((lo+hi)/2),'height_m':hi.z-lo.z}))
 cal=json.loads(camera.read_text());center=Vector(cal['center'])
 if reference:
  for mat in ob.data.materials:
   group='head'if'Head'in mat.name else'bow'if'Bow'in mat.name else'body'
   for n in mat.node_tree.nodes:
    if n.type=='TEX_IMAGE' and n.image and 'normal'in n.image.name:n.image=bpy.data.images.load(str(P/f'textures/rebake/source_{group}_normal.png'),check_existing=True);n.image.colorspace_settings.name='Non-Color'
 for mat in bpy.data.materials:
  if not mat.use_nodes:continue
  bs=mat.node_tree.nodes.get('Principled BSDF')
  if bs:
   bs.inputs['Specular IOR Level'].default_value=.5;bs.inputs['Specular Tint'].default_value=(1,1,1,1);bs.inputs['IOR'].default_value=1.5
   if palette and bs.inputs['Base Color'].links:
    group='head'if'Head'in mat.name else'bow'if'Bow'in mat.name else'body'
    bs.inputs['Base Color'].links[0].from_node.image=bpy.data.images.load(str(P/f'textures/rebake/tiers/{palette[0]}_{palette[1]}_{group}.png'),check_existing=True)
 sc.render.engine='CYCLES'
 if box_filter:sc.cycles.pixel_filter_type='BOX';sc.cycles.filter_width=1.0
 sc.cycles.samples=samples;sc.cycles.use_denoising=True;sc.cycles.device='CPU';sc.render.threads_mode='FIXED';sc.render.threads=4;sc.render.film_transparent=True;sc.view_settings.view_transform='Standard';sc.view_settings.look='None'
 if sc.world is None:sc.world=bpy.data.worlds.new('MetricWorld')
 sc.world.use_nodes=True;sc.world.node_tree.nodes.get('Background').inputs[0].default_value=(.5,.5,.5,1);sc.world.node_tree.nodes.get('Background').inputs[1].default_value=.5
 for name,pos,power,size in [('Key',(3,-4,5),700,4),('Fill',(-3,-2,2),350,4),('Rim',(0,3,4),500,3)]:
  data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;l=bpy.data.objects.new(name,data);sc.collection.objects.link(l);l.location=pos;l.rotation_euler=(center-l.location).to_track_quat('-Z','Y').to_euler()
 res=[1024,768,384,192][level];pixels=[700,550,220,88][level];sc.render.resolution_x=sc.render.resolution_y=res;sc.render.resolution_percentage=100;sc.render.image_settings.color_mode='RGBA'
 for part in parts:
  partob=ob.copy();partob.data=ob.data.copy();sc.collection.objects.link(partob);keep(partob,part);ob.hide_render=True;partob.hide_render=False;partob.hide_viewport=False
  for i in range(views):
   angle=i*math.pi/4;direction=Vector((math.sin(angle),-math.cos(angle),.05)).normalized();cam=common.ortho_camera('MetricCamera',center+direction*6,(0,0,0),cal['height_m']*res/pixels);cam.rotation_mode='QUATERNION';cam.rotation_quaternion=(-direction).to_track_quat('-Z','Y');sc.camera=cam;sc.render.filepath=str(P/f'review/rebake/{tag}_{part}_l{level}_{i}.png');
   if not Path(sc.render.filepath).exists():bpy.ops.render.render(write_still=True)
   bpy.data.objects.remove(cam,do_unlink=True)
  bpy.data.objects.remove(partob,do_unlink=True)
 print('RENDERED',tag,level,flush=True)
if __name__=='__main__':
 path=P/'work/rebake/near60e_baked.blend'
 render(path,'near60e',0,False,1)
