"""Render the actual portable tier-A GLB, all clips and both hands, with standard glTF materials."""
import bpy,sys,math,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(P/'review/viewer/mm6_mer1_a.glb'));s=bpy.context.scene
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');meshes=[o for o in bpy.data.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers)]
for o in list(bpy.data.objects):
 if o.type=='MESH' and o not in meshes:bpy.data.objects.remove(o,do_unlink=True)
s.render.engine='BLENDER_EEVEE';s.world=bpy.data.worlds.new('Review world');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.65,.65,.65,1);s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.5;s.render.film_transparent=True
if hasattr(s,'eevee')and hasattr(s.eevee,'taa_render_samples'):s.eevee.taa_render_samples=16
for pos,power in [((4,-4,5),500),((-3,-1,3),300),((0,3,4),400)]:
 data=bpy.data.lights.new('Review softbox','AREA');data.energy=power;data.shape='DISK';data.size=5;o=bpy.data.objects.new('Review softbox',data);s.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,.85))-o.location).to_track_quat('-Z','Y').to_euler()
O=P/'review/round2/final_frames';O.mkdir(exist_ok=True);report={}
manifest=json.loads((P/'review/viewer/manifest.json').read_text())
for role,info in manifest['clips'].items():
 a=next(a for a in bpy.data.actions if a.name.split('@')[-1].split('|')[-1]==role);rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];rows={v:[]for v in ['front','left','three_quarter']}
 for i in range(6):
  t=info['duration']*i/5;f=t*(s.render.fps/s.render.fps_base);s.frame_set(int(f),subframe=f%1);lo,hi=common.world_bounds(meshes);mid=(lo+hi)*.5
  for v,angle in [('front',0),('left',math.pi/2),('three_quarter',math.radians(35))]:
   extent=hi-lo;wide=abs(math.cos(angle))*extent.x+abs(math.sin(angle))*extent.y;height=max(2.1,extent.z*1.15,wide*480/360*1.15)
   name=common.render_views(str(O/f'{role}_{i}'),mid.z,height,views=(v,),target=(mid.x,mid.y),resolution=(360,480))[0];rows[v].append([name,f'{role} {t:.3f}s'])
 report[role]=rows
# Close-ups include the actual fully curled grip at the blow and the relaxed opposite hand.
a=next(a for a in bpy.data.actions if a.name.split('@')[-1].split('|')[-1]=='Attack');rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];t=.8125;f=t*(s.render.fps/s.render.fps_base);s.frame_set(int(f),subframe=f%1)
for sd in 'LR':
 center=rig.matrix_world@rig.pose.bones[f'B_{sd}_Hand'].head
 for name,offset in [('front',Vector((0,-1,.2))),('outer',Vector((1 if sd=='L'else-1,-.3,.25)))]:
  cam=common.ortho_camera('Hand camera',tuple(center+offset),tuple((center-(center+offset)).to_track_quat('-Z','Y').to_euler()),.38);s.camera=cam;s.render.resolution_x=s.render.resolution_y=640;s.render.filepath=str(P/'review/round2'/f'hand_export_{sd}_{name}.png');bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)
(O/'frames.json').write_text(json.dumps(report,indent=2))

# Rest/body turnarounds and true shoulder close-ups from the final portable export.
for role,t in [('Standing',0),('Attack',.4),('Death',1.3)]:
 a=next(a for a in bpy.data.actions if a.name.split('@')[-1].split('|')[-1]==role);rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];f=t*(s.render.fps/s.render.fps_base);s.frame_set(int(f),subframe=f%1)
 center=sum((rig.matrix_world@rig.pose.bones[f'B_{sd}_UpperArm'].head for sd in 'LR'),Vector())*.5
 common.render_views(str(P/'review/round2'/f'shoulders_{role}'),center.z,.9,views=('front','left','back','right'),target=(center.x,center.y),resolution=(800,800))
 if role=='Standing':common.render_views(str(P/'review/round2/body_final'),.85,1.95,views=('front','left','back','right','three_quarter'),resolution=(750,1000))
