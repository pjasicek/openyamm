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
selected=json.loads((R/'selection.json').read_text());source=W/'unreduced.blend';maps=P/selected['maps']
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
 for trial,head_fraction in enumerate([.10,.15,.20,.25]):
  body,rig=open_source();parts=[]
  for k,is_staff in enumerate([False,False,True]):
   ob=section(body,is_staff)
   if not is_staff:
    bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.material_index!=k],context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(ob.data);bm.free()
   target=int(600*(head_fraction if k==1 else 1-head_fraction)) if not is_staff else 450
   vg=ob.vertex_groups.new(name='_protect')
   a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0)
   matrices={g.index:np.array(rig.pose.bones[g.name].matrix@rig.data.bones[g.name].matrix_local.inverted())for g in ob.vertex_groups if g.name in rig.pose.bones}
   def skin_matrix(v):
    pairs=[(matrices[g.group],g.weight)for g in v.groups if g.group in matrices];total=sum(w for m,w in pairs);return sum(m*(w/total)for m,w in pairs)
   for v in ob.data.vertices:v.co=(skin_matrix(v)@np.r_[v.co,1])[:3]
   ob.data.update();surface=BVHTree.FromPolygons([v.co for v in ob.data.vertices],[tuple(f.vertices)for f in ob.data.polygons]);red.reduce(ob,target/count(ob),level)
   ob.data.update()
   for v in ob.data.vertices:v.co=np.linalg.solve(skin_matrix(v),np.r_[v.co,1])[:3]
   ob.data.update();red.rest(rig);parts.append(ob)
  bpy.data.objects.remove(body,do_unlink=True);bpy.ops.object.select_all(action='DESELECT')
  for ob in parts:ob.select_set(True)
  bpy.context.view_layer.objects.active=parts[0];counts=[count(parts[0])+count(parts[1]),count(parts[2])];bpy.ops.object.join();body=parts[0];body.name='Jackalman'
  tag=f'lod3_material{trial:02d}';red.render(body,rig,tag,maps,pixels)
  metric=json.loads(subprocess.check_output(['/usr/bin/python3',str(P/'scripts/reduction_images.py'),'compare',str(R),f'lod{level}_reference',tag],text=True))
  passed=metric['pooled_iou']>=.97 and all(n<=cap for n,cap in zip(counts,caps[level-1])) and (level==3 or all(n>cap for n,cap in zip(counts,[[1816,504],[600,450]][level-1])))
  row={'level':level,'trial':trial,'body_triangles':counts[0],'staff_triangles':counts[1],'pixels':pixels,**metric,'visual_pass':passed}
  curve.append(row);(R/'lod3_material_curve.json').write_text(json.dumps(curve,indent=2));print('LOD FIT',level,trial,counts,metric['pooled_iou'],passed,flush=True)
  for mat,key in zip(body.data.materials,['body','head','staff']):
   tex=mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].links[0].from_node;tex.image=bpy.data.images.load(str(maps/f'{key}_basecolor.png'),check_existing=True)
  red.rest(rig);file=W/f'lod3_material{trial:02d}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(file));row['blend']=str(file.relative_to(P));previous=row if passed and (previous is None or row['pooled_iou']>previous['pooled_iou']) else previous
 assert previous is not None,(level,curve[-1])
 chosen.append(previous)
(R/'lod3_material_selection.json').write_text(json.dumps(chosen,indent=2))
