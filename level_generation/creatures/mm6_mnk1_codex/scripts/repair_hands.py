import bpy,bmesh,json,sys
import numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/step1.blend'))
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/step1_before_hands.blend'))
body=bpy.data.objects['Body'];me=body.data
bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();piece=bm.verts.layers.int['piece']
labels=json.loads((p/'work/finger_candidates_R.json').read_text());extra=[bm.verts[i] for i in labels['4']]
assert len(extra)==53 and all(v[piece]==3 for v in extra)
# Remove the forked sixth digit, close its small root and relax the scar.
neighbours={q for v in extra for e in v.link_edges for q in e.verts}-set(extra)
bmesh.ops.delete(bm,geom=extra,context='VERTS')
boundary=[e for e in bm.edges if e.is_boundary and all(v[piece]==3 for v in e.verts) and any(v in neighbours for v in e.verts)]
filled=bmesh.ops.holes_fill(bm,edges=boundary,sides=0)['faces']
scar={v for f in filled for v in f.verts}
for _ in range(3):bmesh.ops.smooth_vert(bm,verts=list(scar),factor=.25,use_axis_x=True,use_axis_y=True,use_axis_z=True)
# Replace the corrupted left hand with its corrected anatomical counterpart.
bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[piece]==2],context='VERTS')
right=[v for v in bm.verts if v[piece]==3];faces=[f for f in bm.faces if all(v[piece]==3 for v in f.verts)]
mirror={}
for v in right:
 co=tuple(v.co);q=bm.verts.new((-.012-co[0],co[1],co[2]));q[piece]=2;mirror[v]=q
for f in faces:
 nf=bm.faces.new([mirror[v] for v in reversed(f.verts)]);nf.material_index=f.material_index;nf.smooth=True
bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
co=np.array([tuple(v.co) for v in me.vertices]);me.attributes['orig_co'].data.foreach_set('vector',co.ravel())
pv=np.zeros(len(me.vertices),np.int32);me.attributes['piece'].data.foreach_get('value',pv)
uv=me.uv_layers.active
for f in me.polygons:
 if pv[f.vertices[0]] in (2,3):
  for li in f.loop_indices:uv.data[li].uv=(1.5/8,.5)
assert sum(pv==2)==sum(pv==3) and np.isfinite(co).all()
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/step1.blend'))
(p/'work/hand_repair.json').write_text(json.dumps({'removed_extra_digit_vertices':53,'root_cap_faces':len(filled),'left_hand':'mirrored corrected right about x=-0.006','vertices_each':int(sum(pv==3))},indent=2))
for old in ['finger_joints.json','fingers_fit.json']:
 (p/'work'/old).unlink(missing_ok=True)
common.workbench_clay(bpy.context.scene,textured=True)
for sd,x in [('R',-.52),('L',.51)]:common.render_views(str(p/'review'/f'hand_repaired_{sd}'),.99,.32,views=('front','back'),resolution=(800,800),target=(x,-.10))
