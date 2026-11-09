"""Protected 10% reduction trials; paired eight-view silhouette/texture measurements at actual LOD sizes."""
import bpy,bmesh,json,math,sys,subprocess,os,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];W=P/'work/round2';R=P/'review/round2/reduction';R.mkdir(exist_ok=True);sys.path.insert(0,str(P/'scripts'));import common
def reset(part):
 bpy.ops.wm.open_mainfile(filepath=str(W/'unreduced.blend'));rig=bpy.data.objects['Rig'];rig.animation_data.action=None
 for pb in rig.pose.bones:pb.matrix_basis.identity()
 bpy.context.view_layer.update();ob=bpy.data.objects['Body' if part=='body' else 'BowAsset']
 if part!='body':
  bm=bmesh.new();bm.from_mesh(ob.data);layer=bm.faces.layers.int['bow_part'];bmesh.ops.delete(bm,geom=[f for f in bm.faces if (f[layer]>=3)!=(part=='arrow')],context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(ob.data);bm.free()
 return ob,rig
def reduce(ob,rig,part,level,ratio):
 original=sum(len(f.vertices)-2 for f in ob.data.polygons)
 if ratio==1:return original,{}
 ref=ob.copy();ref.data=ob.data.copy();ref.name='NormalReference';bpy.context.collection.objects.link(ref);ref.hide_render=True
 for m in list(ref.modifiers):ref.modifiers.remove(m)
 pieces=[x.value for x in ob.data.attributes['piece'].data] if part=='body' else []
 names=[g.name for g in ob.vertex_groups];importance=np.zeros(len(ob.data.vertices))
 for v in ob.data.vertices:
  weights={names[g.group]:g.weight for g in v.groups}
  if part=='body':
   if pieces[v.index] in [1,4]+list(range(13,20)):importance[v.index]=1
   if any(('Finger'in n or 'Hand'in n)and w>.01 for n,w in weights.items())or v.co.z<.025:importance[v.index]=1
   if v.co.z>1.45 and sum(w for n,w in weights.items()if n in ('B_Head','B_Neck'))>.2:importance[v.index]=1
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
  if w:vg.add([i],float(w if level==0 else w*.95),'REPLACE')
 bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
 m=ob.modifiers.new('Planar dissolve','DECIMATE');m.decimate_type='DISSOLVE';m.angle_limit=math.radians(.05);m.delimit={'NORMAL','MATERIAL','SEAM','UV'};bpy.ops.object.modifier_move_to_index(modifier=m.name,index=0);bpy.ops.object.modifier_apply(modifier=m.name)
 planar=sum(len(f.vertices)-2 for f in ob.data.polygons)
 m=ob.modifiers.new('Protected collapse','DECIMATE');m.ratio=min(1,original*ratio/planar);m.use_collapse_triangulate=True;m.vertex_group=vg.name;m.invert_vertex_group=True;m.vertex_group_factor=1000 if level==0 else float(os.environ.get("ARC1_LOD_PROTECT_FACTOR","5"))
 bpy.ops.object.modifier_move_to_index(modifier=m.name,index=0);bpy.ops.object.modifier_apply(modifier=m.name)
 m=ob.modifiers.new('Carry corner normals','DATA_TRANSFER');m.object=ref;m.use_loop_data=True;m.data_types_loops={'CUSTOM_NORMAL'};m.loop_mapping='POLYINTERP_NEAREST';m.use_object_transform=False;bpy.ops.object.modifier_move_to_index(modifier=m.name,index=0);bpy.ops.object.modifier_apply(modifier=m.name)
 bpy.data.objects.remove(ref,do_unlink=True);ob.vertex_groups.remove(ob.vertex_groups['_protect']);bpy.ops.object.vertex_group_limit_total(limit=8);bpy.ops.object.vertex_group_normalize_all(lock_active=False)
 # Collapse may extrapolate a border UV by less than one texel; keep it inside the atlas gutter.
 for layer in ob.data.uv_layers:
  for corner in layer.data:
   for axis in range(2):
    value=corner.uv[axis]
    if value<0 or value>1:
     assert -.001<=value<=1.001,(layer.name,value)
     corner.uv[axis]=min(1,max(0,value))
 return sum(len(f.vertices)-2 for f in ob.data.polygons),{'total_vertices':len(importance),'protected':int((importance>0).sum()),'face_hands_soles_contact':int((importance==1).sum()),'deformation_loops':int((importance==.98).sum()),'silhouette':int((importance==.85).sum())}
def render(ob,rig,part,level,tag,texture_root=None):
 sc=bpy.context.scene;common.workbench_clay(sc,True);sc.render.film_transparent=True;sc.display.shading.show_cavity=False;sc.display.shading.show_shadows=False;sc.display.render_aa='32';sc.render.image_settings.color_mode='RGBA';sc.view_settings.view_transform='Standard';sc.view_settings.look='None'
 resolution=[1024,768,384,192][level];pixels=[800,550,220,88][level];sc.render.resolution_x=sc.render.resolution_y=resolution;sc.render.resolution_percentage=100
 for obj in bpy.data.objects:
  if obj.type=='MESH':obj.hide_render=obj!=ob
 ob.data.materials.clear()
 labels=[('Archer_A','arc1_basecolor_1k.png'),('ArcherHead_A','arc1_head_basecolor_1k.png')] if part=='body' else [('Bow_A','bow/basecolor_1k.png')]
 for label,filename in labels:
  mat=bpy.data.materials.new(label);mat.use_nodes=True;nt=mat.node_tree;n=nt.nodes.new('ShaderNodeTexImage');n.image=bpy.data.images.load(str((texture_root or P/'textures')/filename),check_existing=True);nt.links.new(n.outputs['Color'],nt.nodes.get('Principled BSDF').inputs['Base Color']);nt.nodes.active=n;ob.data.materials.append(mat)
 if part=='body':
  uv=ob.data.uv_layers.new(name='MetricUV')
  for i,x in enumerate(ob.data.uv_layers['UVMap'].data):uv.data[i].uv=x.uv
  for f in ob.data.polygons:
   head=ob.data.attributes['head'].data[f.index].value;f.material_index=int(bool(head))
   if head:
    for i in f.loop_indices:uv.data[i].uv=ob.data.uv_layers['HeadUV'].data[i].uv
  ob.data.uv_layers.active=uv;uv.active_render=True
 else:
  for f in ob.data.polygons:f.material_index=0
 a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];sc.frame_set(0)
 if part=='arrow':
  rig.animation_data.action=None;rig.pose.bones['Arrow'].scale=(1,1,1);bpy.context.view_layer.update()
 cal=R/'camera.json';camera=json.loads(cal.read_text())if cal.exists()else{}
 lo,hi=common.world_bounds([ob])
 if part not in camera:
  bodylo,bodyhi=common.world_bounds([bpy.data.objects['Body']]);camera[part]={'center':list((lo+hi)/2),'body_diameter_m':(bodyhi-bodylo).length};cal.write_text(json.dumps(camera,indent=2))
 center=Vector(camera[part]['center']);scale=camera[part]['body_diameter_m']*resolution/pixels
 for i in range(8):
  angle=i*math.pi/4;d=Vector((math.sin(angle),-math.cos(angle),.05)).normalized();cam=common.ortho_camera('MetricCamera',center+d*6,(0,0,0),scale);cam.rotation_mode='QUATERNION';cam.rotation_quaternion=(-d).to_track_quat('-Z','Y');sc.camera=cam;sc.render.filepath=str(R/f'{tag}_{i}.png');bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)
def run():
 curve=[];selected={}
 for part in ['body','bow','arrow']:
  selected[part]={}
  for level in range(4):
   for step in range(0,30):
    ob,rig=reset(part);ratio=([1,.98,.95]+[.9**i for i in range(1,28)])[step];count,protection=reduce(ob,rig,part,level,ratio);tag=f'{part}_l{level}_s{step:02d}'
    bpy.ops.wm.save_as_mainfile(filepath=str(W/f'{tag}.blend'));render(ob,rig,part,level,tag)
    result=json.loads(subprocess.check_output(['/usr/bin/python3',str(P/'scripts/round2_reduction_metrics.py'),str(R),f'{part}_l{level}_s00',tag],text=True))
    row={'part':part,'lod':level,'step':step,'ratio':ratio,'triangles':count,'protected':protection,'projected_diameter_pixels':[800,550,220,88][level],**result,'blend':f'work/round2/{tag}.blend','rig_gates':'pending'if result['pass']else'visual_rejection'}
    curve.append(row);(R/'curve.json').write_text(json.dumps(curve,indent=2));print('REDUCTION',part,level,step,count,result['min_iou'],result['min_ssim'],result['pass'],flush=True)
    if not result['pass']:break
    selected[part][str(level)]=row
   (R/'selected.json').write_text(json.dumps(selected,indent=2))
if __name__=='__main__':run()
