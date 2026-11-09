"""Inspect the immutable Meshy return; oriented components and CPU-only modelling review."""
import hashlib
import json
import math
import os
import sys
from pathlib import Path

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P.with_name("hes_turrets_claude") / "scripts"))
from turret_common import component_labels

RAW = P / "meshy/ion_cannon_geometry_v1/model_urls_glb.glb"
assert hashlib.sha256(RAW.read_bytes()).hexdigest() == "98b798a4f2d4daf4f71a049558a1ee3bc7ad43687e49d7f7bc1d783105977abd"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(RAW))
obj = next(o for o in bpy.context.scene.objects if o.type == "MESH")
bpy.context.view_layer.objects.active = obj
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
obj.data.transform(Matrix.Rotation(-math.pi / 2, 4, "Z"))
obj.name = obj.data.name = "IonCannon"
bm = bmesh.new(); bm.from_mesh(obj.data)
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
labels = component_labels(bm)
rows = []
for c in range(int(labels.max()) + 1):
    verts = [v for v in bm.verts if labels[v.index] == c]
    faces = [f for f in bm.faces if labels[f.verts[0].index] == c]
    co = np.array([v.co[:] for v in verts])
    edge_counts = [len(e.link_faces) for e in {e for f in faces for e in f.edges}]
    rows.append({"id": c, "vertices": len(verts), "tris": sum(len(f.verts)-2 for f in faces),
                 "lo": co.min(0).tolist(), "hi": co.max(0).tolist(), "centre": co.mean(0).tolist(),
                 "boundary_edges": sum(n==1 for n in edge_counts), "nonmanifold_edges": sum(n>2 for n in edge_counts)})
layer = bm.faces.layers.int.new("source_component")
for f in bm.faces:
    f[layer] = int(labels[f.verts[0].index])
bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
bm.to_mesh(obj.data); bm.free()
for f in obj.data.polygons: f.use_smooth = True
(P / "review/geometry").mkdir(parents=True, exist_ok=True)
(P / "work").mkdir(exist_ok=True)
(P / "review/geometry/raw_components.json").write_text(json.dumps(rows, indent=2)+"\n")
bpy.ops.wm.save_as_mainfile(filepath=str(P / "work/ion_cannon_oriented_raw.blend"))
np.savez(P / "work/raw_triangles.npz", co=np.array([v.co[:] for v in obj.data.vertices]),
         faces=np.array([list(f.vertices) for f in obj.data.polygons]),
         components=np.array([x.value for x in obj.data.attributes["source_component"].data]))
mat = bpy.data.materials.new("Clay"); mat.use_nodes=True
mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=(0.52,0.54,0.58,1)
mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value=.8
obj.data.materials.clear(); obj.data.materials.append(mat)
scene=bpy.context.scene; scene.render.engine="CYCLES"; scene.cycles.device="CPU"; scene.cycles.samples=16
scene.cycles.use_denoising=True
scene.render.resolution_x=1200; scene.render.resolution_y=800; scene.render.resolution_percentage=100
scene.render.film_transparent=True
scene.world=bpy.data.worlds.new("World");scene.world.use_nodes=True
scene.world.node_tree.nodes["Background"].inputs["Color"].default_value=(.25,.25,.25,1)
scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value=.5
for name,power,angles in [("Key",2.5,(25,0,-35)),("Fill",1.2,(65,0,150))]:
 light=bpy.data.objects.new(name,bpy.data.lights.new(name,"SUN"));scene.collection.objects.link(light)
 light.data.energy=power;light.rotation_euler=[math.radians(v) for v in angles]
cam=bpy.data.objects.new("Camera",bpy.data.cameras.new("Camera"));scene.collection.objects.link(cam);scene.camera=cam
cam.data.type="ORTHO";cam.data.ortho_scale=1.15
co=np.array([v.co[:] for v in obj.data.vertices]);centre=Vector((co.min(0)+co.max(0))/2)
from bpy_extras.object_utils import world_to_camera_view
for view,(az,el) in {"quarter":(-55,15),"pod_side":(-90,0),"opposite":(90,0),"front":(0,0),"back":(180,0),"top":(0,89)}.items():
 a,e=map(math.radians,(az,el));d=Vector((math.sin(a)*math.cos(e),-math.cos(a)*math.cos(e),math.sin(e)))
 cam.location=centre+d*3;cam.rotation_euler=(-d).to_track_quat("-Z","Y").to_euler()
 scene.render.filepath=str(P / "review/geometry" / f"raw_{view}.png")
 bpy.ops.render.render(write_still=True)
 marks=[]
 for r in rows:
  if r["tris"]>=20:
   v=world_to_camera_view(scene,cam,Vector(r["centre"]));marks.append([r["id"],v.x,1-v.y])
 (P / "review/geometry" / f"raw_{view}_marks.json").write_text(json.dumps(marks))
print("RAW",len(rows),"components",sum(r["tris"] for r in rows),"triangles",flush=True)
# Background Blender on this host can hang during audio shutdown; all outputs are flushed.
sys.stdout.flush();sys.stderr.flush()
os._exit(0)

