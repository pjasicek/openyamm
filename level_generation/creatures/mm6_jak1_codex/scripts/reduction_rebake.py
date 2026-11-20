"""Protected geometry reduction and selected-to-active texture rebake for Jackalman."""
import bpy,bmesh,json,math,sys,subprocess,time
import numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];W=P/'work/round2/reduction';R=P/'review/round2/reduction'
sys.path.insert(0,str(P/'scripts'));import common
TAGS=['body','head','staff'];MATERIALS=['Jackalman_A','JackalmanHead_A','HookedStaff_A']
def rest(rig):
 rig.animation_data.action=None
 for bone in rig.pose.bones:bone.matrix_basis.identity()
 bpy.context.view_layer.update()
def reset():
 bpy.ops.wm.open_mainfile(filepath=str(W/'unreduced.blend'));body=bpy.data.objects['Jackalman'];rig=bpy.data.objects['Rig']
 for o in list(bpy.data.objects):
  if o not in [body,rig]:bpy.data.objects.remove(o,do_unlink=True)
 rest(rig)
 for mat,tag in zip(body.data.materials,TAGS):
  bs=mat.node_tree.nodes.get('Principled BSDF');tex=bs.inputs['Normal'].links[0].from_node.inputs['Color'].links[0].from_node
  tex.image=bpy.data.images.load(str(W/f'high_maps/{tag}_normal.png'),check_existing=True);tex.image.colorspace_settings.name='Non-Color'
 return body,rig
def component_labels(body):
 me=body.data;parent=list(range(len(me.vertices)))
 def root(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 for edge in me.edges:
  a,b=edge.vertices;parent[root(b)]=root(a)
 roots=[root(i)for i in range(len(parent))];unique={v:i for i,v in enumerate(sorted(set(roots)))}
 attr=me.attributes.get('bake_component') or me.attributes.new('bake_component','INT','POINT')
 attr.data.foreach_set('value',[unique[i]for i in roots])
def protect(body,rig,level=0):
 me=body.data;vg=body.vertex_groups.new(name='_protect');weights=np.zeros(len(me.vertices));names={g.index:g.name for g in body.vertex_groups};staff_inv=rig.data.bones['Staff'].matrix_local.inverted()
 for v in me.vertices:
  groups={names[g.group]:g.weight for g in v.groups};w=0
  if sum(a for n,a in groups.items()if 'Hand'in n or 'Finger'in n)>.1:w=1
  if sum(a for n,a in groups.items()if n in ['B_Head','B_Neck'])>.2:w=max(w,.98)
  for side in 'LR':
   if (v.co-rig.data.bones[f'B_{side}_Hand'].head_local).length<.09:w=1
   for bone in ['UpperArm','Forearm','Hand','Thigh','Calf']:
    if (v.co-rig.data.bones[f'B_{side}_{bone}'].head_local).length<.045:w=max(w,.95)
  if sum(a for n,a in groups.items()if 'Foot'in n or 'Toe'in n)>.5 and v.co.z<.04:w=1
  if groups.get('B_Pelvis',0)>.15 and sum(a for n,a in groups.items()if 'Thigh'in n)>.15:w=max(w,.95)
  if groups.get('Staff',0)>.5 and -.12<(staff_inv@v.co).z<.42:w=1
  weights[v.index]=w
 bm=bmesh.new();bm.from_mesh(me);bm.normal_update();bm.verts.ensure_lookup_table()
 for edge in bm.edges:
  faces=edge.link_faces
  silhouette=len(faces)<2 or any((faces[0].normal.dot(Vector((math.sin(a),math.cos(a),0)))>=0)!=(faces[1].normal.dot(Vector((math.sin(a),math.cos(a),0)))>=0)for a in np.arange(8)*math.pi/4)
  if silhouette:
   for v in edge.verts:weights[v.index]=max(weights[v.index],.8)
 bm.free()
 for i,w in enumerate(weights):
  if w:vg.add([i],float(w),'REPLACE')
 return {'protected_vertices':int((weights>0).sum()),'hand_face_joint_vertices':int((weights>=.95).sum())}
def reduce(body,ratio,level=0):
 bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
 bm=bmesh.new();bm.from_mesh(body.data);dv=bm.verts.layers.deform.active;gi=body.vertex_groups['_protect'].index
 edges=[e for e in bm.edges if all(v[dv].get(gi,0)<.5 for v in e.verts)]
 if edges:bmesh.ops.dissolve_limit(bm,angle_limit=math.radians(.5),use_dissolve_boundaries=False,verts=[],edges=edges,delimit={'NORMAL','MATERIAL','SEAM','UV'})
 bm.to_mesh(body.data);bm.free()
 md=body.modifiers.new('Protected collapse','DECIMATE');md.ratio=ratio;md.use_collapse_triangulate=True;md.vertex_group='_protect';md.invert_vertex_group=True;md.vertex_group_factor=[.001,.0004,.0001,.00002][level]
 bpy.ops.object.modifier_move_to_index(modifier=md.name,index=0);bpy.ops.object.modifier_apply(modifier=md.name)
 body.vertex_groups.remove(body.vertex_groups['_protect']);bpy.ops.object.vertex_group_limit_total(limit=8);bpy.ops.object.vertex_group_normalize_all(lock_active=False)
 return sum(len(f.vertices)-2 for f in body.data.polygons)
def render(body,rig,prefix,directory,pixels=700):
 scene=bpy.context.scene;common.workbench_clay(scene,True);scene.render.film_transparent=True;scene.render.resolution_x=scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.view_settings.view_transform='Standard';scene.display.render_aa='16'
 action=bpy.data.actions['Standing'];rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0];scene.frame_set(0)
 height=json.loads((P/'review/posture.json').read_text())['Standing']['body_height_m'];center=Vector((0,0,height/2+.003))
 for tier in 'abc':
  for mat,tag in zip(body.data.materials,TAGS):
   bs=mat.node_tree.nodes.get('Principled BSDF');tex=bs.inputs['Base Color'].links[0].from_node
   tex.image=bpy.data.images.load(str(directory/(f'{tag}_jak1_{tier}.png' if tag!='staff' else 'staff_basecolor.png')),check_existing=True);mat.node_tree.nodes.active=tex
  for i in range(8):
   a=i*math.pi/4;d=Vector((math.sin(a),-math.cos(a),.05)).normalized();cam=common.ortho_camera('Metric camera',center+d*6,(0,0,0),height*1000/pixels);cam.rotation_mode='QUATERNION';cam.rotation_quaternion=(-d).to_track_quat('-Z','Y');scene.camera=cam;scene.render.filepath=str(R/f'{prefix}_{tier}_{i}.png');bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)
def extract(obj,slot,name,material):
 part=obj.copy();part.data=obj.data.copy();part.name=name;bpy.context.scene.collection.objects.link(part);part.hide_render=False
 bm=bmesh.new();bm.from_mesh(part.data);bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.material_index!=slot],context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
 for face in bm.faces:face.material_index=0
 bm.to_mesh(part.data);bm.free();part.data.materials.clear();part.data.materials.append(material);return part
def rebake(high,low,rig,directory):
 rest(rig);directory.mkdir(parents=True,exist_ok=True);scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=1;scene.render.threads_mode='FIXED';scene.render.threads=4
 scene.render.bake.use_selected_to_active=True;scene.render.bake.cage_extrusion=.02;scene.render.bake.max_ray_distance=.08;scene.render.bake.margin=16;scene.render.bake.use_clear=True;scene.render.bake.normal_space='TANGENT';scene.render.bake.normal_r='POS_X';scene.render.bake.normal_g='POS_Y';scene.render.bake.normal_b='POS_Z'
 high.hide_render=True;low.hide_render=True;parts=[];receipt={}
 for slot,(tag,name)in enumerate(zip(TAGS,MATERIALS)):
  source=high.data.materials[slot];source.name='Bake source '+name;target=bpy.data.materials.new(name);target.use_nodes=True
  hp=extract(high,slot,'Source '+tag,source);lp=extract(low,slot,'Reduced '+tag,target);lp.data.validate(clean_customdata=False);lp.data.normals_split_custom_set([(0,0,0)]*len(lp.data.loops))
  for face in lp.data.polygons:face.use_smooth=True
  originals={}
  for obj in [hp,lp]:
   originals[obj]=[v.co.copy()for v in obj.data.vertices]
   for v,a in zip(obj.data.vertices,obj.data.attributes['bake_component'].data):v.co+=Vector(((a.value%16)*3,(a.value//16)*3,0))
   obj.data.update()
  bpy.context.view_layer.update();nodes=source.node_tree.nodes;links=source.node_tree.links;out=next(n for n in nodes if n.type=='OUTPUT_MATERIAL');original=out.inputs['Surface'].links[0].from_socket;emit=nodes.new('ShaderNodeEmission');tex=nodes.new('ShaderNodeTexImage');links.new(tex.outputs['Color'],emit.inputs['Color'])
  bake_node=target.node_tree.nodes.new('ShaderNodeTexImage');target.node_tree.nodes.active=bake_node
  bpy.ops.object.select_all(action='DESELECT');hp.select_set(True);lp.select_set(True);bpy.context.view_layer.objects.active=lp
  for key in ['basecolor','metal_rough','normal']+(['region_mask']if tag!='staff' else []):
   space='sRGB' if key=='basecolor' else 'Non-Color';image=bpy.data.images.new(f'{name} rebake {key}',width=1024,height=1024,alpha=False);image.colorspace_settings.name=space;bake_node.image=image
   if key=='normal':links.new(original,out.inputs['Surface']);kind='NORMAL'
   else:tex.image=bpy.data.images.load(str(W/f'high_maps/{tag}_{key}.png'),check_existing=False);tex.image.colorspace_settings.name=space;links.new(emit.outputs[0],out.inputs['Surface']);kind='EMIT'
   started=time.time();bpy.ops.object.bake(type=kind);image.filepath_raw=str(directory/f'{tag}_{key}.png');image.file_format='PNG';image.save();receipt[f'{tag}_{key}']={'size':1024,'seconds':time.time()-started};print('BAKE',tag,key,flush=True)
  links.new(original,out.inputs['Surface'])
  for obj,coords in originals.items():
   for v,co in zip(obj.data.vertices,coords):v.co=co
   obj.data.update()
  bpy.data.objects.remove(hp,do_unlink=True);bs=target.node_tree.nodes.get('Principled BSDF');bs.inputs['Metallic'].default_value=0
  for key in ['basecolor','metal_rough','normal']:
   node=target.node_tree.nodes.new('ShaderNodeTexImage');node.image=bpy.data.images.load(str(directory/f'{tag}_{key}.png'),check_existing=True);node.image.colorspace_settings.name='sRGB'if key=='basecolor'else'Non-Color'
   if key=='basecolor':target.node_tree.links.new(node.outputs['Color'],bs.inputs['Base Color']);target.node_tree.nodes.active=node
   elif key=='normal':
    normal=target.node_tree.nodes.new('ShaderNodeNormalMap');target.node_tree.links.new(node.outputs['Color'],normal.inputs['Color']);target.node_tree.links.new(normal.outputs['Normal'],bs.inputs['Normal'])
   else:
    sep=target.node_tree.nodes.new('ShaderNodeSeparateColor');target.node_tree.links.new(node.outputs['Color'],sep.inputs['Color']);target.node_tree.links.new(sep.outputs['Green'],bs.inputs['Roughness'])
    # Preserve the packed engine specular mask in R during glTF's ORM export.
    target.node_tree.links.new(sep.outputs['Blue'],bs.inputs['Metallic'])
  parts.append(lp);lp.hide_render=True
 bpy.data.objects.remove(high,do_unlink=True);bpy.data.objects.remove(low,do_unlink=True);bpy.ops.object.select_all(action='DESELECT')
 for part in parts:part.hide_render=False;part.select_set(True)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();body=parts[0];body.name='Jackalman'
 (directory/'bake.json').write_text(json.dumps({'method':'Cycles selected-to-active; component-separated projection; reprojected original charts; tangent OpenGL normals','maps':receipt},indent=2))
 subprocess.run(['/usr/bin/python3',str(P/'scripts/reduction_images.py'),'tiers',str(directory)],check=True)
 return body
def run():
 R.mkdir(parents=True,exist_ok=True);body,rig=reset();render(body,rig,'reference',W/'high_maps');curve=[];last=None
 for step in range(1,25):
  high,rig=reset();component_labels(high);low=high.copy();low.data=high.data.copy();low.name='Reduced candidate';bpy.context.scene.collection.objects.link(low);high.hide_render=True
  protection=protect(low,rig);ratio=.9**step;count=reduce(low,ratio);directory=W/f'step{step:02d}_maps';body=rebake(high,low,rig,directory);render(body,rig,f'step{step:02d}',directory)
  metrics=json.loads(subprocess.check_output(['/usr/bin/python3',str(P/'scripts/reduction_images.py'),'compare',str(R),'reference',f'step{step:02d}'],text=True));passed=metrics['min_iou']>=.99 and metrics['min_ssim']>=.95
  # Restore raw base textures before saving the authoritative reduced mesh.
  for mat,tag in zip(body.data.materials,TAGS):
   node=mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].links[0].from_node;node.image=bpy.data.images.load(str(directory/f'{tag}_basecolor.png'),check_existing=True)
  rest(rig);file=W/f'step{step:02d}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(file));row={'step':step,'ratio':ratio,'triangles':count,'pixels':700,'tiers':['jak1_a','jak1_b','jak1_c'],'protection':protection,**metrics,'visual_pass':passed,'rig_gates':'pending'if passed else'visual rejection','blend':str(file.relative_to(P)),'maps':str(directory.relative_to(P))};curve.append(row);(R/'curve.json').write_text(json.dumps(curve,indent=2));print('REDUCTION',step,count,metrics['min_iou'],metrics['min_ssim'],passed,flush=True)
  if not passed:break
  last=row
 assert last is not None,'No reduced candidate met the visual gates; inspect the first rebake before proceeding.'
 (R/'selection.json').write_text(json.dumps(last,indent=2))
if __name__=='__main__':run()
