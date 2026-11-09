"""Protected 10% reduction trials; paired eight-view silhouette/texture measurements at actual LOD sizes."""
import bpy,bmesh,json,math,sys,subprocess,numpy as np,runpy,os
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];W=P/'work/reduction';W.mkdir(exist_ok=True);R=P/'review/reduction';R.mkdir(exist_ok=True);sys.path.insert(0,str(P/'scripts'));import common
from rebake_candidate import rebake_preview
def reset(part):
 bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured.blend'));rig=bpy.data.objects['Rig'];rig.animation_data.action=None
 for pb in rig.pose.bones:pb.matrix_basis.identity()
 bpy.context.view_layer.update();return bpy.data.objects['Body' if part=='body' else 'StaffMesh'],rig
def reduce(ob,rig,part,level,ratio,preview=True):
 original=sum(len(f.vertices)-2 for f in ob.data.polygons)
 if ratio==1:return original,{}
 ref=ob.copy();ref.data=ob.data.copy();ref.name='NormalReference';bpy.context.collection.objects.link(ref);ref.hide_render=True
 for m in list(ref.modifiers):ref.modifiers.remove(m)
 names=[g.name for g in ob.vertex_groups];importance=np.zeros(len(ob.data.vertices))
 for v in ob.data.vertices:
  weights={names[g.group]:g.weight for g in v.groups}
  if part=='body':
   if abs(v.co.x)>.25 and v.co.z>1.0 and v.co.z<1.28:importance[v.index]=1
   if any(('Finger'in n or 'Hand'in n)and w>.01 for n,w in weights.items())or v.co.z<.025:importance[v.index]=1
   if v.co.z>1.46 and sum(w for n,w in weights.items()if n in ('B_Head','B_Neck'))>.2:importance[v.index]=[1,.97,.9,.8][level]
   if sum(w>.015 for w in weights.values())>1:importance[v.index]=max(importance[v.index],.7)
   for side in 'LR':
    for n in ['UpperArm','Forearm','Hand','Thigh','Calf']:
     if (v.co-rig.data.bones[f'B_{side}_{n}'].head_local).length<.06:importance[v.index]=max(importance[v.index],.98)
  else:
   local=rig.data.bones['Staff'].matrix_local.inverted()@v.co
   if abs(local.y)<.085:importance[v.index]=1
 bm=bmesh.new();bm.from_mesh(ob.data);bm.normal_update()
 for edge in bm.edges:
  if len(edge.link_faces)!=2 or any((edge.link_faces[0].normal.dot(Vector((math.sin(a),math.cos(a),0)))>=0)!=(edge.link_faces[1].normal.dot(Vector((math.sin(a),math.cos(a),0)))>=0)for a in np.arange(8)*math.pi/4):
   for v in edge.verts:importance[v.index]=max(importance[v.index],1. if len(edge.link_faces)!=2 else .999)
 if level>0:
  importance*=.96 if level==1 else .9 if level==2 else .8
  if part=='body':
   for edge in bm.edges:
    if len(edge.link_faces)!=2:
     for v in edge.verts:importance[v.index]=.999
 if level>0 and part=='body':
  pieces=[x.value for x in ob.data.attributes['piece'].data]
  for v in ob.data.vertices:
   if pieces[v.index] in [3,10,11] or (pieces[v.index]==0 and abs(v.co.x)>.25 and 1.0<v.co.z<1.28) or any(names[g.group].startswith('B_R_') and ('Finger' in names[g.group] or 'Hand' in names[g.group]) and g.weight>.01 for g in v.groups):importance[v.index]=1
 bm.free();vg=ob.vertex_groups.new(name='_protect')
 for i,w in enumerate(importance):
  if w:vg.add([i],float(w),'REPLACE')
 bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
 m=ob.modifiers.new('Planar dissolve','DECIMATE');m.decimate_type='DISSOLVE';m.angle_limit=math.radians(.05);m.delimit={'NORMAL','MATERIAL','SEAM','UV'};bpy.ops.object.modifier_move_to_index(modifier=m.name,index=0);bpy.ops.object.modifier_apply(modifier=m.name)
 planar=sum(len(f.vertices)-2 for f in ob.data.polygons)
 m=ob.modifiers.new('Protected collapse','DECIMATE');m.ratio=min(1,original*ratio/planar);m.use_collapse_triangulate=True;m.vertex_group=vg.name;m.invert_vertex_group=True;m.vertex_group_factor=1000 if level==0 else 10
 bpy.ops.object.modifier_move_to_index(modifier=m.name,index=0);bpy.ops.object.modifier_apply(modifier=m.name)
 m=ob.modifiers.new('Carry corner normals','DATA_TRANSFER');m.object=ref;m.use_loop_data=True;m.data_types_loops={'CUSTOM_NORMAL'};m.loop_mapping='POLYINTERP_NEAREST';m.use_object_transform=False;bpy.ops.object.modifier_move_to_index(modifier=m.name,index=0);bpy.ops.object.modifier_apply(modifier=m.name)
 if preview:rebake_preview(ob,ref,R,f'{part}_l{level}_r{ratio:.5f}')
 bpy.data.objects.remove(ref,do_unlink=True);ob.vertex_groups.remove(ob.vertex_groups['_protect']);bpy.ops.object.vertex_group_limit_total(limit=8);bpy.ops.object.vertex_group_normalize_all(lock_active=False)
 return sum(len(f.vertices)-2 for f in ob.data.polygons),{'total_vertices':len(importance),'protected':int((importance>0).sum()),'face_hands_soles_contact':int((importance==1).sum()),'deformation_loops':int((importance==.98).sum()),'silhouette':int((importance==.85).sum())}
def render(ob,rig,part,level,tag):
 sc=bpy.context.scene;common.workbench_clay(sc,True);sc.render.film_transparent=True;sc.display.shading.light='FLAT';sc.display.shading.show_specular_highlight=False;sc.display.shading.show_cavity=False;sc.display.shading.show_shadows=False;sc.display.render_aa='32';sc.render.image_settings.color_mode='RGBA';sc.view_settings.view_transform='Standard';sc.view_settings.look='None'
 resolution=[1024,768,384,192][level];pixels=[700,550,220,88][level];sc.render.resolution_x=sc.render.resolution_y=resolution;sc.render.resolution_percentage=100
 for obj in bpy.data.objects:
  if obj.type=='MESH':obj.hide_render=obj!=ob
 ob.data.uv_layers.active=ob.data.uv_layers['MergedUV'] if part=='body' else ob.data.uv_layers[0]
 a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];sc.frame_set(0)
 cal=R/'camera.json';camera=json.loads(cal.read_text())if cal.exists()else{}
 lo,hi=common.world_bounds([ob])
 if part not in camera:
  bodylo,bodyhi=common.world_bounds([bpy.data.objects['Body']]);camera[part]={'center':list((lo+hi)/2),'body_diameter_m':bodyhi.z-bodylo.z};cal.write_text(json.dumps(camera,indent=2))
 center=Vector(camera[part]['center']);scale=camera[part]['body_diameter_m']*resolution/pixels
 for i in range(8):
  angle=i*math.pi/4;d=Vector((math.sin(angle),-math.cos(angle),.05)).normalized();cam=common.ortho_camera('MetricCamera',center+d*6,(0,0,0),scale);cam.rotation_mode='QUATERNION';cam.rotation_quaternion=(-d).to_track_quat('-Z','Y');sc.camera=cam;sc.render.filepath=str(R/f'{tag}_{i}.png');bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)
def run():
 curve=[];selected={}
 def trial(part,level,step,ratio):
  ob,rig=reset(part);count,protection=reduce(ob,rig,part,level,ratio);tag=f'{part}_l{level}_s{step:02d}'
  bpy.ops.wm.save_as_mainfile(filepath=str(W/f'{tag}.blend'));render(ob,rig,part,level,tag)
  result=json.loads(subprocess.check_output(['/usr/bin/python3',str(P/'scripts/reduction_metrics.py'),str(R),f'{part}_l{level}_s00',tag],text=True))
  row={'part':part,'lod':level,'step':step,'ratio':ratio,'triangles':count,'protected':protection,'actor_height_pixels':[700,550,220,88][level],**result,'blend':f'work/reduction/{tag}.blend','rig_gates':'pending_final_contacts'}
  curve.append(row)
  if result['pass'] and part=='body' and ratio<1:
   os.environ['GATE_BLEND']=row['blend'];os.environ['GATE_REPORT']=f'review/reduction/{tag}_dense.json';os.environ['CLOTH_REPORT']=f'review/reduction/{tag}_cloth.json'
   runpy.run_path(str(P/'scripts/dense_gates.py'),run_name='__main__');runpy.run_path(str(P/'scripts/cloth_surface_gate.py'),run_name='__main__')
   dense=json.loads((P/os.environ['GATE_REPORT']).read_text());cloth=json.loads((P/os.environ['CLOTH_REPORT']).read_text())['clips']
   passed=all(all(a[k] for k in ['G4_pass','G5_pass','elbow_pass','roll_pass']) for a in dense.values()) and all(a['pass'] for a in cloth.values())
   row['rig_gates']='dense_and_cloth_pass_contact_pending' if passed else 'rejected';row['pass']=passed
  if part=='staff' and level==0 and count<1100:row['pass']=False;row['rig_gates']='prop_detail_budget_floor'
  (R/'curve.json').write_text(json.dumps(curve,indent=2));print('REDUCTION',part,level,step,count,row['min_iou'],row['min_ssim'],row['pass'],flush=True)
  return row
 for part in ['body','staff']:
  selected[part]={}
  for level in range(4):
   chosen=trial(part,level,0,1.);step=1
   for ratio in [.8**i for i in range(1,12)]:
    row=trial(part,level,step,ratio);step+=1
    if row['pass']:chosen=row;continue
    failed=ratio;passed=chosen['ratio']
    for _ in range(3):
     mid=(failed+passed)/2;row=trial(part,level,step,mid);step+=1
     if row['pass']:chosen=row;passed=mid
     else:failed=mid
    break
   selected[part][str(level)]=chosen;(R/'selected.json').write_text(json.dumps(selected,indent=2))
if __name__=='__main__':run()
