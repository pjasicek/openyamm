"""Separate worn layers on the selected meshes; retain UVs, topology and existing floor/grip fitting."""
import bpy,sys,json,math,shutil,runpy
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
selection=json.loads((P/'review/round4/lod_selection.json').read_text())
meta=json.loads((P/'review/rebake/round4_shared_bake.json').read_text());reports={}
for level in range(4):
 bpy.ops.wm.open_mainfile(filepath=str(P/selection[str(level)]['blend']))
 r=bpy.data.objects['Rig'];ob=bpy.data.objects['Body'];me=ob.data;sc=bpy.context.scene
 old=bpy.data.actions['Walking'];old.name='WalkingPrevious';r.animation_data.action=None
 with bpy.data.libraries.load(str(P/'work/round5/motion.blend'),link=False)as(src,dst):dst.actions=['Walking']
 walk=bpy.data.actions['Walking'];walk.use_fake_user=True
 def curves(a):return [fc for l in a.layers for s in l.strips for bag in s.channelbags for fc in bag.fcurves]
 # Retain the prior surface-grounding correction, which only changed pelvis translation.
 source={ (fc.data_path,fc.array_index):fc for fc in curves(old)}
 for fc in curves(walk):
  if fc.data_path=='pose.bones["B_Pelvis"].location':
   orig=source[fc.data_path,fc.array_index]
   for k in fc.keyframe_points:k.co.y=orig.evaluate(k.co.x)
 bpy.data.actions.remove(old)
 for b in r.pose.bones:b.matrix_basis.identity()
 bpy.context.view_layer.update();pv=np.array([a.value for a in me.attributes['piece'].data])
 def weights(v,items):
  for g in list(v.groups):ob.vertex_groups[g.group].remove([v.index])
  total=sum(items.values());assert total>0
  for gi,w in items.items():
   if w>1e-8:ob.vertex_groups[gi].add([v.index],w/total,'REPLACE')
 pelvis=ob.vertex_groups['B_Pelvis'].index
 for v in me.vertices:
  if pv[v.index]==2 and abs(v.co.x)>.08 and v.co.z>1.08:
   side='L'if v.co.x>0 else'R';w=float(np.clip((abs(v.co.x)-.08)/.06,0,1)*np.clip((v.co.z-1.08)/.12,0,1))
   ww={g.group:g.weight*(1-w)for g in v.groups}
   for name,part in [('B_Spine2',.7),(f'B_{side}_UpperArm',.3)]:
    gi=ob.vertex_groups[name].index;ww[gi]=ww.get(gi,0)+part*w
   weights(v,ww)
  if pv[v.index]in [2,15] and v.co.z<1.25:
   t=float(np.clip((1.25-v.co.z)/.12,0,1));radial=Vector((v.co.x,v.co.y-.025,0)).normalized();v.co-=radial*(.015*t)
  if pv[v.index]==2 and v.co.z<1.22:
   w=float(np.clip((1.22-v.co.z)/.09,0,1))
   oldw={g.group:g.weight*(1-w)for g in v.groups};oldw[pelvis]=oldw.get(pelvis,0)+w;weights(v,oldw)
  if pv[v.index]==15 and v.co.z>.90:
   w=float(np.clip((v.co.z-.90)/.085,0,1))
   oldw={g.group:g.weight*(1-w)for g in v.groups};oldw[pelvis]=oldw.get(pelvis,0)+w;weights(v,oldw)
 me.calc_loop_triangles()
 def fit(outer,inner,clearance,copy_weights=True):
  if not any(x in outer for x in pv):return {'vertices':0,'reason':'component absent at this LOD'}
  coords=[v.co.copy()for v in me.vertices]
  faces=[list(f.vertices)for f in me.loop_triangles if all(pv[i]in inner for i in f.vertices)]
  assert faces,(level,inner)
  tree=BVHTree.FromPolygons(coords,faces,all_triangles=True);amount=[]
  for v in me.vertices:
   if pv[v.index] not in outer:continue
   hit,n,fi,d=tree.find_nearest(v.co);tri=faces[fi]
   radial=v.co-Vector((0,.025,1.22 if 16 in outer else v.co.z))
   if n.dot(radial)<0:n=-n
   signed=(v.co-hit).dot(n);target=hit+n*max(clearance,signed+clearance)
   amount.append((target-v.co).length);v.co=target
   if copy_weights:
    A=np.array([coords[i][:]for i in tri]);bc=np.linalg.lstsq(np.vstack((A.T,np.ones(3))),np.r_[hit[:],1],rcond=None)[0]
    bc=np.maximum(bc,0);bc/=bc.sum();out={}
    for i,w in zip(tri,bc):
     for g in me.vertices[i].groups:out[g.group]=out.get(g.group,0)+g.weight*w
    weights(v,out)
  me.update()
  return {'vertices':len(amount),'max_offset_m':max(amount,default=0),'clearance_m':clearance}
 report={}
 report['shoulders']=fit({16,17},{2},.006,False)
 for v in me.vertices:
  if pv[v.index]in [16,17]:
   side='R'if pv[v.index]==16 else'L';weights(v,{ob.vertex_groups['B_Spine2'].index:.7,ob.vertex_groups[f'B_{side}_UpperArm'].index:.3})
 report['belt']=fit({12},{2,10,15},.006,True)
 report['buckle']=fit({23},{12},.004,True)if any(all(pv[i]==12 for i in f.vertices)for f in me.loop_triangles)else fit({23},{2,10,15},.010,True)
 for v in me.vertices:
  if pv[v.index]in [16,17]:v.co+=Vector((.008 if v.co.x>0 else-.008,0,.012+(.022 if level>=2 else 0)))
  if pv[v.index]in [12,23]:
   radial=Vector((v.co.x,v.co.y-.025,0)).normalized();v.co+=radial*.026
 me.update()
 # Exact shared material identities are needed by the existing LOD packer.
 targets=[bpy.data.materials[meta[g]['material']]for g in ['body','head','bow']]
 mats=list(me.materials);indices=[2 if 'Bow'in mats[f.material_index].name else 1 if 'Head'in mats[f.material_index].name else 0 for f in me.polygons]
 me.materials.clear()
 for m in targets:me.materials.append(m)
 for f,i in zip(me.polygons,indices):f.material_index=i
 path=P/f'work/round5/lod{level}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path));reports[str(level)]=report
 # Preserve piece IDs and bind positions to select these exact layers in the shared runtime evaluator.
 (P/f'work/round5/lod{level}_pieces.json').write_text(json.dumps({'positions':[list(v.co)for v in me.vertices],'pieces':pv.tolist()}))
 if level==0:
  shutil.copyfile(path,P/'work/master.blend')
  runpy.run_path(str(P/'scripts/export_runtime.py'),run_name='__main__')
  runpy.run_path(str(P/'scripts/patch_string_export.py'),run_name='__main__')
  shutil.copyfile(P/'export/mm6_lzd_raw.glb',P/'export/mm6_lzd_lod0.glb')
 else:
  bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);r.select_set(True);bpy.context.view_layer.objects.active=r;ob.name=ob.data.name='Lizard'
  bpy.ops.export_scene.gltf(filepath=str(P/f'export/mm6_lzd_level{level}.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=False,export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,export_image_format='AUTO')
(P/'review/round5/repairs.json').write_text(json.dumps(reports,indent=2))
print('ROUND5_LAYERS_EXPORTED',reports,flush=True)
