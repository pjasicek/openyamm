"""Keep the covered neck skin and its rigid fitted control band together; freed bodies stay untouched."""
import bpy,sys,os,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
P=Path(__file__).resolve().parents[1];path=P/'work/addons_v2/equipped.blend';bpy.ops.wm.open_mainfile(filepath=str(path));r=bpy.data.objects['Rig'];b=bpy.data.objects['Kept'];r.animation_data.action=None
for p in r.pose.bones:p.matrix_basis.identity()
co=[v.co.copy() for v in b.data.vertices];pc=[a.value for a in b.data.attributes['piece'].data];grp=b.vertex_groups.get('Kept_Collar') or b.vertex_groups.new(name='Kept_Collar');changes=[]
for v in b.data.vertices:
 if pc[v.index]!=1:continue
 z=v.co.z;t=max(0,min(1,(z-1.405)/.025,(1.515-z)/.025))
 if t<=0:continue
 old={g.group:g.weight for g in v.groups}
 for i,w in old.items():b.vertex_groups[i].add([v.index],w*(1-t),'REPLACE')
 grp.add([v.index],t,'REPLACE');changes.append({'vertex':v.index,'amount':t,'position':list(v.co)})
# Leather and plate follow the shirt they cover, not the separately closed neck/chest skin under it.
fs=[p.vertices[:] for p in b.data.polygons if pc[p.vertices[0]]==0];tree=BVHTree.FromPolygons(co,fs);o=bpy.data.objects['hes_kept_plate'];o.vertex_groups.clear()
for g in b.vertex_groups:o.vertex_groups.new(name=g.name)
for v in o.data.vertices:
 h,n,i,d=tree.find_nearest(v.co);ids=fs[i];w=barycentric_transform(h,*[co[j] for j in ids],Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)));acc={}
 for j,f in zip(ids,w):
  for g in b.data.vertices[j].groups:acc[g.group]=acc.get(g.group,0)+max(0,f)*g.weight
 acc=sorted(acc.items(),key=lambda p:-p[1])[:8];total=sum(w for k,w in acc)
 for k,w in acc:
  if w>1e-8:o.vertex_groups[k].add([v.index],w/total,'REPLACE')
(P/'review/addons_v2/neck_band_weights.json').write_text(json.dumps({'scope':'collared male only; covered neck band with smooth transitions to original skin','carrier':'Kept_Collar (child of B_Neck)','vertices':changes},indent=2)+'\n');bpy.ops.wm.save_as_mainfile(filepath=str(path));print('NECK_BAND',len(changes),flush=True);sys.stdout.flush();sys.stderr.flush();os._exit(0)
