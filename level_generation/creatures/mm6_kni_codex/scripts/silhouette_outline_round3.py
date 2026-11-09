"""Protect visible eight-view outlines rather than occluded crease edges."""
import bpy,bmesh,json,sys,math,subprocess,numpy as np
from pathlib import Path
from mathutils import Vector,kdtree
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];W=P/'work/round3';R=P/'review/round3';sys.path.insert(0,str(P/'scripts'));import reduce_round2 as old
old.R=R

def protect(body,rig):
 me=body.data;names=[g.name for g in body.vertex_groups];a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0)
 ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());posed=ev.to_mesh();bm=bmesh.new();bm.from_mesh(posed);tree=BVHTree.FromPolygons([v.co for v in posed.vertices],[tuple(p.vertices)for p in posed.polygons]);keys=[tuple(round(x,6)for x in v.co)for v in posed.vertices];ev.to_mesh_clear();bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7);bm.normal_update();visible=set()
 for i in range(8):
  d=Vector((math.sin(i*math.pi/4),-math.cos(i*math.pi/4),.05)).normalized()
  for edge in bm.edges:
   fs=edge.link_faces
   if len(fs)==2 and (fs[0].normal.dot(d)>=0)==(fs[1].normal.dot(d)>=0):continue
   midpoint=(edge.verts[0].co+edge.verts[1].co)/2
   if tree.ray_cast(midpoint+d*.0001,d,10)[0]is None:
    visible.update(tuple(round(x,6)for x in v.co)for v in edge.verts)
 # Keep only true outer silhouette pixels; visible internal armour creases are bake detail.
 masks=np.load(W/'outline_masks.npz')['masks'];height=json.loads((R/'silhouette_curve.json').read_text())[0]['body_standing_height_m'];scale=height*1024/700;centre=Vector((0,0,.95));outer=set()
 for i in range(8):
  d=Vector((math.sin(i*math.pi/4),-math.cos(i*math.pi/4),.05)).normalized();q=(-d).to_track_quat('-Z','Y');right=q@Vector((1,0,0));up=q@Vector((0,1,0))
  for v in bm.verts:
   key=tuple(round(x,6)for x in v.co)
   if key not in visible:continue
   x=int((.5+(v.co-centre).dot(right)/scale)*1024);y=int((.5-(v.co-centre).dot(up)/scale)*1024)
   if 0<=x<1024 and 0<=y<1024 and masks[i,y,x] and tree.ray_cast(v.co+d*.0002,d,10)[0]is None:outer.add(key)
 visible=outer
 bm.free();rig.animation_data.action=None
 for pb in rig.pose.bones:pb.matrix_basis.identity()
 bpy.context.view_layer.update();vg=body.vertex_groups.new(name='_protect');hard=0
 for v in me.vertices:
  groups={names[g.group]:g.weight for g in v.groups};w=0.
  if any(('Hand'in n or 'Finger'in n)and a>.1 for n,a in groups.items()):w=1.
  if sum(a for n,a in groups.items()if n in ['B_Head','B_Neck'])>.2:w=max(w,.98)
  for sd in 'LR':
   for n in ['UpperArm','Forearm','Hand','Thigh','Calf']:
    if (v.co-rig.data.bones[f'B_{sd}_{n}'].head_local).length<.045:w=max(w,.95)
  if keys[v.index]in visible:w=1.
  if w:vg.add([v.index],w,'REPLACE')
  hard+=w==1
 return {'hard_protected_vertices':hard,'vertices':len(me.vertices),'visible_silhouette_positions':len(visible)}
def make(ratio,factor=.0001):
 body,rig=old.reset(0);bpy.context.view_layer.objects.active=body;bpy.ops.object.select_all(action='DESELECT');body.select_set(True)
 bm=bmesh.new();bm.from_mesh(body.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7);bm.to_mesh(body.data);bm.free();prot=protect(body,rig)
 md=body.modifiers.new('Planar','DECIMATE');md.decimate_type='DISSOLVE';md.angle_limit=math.radians(.00001);md.delimit={'MATERIAL','SEAM','UV'};bpy.ops.object.modifier_move_to_index(modifier=md.name,index=0);bpy.ops.object.modifier_apply(modifier=md.name)
 md=body.modifiers.new('Visible silhouette protected','DECIMATE');md.ratio=ratio;md.use_collapse_triangulate=True;md.vertex_group='_protect';md.invert_vertex_group=True;md.vertex_group_factor=factor;bpy.ops.object.modifier_move_to_index(modifier=md.name,index=0);bpy.ops.object.modifier_apply(modifier=md.name);body.vertex_groups.remove(body.vertex_groups['_protect']);bpy.ops.object.vertex_group_limit_total(limit=8);bpy.ops.object.vertex_group_normalize_all(lock_active=False)
 return body,rig,prot
if __name__=='__main__':
 curve=json.loads((R/'silhouette_curve.json').read_text());h=curve[0]['body_standing_height_m'];pixels=2.1778047/h*700;prev=0
 for step in range(4,17):
  ratio=.9**step;body,rig,prot=make(ratio);count=sum(len(p.vertices)-2 for p in body.data.polygons);tag=f'outline_s{step:02d}';bpy.ops.wm.save_as_mainfile(filepath=str(W/f'{tag}.blend'));old.render(body,rig,tag,pixels)
  m=json.loads(subprocess.check_output(['/usr/bin/python3',str(P/'scripts/reduction_metrics_round2.py'),str(R),'high_silhouette',tag],text=True));row={'tag':tag,'ratio':ratio,'triangles':count,'min_iou':m['min_iou'],'views':[x['iou']for x in m['views']],'silhouette_pass':m['min_iou']>=.99,'actor_height_px':700,'body_standing_height_m':h,'protection':prot,'blend':f'work/round3/{tag}.blend'};curve.append(row);(R/'silhouette_curve.json').write_text(json.dumps(curve,indent=2));print('VISIBLE',tag,count,row['min_iou'],prot,flush=True)
  if not row['silhouette_pass']or count==prev:break
  prev=count
