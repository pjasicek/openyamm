"""Open-panel G6 poke-through check, following mm6_gob2_claude/scripts/g6_skirt_poke.py.

The Cyclops panels are fused to a closed torso with internal hip caps; a fabricated skirt volume is not its skin.
Track skin that starts behind an outward panel and crosses its face, using the playbook's 45-degree proximity cone.
"""
from pathlib import Path
import hashlib,json,math,sys,time,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import closest_point_on_tri
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p.parent/'claude_shared/gates'))
from run_gates import Glb,Report,configure_mesh,load_meshes,sample_grid
path=Path(sys.argv[sys.argv.index('--')+1]) if '--' in sys.argv else p/'export/mm8_m520.glb'
cfg=json.loads((p/'gates.json').read_text());g=Glb(path);rows=[];started=time.perf_counter()
def outer_side(point,hit):
 location,normal,face,distance=hit
 if location is None or distance<1e-8:return False
 return (Vector(point)-location).dot(normal)>distance*math.sqrt(.5)
assert outer_side((0,-.01,0),(Vector(),Vector((0,-1,0)),0,.01))
assert not outer_side((0,.01,0),(Vector(),Vector((0,-1,0)),0,.01))
assert not outer_side((.02,-.01,0),(Vector(),Vector((0,-1,0)),0,math.sqrt(.0005)))
for mesh in load_meshes(g):
 configure_mesh(mesh,cfg,Report(cfg));cloth=mesh.regions['loincloth'];tris=mesh.faces[cloth[mesh.faces].all(1)]
 centers=mesh.rest[tris].mean(1);normals=np.cross(mesh.rest[tris[:,1]]-mesh.rest[tris[:,0]],mesh.rest[tris[:,2]]-mesh.rest[tris[:,0]])
 normals/=np.maximum(np.linalg.norm(normals,axis=1,keepdims=True),1e-12)
 radial=centers.copy();radial[:,1]-=.08;radial[:,2]=0;radial/=np.maximum(np.linalg.norm(radial,axis=1,keepdims=True),1e-12)
 # Outer walls are cloth; inward-facing torso caps are hidden body overlap.
 tris=tris[((normals*radial).sum(1)>.3)&(abs(normals[:,2])<.75)]
 skin=np.flatnonzero((mesh.weight(['B_*_Thigh','B_*_Calf'])>.5)&~cloth&(mesh.rest[:,2]>.95)&(mesh.rest[:,2]<1.35))
 assert len(tris)>=3 and len(skin)>=3,(mesh.label,len(tris),len(skin))
 def sides(points):
  tree=BVHTree.FromPolygons(points.tolist(),tris.tolist(),all_triangles=True)
  return [tree.find_nearest(Vector(points[i]),.05) for i in skin]
 rest_normals=np.cross(mesh.rest[tris[:,1]]-mesh.rest[tris[:,0]],mesh.rest[tris[:,2]]-mesh.rest[tris[:,0]])
 rest_normals/=np.maximum(np.linalg.norm(rest_normals,axis=1,keepdims=True),1e-12)
 covered_cache={}
 for clip,a,lo,hi in g.clips():
  worst={'depth_mm':0.,'time_s':0.,'vertex':None};times=sample_grid(lo,hi,48)
  for t,pose in zip(times,g.pose(a,times)):
   points=mesh.posed(pose)
   for i,hit in zip(skin,sides(points)):
    if not outer_side(points[i],hit):continue
    # Compare the same material face: exposed thigh beside an open edge was never covered by it.
    face=hit[2];key=(int(i),face)
    if key not in covered_cache:
     point=Vector(mesh.rest[i]);nearest=closest_point_on_tri(point,*[Vector(v) for v in mesh.rest[tris[face]]])
     covered_cache[key]=outer_side(point,(nearest,-Vector(rest_normals[face]),face,(point-nearest).length))
    if covered_cache[key] and hit[3]*1000>worst['depth_mm']:
     worst={'depth_mm':hit[3]*1000,'time_s':float(t),'vertex':int(i)}
  rows.append({'lod':mesh.label,'clip':clip,'status':'PASS' if worst['depth_mm']<=2 else 'FAIL','limit_mm':2.,'outer_faces':len(tris),'skin_samples':len(skin),**worst})
 print('OPEN_PANELS',mesh.label,max(r['depth_mm'] for r in rows if r['lod']==mesh.label),flush=True)
report={'method':'playbook open-panel outward crossing; same-face covered-side rest baseline, 45-degree cones on both sides, 50 mm proximity, 48 Hz','source':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'seconds':time.perf_counter()-started,'results':rows,'status':'PASS' if all(r['status']=='PASS' for r in rows) else 'FAIL'}
(p/'work/cloth_surface_gates.json').write_text(json.dumps(report,indent=2)+'\n');print('OPEN_PANEL_RESULT',report['status'],[r for r in rows if r['status']=='FAIL'],flush=True)

if report['status']!='PASS':raise RuntimeError('Open cloth panel gate failed; see work/cloth_surface_gates.json')
