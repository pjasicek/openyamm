import bpy,sys,math,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'));import common,reduction_common as C

def render(blend,folder,texfolder,heightpx=700):
 bpy.ops.wm.open_mainfile(filepath=str(blend));C.cleanup();C.activate('Standing',0);s=bpy.context.scene;s.render.engine='BLENDER_EEVEE';s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.65,.65,.65,1);s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.5
 for pos,power in [((4,-4,5),500),((-3,-1,3),300),((0,3,4),400)]:
  data=bpy.data.lights.new('Review softbox','AREA');data.energy=power;data.shape='DISK';data.size=5;light=bpy.data.objects.new('Review softbox',data);s.collection.objects.link(light);light.location=pos;light.rotation_euler=(Vector((0,0,.85))-light.location).to_track_quat('-Z','Y').to_euler()
 s.render.film_transparent=True;s.render.resolution_x=820;s.render.resolution_y=820;s.render.resolution_percentage=100;s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=0
 folder.mkdir(parents=True,exist_ok=True);nodes={}
 for name,tags in [('Body',['body','head']),('SpearMesh',['spear']),('BucklerMesh',['buckler'])]:
  o=bpy.data.objects[name];o.hide_render=False
  for m,tag in zip(o.data.materials,tags):nodes[tag]=m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].links[0].from_node
 for tier in (['natm_a','natm_b','natm_c'] if heightpx==700 else ['natm_b']):
  for tag,node in nodes.items():
   base=texfolder if texfolder==P/'textures'else texfolder/('body'if tag=='head'else tag);node.image=bpy.data.images.load(str(base/f'{tier}_{tag}_preview.png'),check_existing=True)
  for i in range(8):
   angle=i*math.pi/4;target=Vector((0,0,.85));cam=common.ortho_camera('Reduction camera',tuple(target+Vector((math.sin(angle),-math.cos(angle),0))*6),(math.pi/2,0,angle),1.7129090557573363*820/heightpx);s.camera=cam;s.render.filepath=str(folder/f'{tier}_{i}.png');bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)
 print('RENDER_DONE',folder,s.render.engine,flush=True)
if __name__=='__main__':
 render(P/'work/authoring_high.blend',P/'review/reduction/reference700',P/'textures')
 render(P/'work/reduced_baked_probe.blend',P/'review/reduction/probe700',P/'work/reduction/lod0_50')
