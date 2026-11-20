import bpy,json,math,numpy as np,sys,os
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import rebake_final,final_refinements;from refit_lower_coat import refit;sel=json.loads((p/'review/reduction/selected.json').read_text());out=p/'export';out.mkdir(exist_ok=True);roles=['Standing','Walking','Running','Attack','Cast','Hit','Death','Dead','Fidget'];info={'clips':{},'lods':[]};staffinfo=json.loads((p/'work/staff_geometry.json').read_text())
def act(r,a):r.animation_data_create();r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
def neutral(r):
 r.animation_data.action=None
 for pb in r.pose.bones:pb.matrix_basis.identity()
 bpy.context.view_layer.update()
for level in range(4):
 bpy.ops.wm.open_mainfile(filepath=str(p/sel['body'][str(level)]['blend']));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];sc=bpy.context.scene;neutral(r)
 bpy.data.objects.remove(bpy.data.objects['StaffMesh'],do_unlink=True)
 with bpy.data.libraries.load(str(p/sel['staff'][str(level)]['blend']),link=False) as (src,dst):dst.meshes=[n for n in src.meshes if n.startswith('StaffMesh')][:1]
 assert len(dst.meshes)==1;me=dst.meshes[0];staff=bpy.data.objects.new('StaffMesh',me);bpy.context.collection.objects.link(staff);staff.parent=r;mod=staff.modifiers.new('Armature','ARMATURE');mod.object=r;staff.vertex_groups.new(name='Staff').add(list(range(len(me.vertices))),1.,'REPLACE');me.materials.clear();me.materials.append(bpy.data.materials['MepStaff_A']);me.attributes.new('piece','INT','POINT').data.foreach_set('value',[100]*len(me.vertices))
 if 'MergedUV' not in me.uv_layers:me.uv_layers.active.name='MergedUV'
 if level>=2:refit(b)
 rebake_final.bake(b,'Body',level);rebake_final.bake(staff,'StaffMesh',level)
 for obj in bpy.data.objects:obj.select_set(obj in [b,staff])
 bpy.context.view_layer.objects.active=b;bpy.ops.object.join();bpy.ops.object.vertex_group_limit_total(limit=8);bpy.ops.object.vertex_group_normalize_all(lock_active=False)
 deviations=[]
 for v in b.data.vertices:
  groups=[(g.group,g.weight) for g in v.groups if b.vertex_groups[g.group].name in r.data.bones and g.weight>0]
  total=sum(w for _,w in groups);assert total>0,('unweighted',v.index,list(v.co))
  deviations.append(abs(total-1))
  for g in list(v.groups):b.vertex_groups[g.group].remove([v.index])
  for gi,w in groups:b.vertex_groups[gi].add([v.index],w/total,'REPLACE')
 print('NORMALIZE',level,max(deviations),flush=True)
 assert all(abs(sum(g.weight for g in v.groups)-1)<1e-5 for v in b.data.vertices)
 for a in list(bpy.data.actions):
  if a.name not in roles:bpy.data.actions.remove(a)
 final_refinements.apply(r,b)
 # Tiny post-skin fall clearance is corrected by the pelvis, not by scaling limbs.
 death=bpy.data.actions['Death'];act(r,death);values=[];pv=np.array([x.value for x in b.data.attributes['piece'].data])
 for f in np.arange(0,float(death.frame_range[1])+.01,.5):
  sc.frame_set(int(f),subframe=f%1);ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();low=min(v.co.z for v in m.vertices if pv[v.index]!=100);ev.to_mesh_clear();saved_staff=r.pose.bones['Staff'].matrix.copy();pelvis=r.pose.bones['B_Pelvis'];M=pelvis.matrix.copy();M.translation.z+=.002-low;pelvis.matrix=M;bpy.context.view_layer.update()
  if f>=final_refinements.RELEASE:r.pose.bones['Staff'].matrix=saved_staff;bpy.context.view_layer.update()
  ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();staff_low=min(v.co.z for v in m.vertices if pv[v.index]==100);ev.to_mesh_clear()
  if f>=final_refinements.RELEASE and staff_low<.004:
   M=r.pose.bones['Staff'].matrix.copy();M.translation.z+=.004-staff_low;r.pose.bones['Staff'].matrix=M;bpy.context.view_layer.update()
  values.append((float(f),pelvis.location.copy(),r.pose.bones['Staff'].location.copy(),r.pose.bones['Staff'].rotation_quaternion.copy()))
 for f,loc,sloc,sq in values:
  pb=r.pose.bones['B_Pelvis'];pb.location=loc;pb.keyframe_insert('location',frame=f);pb=r.pose.bones['Staff'];pb.location=sloc;pb.rotation_quaternion=sq;pb.keyframe_insert('location',frame=f);pb.keyframe_insert('rotation_quaternion',frame=f)
 sc.frame_set(int(death.frame_range[1]));held={pb.name:(pb.rotation_quaternion.copy(),pb.location.copy()) for pb in r.pose.bones};bpy.data.actions.remove(bpy.data.actions['Dead']);dead=bpy.data.actions.new('Dead');dead.use_fake_user=True;r.animation_data.action=dead
 for f in [0,30]:
  for n,(q,l) in held.items():
   pb=r.pose.bones[n];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.location=l;pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('location',frame=f)
 dead.use_frame_range=True;dead.frame_start=0;dead.frame_end=30
 for a in bpy.data.actions:
  for layer in a.layers:
   for strip in layer.strips:
    for cb in strip.channelbags:
     groups={}
     for fc in cb.fcurves:
      for k in fc.keyframe_points:k.interpolation='LINEAR'
      if fc.data_path.endswith('rotation_quaternion'):groups.setdefault(fc.data_path,{})[fc.array_index]=fc
     for curves in groups.values():
      keys=[curves[i].keyframe_points for i in range(4)];previous=None
      for j in range(len(keys[0])):
       q=np.array([keys[i][j].co.y for i in range(4)]);q/=np.linalg.norm(q)
       if previous is not None and q@previous<0:q=-q
       for i in range(4):keys[i][j].co.y=float(q[i])
       previous=q
 if level>0:
  neutral(r)
  for action in list(bpy.data.actions):bpy.data.actions.remove(action)
  with bpy.data.libraries.load(str(out/'mm6_mep.blend'),link=False) as (source,target):target.actions=list(source.actions)
  assert {a.name for a in bpy.data.actions}==set(roles)
  for action in bpy.data.actions:action.use_fake_user=True
 neutral(r);bpy.ops.wm.save_as_mainfile(filepath=str(p/f'work/final_lod{level}.blend'));b.name=b.data.name='Mep';info['lods'].append({'level':level,'total_triangles':sum(len(f.vertices)-2 for f in b.data.polygons),'body_triangles':sel['body'][str(level)]['triangles'],'staff_triangles':sel['staff'][str(level)]['triangles']})
 if level==0:
  info['bones']=len(r.data.bones)
  for role in roles:
   a=bpy.data.actions[role];act(r,a);end=float(a.frame_range[1]);bounds=[];samples=[]
   for t in sorted(set(list(np.arange(0,end/30+.00001,1/48))+[end/30])):
    f=t*30;sc.frame_set(int(f),subframe=f%1);ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();P=np.array([v.co[:] for v in m.vertices]);ev.to_mesh_clear();bounds.append([P.min(0),P.max(0)]);M=r.pose.bones['Staff'].matrix;samples.append([t,list(M@Vector((0,staffinfo['bottom'],0))),list(M@Vector((0,staffinfo['top'],0))),list(M.translation)])
   entry={'duration':end/30,'mode':'loop' if role in ['Standing','Walking','Running','Dead'] else 'once','bounds':np.array(bounds)[:,0].min(0).tolist()+np.array(bounds)[:,1].max(0).tolist()}
   if role in ['Attack','Cast']:
    ts=np.array([s[0] for s in samples]);tip=np.array([s[1 if role=='Attack' else 2] for s in samples]);hand=np.array([s[3] for s in samples]);velocity=np.diff(tip,axis=0)/np.diff(ts)[:,None];direction=tip[1:]-hand[1:];eligible=(direction[:,1]<-.03)&(velocity[:,1]<0)&(ts[1:]>.24);speed=np.linalg.norm(velocity,axis=1);assert eligible.any(),role;ix=int(np.argmax(np.where(eligible,speed,-1)))+1;entry.update(impact=round(float(ts[ix]),6),tip_speed_mps=float(speed[ix-1]),forward_velocity_mps=float(-velocity[ix-1,1]));(p/f'review/{role.lower()}_tip_samples.json').write_text(json.dumps(samples))
   info['clips'][role]=entry
   if role=='Standing':info['standing_height_m']=float(max(x[1][2]-x[0][2] for x in bounds))
  neutral(r);bpy.ops.wm.save_as_mainfile(filepath=str(out/'mm6_mep.blend'))
 # glTF uses a single material-specific coordinate set, including the dedicated head layout.
 b.data.uv_layers.active=b.data.uv_layers['MergedUV'];b.data.uv_layers['MergedUV'].active_render=True
 for uv in list(b.data.uv_layers):
  if uv.name!='MergedUV':b.data.uv_layers.remove(uv)
 b.data.uv_layers.active.name='UVMap'
 if level==0:
  for a in bpy.data.actions:
   start,end=map(float,a.frame_range)
   for layer in a.layers:
    for strip in layer.strips:
     for cb in strip.channelbags:
      for fc in cb.fcurves:
       for key in fc.keyframe_points:key.co.x*=8;key.handle_left.x*=8;key.handle_right.x*=8
       fc.update()
   a.frame_start=start*8;a.frame_end=end*8
  sc.render.fps=240
 neutral(r)
 for o in bpy.data.objects:o.select_set(o in [r,b])
 bpy.context.view_layer.objects.active=r
 bpy.ops.export_scene.gltf(filepath=str(out/f'mm6_mep_raw_lod{level}.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=level==0,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,export_reset_pose_bones=True,export_anim_slide_to_zero=True)
 print('EXPORTED_LOD',level,info['lods'][-1],flush=True)
(out/'export_info.json').write_text(json.dumps(info,indent=2));print('EXPORT_INFO',json.dumps(info),flush=True)
