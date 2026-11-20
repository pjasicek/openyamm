"""Localize saved shared-gate cloth findings; this does not alter gate verdicts."""
import sys,json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'claude_shared/gates'));import run_gates as G
report=json.loads((P/'review/gates/gates.json').read_text());cfg=json.loads((P/'gates.json').read_text());g=G.Glb(P/'export/mm6_mer1.glb');meshes={m.label:m for m in G.load_meshes(g)};rows=[]
for failure in report['gates']:
 if failure['status']!='FAIL' or failure['gate']!='cloth_penetration_mm' or failure['region']!='coat hem' or '/shadow'in failure['lod']:continue
 m=meshes[failure['lod']];reg=cfg['lod_regions'][m.label.split('/')[-1]];mask=np.zeros(len(m.rest),bool);mask[reg['skirt']['vertices']]=1;ids=np.array(reg['boots']['vertices']);surface=G.Surface(m,mask,cap=True,opening={'axis':[0,0,-1]});anim=next(a for a in g.doc['animations']if a['name']==failure['clip']);pose=g.pose(anim,np.array([failure['time_s']]))[0];points=m.posed(pose);surface.build(points,pose);idx=ids[failure['detail']['sample_vertex']];pt=Vector(points[idx]);loc,n,fi,d=surface.tree.find_nearest(pt);real=BVHTree.FromPolygons(surface.points.tolist(),surface.faces.tolist(),all_triangles=True);hit=real.find_nearest(pt)
 rows.append({'clip':failure['clip'],'lod':failure['lod'],'time_s':failure['time_s'],'shared_depth_mm':failure['worst'],'rest_vertex':m.rest[idx].tolist(),'posed_vertex':points[idx].tolist(),'nearest_is_synthetic_cap':fi in surface.caps,'real_cloth_distance_mm':float(hit[3]*1000)})
(P/'review/round3/cloth_findings.json').write_text(json.dumps({'purpose':'Explain saved failures, not waive or replace shared gates. A folded hem is not planar; nearest synthetic caps may count legal boot exits. Actual cloth contact still requires inspection.','findings':rows},indent=2))
