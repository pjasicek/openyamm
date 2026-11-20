"""Close the female cap's visible front rim against the scalp, retaining its paid UVs and triangles."""
import bpy,sys,os,json,collections
from pathlib import Path
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/female/rig_uv.blend'));body=bpy.data.objects['Body'];me=body.data;pc=[a.value for a in me.attributes['piece'].data]
faces=[p.vertices[:] for p in me.polygons if pc[p.vertices[0]]==1];bvh=BVHTree.FromPolygons([v.co for v in me.vertices],faces,all_triangles=True)
edges=collections.Counter();adj=collections.defaultdict(set)
for p in me.polygons:
 if pc[p.vertices[0]]!=6:continue
 for i,a in enumerate(p.vertices):
  b=p.vertices[(i+1)%3];edges[tuple(sorted((a,b)))]+=1;adj[a].add(b);adj[b].add(a)
rim={i for e,n in edges.items() if n==1 for i in e};front={i for i in rim if me.vertices[i].co.y<-.015 and me.vertices[i].co.z>1.56}
print('RIM',len(rim),'FRONT',len(front),[(i,list(me.vertices[i].co)) for i in sorted(front)],flush=True)
assert len(front)>3
# The open front rim should meet the hair painted on the scalp; 0.5 mm offset prevents z-fighting.
changes={};distances=[]
for i in front:
 co=me.vertices[i].co;p,n,_,dist=bvh.find_nearest(co);delta=p+n*.0005-co;changes[i]=delta;distances.append(dist)
for i in {j for i in front for j in adj[i]}-front:
 ns=[changes[j] for j in adj[i] if j in front]
 if ns:changes[i]=sum(ns,ns[0]*0)/len(ns)*.45
for i,delta in changes.items():me.vertices[i].co+=delta
me.update();assert max(distances)<.035,max(distances)
r={'cause':'open hair-cap front edge stood away from scalp; flat albedo has no black band','rim_vertices':len(front),'feather_vertices':len(changes)-len(front),'max_original_gap_m':max(distances),'rim_offset_m':.0005,'topology_uv_weights_animations':'unchanged','moved_vertex_ids':sorted(changes)}
(P/'review/female/hairline_repair.json').write_text(json.dumps(r,indent=2)+'\n');bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/female/rig_uv_hairfixed.blend'))
print('HAIR',r,flush=True);sys.stdout.flush();sys.stderr.flush();os._exit(0)
