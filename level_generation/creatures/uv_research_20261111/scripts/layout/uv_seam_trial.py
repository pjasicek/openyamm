"""Hidden-seam trial (candidate 2): per-face camera visibility, then uv_atlas_seam.unwrap with the chosen options, seam
metrics by visibility, a neutral static upload GLB (as the production uv_atlas_v8.py writes it), a skinned measurement
GLB with a 2K placeholder texture for texture_quality.py, and an npz for renders.

Run: tools/run_creature_blender.sh level_generation/creatures/uv_research_20261111/scripts/layout/uv_seam_trial.py \
       <source .blend | .glb> <out dir> <name> mesh=<Body> rig=<MM9_Rig> head=<g1,g2,...> head_factor=1.8 \
       [mode=measure] [any uv_atlas_seam.unwrap option=value]
mode=measure only measures the mesh's current UVs (the production layout) and writes the same outputs.
mode=export writes <name>_mesh.npz (pos, tri, skin weights, vis) of the prepared mesh for partuv_run.py and stops;
charts_npz=<partuv_t*.npz> then starts the unwrap from those charts (same face order), packer=none leaves them
unpacked for sparrow_pack.py (combined-layout study, ../../combo/).
A .glb source is imported (installed creatures): its armature goes to rest, `mesh` names the LOD0 mesh object.
"""
import json
import math
import os
import sys
import time

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import uv_atlas_seam  # noqa: E402

argv = sys.argv[sys.argv.index('--') + 1:]
SRC, OUT, NAME = argv[:3]
SRC, OUT = os.path.abspath(SRC), os.path.abspath(OUT)   # relative paths break the measure GLB's image
opts = dict(a.split('=', 1) for a in argv[3:])


def value(v):
    for cast in (int, float):
        try:
            return cast(v)
        except ValueError:
            pass
    return {'True': True, 'False': False}.get(v, v)


MESH = opts.pop('mesh', 'Body')
RIG = opts.pop('rig', None)
HEAD = tuple(g for g in opts.pop('head', '').split(',') if g)
MODE = opts.pop('mode', 'unwrap')
SUBSET = opts.pop('subset', '')
WELD = float(opts.pop('weld', 0))   # merge-by-distance (metres) after the subset: GLB imports keep split vertices     # material:A,B | u_lt:0.5 | u_gt:0.5 (faces kept for the unwrap)
ELEV = [float(x) for x in opts.pop('elevations', '5,20,35').split(',')]
AZ = int(opts.pop('azimuths', 24))
unwrap_opts = {k: value(v) for k, v in opts.items()}
os.makedirs(OUT, exist_ok=True)

if SRC.endswith('.blend'):
    bpy.ops.wm.open_mainfile(filepath=SRC)
else:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=SRC, merge_vertices=True)
rig = bpy.data.objects[RIG] if RIG else next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)
mesh = next(o for o in bpy.data.objects if o.type == 'MESH' and (o.name == MESH or o.data.name == MESH))
if rig is not None:
    if rig.animation_data:
        rig.animation_data.action = None
    for b in rig.pose.bones:
        b.matrix_basis.identity()
bpy.context.view_layer.update()
me = mesh.data
if any(len(p.vertices) != 3 for p in me.polygons):
    raise ValueError('mesh must be triangulated')

# ---- visibility: share of typical game views (slightly above, all around) that see each face, cosine-weighted
mw = mesh.matrix_world
verts = [mw @ v.co for v in me.vertices]
polys = [tuple(p.vertices) for p in me.polygons]
bvh = BVHTree.FromPolygons(verts, polys, all_triangles=True)
centres = np.array([sum((verts[i] for i in p), Vector()) / 3 for p in polys])
normals = []
for p in polys:
    n = (verts[p[1]] - verts[p[0]]).cross(verts[p[2]] - verts[p[0]])
    normals.append(n.normalized() if n.length > 0 else Vector((0, 0, 1)))
normals = np.array(normals)
pos = np.array(verts)
extent = float(np.ptp(pos, 0).max())
dirs = []
for e in ELEV:
    for k in range(AZ):
        a = 2 * math.pi * k / AZ
        dirs.append((math.cos(math.radians(e)) * math.cos(a), math.cos(math.radians(e)) * math.sin(a),
                     math.sin(math.radians(e))))
dirs = np.array(dirs)
t0 = time.time()
vis_raw = np.zeros(len(polys))
eps = extent * 1e-4
for f in range(len(polys)):
    c, n = Vector(centres[f]), Vector(normals[f])
    dots = dirs @ normals[f]
    acc = 0.0
    for d, dot in zip(dirs, dots):
        if dot <= 0.05:
            continue
        hit = bvh.ray_cast(c + n * eps + Vector(d) * eps, Vector(d), extent * 4)
        if hit[0] is None:
            acc += dot
    vis_raw[f] = acc / len(dirs)
vis = np.clip(vis_raw / max(np.percentile(vis_raw, 95), 1e-9), 0, 1)
if SUBSET:
    kind, arg = SUBSET.split(':', 1)
    if kind == 'material':
        names = arg.split(',')
        keep = np.array([me.materials[p.material_index].name.split('.')[0] in names for p in me.polygons])
    else:
        flat0 = np.zeros(len(me.loops) * 2, np.float32)
        me.uv_layers[0].data.foreach_get('uv', flat0)
        flat0 = flat0.reshape(-1, 2)
        mu = np.array([flat0[list(p.loop_indices)][:, 0].mean() for p in me.polygons])
        keep = mu < float(arg) if kind == 'u_lt' else mu > float(arg)
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if not keep[f.index]], context='FACES')
    if WELD:
        before = len(bm.verts)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=WELD)
        print(f'WELD {before} -> {len(bm.verts)} vertices', flush=True)
    bm.to_mesh(me)
    bm.free()
    me.update()
    vis, vis_raw = vis[keep], vis_raw[keep]
    verts = [mw @ v.co for v in me.vertices]
    polys = [tuple(p.vertices) for p in me.polygons]
    pos = np.array(verts)
    print(f'SUBSET {SUBSET}: {int(keep.sum())} of {len(keep)} faces', flush=True)
print(f'VIS {len(polys)} faces x {len(dirs)} views in {time.time() - t0:.0f}s; hidden(<0.15) '
      f'{100 * (vis < 0.15).mean():.1f}% of faces', flush=True)

if not SRC.endswith('.blend'):
    # an installed GLB carries its non-square atlas material (m620 4128x2048, hyd heads 1536x1024): Blender's unwrap
    # with correct_aspect=True would squeeze every SLIM-flattened chart by that aspect (found here: p90 stretch 2.2)
    for slot in mesh.material_slots:
        slot.link = 'DATA'
    me.materials.clear()

if MODE == 'export':
    # combined-layout study: this exact mesh (subset, weld, face order) for partuv_run.py: positions, triangles,
    # per-vertex skin weights (bone part tree) and the face visibility
    weights = np.zeros((len(me.vertices), max(len(mesh.vertex_groups), 1)), np.float32)
    for v in me.vertices:
        for g in v.groups:
            weights[v.index, g.group] = g.weight
    groups = np.array([g.name for g in mesh.vertex_groups] or ['none'])
    np.savez(os.path.join(OUT, f'{NAME}_mesh.npz'), pos=pos, tri=np.array(polys), weights=weights, groups=groups,
             vis=vis)
    print('EXPORTED', NAME, len(pos), 'vertices', len(polys), 'triangles', len(groups), 'groups', flush=True)
    raise SystemExit(0)

# ---- unwrap
report = {'name': NAME, 'mode': MODE, 'options': unwrap_opts}
t0 = time.time()
if MODE == 'unwrap':
    report.update(uv_atlas_seam.unwrap(mesh, head_groups=HEAD, head_factor=float(unwrap_opts.pop('head_factor', 1.8)),
                                       vis=vis, **unwrap_opts))
report['seconds'] = round(time.time() - t0)

# ---- seam metrics on the final UVs
flat = np.zeros(len(me.loops) * 2, np.float32)
me.uv_layers['UVMap' if 'UVMap' in me.uv_layers else 0].data.foreach_get('uv', flat)
flat = flat.reshape(-1, 2)
tri = np.array(polys)
cuv = np.array([flat[list(p.loop_indices)] for p in me.polygons], np.float64)
edge_faces = {}
for f, t in enumerate(tri):
    for k in range(3):
        a, b = int(t[k]), int(t[(k + 1) % 3])
        edge_faces.setdefault((min(a, b), max(a, b)), []).append((f, k))


def corner_uv(f, v):
    k = int(np.nonzero(tri[f] == v)[0][0])
    return cuv[f, k]


seams = []
for (a, b), fk in edge_faces.items():
    if len(fk) != 2:
        seams.append((a, b, fk[0][0], fk[0][0]))
        continue
    (f, _), (g, _) = fk
    if (np.abs(corner_uv(f, a) - corner_uv(g, a)).max() > 1e-6 or np.abs(corner_uv(f, b) - corner_uv(g, b)).max() > 1e-6):
        seams.append((a, b, f, g))
seam_len = np.array([np.linalg.norm(pos[a] - pos[b]) for a, b, _, _ in seams]) / extent
seam_vis = np.array([(vis[f] + vis[g]) / 2 for _, _, f, g in seams])
all_len = np.array([np.linalg.norm(pos[a] - pos[b]) for a, b in edge_faces]) / extent
report['seams'] = {
    'total_len': round(float(seam_len.sum()), 2),
    'vis_weighted_len': round(float((seam_len * seam_vis).sum()), 2),
    'hidden_len': round(float(seam_len[seam_vis < 0.15].sum()), 2),
    'mid_len': round(float(seam_len[(seam_vis >= 0.15) & (seam_vis < 0.5)].sum()), 2),
    'exposed_len': round(float(seam_len[seam_vis >= 0.5].sum()), 2),
    'hidden_share_pct': round(100 * float(seam_len[seam_vis < 0.15].sum() / seam_len.sum()), 1),
    'exposed_share_pct': round(100 * float(seam_len[seam_vis >= 0.5].sum() / seam_len.sum()), 1),
    'mesh_edge_len_total': round(float(all_len.sum()), 1),
    'surface_hidden_pct': round(100 * float((vis < 0.15).mean()), 1),
    'note': 'lengths in creature sizes (largest bounding-box extent); vis = cosine-weighted share of views '
            f'(elevations {ELEV}, {AZ} azimuths) that see the face, / its p95, clipped to 1'}
uv_area = np.abs((cuv[:, 1, 0] - cuv[:, 0, 0]) * (cuv[:, 2, 1] - cuv[:, 0, 1])
                 - (cuv[:, 2, 0] - cuv[:, 0, 0]) * (cuv[:, 1, 1] - cuv[:, 0, 1])).sum() / 2
report['uv_area_pct'] = round(100 * float(uv_area), 2)
print('SEAMS', json.dumps(report['seams']), flush=True)
np.savez(os.path.join(OUT, f'{NAME}_faces.npz'), pos=pos, tri=tri, uv=cuv, vis=vis, vis_raw=vis_raw,
         seams=np.array([(a, b) for a, b, _, _ in seams]).reshape(-1, 2), seam_vis=seam_vis)
json.dump(report, open(os.path.join(OUT, f'{NAME}_report.json'), 'w'), indent=1)

# ---- exports: neutral static upload (as uv_atlas_v8.py) and a skinned measurement GLB with a placeholder 2K map
dup = mesh.copy()
dup.data = mesh.data.copy()
dup.modifiers.clear()
dup.parent = None
dup.matrix_world = mesh.matrix_world
bpy.context.scene.collection.objects.link(dup)
for o in bpy.data.objects:
    o.select_set(o == dup)
bpy.context.view_layer.objects.active = dup
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, f'{NAME}_upload.glb'), use_selection=True, export_format='GLB',
                          export_yup=True, export_skins=False, export_animations=False, export_materials='NONE',
                          export_attributes=False)
bpy.data.objects.remove(dup)
img_path = os.path.join(OUT, 'placeholder_2k.png')
if not os.path.exists(img_path):
    im = bpy.data.images.new('placeholder_2k', 2048, 2048)
    im.filepath_raw = img_path
    im.file_format = 'PNG'
    im.save()
im = bpy.data.images.load(img_path, check_existing=True)
mat = bpy.data.materials.new('measure')
mat.use_nodes = True
bsdf = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
tex = mat.node_tree.nodes.new('ShaderNodeTexImage')
tex.image = im
mat.node_tree.links.new(tex.outputs[0], bsdf.inputs[0])
me.materials.clear()
me.materials.append(mat)
for slot in mesh.material_slots:
    slot.link = 'DATA'
    slot.material = mat
for p in me.polygons:
    p.material_index = 0
if hasattr(me, 'gltf2_variant_mesh_data'):
    me.gltf2_variant_mesh_data.clear()
for sc in bpy.data.scenes:
    if hasattr(sc, 'gltf2_KHR_materials_variants_variants'):
        sc.gltf2_KHR_materials_variants_variants.clear()
for m in list(bpy.data.materials):
    if m != mat:
        bpy.data.materials.remove(m)
for o in bpy.data.objects:
    o.select_set(o == mesh or o == rig)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, f'{NAME}_measure.glb'), use_selection=True, export_format='GLB',
                          export_yup=True, export_skins=True, export_animations=False, export_materials='EXPORT',
                          export_attributes=False)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, f'{NAME}.blend'))
print('TRIAL done', NAME, json.dumps({k: v for k, v in report.items() if k != 'seam_log'}), flush=True)
