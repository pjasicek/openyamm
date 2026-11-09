import bpy,bmesh,json,math,sys,subprocess,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];W=P/'work/reduction_props';R=P/'review/reduction_props';W.mkdir(exist_ok=True);R.mkdir(exist_ok=True);sys.path.insert(0,str(P/'scripts'));sys.dont_write_bytecode=True
import common
from rebake_maps import bake,TAGS
from fit_surface import fit
ROLES=['Standing','Walking','Running','Attack','Cast','Hit','Death','Dead','Fidget']
def reset(part):
 bpy.ops.wm.open_mainfile(filepath=str(P/'work/accepted_master.blend'));rig=bpy.data.objects['Rig'];rig.animation_data.action=None
 for pb in rig.pose.bones:pb.matrix_basis.identity()
 bpy.context.view_layer.update()
 for ob in [bpy.data.objects[n]for n in ['Body','ForearmBlade','LeafShield']]:
  for mat in ob.data.materials:
   name=mat.name.split('.')[0]
   if mat.name!=name:
    old=bpy.data.materials.get(name)
    if old:old.name=name+'_Unused'
    mat.name=name
 return bpy.data.objects[part],rig
def count(ob):return sum(len(f.vertices)-2 for f in ob.data.polygons)
def reduce(ob,rig,level,ratio,tag):
 original=count(ob);ref=ob.copy();ref.data=ob.data.copy();ref.name='BakeReference';bpy.context.collection.objects.link(ref);ref.hide_render=True
 for m in list(ref.modifiers):ref.modifiers.remove(m)
 parts=[a.value for a in ob.data.attributes['piece'].data]if 'piece'in ob.data.attributes else [0]*len(ob.data.vertices);names=[g.name for g in ob.vertex_groups];importance=np.zeros(len(ob.data.vertices));body=ob.name=='Body'
 for v in ob.data.vertices:
  weights={names[g.group]:g.weight for g in v.groups}
  if body:
   if any(('Finger'in n or 'Hand'in n)and w>.05 for n,w in weights.items()):importance[v.index]=[1,.5,.25,.08][level]
   if v.co.z<.025:importance[v.index]=[.4,.3,.15,.05][level]
   if v.co.z>1.4:importance[v.index]=([1,.55,.25,.1]if parts[v.index]==0 else [.3,.2,.1,.05])[level]
   if parts[v.index]in [4,6,7,8,9,10,11,12,13,14,15]:importance[v.index]=[1,.6,.25,.1][level]
   if sum(w>.015 for w in weights.values())>1:importance[v.index]=max(importance[v.index],[.15,.1,.07,.03][level])
   for side in 'LR':
    for n in ['UpperArm','Forearm','Hand','Thigh','Calf']:
     if (v.co-rig.data.bones[f'B_{side}_{n}'].head_local).length<.05:importance[v.index]=max(importance[v.index],[.4,.3,.15,.05][level])
  else:
   local=rig.data.bones[ob.name].matrix_local.inverted()@v.co
   if (ob.name=='LeafShield'and abs(local.x)<.085 and abs(local.z-.26)<.025)or(ob.name=='ForearmBlade'and local.z<.19):importance[v.index]=[.4,.3,.2,.1][level]
   if ob.name=='ForearmBlade'and local.z>.19:importance[v.index]=[.99,.8,.6,.3][level]
 bm=bmesh.new();bm.from_mesh(ob.data);bm.normal_update()
 for edge in bm.edges:
  border=len(edge.link_faces)!=2;sil=border or any((edge.link_faces[0].normal.dot(Vector((math.sin(a),math.cos(a),0)))>=0)!=(edge.link_faces[1].normal.dot(Vector((math.sin(a),math.cos(a),0)))>=0)for a in np.arange(8)*math.pi/4)
  if sil:
   for v in edge.verts:importance[v.index]=max(importance[v.index],[.6,.4,.2,.08][level])
 bm.free();vg=ob.vertex_groups.new(name='_protect')
 for i,w in enumerate(importance):
  if w:vg.add([i],float(w),'REPLACE')
 def collapse(obj,rr):
  bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
  m=obj.modifiers.new('Planar dissolve','DECIMATE');m.decimate_type='DISSOLVE';m.angle_limit=math.radians(.05);m.delimit={'MATERIAL','SEAM','UV'};bpy.ops.object.modifier_move_to_index(modifier=m.name,index=0);bpy.ops.object.modifier_apply(modifier=m.name)
  m=obj.modifiers.new('Protected collapse','DECIMATE');m.ratio=rr;m.use_collapse_triangulate=True;m.vertex_group='_protect';m.invert_vertex_group=True;m.vertex_group_factor=1
  bpy.ops.object.modifier_move_to_index(modifier=m.name,index=0);bpy.ops.object.modifier_apply(modifier=m.name)
 if body:
  segments=[]
  for part in sorted(set(parts)):
   pts=np.array([tuple(v.co)for v in ob.data.vertices if parts[v.index]==part])
   if level==3 and part>=16 and np.ptp(pts,axis=0).max()<.05:continue
   seg=ob.copy();seg.data=ob.data.copy();seg.name=f'Segment{part}';bpy.context.collection.objects.link(seg);bm=bmesh.new();bm.from_mesh(seg.data);layer=bm.verts.layers.int['piece'];bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[layer]!=part],context='VERTS');bm.to_mesh(seg.data);bm.free()
   rr=ratio
   if part==0:rr=min(1,ratio*1.25)
   elif part==1:rr=ratio*.55
   elif part in [3,5]:rr=ratio*.85
   elif part in [4,6,7,8,9,10,11,12,13,14,15]:rr=max(ratio,[.9,.4,.15,.05][level])
   rr=max(min(1,rr),min(1,4/max(count(seg),1)));collapse(seg,rr);segments.append(seg)
  bpy.ops.object.select_all(action='DESELECT')
  for seg in segments:seg.select_set(True)
  bpy.context.view_layer.objects.active=segments[0];bpy.ops.object.join();merged=segments[0];ob.data=merged.data.copy();bpy.data.objects.remove(merged,do_unlink=True)
 else:collapse(ob,ratio)
 bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob;ob.vertex_groups.remove(ob.vertex_groups['_protect'])
 if body:fit(ob,ref,level)
 m=ob.modifiers.new('Transferred corner normals','DATA_TRANSFER');m.object=ref;m.use_loop_data=True;m.data_types_loops={'CUSTOM_NORMAL'};m.loop_mapping='POLYINTERP_NEAREST';m.use_object_transform=False;bpy.ops.object.modifier_move_to_index(modifier=m.name,index=0);bpy.ops.object.modifier_apply(modifier=m.name)
 bpy.ops.object.vertex_group_limit_total(limit=8);bpy.ops.object.vertex_group_normalize_all(lock_active=False)
 for uv in list(ob.data.uv_layers):
  if uv.name!='UVMap':ob.data.uv_layers.remove(uv)
 # Save exact topology before baking; all maps are generated from the original surface, including its normal detail.
 maps=bake(ob,ref,R,tag,size=[1024,1024,512,256][level]);bpy.data.objects.remove(ref,do_unlink=True)
 return count(ob),maps,{'vertices':len(importance),'high_priority':int((importance>=.9).sum())}
def preview(ob,maps,variant):
 ramps=json.loads((P/'textures/natf_ramps.json').read_text());byname={d['base']:d for d in ramps['materials']}
 for mat,row in zip(ob.data.materials,maps):
  nt=mat.node_tree;bs=nt.nodes.get('Principled BSDF');base=bpy.data.images.load(str(P/row['maps']['basecolor']),check_existing=True);tex=bs.inputs['Base Color'].links[0].from_node
  if row['name']not in byname:nt.nodes.active=tex;continue
  spec=byname[row['name']];mask=bpy.data.images.load(str(P/row['maps']['region_mask']),check_existing=True);mask.colorspace_settings.name='Non-Color';mask.alpha_mode='CHANNEL_PACKED';N=base.size[0];a=np.empty(N*N*4,np.float32);b=a.copy();base.pixels.foreach_get(a);mask.pixels.foreach_get(b);a=a.reshape(-1,4);b=b.reshape(-1,4);rgb=a[:,:3].copy();lum=rgb@np.array([.2126,.7152,.0722]);weights=b[:,:len(spec['ramps'][variant])];total=weights.sum(1);out=rgb.copy()
  for i,r in enumerate(spec['ramps'][variant]):
   t=np.clip((lum-r['range'][0])/(r['range'][1]-r['range'][0]),0,1)*15;k=np.minimum(t.astype(int),14);f=t-k;c=np.array(r['colors']);mapped=c[k]*(1-f[:,None])+c[k+1]*f[:,None];out=out*(1-weights[:,i,None])+mapped*weights[:,i,None]
  a[:,:3]=out;a[:,3]=1;im=bpy.data.images.new(f'preview_{row["name"]}_{variant}',width=N,height=N,alpha=False);im.pixels.foreach_set(a.ravel());node=nt.nodes.new('ShaderNodeTexImage');node.image=im;nt.nodes.active=node
  # Only the active Workbench image changes; runtime shader inputs remain on the rebaked base.
def render(ob,rig,level,tag,maps,whole=False):
 sc=bpy.context.scene;common.workbench_clay(sc,True);sc.render.film_transparent=True;sc.display.shading.light='STUDIO';sc.display.shading.show_specular_highlight=False;sc.display.shading.show_cavity=False;sc.display.shading.show_shadows=False;sc.display.render_aa='32';sc.render.image_settings.color_mode='RGBA';sc.view_settings.view_transform='Standard';sc.view_settings.look='None'
 resolution=[960,768,384,192][level];pixels=[700,550,220,88][level];sc.render.resolution_x=sc.render.resolution_y=resolution;sc.render.resolution_percentage=100
 for o in bpy.data.objects:
  if o.type=='MESH':o.hide_render=(not whole and o!=ob)
 a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];sc.frame_set(0);cal=R/'camera.json';camera=json.loads(cal.read_text())if cal.exists()else{}
 if ob.name not in camera:
  lo,hi=common.world_bounds([ob]);blo,bhi=common.world_bounds([bpy.data.objects['Body']]);camera[ob.name]={'center':list((lo+hi)/2),'body_height':bhi.z-blo.z};cal.write_text(json.dumps(camera,indent=2))
 c=Vector(camera[ob.name]['center']);scale=camera[ob.name]['body_height']*resolution/pixels
 for tier in ['natf_a','natf_b','natf_c']:
  if whole:
   for name,rows in maps.items():preview(bpy.data.objects[name],rows,tier)
  else:preview(ob,maps,tier)
  for i in range(8):
   angle=i*math.pi/4;d=Vector((math.sin(angle),-math.cos(angle),.05)).normalized();cam=common.ortho_camera('MetricCamera',c+d*6,(0,0,0),scale);cam.rotation_mode='QUATERNION';cam.rotation_quaternion=(-d).to_track_quat('-Z','Y');sc.camera=cam;sc.render.filepath=str(R/f'{tag}_{tier}_{i}.png');bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)
def trial(part,level,ratio):
 ob,rig=reset(part);tag=f'{part}_l{level}_r{ratio:.4f}'
 if ratio==1:
  maps=[{'name':m.name,'maps':{'basecolor':f'textures/{TAGS[m.name]}_basecolor_1k.png','region_mask':f'textures/{TAGS[m.name]}_region_mask.png'}}for m in ob.data.materials];n=count(ob);protected={}
 else:n,maps,protected=reduce(ob,rig,level,ratio,tag)
 blend=W/f'{tag}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(blend));render(ob,rig,level,tag,maps)
 code="import sys,json;from pathlib import Path;sys.path.insert(0,sys.argv[1]);from reduction_metrics import compare;root=Path(sys.argv[2]);a,b=sys.argv[3:5];rows=[compare(root/f'{a}_{t}_{i}.png',root/f'{b}_{t}_{i}.png')for t in ['natf_a','natf_b','natf_c']for i in range(8)];print(json.dumps({'views':rows,'min_iou':min(r['iou']for r in rows),'mean_iou':sum(r['iou']for r in rows)/len(rows),'pooled_iou':sum(r['intersection_pixels']for r in rows)/sum(r['union_pixels']for r in rows),'min_ssim':min(r['ssim']for r in rows)}))"
 result=json.loads(subprocess.check_output(['/usr/bin/python3','-c',code,str(P/'scripts'),str(R),f'{part}_l{level}_r1.0000',tag],text=True));result['pass']=(result['min_iou']>=.99 and result['min_ssim']>=.95)if level==0 else result['pooled_iou']>=.97
 row={'part':part,'lod':level,'ratio':ratio,'triangles':n,'actor_height_px':[700,550,220,88][level],'blend':str(blend.relative_to(P)),'maps':maps,'protection':protected,**result};path=R/'curve.json';curve=json.loads(path.read_text())if path.exists()else[];curve.append(row);path.write_text(json.dumps(curve,indent=2));print('TRIAL',part,level,ratio,n,result,flush=True);return row
if __name__=='__main__':
 trial('Body',0,1);trial('Body',0,.55);trial('Body',0,.7)
