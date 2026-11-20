import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_master.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];staff=bpy.data.objects['StaffMesh'];rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
roll=max(json.loads((P/'work/staff_roll_sweep.json').read_text()),key=lambda r:r['signed_edge_lead'])['roll_deg']
# Roll the actual hooked edge into its swing plane; all hand/arm animation remains unchanged.
M=rig.data.bones['Staff'].matrix_local.copy();delta=M@Matrix.Rotation(math.radians(roll),4,'Z')@M.inverted();staff.data.transform(delta);bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for name in ['Staff','StaffTip']:rig.data.edit_bones[name].matrix=delta@rig.data.edit_bones[name].matrix
bpy.ops.object.mode_set(mode='OBJECT')
# Build up both grasping sections to fit the closed palms and every digit, with tapered transitions.
staff_frame=rig.matrix_world@rig.data.bones['Staff'].matrix_local;staff_inverse=staff_frame.inverted()
for vertex in staff.data.vertices:
 q=staff_inverse@staff.matrix_world@vertex.co;radius=math.hypot(q.x,q.y);extra=0
 for center,target_radius in [(0,.016),(.29,.017)]:
  u=max(0,min(1,(.09-abs(q.z-center))/.035));extra+=max(0,target_radius-radius)*u*u*(3-2*u)
 if radius>1e-7:q.x*=1+extra/radius;q.y*=1+extra/radius
 vertex.co=staff.matrix_world.inverted()@staff_frame@q
(P/'work/staff_grip_geometry.json').write_text(json.dumps({'minimum_grip_radius_m':{'dominant':.016,'offhand':.017},'ornament_radii':'preserved','centers_staff_local_z_m':[0,.29],'constant_half_length_m':.055,'taper_length_m':.035,'new_triangles':0},indent=2))
def material(name,tag):
 mat=bpy.data.materials.new(name);mat.use_nodes=True;nt=mat.node_tree;bs=nt.nodes.get('Principled BSDF')
 def tex(suffix,space):
  path=P/'textures'/(f'jak1_{tag}_{suffix}' if tag!='staff' else 'staff/'+suffix);node=nt.nodes.new('ShaderNodeTexImage');node.image=bpy.data.images.load(str(path));node.image.colorspace_settings.name=space;return node
 nt.links.new(tex('basecolor_1k.png','sRGB').outputs['Color'],bs.inputs['Base Color']);normal=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(tex('normal_1k.png','Non-Color').outputs['Color'],normal.inputs['Color']);nt.links.new(normal.outputs['Normal'],bs.inputs['Normal']);sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(tex('metal_rough_1k.png','Non-Color').outputs['Color'],sep.inputs['Color']);nt.links.new(sep.outputs['Green'],bs.inputs['Roughness']);nt.links.new(sep.outputs['Blue'],bs.inputs['Metallic']);return mat
body.data.materials.clear();body.data.materials.append(material('Jackalman_A','body'));body.data.materials.append(material('JackalmanHead_A','head'));flags=[a.value for a in body.data.attributes['head'].data]
for face in body.data.polygons:
 face.material_index=flags[face.index]
 if face.material_index:
  for li in face.loop_indices:body.data.uv_layers['UVMap'].data[li].uv=body.data.uv_layers['HeadUV'].data[li].uv
body.data.uv_layers.remove(body.data.uv_layers['HeadUV']);body.data.uv_layers.active=body.data.uv_layers['UVMap'];body.data.uv_layers['UVMap'].active_render=True
staff.data.materials.clear();staff.data.materials.append(material('HookedStaff_A','staff'))
for f in staff.data.polygons:f.material_index=0
pa=staff.data.attributes.get('piece') or staff.data.attributes.new('piece','INT','POINT');pa.data.foreach_set('value',[100]*len(pa.data))
for o in bpy.data.objects:o.select_set(o in (body,staff))
bpy.context.view_layer.objects.active=body;bpy.ops.object.join();body.name='Jackalman'
keep=['Standing','Walking','Attack','Cast','Hit','Death','Dead','Fidget']
for a in list(bpy.data.actions):
 if a.name not in keep:
  bpy.data.actions.remove(a);continue
 for layer in a.layers:
  for strip in layer.strips:
   for cb in strip.channelbags:
    groups={}
    for fc in cb.fcurves:
     if fc.data_path.endswith('rotation_quaternion'):groups.setdefault(fc.data_path,{})[fc.array_index]=fc
    for comps in groups.values():
     if len(comps)!=4:continue
     prev=None;ks=[comps[i].keyframe_points for i in range(4)]
     for j in range(min(map(len,ks))):
      q=[ks[i][j].co.y for i in range(4)]
      if prev is not None and sum(x*y for x,y in zip(prev,q))<0:
       for i in range(4):ks[i][j].co.y*=-1;ks[i][j].handle_left.y*=-1;ks[i][j].handle_right.y*=-1
       q=[-v for v in q]
      prev=q
     for fc in comps.values():fc.update()
# Bound the complete rolled staff and skin between keys before freezing the corpse pose.
staff_group=body.vertex_groups['Staff'].index;floor_ids=[v.index for v in body.data.vertices if not any(g.group==staff_group and g.weight>.5 for g in v.groups)]
root=rig.pose.bones['B_Pelvis'];root_inv=rig.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted();death=bpy.data.actions['Death'];rig.animation_data.action=death;rig.animation_data.action_slot=death.slots[0];last=int(death.frame_range[1]);floor_changes=[]
for iteration in range(2):
 lifts=np.zeros(last+1)
 for f in range(last+1):
  bpy.context.scene.frame_set(int(f),subframe=float(f-int(f)));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();z=min(mesh.vertices[i].co.z for i in floor_ids);ev.to_mesh_clear();dz=max(0,.003-z)
  lifts[int(f)]=max(lifts[int(f)],dz);lifts[min(last,math.ceil(f))]=max(lifts[min(last,math.ceil(f))],dz)
 roots=[]
 for f in range(last+1):
  bpy.context.scene.frame_set(f);roots.append(root.location.copy()+root_inv@Vector((0,0,float(lifts[f]))))
 for f,value in enumerate(roots):root.location=value;root.keyframe_insert('location',frame=f)
 for layer in death.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for curve in bag.fcurves:
     if curve.data_path.endswith('location'):
      for key in curve.keyframe_points:key.interpolation='LINEAR'
 floor_changes.append(float(lifts.max()))
bpy.context.scene.frame_set(last);end_root=root.location.copy();dead=bpy.data.actions['Dead'];rig.animation_data.action=dead;rig.animation_data.action_slot=dead.slots[0]
for f in range(int(dead.frame_range[1])+1):root.location=end_root;root.keyframe_insert('location',frame=f)
(P/'work/export_floor_correction.json').write_text(json.dumps({'sample_hz':bpy.context.scene.render.fps,'max_lifts_per_iteration_m':floor_changes},indent=2))
from staff_drop import bake_staff_drop
bake_staff_drop(rig,body,P)
from retime_acceleration import retime
retime(rig,P)
# Exact Walking stride in authored metres; run binding aliases this native gait.
a=bpy.data.actions['Walking'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];feet={s:[]for s in 'LR'}
for f in range(int(a.frame_range[1])+1):
 bpy.context.scene.frame_set(f)
 for s in feet:feet[s].append(rig.pose.bones[f'B_{s}_Foot'].head.y)
stride=float(np.mean([2*(max(v)-min(v))for v in feet.values()]));info={'stride_m':stride,'staff_roll_deg':roll,'clips':{a.name:(a.frame_range[1]-a.frame_range[0])/bpy.context.scene.render.fps for a in bpy.data.actions},'bones':len(rig.data.bones),'triangles':sum(len(f.vertices)-2 for f in body.data.polygons)}
rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];bpy.context.scene.frame_set(0);bpy.context.scene.render.fps=240
for o in bpy.data.objects:o.select_set(o in (body,rig))
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(P/'export/mm6_jak1_lod0.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,export_reset_pose_bones=True,export_anim_slide_to_zero=True)
for im in bpy.data.images:
 if im.source=='FILE' and im.has_data:im.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/runtime_master.blend'));(P/'export/export_info.json').write_text(json.dumps(info,indent=2));print('EXPORT',info,flush=True)
