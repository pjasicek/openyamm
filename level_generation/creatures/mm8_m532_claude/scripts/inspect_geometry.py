"""Inspect the immutable Meshy return in isolated Blender; save the grounded working copy and measured views."""
from pathlib import Path
import bpy, bmesh, json
import numpy as np
from mathutils import Vector
P = Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(P / "meshy/body_geometry_v2/model_urls_glb.glb"))
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
assert meshes, "Missing Meshy geometry"
for o in bpy.context.scene.objects:
    o.select_set(o in meshes)
bpy.context.view_layer.objects.active = meshes[0]
bpy.ops.object.join()
o = bpy.context.object
o.name = o.data.name = "Centaur"
o.parent = None
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
co = np.array([tuple(v.co) for v in o.data.vertices])
# Meshy uses a normalized box; keep its proportions and set an explicit 2.6 m standing height.
scale = 2.6 / np.ptp(co[:, 2])
co *= scale
co[:, 2] -= co[:, 2].min()
co[:, 0] -= (co[:, 0].min() + co[:, 0].max()) / 2
for v, c in zip(o.data.vertices, co):
    v.co = c
bm = bmesh.new(); bm.from_mesh(o.data)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
# Meshy left two tangled skin patches (abdomen and right elbow); replace only their immediate face rings.
bm.verts.ensure_lookup_table()
seen=set();components=[]
for seed in bm.verts:
    if seed in seen: continue
    stack=[seed];part=set()
    while stack:
        q=stack.pop()
        if q in seen: continue
        seen.add(q);part.add(q);stack.extend(e.other_vert(q) for e in q.link_edges)
    components.append(part)
main=max(components,key=len)
bad=[e for e in bm.edges if e.is_boundary and all(x in main for x in e.verts)]
if bad:
    patch={f for e in bad for v in e.verts for f in v.link_faces}
    patch|={f for p in list(patch) for v in p.verts for f in v.link_faces}
    border=[e for e in bm.edges if sum(f in patch for f in e.link_faces)==1 and len(e.link_faces)==2]
    bmesh.ops.delete(bm,geom=list(patch),context='FACES_ONLY')
    bmesh.ops.delete(bm,geom=[e for e in bm.edges if not e.link_faces],context='EDGES')
    bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_edges],context='VERTS')
    fill=bmesh.ops.holes_fill(bm,edges=border,sides=0)['faces']
    assert fill,'Local skin repair failed'
    bmesh.ops.triangulate(bm,faces=fill)
    print('Rebuilt damaged skin patches:',len(fill))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
report = {"vertices": len(bm.verts), "triangles": sum(len(f.verts)-2 for f in bm.faces),
          "boundary_edges": sum(e.is_boundary for e in bm.edges), "nonmanifold_edges": sum(not e.is_manifold for e in bm.edges)}
bm.to_mesh(o.data); bm.free()
for face in o.data.polygons:
    face.use_smooth = True
co = np.array([tuple(v.co) for v in o.data.vertices]);lo=co.min(0);hi=co.max(0)
report.update(bounds=[lo.tolist(),hi.tolist()],scale_from_meshy=float(scale))
np.savez(P/'work/geometry_v1.npz', vertices=co, faces=np.array([tuple(f.vertices) for f in o.data.polygons]))
(P/'work/geometry_report.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/geometry_v1.blend'))
sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH'
sh=sc.display.shading;sh.light='STUDIO';sh.color_type='SINGLE';sh.single_color=(.65,.64,.60)
sh.show_cavity=True;sh.show_shadows=False;sh.background_type='WORLD'
sc.world=bpy.data.worlds.new('ReviewWorld');sc.world.color=(.18,.18,.18)
sc.render.resolution_x=900;sc.render.resolution_y=900;sc.render.resolution_percentage=100
cam=bpy.data.objects.new('ReviewCamera',bpy.data.cameras.new('ReviewCamera'));sc.collection.objects.link(cam);sc.camera=cam
cam.data.type='ORTHO';center=Vector((lo+hi)/2);cam.data.ortho_scale=float(max(hi-lo)*1.15)
views={'front':(0,-7,1.5),'side':(-7,0,1.5),'back':(0,7,1.5),'quarter':(-6,-7,3)}
for name,pos in views.items():
    cam.location=Vector(pos);cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=str(P/'review'/f'geometry_{name}.png');bpy.ops.render.render(write_still=True)
print(json.dumps(report))
