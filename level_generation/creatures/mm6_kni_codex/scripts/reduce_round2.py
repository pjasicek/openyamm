"""Measured, protected reduction of the accepted exported body; no new rig or texture data."""
import bpy,bmesh,json,math,sys,subprocess,numpy as np
from pathlib import Path
from mathutils import Vector,kdtree
P=Path(__file__).resolve().parents[1];W=P/'work/round2';R=P/'review/round2';sys.path.insert(0,str(P/'scripts'));import common

def reset(level=0):
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(W/f'baseline_body_l{level}.glb'));body=bpy.data.objects['KnightPlate'];body.name='Body';rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rig.name='Rig'
 for o in list(bpy.data.objects):
  if o not in [body,rig]:bpy.data.objects.remove(o,do_unlink=True)
 rig.animation_data.action=None
 for pb in rig.pose.bones:pb.matrix_basis.identity()
 bpy.context.view_layer.update();data=np.load(W/'pieces.npz');tree=kdtree.KDTree(len(data['co']))
 for i,c in enumerate(data['co']):tree.insert(c,i)
 tree.balance();at=body.data.attributes.new('piece','INT','POINT');dist=[]
 for v in body.data.vertices:
  _,i,d=tree.find(v.co);at.data[v.index].value=int(data['piece'][i]);dist.append(d)
 assert max(dist)<(.00001 if level==0 else .10),max(dist)
 for mat in body.data.materials:
  bs=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');mat.node_tree.nodes.active=bs.inputs['Base Color'].links[0].from_node
 return body,rig

def protect(body,rig,level):
 me=body.data;bm=bmesh.new();bm.from_mesh(me);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7);bm.verts.ensure_lookup_table();bm.edges.ensure_lookup_table();bm.normal_update();names=[g.name for g in body.vertex_groups];weights=np.zeros(len(me.vertices));counts={}
 for v in me.vertices:
  groups={names[g.group]:g.weight for g in v.groups};w=0.
  if any(('Hand'in n or 'Finger'in n)and a>.1 for n,a in groups.items()):w=1.
  if sum(a for n,a in groups.items()if n in ['B_Head','B_Neck'])>.2:w=max(w,.98)
  for s in 'RL':
   for name in ['UpperArm','Forearm','Hand','Thigh','Calf']:
    if (v.co-rig.data.bones[f'B_{s}_{name}'].head_local).length<.045:w=max(w,.95)
  weights[v.index]=w
 silhouette_coords=set()
 for e in bm.edges:
  silhouette=len(e.link_faces)<2 or any((e.link_faces[0].normal.dot(Vector((math.sin(a),math.cos(a),0)))>=0)!=(e.link_faces[1].normal.dot(Vector((math.sin(a),math.cos(a),0)))>=0)for a in np.arange(8)*math.pi/4)
  if silhouette:
   for v in e.verts:silhouette_coords.add(tuple(round(x,6)for x in v.co))
 for v in me.vertices:
  if tuple(round(x,6)for x in v.co)in silhouette_coords:weights[v.index]=max(weights[v.index],.80)
 bm.free();vg=body.vertex_groups.new(name='_protect')
 for v,w in enumerate(weights):
  if w:vg.add([v],float(w),'REPLACE')
 return {'vertices':len(weights),'protected':int((weights>0).sum()),'hand_or_face':int((weights>=.98).sum()),'deformation':int((weights>=.9).sum()),'silhouette':int((weights==.8).sum())}

def reduce(body,ratio,level):
 bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
 # Keep glTF seams split: welding damaged smooth shading and UV interpolation in measured probes.
 md=body.modifiers.new('Planar patches','DECIMATE');md.decimate_type='DISSOLVE';md.angle_limit=math.radians(.00001);md.delimit={'NORMAL','MATERIAL','SEAM','UV'};bpy.ops.object.modifier_move_to_index(modifier=md.name,index=0);bpy.ops.object.modifier_apply(modifier=md.name)
 md=body.modifiers.new('Protected collapse','DECIMATE');md.ratio=ratio;md.use_collapse_triangulate=True;md.vertex_group='_protect';md.invert_vertex_group=True;md.vertex_group_factor=[.001,.0004,.0001,.00002][level];bpy.ops.object.modifier_move_to_index(modifier=md.name,index=0);bpy.ops.object.modifier_apply(modifier=md.name)
 body.vertex_groups.remove(body.vertex_groups['_protect']);bpy.ops.object.vertex_group_limit_total(limit=8);bpy.ops.object.vertex_group_normalize_all(lock_active=False)
 # The carried UV map is retained; custom normals remain in Blender's loop data.
 return sum(len(p.vertices)-2 for p in body.data.polygons)

def render(body,rig,prefix,diam_pixels):
 scene=bpy.context.scene;common.workbench_clay(scene,True);scene.render.film_transparent=True;scene.render.resolution_x=scene.render.resolution_y=1024;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.view_settings.view_transform='Standard';scene.display.render_aa='16';scene.render.threads_mode='FIXED';scene.render.threads=4
 act=bpy.data.actions['Standing'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];scene.frame_set(0)
 # Fixed accepted A-pose diameter and Standing centre, shared by baseline and all candidates.
 center=Vector((0,0,.95));scale=2.1778047*1024/diam_pixels
 for i in range(8):
  ang=i*math.pi/4;d=Vector((math.sin(ang),-math.cos(ang),.05)).normalized();cam=common.ortho_camera('MetricCamera',center+d*6,(0,0,0),scale);cam.rotation_mode='QUATERNION';cam.rotation_quaternion=(-d).to_track_quat('-Z','Y');scene.camera=cam;scene.render.filepath=str(R/f'{prefix}_{i}.png');bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)

def run():
 curve=[]
 # Each accepted LOD is its own unreduced reference, measured at its runtime switch size.
 for level,pixels in enumerate([800,550,220,88]):
  body,rig=reset(level);render(body,rig,f'body_l{level}_reference',pixels);last=None
  for step in range(1,31):
   body,rig=reset(level);prot=protect(body,rig,level);ratio=.9**step;count=reduce(body,ratio,level);tag=f'body_l{level}_s{step:02d}';bpy.ops.wm.save_as_mainfile(filepath=str(W/f'{tag}.blend'));render(body,rig,tag,pixels)
   result=json.loads(subprocess.check_output(['/usr/bin/python3',str(P/'scripts/reduction_metrics_round2.py'),str(R),f'body_l{level}_reference',tag],text=True));row={'part':'body','lod':level,'step':step,'ratio':ratio,'triangles':count,'projected_diameter_pixels':pixels,'protection':prot,**result,'blend':f'work/round2/{tag}.blend','reference':f'work/round2/baseline_body_l{level}.glb','rig_gate':'pending'if result['pass']else 'not_run_visual_rejection'};curve.append(row);(R/'reduction_curve.json').write_text(json.dumps(curve,indent=2));print('CURVE',json.dumps({k:v for k,v in row.items()if k not in ['views','protection']}),flush=True)
   if not result['pass']:break
   last=row
  if last is None:print('NO PASSING CUT',level,flush=True)
  else:print('VISUAL SELECT',level,last['triangles'],last['blend'],flush=True)
if __name__=='__main__':run()
