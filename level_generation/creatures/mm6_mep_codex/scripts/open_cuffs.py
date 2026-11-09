import bpy,bmesh,json,numpy as np
from pathlib import Path
from mathutils import Vector,kdtree
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/textured.blend'));b=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];me=b.data;r.animation_data.action=None
for pb in r.pose.bones:pb.matrix_basis.identity()
pv=np.array([x.value for x in me.attributes['piece'].data]);axes={s:(r.data.bones[f'B_{s}_Forearm'].head_local.copy(),(r.data.bones[f'B_{s}_Hand'].head_local-r.data.bones[f'B_{s}_Forearm'].head_local).normalized()) for s in 'LR'};remove=[]
for f in me.polygons:
 if not all(pv[i]==0 for i in f.vertices):continue
 pts=[me.vertices[i].co for i in f.vertices];c=sum(pts,Vector())/len(pts)
 if abs(c.x)<.265 or c.z<1.01:continue
 sd='L' if c.x>0 else 'R';el,axis=axes[sd];t=[(v-el).dot(axis) for v in pts];rad=[((v-el)-axis*(v-el).dot(axis)).length for v in pts]
 if min(t)>-.06 and max(t)<.13 and np.mean(rad)<.036 and min(rad)<.028 and abs(f.normal.dot(axis))>.25:remove.append(f.index)
bm=bmesh.new();bm.from_mesh(me);bm.faces.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.faces[i] for i in remove],context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(me);bm.free();pv=np.array([x.value for x in me.attributes['piece'].data])
for sd,pi in [('L',2),('R',3)]:
 el,axis=axes[sd];ids=[v.index for v in me.vertices if pv[v.index]==pi];tree=kdtree.KDTree(len(ids))
 for i in ids:tree.insert(me.vertices[i].co,i)
 tree.balance()
 for v in me.vertices:
  if pv[v.index]!=0 or abs(v.co.x)<.25 or (v.co.x>0)!=(sd=='L') or v.co.z<1.0:continue
  t=(v.co-el).dot(axis)
  if t<-.035:continue
  _,i,d=tree.find(v.co);blend=min(1,max(0,(t+.035)/.05));old={g.group:g.weight for g in v.groups};src={g.group:g.weight for g in me.vertices[i].groups};merged={k:old.get(k,0)*(1-blend)+src.get(k,0)*blend for k in old.keys()|src.keys()}
  for g in list(v.groups):b.vertex_groups[g.group].remove([v.index])
  for k,w in merged.items():
   if w>.00001:b.vertex_groups[k].add([v.index],w,'REPLACE')
bpy.context.view_layer.objects.active=b;bpy.ops.object.vertex_group_limit_total(limit=8);bpy.ops.object.vertex_group_normalize_all(lock_active=False);me.update();bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/textured.blend'));print('OPEN_CUFFS',len(remove),flush=True);(p/'review/cuff_openings.json').write_text(json.dumps({'removed_closed_cap_triangles':len(remove),'reason':'Native rolled cuffs have openings. Meshy had transverse triangles across the forearm tunnel.','remaining_uvs_and_visible_outer_rim':'preserved'},indent=2))
