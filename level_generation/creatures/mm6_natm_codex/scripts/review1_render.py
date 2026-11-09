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

sc,r,meshes=load(P/'review/viewer/mm6_natm_b.glb');print('RUNTIME_ACTIONS',[a.name for a in bpy.data.actions],flush=True)
for role,row in info['clips'].items():
 times=np.linspace(0,row['duration'],7);bounds=[]
 for t in times:activate(r,role,t);lo,hi=common.world_bounds(meshes);bounds.append([lo[:],hi[:]])
 lo=np.min(np.array(bounds)[:,0],0);hi=np.max(np.array(bounds)[:,1],0);row['bounds']=lo.tolist()+hi.tolist();center=(lo+hi)/2;height=max((hi-lo)[2],np.linalg.norm((hi-lo)[:2])*520/420)*1.10
 for i,t in enumerate(times):
  activate(r,role,t);common.render_views(str(folder/f'{role}_{i:02}'),center[2],max(height,1.9),views=('front','left','three_quarter'),resolution=(420,520),target=tuple(center[:2]))
 print('RUNTIME_CLIP_REVIEW',role,flush=True)
activate(r,'Standing',0)
for tag in ['Spear','Buckler']:
 target=next(o for o in meshes if o.name==tag+'Mesh')
 for o in meshes:o.hide_render=o!=target
 lo,hi=common.world_bounds([target]);center=(lo+hi)/2;common.render_views(str(folder/f'prop_{tag.lower()}'),center.z,max(hi-lo)*1.15,views=('front','left','three_quarter'),resolution=(720,720),target=(center.x,center.y))
for o in meshes:o.hide_render=False
common.render_views(str(folder/'grip_and_straps'),.95,.70,views=('front','left','three_quarter'),resolution=(720,720),target=(-.2,-.04));common.render_views(str(folder/'head'),1.53,.45,views=('front','left','three_quarter'),resolution=(720,720))
activate(r,'Dead',0);bpy.ops.mesh.primitive_plane_add(size=6,location=(0,0,0));ground=bpy.context.object;ground.name='Review floor';mat=bpy.data.materials.new('Floor');mat.diffuse_color=(.17,.19,.20,1);ground.data.materials.append(mat)
lo,hi=common.world_bounds(meshes);center=(lo+hi)/2
for i,direction in enumerate([(3,-4,2),(4,0,.6),(0,4,2)]):
 cam=common.ortho_camera('Floor review',tuple(center+Vector(direction)),(0,0,0),2.3);cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();sc.camera=cam;sc.render.resolution_x=1000;sc.render.resolution_y=650;sc.render.filepath=str(folder/f'corpse_floor_{i}.png');bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)
(P/'export/export_info.json').write_text(json.dumps(info,indent=2))
# Eight-view final colour review at every switch size. The unchanged high reference remains the comparison baseline.
for level,size in [(0,700),(1,550),(2,220),(3,88)]:
 for tier in (['natm_a','natm_b','natm_c']if level==0 else['natm_b']):
  file=P/f'review/viewer/mm6_{tier}.glb'if level==0 else P/f'review/runtime/lod{level}_{tier}.glb';sc,r,meshes=load(file);activate(r,'Standing',0);sc.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.65,.65,.65,1);sc.render.film_transparent=True;sc.render.resolution_x=sc.render.resolution_y=820
  dest=P/f'review/reduction/round1_lod{level}_{size}';dest.mkdir(exist_ok=True)
  for i in range(8):
   angle=i*math.pi/4;target=Vector((0,0,.85));cam=common.ortho_camera('Review',tuple(target+Vector((math.sin(angle),-math.cos(angle),0))*6),(math.pi/2,0,angle),1.7129090557573363*820/size);sc.camera=cam;sc.render.filepath=str(dest/f'{tier}_{i}.png');bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)
 print('RUNTIME_LOD_REVIEW',level,flush=True)
print('ROUND1_REVIEW_COMPLETE',flush=True)
