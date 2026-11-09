"""Protected reduction curve with eight-view image checks and the existing 48 Hz rig gates."""
import bpy,bmesh,json,math,sys,subprocess,runpy
import numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];W=P/'work/round3_reduction';R=P/'review/reduction';W.mkdir(exist_ok=True);R.mkdir(exist_ok=True)
sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'));import common
from round3_candidate_gates import check
def keep(ob,part,complement=False):
 bm=bmesh.new();bm.from_mesh(ob.data);layer=bm.verts.layers.int['piece']
 remove=[f for f in bm.faces if ((all(v[layer]==201 for v in f.verts)) != (part=='bow')) != complement]
 bmesh.ops.delete(bm,geom=remove,context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(ob.data);bm.free()
def reset(part):
 bpy.ops.wm.open_mainfile(filepath=str(P/'work/round3_unreduced.blend'));rig=bpy.data.objects['Rig'];rig.animation_data.action=None
 for pb in rig.pose.bones:pb.matrix_basis.identity()
 bpy.context.view_layer.update();ob=bpy.data.objects['Body'];other=ob.copy();other.data=ob.data.copy();other.name='Complement';bpy.context.collection.objects.link(other);keep(ob,part);keep(other,part,True)
 return ob,other,rig
def reduce(ob,rig,part,level,ratio):
 original=sum(len(f.vertices)-2 for f in ob.data.polygons)
 if ratio==1:return original,{}
 ref=ob.copy();ref.data=ob.data.copy();ref.name='NormalReference';bpy.context.collection.objects.link(ref);ref.hide_render=True
 for m in list(ref.modifiers):ref.modifiers.remove(m)
 names=[g.name for g in ob.vertex_groups];importance=np.zeros(len(ob.data.vertices));pieces=[x.value for x in ob.data.attributes['piece'].data]
 for v in ob.data.vertices:
  weights={names[g.group]:g.weight for g in v.groups}
  if part=='body':
   if pieces[v.index]>=202:importance[v.index]=1
   if any(('Finger'in n or 'Hand'in n)and w>.01 for n,w in weights.items())or v.co.z<.025:importance[v.index]=1
   if v.co.z>1.43 and sum(w for n,w in weights.items()if n in ('B_Head','B_Neck'))>.2:importance[v.index]=1
   if sum(w>.015 for w in weights.values())>1:importance[v.index]=max(importance[v.index],.7)
   for side in 'LR':
    for n in ['UpperArm','Forearm','Hand','Thigh','Calf']:
     if (v.co-rig.data.bones[f'B_{side}_{n}'].head_local).length<.06:importance[v.index]=max(importance[v.index],.98)
  else:
   local=rig.data.bones['Bow' if part=='bow' else 'Arrow'].matrix_local.inverted()@v.co
   if part=='bow' and abs(local.z)<.085:importance[v.index]=1
 bm=bmesh.new();bm.from_mesh(ob.data);bm.normal_update()
 for edge in bm.edges:
  if len(edge.link_faces)!=2 or any((edge.link_faces[0].normal.dot(Vector((math.sin(a),math.cos(a),0)))>=0)!=(edge.link_faces[1].normal.dot(Vector((math.sin(a),math.cos(a),0)))>=0)for a in np.arange(8)*math.pi/4):
   for v in edge.verts:importance[v.index]=max(importance[v.index],.999)
 bm.free();vg=ob.vertex_groups.new(name='_protect')
 for i,w in enumerate(importance):
  if w:vg.add([i],float(w),'REPLACE')
 bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
 m=ob.modifiers.new('Planar dissolve','DECIMATE');m.decimate_type='DISSOLVE';m.angle_limit=math.radians(.05);m.delimit={'NORMAL','MATERIAL','SEAM','UV'};bpy.ops.object.modifier_move_to_index(modifier=m.name,index=0);bpy.ops.object.modifier_apply(modifier=m.name)
 planar=sum(len(f.vertices)-2 for f in ob.data.polygons)
 m=ob.modifiers.new('Protected collapse','DECIMATE');m.ratio=min(1,original*ratio/planar);m.use_collapse_triangulate=True;m.vertex_group=vg.name;m.invert_vertex_group=True;m.vertex_group_factor=1000
 bpy.ops.object.modifier_move_to_index(modifier=m.name,index=0);bpy.ops.object.modifier_apply(modifier=m.name)
 m=ob.modifiers.new('Carry corner normals','DATA_TRANSFER');m.object=ref;m.use_loop_data=True;m.data_types_loops={'CUSTOM_NORMAL'};m.loop_mapping='POLYINTERP_NEAREST';m.use_object_transform=False;bpy.ops.object.modifier_move_to_index(modifier=m.name,index=0);bpy.ops.object.modifier_apply(modifier=m.name)
 bpy.data.objects.remove(ref,do_unlink=True);ob.vertex_groups.remove(ob.vertex_groups['_protect']);bpy.ops.object.vertex_group_limit_total(limit=8);bpy.ops.object.vertex_group_normalize_all(lock_active=False)
 return sum(len(f.vertices)-2 for f in ob.data.polygons),{'total_vertices':len(importance),'protected':int((importance>0).sum()),'face_hands_soles_contact':int((importance==1).sum()),'deformation_loops':int((importance==.98).sum()),'silhouette':int((importance==.999).sum())}
def render(ob,rig,part,level,tag):
 sc=bpy.context.scene;common.workbench_clay(sc,True);sc.render.film_transparent=True;sc.display.shading.show_cavity=False;sc.display.shading.show_shadows=False;sc.display.render_aa='32';sc.render.image_settings.color_mode='RGBA';sc.view_settings.view_transform='Standard';sc.view_settings.look='None'
 resolution=[1024,768,384,192][level];pixels=[800,550,220,88][level];sc.render.resolution_x=sc.render.resolution_y=resolution;sc.render.resolution_percentage=100
 for obj in bpy.data.objects:
  if obj.type=='MESH':obj.hide_render=obj!=ob
 a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];sc.frame_set(0)
 cal=R/'camera.json';camera=json.loads(cal.read_text())if cal.exists()else{}
 lo,hi=common.world_bounds([ob])
 if part not in camera:
  bodylo,bodyhi=common.world_bounds([bpy.data.objects['Body'],bpy.data.objects['Complement']]);camera[part]={'center':list((lo+hi)/2),'body_diameter_m':(bodyhi-bodylo).length};cal.write_text(json.dumps(camera,indent=2))
 center=Vector(camera[part]['center']);scale=camera[part]['body_diameter_m']*resolution/pixels
 for i in range(8):
  angle=i*math.pi/4;d=Vector((math.sin(angle),-math.cos(angle),.05)).normalized();cam=common.ortho_camera('MetricCamera',center+d*6,(0,0,0),scale);cam.rotation_mode='QUATERNION';cam.rotation_quaternion=(-d).to_track_quat('-Z','Y');sc.camera=cam;sc.render.filepath=str(R/f'{tag}_{i}.png');bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)
def run():
 curve=[];selected={};gatecache={}
 for part in ['body','bow']:
  selected[part]={}
  for level in range(4):
   for step in range(0,28):
    ob,other,rig=reset(part);ratio=.9**step;count,protection=reduce(ob,rig,part,level,ratio);tag=f'{part}_l{level}_s{step:02d}';render(ob,rig,part,level,tag)
    result=json.loads(subprocess.check_output(['/usr/bin/python3',str(P/'scripts/round3_reduction_metrics.py'),str(R),f'{part}_l{level}_s00',tag],text=True))
    # Rejoin the complementary unchanged component before every complete geometry gate.
    bpy.ops.object.select_all(action='DESELECT')
    for o in [ob,other]:o.hide_render=False;o.select_set(True)
    bpy.context.view_layer.objects.active=ob;bpy.ops.object.join();ob.name='Body'
    rig.animation_data.action=None
    for b in rig.pose.bones:b.matrix_basis.identity()
    key=f'{part}_s{step:02d}';path=W/f'{key}.blend'
    if not path.exists():bpy.ops.wm.save_as_mainfile(filepath=str(path))
    gates=None
    if result['pass']:
     if key not in gatecache:
      receipt=R/f'{key}_gates.json'
      if receipt.exists():gatecache[key]=json.loads(receipt.read_text())
      else:gatecache[key]=check(path);receipt.write_text(json.dumps(gatecache[key],indent=2))
     gates=gatecache[key]
    passed=result['pass'] and gates is not None and gates['passed']
    row={'part':part,'lod':level,'step':step,'ratio':ratio,'triangles':count,'protected':protection,'projected_diameter_pixels':[800,550,220,88][level],**result,'visual_pass':result['pass'],'pass':passed,'blend':str(path.relative_to(P)),'rig_gates':str((R/f'{key}_gates.json').relative_to(P)) if gates else 'not_run_visual_rejection'}
    curve.append(row);(R/'curve.json').write_text(json.dumps(curve,indent=2));print('REDUCTION',part,level,step,count,result['min_iou'],result['min_ssim'],passed,flush=True)
    if step==0:assert passed,(part,level,gates)
    if not passed:break
    selected[part][str(level)]=row
   (R/'selected.json').write_text(json.dumps(selected,indent=2))
if __name__=='__main__':run()
