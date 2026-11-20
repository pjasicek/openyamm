"""Export the frozen textured rig with every half-frame preserved at 60 Hz."""
import bpy,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parents[1];out=p/'export';out.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(p/'work/animation_finish.blend'))
r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];sc=bpy.context.scene
r.animation_data.action=None
for pb in r.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update();sockets={}
bpy.context.view_layer.objects.active=r;bpy.ops.object.mode_set(mode='EDIT')
for sd,label in [('L','Left'),('R','Right')]:
 B=r.data.bones;w=B[f'B_{sd}_Hand'].head_local;k=B[f'B_{sd}_Finger2'].head_local
 across=B[f'B_{sd}_Finger1'].head_local-B[f'B_{sd}_Finger4'].head_local
 normal=(k-w).cross(across).normalized()
 if normal.x*w.x>0:normal=-normal
 pos=w+(k-w)*.45+normal*.025
 eb=r.data.edit_bones.new('Socket_Palm_'+label);eb.head=pos;eb.tail=pos+normal*.05;eb.parent=r.data.edit_bones[f'B_{sd}_Hand'];eb.use_deform=False
 sockets[eb.name]=list(pos)
bpy.ops.object.mode_set(mode='OBJECT')
mat=bpy.data.materials.new('Monk_A');mat.use_nodes=True;nt=mat.node_tree;bsdf=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED')
def tex(filename,space):
 n=nt.nodes.new('ShaderNodeTexImage');n.image=bpy.data.images.load(str(p/'textures'/filename));n.image.colorspace_settings.name=space;n.image.pack();return n
base=tex('mnk1_basecolor_2k.png','sRGB');nt.links.new(base.outputs['Color'],bsdf.inputs['Base Color']);nt.nodes.active=base
normal=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(tex('mnk1_normal_1k.png','Non-Color').outputs['Color'],normal.inputs['Color']);nt.links.new(normal.outputs['Normal'],bsdf.inputs['Normal'])
sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(tex('mnk1_orm_1k.png','Non-Color').outputs['Color'],sep.inputs['Color']);nt.links.new(sep.outputs['Green'],bsdf.inputs['Roughness']);nt.links.new(sep.outputs['Blue'],bsdf.inputs['Metallic'])
b.data.materials.clear();b.data.materials.append(mat)
for f in b.data.polygons:f.material_index=0;f.use_smooth=True
b.data.uv_layers.active=b.data.uv_layers['UVMap']
for uv in list(b.data.uv_layers):
 if uv.name!='UVMap':b.data.uv_layers.remove(uv)
# Recreate the corpse hold: retained intermediate keys must not override the final Death pose.
death=bpy.data.actions['Death'];r.animation_data.action=death;r.animation_data.action_slot=death.slots[0];sc.frame_set(int(death.frame_range[1]))
held={pb.name:(pb.rotation_quaternion.copy(),pb.location.copy()) for pb in r.pose.bones}
bpy.data.actions.remove(bpy.data.actions['Dead']);dead=bpy.data.actions.new('Dead');dead.use_fake_user=True;r.animation_data.action=dead
for frame in [0,30]:
 for n,(q,l) in held.items():
  pb=r.pose.bones[n];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.location=l;pb.keyframe_insert('rotation_quaternion',frame=frame);pb.keyframe_insert('location',frame=frame)
dead.use_frame_range=True;dead.frame_start=0;dead.frame_end=30
# q and -q are the same rotation, but Blender interpolates quaternion component curves before normalizing.
for action in bpy.data.actions:
 curves={}
 for layer in action.layers:
  for strip in layer.strips:
   for cb in strip.channelbags:
    for fc in cb.fcurves:
     if fc.data_path.endswith('rotation_quaternion'):curves.setdefault(fc.data_path,{})[fc.array_index]=fc
 for components in curves.values():
  assert len(components)==4
  keys=[components[i].keyframe_points for i in range(4)];assert len(set(map(len,keys)))==1;previous=None
  for j in range(len(keys[0])):
   q=np.array([keys[i][j].co.y for i in range(4)]);q/=np.linalg.norm(q)
   if previous is not None and q@previous<0:q=-q
   for i in range(4):keys[i][j].co.y=float(q[i]);keys[i][j].interpolation='LINEAR'
   previous=q
  for fc in components.values():fc.update()
# The authored unfold changes palm orientation faster than the selected source death. Preserve its collision-free
# pose path, giving only those authored intervals the time needed for a <=15 degree hand step per 30 fps frame.
act=bpy.data.actions['Death'];r.animation_data.action=act;r.animation_data.action_slot=act.slots[0];end=int(act.frame_range[1]);timing=[0];previous=None
for f in range(end+1):
 sc.frame_set(f);current={n:r.pose.bones[n].matrix.to_quaternion().copy() for n in ['B_L_Hand','B_R_Hand']}
 if previous:
  angle=max(min(math.degrees(previous[n].rotation_difference(current[n]).angle),360-math.degrees(previous[n].rotation_difference(current[n]).angle)) for n in current)
  timing.append(timing[-1]+max(1,math.ceil(angle/15)))
 previous=current
for layer in act.layers:
 for strip in layer.strips:
  for cb in strip.channelbags:
   for fc in cb.fcurves:
    for key in fc.keyframe_points:
     for point in [key.co,key.handle_left,key.handle_right]:point.x=float(np.interp(point.x,np.arange(end+1),timing))
    fc.update()
act.frame_end=timing[-1]
(p/'work/death_timing.json').write_text(json.dumps({'original_duration_s':end/30,'final_duration_s':timing[-1]/30,'old_frame_to_new':timing,'reason':'Only fast authored palm-unfold intervals expanded; the previously gated whole-body pose path and remaining source cadence are preserved.'},indent=2))
r.animation_data.action=None
for pb in r.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
# Store an editable 30 fps master, including custom labels and half-frame cloth keys.
bpy.ops.wm.save_as_mainfile(filepath=str(out/'mm6_mnk1.blend'))
roles=['Standing','Walking','Running','Attack','Cast','Hit','Death','Dead','Fidget']
for a in list(bpy.data.actions):
 if a.name not in roles:bpy.data.actions.remove(a)
info={'triangles':sum(len(f.vertices)-2 for f in b.data.polygons),'bones':len(r.data.bones),'sockets':sockets,'clips':{}}
def setact(a):r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
for a in bpy.data.actions:
 setact(a);start,end=map(float,a.frame_range);frames=[];bounds=[]
 for f in np.arange(start,end+.01,.5):
  sc.frame_set(int(f),subframe=float(f%1));ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();P=np.array([tuple(v.co) for v in me.vertices]);ev.to_mesh_clear();bounds.append([P.min(0).tolist(),P.max(0).tolist()]);frames.append([float(f/30),*[list(r.pose.bones[n].head) for n in sockets]])
 entry={'duration':(end-start)/30,'mode':'loop' if a.name in ['Standing','Walking','Running','Dead'] else 'once','bounds':np.array(bounds).min(0)[0].tolist()+np.array(bounds).max(0)[1].tolist()}
 if a.name in ['Attack','Cast']:
  q=np.array([x[2] for x in frames]);speed=-np.diff(q[:,1])*60;ix=int(speed.argmax())+1;entry['release_time']=float(frames[ix][0]);entry['forward_palm_speed_mps']=float(speed[ix-1])
 info['clips'][a.name]=entry
 if a.name=='Standing':info['standing_height_m']=float(max(x[1][2]-x[0][2] for x in bounds))
 for layer in a.layers:
  for strip in layer.strips:
   for cb in strip.channelbags:
    for fc in cb.fcurves:
     for key in fc.keyframe_points:key.co.x*=2;key.handle_left.x*=2;key.handle_right.x*=2
     fc.update()
 a.frame_start=start*2;a.frame_end=end*2
sc.render.fps=60;sc.render.fps_base=1
setact(bpy.data.actions['Standing']);sc.frame_set(0)
b.name=b.data.name='Monk'
for obj in bpy.data.objects:obj.select_set(obj in [r,b])
bpy.context.view_layer.objects.active=r
bpy.ops.export_scene.gltf(filepath=str(out/'mm6_mnk1_lod0.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,export_image_format='AUTO',export_reset_pose_bones=True,export_anim_slide_to_zero=True)
(out/'export_info.json').write_text(json.dumps(info,indent=2))
print('EXPORTED',json.dumps(info))
