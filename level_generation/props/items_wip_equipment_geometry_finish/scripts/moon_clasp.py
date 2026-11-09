"""Add the missing physical brooch while preserving the prior baked cloth body and its exact UVs."""
import math,sys,hashlib,json
from pathlib import Path
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P/'scripts'))
from repair_shapes import mesh,join
from repair_geometry import activate
bpy.ops.wm.read_factory_settings(use_empty=True)
source=P/'references/candidate_exports/equipment_7item348_export.glb'
bpy.ops.import_scene.gltf(filepath=str(source))
body=next(o for o in bpy.context.scene.objects if o.type=='MESH')
activate(body);bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
original=[v.co.copy() for v in body.data.vertices]
original_uv=[uv.uv.copy() for uv in body.data.uv_layers.active.data]
bvh=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())
hit,normal,_,_=bvh.ray_cast(Vector((.17,.17,2)),Vector((0,0,-1)))
assert hit is not None
if normal.z<0:normal=-normal
normal=(Vector((0,0,1))*.85+normal*.15).normalized()
# A closed curved strip avoids the self-intersections caused by triangulating a concave ngon.
n=25;points=[]
for radius,offset,start,sweep in [(.13,0,60,240),((.13**2-.065**2)**.5,.065,90,180)]:
    for i in range(n):
        angle=math.radians(start+sweep*i/(n-1))
        points.append((offset+radius*math.cos(angle),radius*math.sin(angle)))
vertices=[(x,y,z) for z in [0,.018] for x,y in points];faces=[]
for i in range(n-1):
    j=i+1
    faces.extend([(i,j,n+j,n+i),(2*n+i,3*n+i,3*n+j,2*n+j),
                  (i,2*n+i,2*n+j,j),(n+i,n+j,3*n+j,3*n+i)])
faces.extend([(0,n,3*n,2*n),(n-1,3*n-1,4*n-1,2*n-1)])
clasp=mesh('physical_gold_crescent',vertices,faces)
rotation=Vector((0,0,1)).rotation_difference(normal)
for v in clasp.data.vertices:v.co=rotation@v.co+hit+normal*.002
# Seat the nearly horizontal brooch against the highest supporting cloth fold.
lift=0
for vertex in list(clasp.data.vertices)[:2*n]:
    point=vertex.co
    surface=bvh.ray_cast(Vector((point.x,point.y,2)),Vector((0,0,-1)))[0]
    if surface is not None:lift=max(lift,surface.z+.002-point.z)
for vertex in clasp.data.vertices:vertex.co.z+=lift
activate(clasp)
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(island_margin=.01);bpy.ops.object.mode_set(mode='OBJECT')
material=bpy.data.materials.new('solid_gold_crescent');material.use_nodes=True
shader=material.node_tree.nodes.get('Principled BSDF');shader.inputs['Base Color'].default_value=(.83,.55,.12,1)
shader.inputs['Metallic'].default_value=1;shader.inputs['Roughness'].default_value=.35
clasp.data.materials.clear();clasp.data.materials.append(material)
assert all((v.co-before).length<1e-9 for v,before in zip(body.data.vertices,original))
assert all((uv.uv-before).length<1e-9 for uv,before in zip(body.data.uv_layers.active.data,original_uv))
for image in bpy.data.images:
    if image.source=='FILE':image.pack()
obj=join([body,clasp]);obj.name='equipment_7item348'
obj.data.calc_loop_triangles();assert len(obj.data.loop_triangles)<=3500
path=P/'work/codex_tex/geometryfinish_7item348_export.glb'
activate(obj)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/codex_tex/geometryfinish_7item348_pbr.blend'))
bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True)
(P/'receipts/moon_body_registration.json').write_text(json.dumps(dict(source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),preserved_body_vertices=len(original),preserved_uv_loops=len(original_uv),body_geometry_and_uv_unchanged=True,method='Prior painted PBR body retained without reprojecting or resampling. Only new closed crescent geometry/material added. Gold uses physical constant metal/roughness; cloth retains all three embedded maps.'),indent=2)+'\n')
