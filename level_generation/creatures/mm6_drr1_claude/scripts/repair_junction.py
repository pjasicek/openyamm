"""Close and relax the five-edge chest opening; preserve the rig, clips and existing UV corners."""
import bpy,bmesh,json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.geometry import barycentric_transform
P=Path(__file__).resolve().parents[1];O=P/'review/revision03';O.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_v3.blend'))
body=bpy.data.objects['Wyrm'];me=body.data;rig=bpy.data.objects['Wyrm_Rig']
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update()
original=np.array([v.co[:] for v in me.vertices]);old_uv=np.array([l.uv[:] for l in me.uv_layers.active.data])
bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();bm.faces.ensure_lookup_table()
uv=bm.loops.layers.uv.active;deform=bm.verts.layers.deform.active
boundary=[e for e in bm.edges if e.is_boundary and all(-.37<v.co.y<-.35 and .15<v.co.z<.17 for v in e.verts)]
assert len(boundary)==5
rim={v for e in boundary for v in e.verts};assert len(rim)==5
assert all(sum(v in e.verts for e in boundary)==2 for v in rim)
source=[(f,[v.co.copy() for v in f.verts],[Vector((*l[uv].uv,0)) for l in f.loops]) for f in bm.faces if any(v in rim for v in f.verts)]
patch=bmesh.ops.holes_fill(bm,edges=boundary,sides=5)['faces'];assert len(patch)==1
patch=bmesh.ops.triangulate(bm,faces=patch)['faces'];assert len(patch)==3
# Keep the repair local, with a fixed outer ring instead of smoothing the whole model.
strength={v:1.0 for v in rim}
for depth,factor in [(1,.65),(2,.25)]:
 for v in list(strength):
  for e in v.link_edges:
   other=e.other_vert(v)
   if other not in strength:strength[other]=factor
# Diffuse the abrupt shoulder/chest weight changes alongside the folded surface.
for _ in range(12):
 updates={}
 for v,falloff in strength.items():
  adjacent=[e.other_vert(v) for e in v.link_edges];alpha=.45*falloff
  co=sum((n.co for n in adjacent),Vector())/len(adjacent)
  keys={k for n in adjacent+[v] for k in n[deform].keys()}
  weights={k:(1-alpha)*v[deform].get(k,0)+alpha*sum(n[deform].get(k,0) for n in adjacent)/len(adjacent) for k in keys}
  updates[v]=(v.co.lerp(co,alpha),weights)
 for v,(co,weights) in updates.items():
  v.co=co;v[deform].clear()
  weights={k:w for k,w in sorted(weights.items(),key=lambda p:-p[1])[:8] if w>1e-6};total=sum(weights.values())
  for k,w in weights.items():v[deform][k]=w/total
bm.normal_update()
for f in patch:
 f.material_index=0;f.smooth=True
 center=f.calc_center_median()
 candidates=[s for s in source if s[0] not in patch and s[0].normal.dot(f.normal)>.3]
 src,co,tex=min(candidates,key=lambda s:(s[0].calc_center_median()-center).length)
 for l in f.loops:l[uv].uv=barycentric_transform(l.vert.co,*[v.co for v in src.verts],*tex).xy
assert all(e.is_manifold for e in boundary)
assert all(e.is_manifold for f in patch for e in f.edges)
changed=sorted(v.index for v in strength)
report={'revision':'03','repair':'Closed five-edge chest/foreleg opening and locally relaxed the folded surface and skin weights','added_triangles':3,'affected_vertices':len(changed),'max_vertex_move_m':max((v.co-Vector(original[v.index])).length for v in strength),'existing_uvs_unchanged':True,'clips_and_rig_unchanged':True}
bm.to_mesh(me);bm.free();me.update()
assert len(me.polygons)==14416
assert np.array_equal(old_uv,np.array([l.uv[:] for l in me.uv_layers.active.data])[:len(old_uv)])
assert all(abs(sum(g.weight for g in v.groups)-1)<1e-4 for v in me.vertices)
assert np.array_equal(original[np.setdiff1d(np.arange(len(original)),changed)],np.array([v.co[:] for v in me.vertices])[np.setdiff1d(np.arange(len(original)),changed)])
rig.animation_data.action=bpy.data.actions['Standing'];bpy.context.scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/anim_v4.blend'))
(O/'junction.json').write_text(json.dumps(report,indent=2)+'\n')
selection=json.loads((P/'review/reduction/selection.json').read_text());selection.update(blend='work/anim_v4.blend',selected_triangles=14416,junction_repair='review/revision03/junction.json');(P/'review/reduction/selection.json').write_text(json.dumps(selection,indent=2)+'\n')
print(json.dumps(report))
