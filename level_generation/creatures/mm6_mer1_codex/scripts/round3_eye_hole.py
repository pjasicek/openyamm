import bpy,bmesh,sys,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common,reduction_common as C
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round3/master.blend1'));C.reset();o=bpy.data.objects['Body'];bm=bmesh.new();bm.from_mesh(o.data);pv=bm.verts.layers.int['piece'];uv=bm.loops.layers.uv.active
edges=[e for e in bm.edges if e.is_boundary and all(v[pv]==0 and -.075<v.co.x<-.015 and 1.54<v.co.z<1.60 and v.co.y<.015 for v in e.verts)];verts={v for e in edges for v in e.verts};saved={v:next(l[uv].uv.copy() for l in v.link_loops if l.face.material_index==1)for v in verts}
touch=set(verts)
for _ in range(100):
 new={e.other_vert(v)for v in touch for e in v.link_edges if e.is_boundary}
 if new<=touch:break
 touch|=new
edges=[e for e in bm.edges if e.is_boundary and all(v in touch for v in e.verts)];print('HOLE',len(edges),[list(v.co)for v in touch],flush=True)
saved={v:next(l[uv].uv.copy()for l in v.link_loops if l.face.material_index==1)for v in touch}
print('HOLEFACES',[(f.index,[v.index for v in f.verts],list(f.normal))for f in {f for v in touch for f in v.link_faces}],flush=True)
order=[edges[0].verts[0],edges[0].verts[1]]
while len(order)<len(touch):
 order.append(next(e.other_vert(order[-1])for e in order[-1].link_edges if e in edges and e.other_vert(order[-1])not in order))
faces=[bm.faces.new(order)]
for f in faces:
 f.material_index=1;f.smooth=True
 for l in f.loops:l[uv].uv=saved[l.vert]
bmesh.ops.triangulate(bm,faces=faces);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round3/master.blend'));C.activate('Standing');common.workbench_clay(bpy.context.scene,True);bpy.context.scene.display.shading.show_specular_highlight=False;common.render_views(str(P/'review/round3/eye_closed'),1.52,.43,views=('front','left','three_quarter'),resolution=(800,800));(P/'review/round3/eye_hole_repair.json').write_text(json.dumps({'accidental_upper_eyelid_hole_boundary_edges':len(edges),'closed_faces':len(faces),'method':'Fill the isolated five-edge upper-eyelid hole; retained original eyelid positions. Head UVs only, no body projection.'}))
