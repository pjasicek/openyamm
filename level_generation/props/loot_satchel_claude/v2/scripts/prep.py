"""Prepare the shared v2 sack (one Meshy Smart Topology mesh for all six tiers) for the retextures.
Usage: blender --background --python v2/scripts/prep.py
Reads v2/meshy/st/model_urls_glb.glb. Joins the parts, drops tiny floaters, turns it by YAW_DEG so the clasp faces -Y
(the glTF/engine front), scales it to a 1 m plan width (finish.py scales each tier to its own width), centres the plan
bounds on the origin, sets the lowest point on the ground (z = 0), smooths a copy and collapse-decimates it to
LOD0_TRIANGLES, makes a packed Smart UV unwrap, and writes work/shared.blend (LOD0 plus the full-detail High object)
and work/high_upload.glb (High, the retexture input for all six tiers; Meshy makes its UVs)."""
import bpy, bmesh, sys, os, math
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tiers import ROOT, LOD0_TRIANGLES

CFG = {'width': 1.0, 'lod0': LOD0_TRIANGLES, 'yaw_deg': float(os.environ.get('YAW_DEG', 0))}
for key in ('smooth', 'smooth_angle'):
    if os.environ.get('PREP_' + key.upper()):
        CFG[key] = float(os.environ['PREP_' + key.upper()])
WORK = os.path.join(ROOT, 'work')

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT, 'meshy', 'st', 'model_urls_glb.glb'))
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
bpy.ops.object.select_all(action='DESELECT')
for o in meshes:
    o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
if len(meshes) > 1:
    bpy.ops.object.join()
obj = bpy.context.view_layer.objects.active
obj.name = 'LootSatchel'
bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
for o in list(bpy.context.scene.objects):
    if o is not obj:
        bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
obj.rotation_mode = 'XYZ'
obj.rotation_euler = (0, 0, math.radians(CFG.get('yaw_deg', 0)))
bpy.ops.object.transform_apply(rotation=True)

# Drop floaters: connected pieces with very few faces.
bm = bmesh.new(); bm.from_mesh(obj.data)
bm.faces.ensure_lookup_table()
seen = set(); drop = []
for f in bm.faces:
    if f.index in seen:
        continue
    stack = [f]; island = []
    seen.add(f.index)
    while stack:
        g = stack.pop(); island.append(g)
        for e in g.edges:
            for h in e.link_faces:
                if h.index not in seen:
                    seen.add(h.index); stack.append(h)
    if len(island) < CFG.get('min_island_faces', 12):
        drop.extend(island)
bmesh.ops.delete(bm, geom=drop, context='FACES')
bm.to_mesh(obj.data); bm.free()

co = [obj.matrix_world @ v.co for v in obj.data.vertices]
lo = Vector((min(c.x for c in co), min(c.y for c in co), min(c.z for c in co)))
hi = Vector((max(c.x for c in co), max(c.y for c in co), max(c.z for c in co)))
s = CFG['width'] / max(hi.x - lo.x, hi.y - lo.y)
obj.scale = (s, s, s)
bpy.ops.object.transform_apply(scale=True)
lo *= s; hi *= s
obj.location = (-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z)
bpy.ops.object.transform_apply(location=True)

bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.remove_doubles(threshold=0.0005)
bpy.ops.mesh.customdata_custom_splitnormals_clear()
bpy.ops.mesh.quads_convert_to_tris()
bpy.ops.mesh.normals_make_consistent(inside=False)      # Smart Topology returns some inward-wound patches
bpy.ops.object.mode_set(mode='OBJECT')
tris = len(obj.data.polygons)
# High: the full Smart Topology surface; it goes to the retexture and is the texture source for LOD0.
high = obj.copy(); high.data = obj.data.copy(); bpy.context.scene.collection.objects.link(high)
high.name = 'LootSatchel_High'
bpy.context.view_layer.objects.active = obj

if CFG.get('smooth', 3):
    # Soften stitch-scale detail first: collapse then spends its budget on the silhouette and big folds.
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.vertices_smooth(factor=0.5, repeat=int(CFG.get('smooth', 3)))
    bpy.ops.object.mode_set(mode='OBJECT')
mod = obj.modifiers.new('dec', 'DECIMATE'); mod.decimate_type = 'COLLAPSE'
mod.ratio = CFG['lod0'] / len(obj.data.polygons); mod.use_collapse_triangulate = True
bpy.ops.object.modifier_apply(modifier=mod.name)
# Re-fit after smoothing and decimation: exact plan width, plan centre on the origin, lowest point on the ground.
# The high mesh takes the same transform so the texture transfer lines up.
co = [v.co.copy() for v in obj.data.vertices]
lo = Vector((min(c.x for c in co), min(c.y for c in co), min(c.z for c in co)))
hi = Vector((max(c.x for c in co), max(c.y for c in co), max(c.z for c in co)))
k = CFG['width'] / max(hi.x - lo.x, hi.y - lo.y)
for o in (obj, high):
    for v in o.data.vertices:
        v.co = Vector(((v.co.x - (lo.x + hi.x) / 2) * k, (v.co.y - (lo.y + hi.y) / 2) * k, (v.co.z - lo.z) * k))



def orient_outward(o, rays=32):
    """Flip LOD0 faces whose front side cannot see out while their back side can: collapse on the thin, folded
    leather leaves some faces wound inward, and those would render as back faces."""
    from mathutils.bvhtree import BVHTree
    golden = math.pi * (3 - math.sqrt(5))
    dirs = [Vector((math.cos(golden * i) * math.sqrt(1 - z * z), math.sin(golden * i) * math.sqrt(1 - z * z), z))
            for i, z in ((i, 1 - 2 * (i + 0.5) / rays) for i in range(rays))]
    bvh = BVHTree.FromObject(o, bpy.context.evaluated_depsgraph_get())
    eps = 1e-4 * o.dimensions.length
    flip = []
    for poly in o.data.polygons:
        escape = [0, 0]
        for d in dirs:
            side = d.dot(poly.normal)
            if abs(side) > 0.1 and bvh.ray_cast(poly.center + d * eps, d)[0] is None:
                escape[side < 0] += 1
        if escape[1] > escape[0]:
            flip.append(poly.index)
    bm = bmesh.new(); bm.from_mesh(o.data); bm.faces.ensure_lookup_table()
    bmesh.ops.reverse_faces(bm, faces=[bm.faces[i] for i in flip]); bm.to_mesh(o.data); bm.free()
    print('PREP faces turned outward', len(flip), 'of', len(o.data.polygons))


orient_outward(obj)
for o in (obj, high):
    for uv in list(o.data.uv_layers):
        o.data.uv_layers.remove(uv)
obj.data.uv_layers.new(name='UVMap')
bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True); bpy.context.view_layer.objects.active = obj
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.003, area_weight=0.0)
bpy.ops.uv.select_all(action='SELECT')
bpy.ops.uv.pack_islands(margin=0.004, rotate=True, shape_method='CONCAVE')
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.shade_smooth_by_angle(angle=math.radians(CFG.get('smooth_angle', 65)))
mat = bpy.data.materials.new('LootSatchel'); mat.use_nodes = True
for o in (obj, high):
    o.data.materials.clear(); o.data.materials.append(mat)
bpy.context.view_layer.objects.active = high
bpy.ops.object.select_all(action='DESELECT'); high.select_set(True)
bpy.ops.object.shade_smooth()

print('PREP tris', tris, '->', len(obj.data.polygons), 'dims', [round(d, 3) for d in obj.dimensions])
high.hide_render = True
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'shared.blend'))
bpy.ops.export_scene.gltf(filepath=os.path.join(WORK, 'high_upload.glb'), use_selection=True,
                          export_format='GLB', export_yup=True, export_animations=False, export_skins=False,
                          export_morph=False, export_materials='PLACEHOLDER', export_extras=False)
