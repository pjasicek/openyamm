"""Retain the reference's long front bone segments and fit shoulder leather closely over the shirt."""
import bpy,sys,os,json,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];path=P/'work/addons_v2/equipped.blend';bpy.ops.wm.open_mainfile(filepath=str(path));r=bpy.data.objects['Rig'];body=bpy.data.objects['Kept'];r.animation_data.action=None
for p in r.pose.bones:p.matrix_basis.identity()
def components(o):
 adj={v.index:set()for v in o.data.vertices}
 for e in o.data.edges:a,b=e.vertices;adj[a].add(b);adj[b].add(a)
 unseen=set(adj);out=[]
 while unseen:
  ids={unseen.pop()};todo=list(ids)
  while todo:
   for j in adj[todo.pop()]-ids:ids.add(j);todo.append(j)
  unseen-=ids;out.append(ids)
 return out
with bpy.data.libraries.load(str(P/'work/addons_v2/raw_props.blend'),link=False) as (src,dst):dst.objects=['hes_kept_collar']
raw=dst.objects[0];collar=bpy.data.objects['hes_kept_collar'];assert [p.vertices[:]for p in raw.data.polygons]==[p.vertices[:]for p in collar.data.polygons];restored=[]
for ids in components(raw):
 if len(ids)!=35 or sum(raw.data.vertices[i].co.y for i in ids)/len(ids)>=.034:continue
 for i in ids:collar.data.vertices[i].co=raw.data.vertices[i].co
 restored.append(len(ids))
assert len(restored)==6,restored
bpy.data.objects.remove(raw,do_unlink=True)
pc=[v.value for v in body.data.attributes['piece'].data];tree=BVHTree.FromPolygons([v.co for v in body.data.vertices],[p.vertices[:]for p in body.data.polygons if pc[p.vertices[0]]==0]);o=bpy.data.objects['hes_kept_plate'];o.data.update();old=[v.co.copy()for v in o.data.vertices];fitted=[]
for ids in components(o):
 zs=[old[i].z for i in ids]
 if min(zs)<1.30 or max(zs)<1.39:continue
 for i in ids:
  v=o.data.vertices[i];h,n,ix,d=tree.find_nearest(old[i]);j=min(ids-{i},key=lambda j:(old[i]-old[j]).length);diff=old[i]-old[j];outer=diff.dot(n)>0 if diff.length<.006 and abs(diff.dot(n))>.001 else v.normal.dot(n)>0;v.co=h+n*(.006 if outer else .002)
 fitted.append(len(ids))
assert len(fitted)==2,fitted
bpy.ops.wm.save_as_mainfile(filepath=str(path));(P/'review/addons_v2/final_look_fit.json').write_text(json.dumps({'front_bone_segments_restored':len(restored),'fitted_shoulder_strap_vertices':fitted,'inner_outer_cloth_gap_m':[.002,.006]},indent=2)+'\n');sys.stdout.flush();sys.stderr.flush();os._exit(0)
