"""Fit colour LODs to measured switch-size silhouettes, then retain one runtime rig."""
import bpy,bmesh,json,sys,copy,struct,subprocess,math,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));sys.path.insert(0,str(P.parents[2]/'tools'))
sys.dont_write_bytecode=True
import reduction_rebake as red
from build_actor_lods import read_glb,write_glb,accessor_bytes,append_accessor,merge_shadow
W=P/'work/round2/reduction';R=P/'review/round2/reduction'
selected=json.loads((R/'selection.json').read_text());source=P/selected['blend'];maps=P/selected['maps']
def count(ob):return sum(len(f.vertices)-2 for f in ob.data.polygons)
def open_source():
 bpy.ops.wm.open_mainfile(filepath=str(source));body=bpy.data.objects['Jackalman'];rig=bpy.data.objects['Rig'];red.rest(rig)
 for ob in list(bpy.data.objects):
  if ob not in [body,rig]:bpy.data.objects.remove(ob,do_unlink=True)
 return body,rig
def section(body,staff):
 ob=body.copy();ob.data=body.data.copy();bpy.context.collection.objects.link(ob)
 bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.delete(bm,geom=[f for f in bm.faces if (f.material_index==2)!=staff],context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6);bm.to_mesh(ob.data);bm.free();return ob
body,rig=open_source();base=[sum(len(f.vertices)-2 for f in body.data.polygons if (f.material_index==2)==s)for s in [False,True]]
caps=[[5052,1462],[1816,526],[600,526]];curve=[];chosen=[]
for level,pixels in [(3,88)]:
 body,rig=open_source();red.render(body,rig,f'lod{level}_reference',maps,pixels)
 previous=None
 for trial,inflate in enumerate([0.,.003,.006,.009,.012,.015,.018]):
  body,rig=open_source();parts=[]
  for k,is_staff in enumerate([False,True]):
   ob=section(body,is_staff);initial=min(base[k]*[.55,.25,.10][level-1],caps[level-1][k]) if not(is_staff and level==3) else 450;target=int(initial)
   red.protect(ob,rig,level)
   # Distance LODs preserve contact landmarks; freezing every hand/shaft vertex starves the silhouette.
   vg=ob.vertex_groups['_protect'];indices={g.index:g.name for g in ob.vertex_groups}
   for v in ob.data.vertices:
    old=next((g.weight for g in v.groups if g.group==vg.index),0);vg.add([v.index],min(old,.8),'REPLACE')
   for side in 'LR':
    for suffix in ['Hand','Finger0','Finger1','Finger2','Finger3','Finger4']:
     group=ob.vertex_groups.get(f'B_{side}_{suffix}')
     if group:
      candidates=[v for v in ob.data.vertices if any(g.group==group.index and g.weight>.3 for g in v.groups)]
      if candidates:
       point=rig.data.bones[f'B_{side}_{suffix}'].head_local
       for v in sorted(candidates,key=lambda v:(v.co-point).length)[:1]:vg.add([v.index],1,'REPLACE')
   a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0)
   matrices={g.index:np.array(rig.pose.bones[g.name].matrix@rig.data.bones[g.name].matrix_local.inverted())for g in ob.vertex_groups if g.name in rig.pose.bones}
   def skin_matrix(v):
    pairs=[(matrices[g.group],g.weight)for g in v.groups if g.group in matrices];total=sum(w for m,w in pairs);return sum(m*(w/total)for m,w in pairs)
   for v in ob.data.vertices:v.co=(skin_matrix(v)@np.r_[v.co,1])[:3]
   if level==3 and not is_staff:
    masks=np.load(W/'outlines.npy');height=json.loads((P/'review/posture.json').read_text())['Standing']['body_height_m'];center=Vector((0,0,height/2+.003));visible=set()
    for view in range(8):
     direction=Vector((math.sin(view*math.pi/4),-math.cos(view*math.pi/4),.05)).normalized();rotation=(-direction).to_track_quat('-Z','Y');right=rotation@Vector((1,0,0));up=rotation@Vector((0,1,0))
     for v in ob.data.vertices:
      delta=v.co-center;x=int(500+delta.dot(right)*700/height);y=int(500-delta.dot(up)*700/height)
      if 0<=x<1000 and 0<=y<1000 and masks[view,y,x]:visible.add(v.index)
    for index in visible:vg.add([index],.98,'REPLACE')
    print('DISTANT OUTLINE VERTICES',len(visible),flush=True)
   ob.data.update();surface=BVHTree.FromPolygons([v.co for v in ob.data.vertices],[tuple(f.vertices)for f in ob.data.polygons]);red.reduce(ob,target/count(ob),level)
   ob.data.update()
   if not is_staff:
    for v in ob.data.vertices:
     hand=sum(g.weight for g in v.groups if g.group in indices and ('Hand' in indices[g.group] or 'Finger' in indices[g.group]))
     if hand<.2 and v.co.z>.025:v.co+=v.normal*inflate
   for v in ob.data.vertices:v.co=np.linalg.solve(skin_matrix(v),np.r_[v.co,1])[:3]
   ob.data.update();red.rest(rig);parts.append(ob)
  bpy.data.objects.remove(body,do_unlink=True);bpy.ops.object.select_all(action='DESELECT')
  for ob in parts:ob.select_set(True)
  bpy.context.view_layer.objects.active=parts[0];counts=[count(ob)for ob in parts];bpy.ops.object.join();body=parts[0];body.name='Jackalman'
  tag=f'lod3_inflate{trial:02d}';red.render(body,rig,tag,maps,pixels)
  metric=json.loads(subprocess.check_output(['/usr/bin/python3',str(P/'scripts/reduction_images.py'),'compare',str(R),f'lod{level}_reference',tag],text=True))
  passed=metric['pooled_iou']>=.97 and all(n<=cap for n,cap in zip(counts,caps[level-1])) and (level==3 or all(n>cap for n,cap in zip(counts,[[1816,504],[600,450]][level-1])))
  row={'level':level,'trial':trial,'body_triangles':counts[0],'staff_triangles':counts[1],'pixels':pixels,**metric,'visual_pass':passed,'inflate_m':inflate}
  curve.append(row);(R/'lod3_inflation_curve.json').write_text(json.dumps(curve,indent=2));print('LOD FIT',level,trial,counts,metric['pooled_iou'],passed,flush=True)
  for mat,key in zip(body.data.materials,['body','head','staff']):
   tex=mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].links[0].from_node;tex.image=bpy.data.images.load(str(maps/f'{key}_basecolor.png'),check_existing=True)
  red.rest(rig);file=W/f'lod3_inflate{trial:02d}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(file));row['blend']=str(file.relative_to(P));previous=row if passed and (previous is None or row['pooled_iou']>previous['pooled_iou']) else previous
 assert previous is not None,(level,curve[-1])
 chosen.append(previous)
(R/'lod3_inflation_selection.json').write_text(json.dumps(chosen,indent=2))
