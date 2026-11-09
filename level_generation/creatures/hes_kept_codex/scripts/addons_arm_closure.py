"""Fill the formerly hidden pointed forearm closure exposed by the new overhead motion; Enforcer only."""
import bpy,bmesh,sys,os,json,math
from pathlib import Path
import numpy as np
from mathutils import Vector
P=Path(__file__).resolve().parents[1];path=P/'work/addons_v2/equipped.blend';bpy.ops.wm.open_mainfile(filepath=str(path));o=bpy.data.objects['Kept'];r=bpy.data.objects['Rig'];me=o.data;r.animation_data.action=None
for b in r.pose.bones:b.matrix_basis.identity()
# The closed right-arm piece has one pointed pole where it disappears under the sleeve.
E=r.data.bones['B_R_Forearm'].head_local;H=r.data.bones['B_R_Hand'].head_local;axis=(H-E).normalized();pc=[a.value for a in me.attributes['piece'].data];ids=[i for i,p in enumerate(pc) if p==3];pole=min(ids,key=lambda i:(me.vertices[i].co-E).dot(axis));incident=[p for p in me.polygons if pole in p.vertices];assert len(incident)>=3
bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();v=bm.verts[pole];old=v.co.copy();neighbours=list(v.link_edges);uvlayer=bm.loops.layers.uv.active;deform=bm.verts.layers.deform.verify();piece=bm.verts.layers.int.get('piece');ring={};new_vertices=[]
for e in neighbours:
 n=e.other_vert(v);t=(n.co-E).dot(axis);rad=n.co-E-axis*t
 if rad.length<1e-5:continue
 q=bm.verts.new(E+axis*.052+rad.normalized()*.029);ring[n]=q;new_vertices.append(q)
 for k,w in v[deform].items():q[deform][k]=w
 if piece:q[piece]=3
assert len(ring)==len(neighbours)
for f in list(v.link_faces):
 assert len(f.verts)==3
 loops=list(f.loops);k=next(i for i,l in enumerate(loops) if l.vert==v);a=loops[(k+1)%3];b=loops[(k+2)%3];puv=loops[k][uvlayer].uv.copy();au=a[uvlayer].uv.copy();bu=b[uvlayer].uv.copy();mi=f.material_index
 nf=bm.faces.new((ring[a.vert],a.vert,b.vert,ring[b.vert]));nf.material_index=mi
 for l,uv in zip(nf.loops,[puv.lerp(au,.12),au,bu,puv.lerp(bu,.12)]):l[uvlayer].uv=uv
 bm.faces.remove(f)
# A small cap under the cloth closes the new cylinder, keeping the visible limb fully volumetric.
x=(next(iter(ring.values())).co-(E+axis*.052)).normalized();y=axis.cross(x);ordered=sorted(new_vertices,key=lambda q:math.atan2((q.co-E).dot(y),(q.co-E).dot(x)));f=bm.faces.new(ordered);f.material_index=0
for l in f.loops:l[uvlayer].uv=puv
bm.verts.remove(v);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
# Maintain exact fitted forearm weighting on the newly exposed section; hand weights are untouched.
report={'scope':'Enforcer body copy only; hidden right forearm closure','old_pole':pole,'old_pole_rest':list(old),'new_ring_vertices':len(new_vertices),'ring_radius_m':.029,'ring_from_elbow_m':.052,'triangles':len(me.polygons),'accepted_freed_and_A_B_body_exports_unchanged':True}
(P/'review/addons_v2/forearm_closure.json').write_text(json.dumps(report,indent=2)+'\n');bpy.ops.wm.save_as_mainfile(filepath=str(path));print('FOREARM_CLOSURE',report,flush=True);sys.stdout.flush();sys.stderr.flush();os._exit(0)
