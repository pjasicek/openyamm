"""Fit the remaining coarse-layer contacts against the shared evaluator's posed surfaces."""
import bpy,sys,json,shutil,runpy
import numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P.parent/'claude_shared/gates'))
from run_gates import Glb,load_meshes,Surface,sample_grid
g=Glb(P/'export/mm6_lzd.glb');report={}
poses=[(name,t,pose)for name,a,start,end in g.clips()for t,pose in zip(sample_grid(start,end,48),g.pose(a,sample_grid(start,end,48)))]
for level,outer,inner in [(3,[16,17],[2])]:
 m=next(m for m in load_meshes(g)if m.label.endswith('colour'+str(level)))
 data=json.loads((P/f'work/round5/lod{level}_pieces.json').read_text());co=np.array(data['positions']);pv=np.array(data['pieces'])
 indices=np.linalg.norm(m.rest[:,None,:]-co,axis=2).argmin(1);parts=pv[indices]
 tri=m.faces[np.all(np.isin(parts,outer)[m.faces],axis=1)];surf=Surface(m,np.isin(parts,inner));bary=np.array([[1,0,0],[0,1,0],[0,0,1],[.5,.5,0],[0,.5,.5],[.5,0,.5],[1/3]*3])
 original=co.copy();edits=0
 for iteration in range(12):
  worst=1;change=np.zeros_like(co);hits=0
  for clip,t,pose in poses:
   points=m.posed(pose);surf.build(points,pose);query=np.einsum('sk,tkj->tsj',bary,points[tri]).reshape(-1,3)
   near=[surf.tree.find_nearest(Vector(pt))for pt in query]
   for j,(hit,n,face,dist)in enumerate(near):
    worst=min(worst,dist)
    if dist>=.002:continue
    delta=np.array(n)*(.0035-np.dot(query[j]-np.array(hit),np.array(n)));ids=tri[j//7];bc=bary[j%7]
    for i,w in zip(ids,bc):
     if not w:continue
     matrices=pose[m.skin_nodes[m.joints[i]]]@m.bind[m.joints[i]];skin=(matrices*m.weights[i,:,None,None]).sum(0)
     rest=(g.rest[m.skin_nodes[m.joints[i]]]@m.bind[m.joints[i]]*m.weights[i,:,None,None]).sum(0)
     d=rest[:3,:3]@np.linalg.solve(skin[:3,:3],delta)*(w/(bc@bc))
     k=indices[i]
     if np.linalg.norm(d)>np.linalg.norm(change[k]):change[k]=d
    hits+=1
  print('FIT',level,iteration,worst,hits,flush=True)
  if not hits:break
  # UV seam copies share one authored vertex; limit each update to avoid a local overshoot.
  sizes=np.linalg.norm(change,axis=1);change*=np.minimum(1,.004/np.maximum(sizes,1e-12))[:,None]
  co+=change;edits+=int((sizes>0).sum())
  m.rest=co[indices]
  for i in np.flatnonzero(np.isin(parts,outer)):
   rest=(g.rest[m.skin_nodes[m.joints[i]]]@m.bind[m.joints[i]]*m.weights[i,:,None,None]).sum(0)
   m.vertices[i]=np.linalg.solve(rest[:3,:3],m.rest[i]-rest[:3,3])
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/round5/lod{level}.blend'));o=bpy.data.objects['Body'];r=bpy.data.objects['Rig']
 for v in o.data.vertices:v.co=co[v.index]
 o.data.update();path=P/f'work/round5/lod{level}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path))
 data['positions']=co.tolist();(P/f'work/round5/lod{level}_pieces.json').write_text(json.dumps(data))
 report[str(level)]={'updates':edits,'maximum_vertex_displacement_m':float(np.linalg.norm(co-original,axis=1).max()),'last_iteration_minimum_m':worst}
 if level==0:
  shutil.copyfile(path,P/'work/master.blend');runpy.run_path(str(P/'scripts/export_runtime.py'),run_name='__main__');runpy.run_path(str(P/'scripts/patch_string_export.py'),run_name='__main__');shutil.copyfile(P/'export/mm6_lzd_raw.glb',P/'export/mm6_lzd_lod0.glb')
 else:
  bpy.ops.object.select_all(action='DESELECT');o.select_set(True);r.select_set(True);bpy.context.view_layer.objects.active=r;o.name=o.data.name='Lizard'
  bpy.ops.export_scene.gltf(filepath=str(P/f'export/mm6_lzd_level{level}.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=False,export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,export_image_format='AUTO')
(P/'review/round5/contact_fit.json').write_text(json.dumps(report,indent=2))

shutil.copyfile(P/'work/round5/lod0.blend',P/'work/master.blend')
runpy.run_path(str(P/'scripts/export_runtime.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/patch_string_export.py'),run_name='__main__')
shutil.copyfile(P/'export/mm6_lzd_raw.glb',P/'export/mm6_lzd_lod0.glb')
