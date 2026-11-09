"""Keep each scapula and each half of the clavicle rigid while the shoulder girdle moves."""
import bpy,bmesh
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/pilot_feet.blend'))
body=bpy.data.objects['Body']; me=body.data
piece=me.attributes['piece']; parts=[]
for pid,side in [(30,'L'),(32,'R')]:
    ids=[v.index for v in me.vertices if piece.data[v.index].value==pid]
    for g in body.vertex_groups:g.remove(ids)
    body.vertex_groups[f'B_{side}_Clavicle'].add(ids,1,'REPLACE')
for side in 'LR':
    bm=bmesh.new(); bm.from_mesh(me); pl=bm.verts.layers.int['piece']
    bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[pl]!=12],context='VERTS')
    bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-6,
        plane_co=(-.0153,0,0),plane_no=(1,0,0),clear_inner=side=='L',clear_outer=side=='R')
    bmesh.ops.holes_fill(bm,edges=[e for e in bm.edges if e.is_boundary],sides=0)
    deform=bm.verts.layers.deform.verify(); group=body.vertex_groups[f'B_{side}_Clavicle'].index
    for v in bm.verts:v[deform].clear(); v[deform][group]=1; v[pl]=1120+(side=='R')
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    mesh=bpy.data.meshes.new('Clavicle'+side); bm.to_mesh(mesh); bm.free()
    ob=bpy.data.objects.new(mesh.name,mesh); bpy.context.collection.objects.link(ob)
    for g in body.vertex_groups:ob.vertex_groups.new(name=g.name)
    for m in me.materials:mesh.materials.append(m)
    parts.append(ob)
bm=bmesh.new();bm.from_mesh(me);pl=bm.verts.layers.int['piece']
bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[pl]==12],context='VERTS');bm.to_mesh(me);bm.free()
bpy.ops.object.select_all(action='DESELECT');body.select_set(True)
for ob in parts:ob.select_set(True)
bpy.context.view_layer.objects.active=body;bpy.ops.object.join()
assert all(abs(sum(g.weight for g in v.groups)-1)<1e-5 for v in body.data.vertices)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/pilot_shoulders.blend'))
