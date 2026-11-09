import bpy,bmesh,json,shutil
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/step1.blend'));ob=bpy.data.objects['Body'];me=ob.data
shutil.copy2(P/'work/step1.blend',P/'work/step1_six_digits.blend')
ids=set()
for side in ['R','L']:
 d=json.loads((P/f'work/finger_candidates_{side}.json').read_text());i=min(range(len(d['centres'])),key=lambda i:d['centres'][i][1]);assert d['centres'][i][1]<-.07;ids.update(d['fingers'][i])
bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();bm.edges.ensure_lookup_table();old_boundary={e for e in bm.edges if e.is_boundary};gone=[bm.verts[i] for i in ids]
bmesh.ops.delete(bm,geom=gone,context='VERTS');new_boundary=[e for e in bm.edges if e.is_boundary and e not in old_boundary];assert 6<len(new_boundary)<70,len(new_boundary)
res=bmesh.ops.holes_fill(bm,edges=new_boundary,sides=0);new_faces=res['faces'];assert new_faces
bmesh.ops.triangulate(bm,faces=new_faces);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();me.update()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/step1.blend'));(P/'work/finger_correction.json').write_text(json.dumps({'removed_vertices':len(ids),'boundary_edges_closed':len(new_boundary),'source':'work/step1_six_digits.blend','reason':'Meshy duplicated the front index branch on each hand. Delete only disconnected distal branch vertices and close its root; refit fingers afterward.'},indent=2))
print('Removed extra finger branches',len(ids),'verts, cap edges',len(new_boundary),flush=True)
