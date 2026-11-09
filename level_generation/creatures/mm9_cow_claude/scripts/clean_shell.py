"""Clean the Meshy Smart Topology return without remeshing (keeps Meshy's even triangles; a voxel remesh of this
body cannot be decimated cleanly: collapse decimation of the 2-2.5 mm voxel surface stalls at ~23k triangles and
throws spikes).

1. Weld (1e-5) the main component; the small separate pieces (eyes, teats, tassel, beard) are kept as returned.
2. Hidden inner shell: faces under the skin (the ray along the normal hits it within MAXD) from which every one
   of 48 hemisphere rays hits the mesh again within REACH are deleted
   (Meshy returned a second, inner body: cow 41 % of the area, goat 10 %), loose vertices dropped.
3. What remains of the inner shell and any fin: components of the main body other than the largest are deleted.
4. The holes left where the shells met are filled (fan-free: bmesh holes_fill, then triangulated), normals made
   consistent, a light smooth on the filled patches only.
Args: <meshy glb> <out glb> [reach] [maxd]"""
import bpy, bmesh, sys, math, random
from mathutils import Vector
from mathutils.bvhtree import BVHTree
argv = sys.argv[sys.argv.index('--') + 1:]
SRC, OUT = argv[0], argv[1]
REACH = float(argv[2]) if len(argv) > 2 else 5.0
MAXD = float(argv[3]) if len(argv) > 3 else 0.015
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
src = next(o for o in bpy.data.objects if o.type == 'MESH')
bm = bmesh.new(); bm.from_mesh(src.data); bm.transform(src.matrix_world)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)


def components(bm):
    bm.verts.ensure_lookup_table()
    seen, comps = set(), []
    for v in bm.verts:
        if v.index in seen:
            continue
        c, st = [], [v]; seen.add(v.index)
        while st:
            x = st.pop(); c.append(x)
            for e in x.link_edges:
                y = e.other_vert(x)
                if y.index not in seen:
                    seen.add(y.index); st.append(y)
        comps.append(c)
    comps.sort(key=len, reverse=True)
    return comps


comps = components(bm)
main = set(comps[0])
pieces_n = len(comps) - 1
bm.faces.ensure_lookup_table()
bvh = BVHTree.FromBMesh(bm)
rng = random.Random(1)
dirs = []
for k in range(48):
    z = rng.random() * 0.95 + 0.05
    phi = rng.random() * 2 * math.pi
    r = math.sqrt(1 - z * z)
    dirs.append(Vector((r * math.cos(phi), r * math.sin(phi), z)))
interior = []
for f in bm.faces:
    if f.verts[0] not in main:
        continue
    n = f.normal
    if n.length < 1e-9:
        continue
    t = n.orthogonal().normalized(); b = n.cross(t)
    o = f.calc_center_median() + n * 1e-4
    hn = bvh.ray_cast(o, n, REACH)
    if hn[0] is None or hn[3] > MAXD:   # the inner layer sits 0.5-6 mm under the skin; crevices are not it
        continue
    if all(bvh.ray_cast(o, t * d.x + b * d.y + n * d.z, REACH)[0] is not None for d in dirs):
        interior.append(f)
bmesh.ops.delete(bm, geom=interior, context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
# drop remaining main-body fragments (inner shell remnants): any component that is not a small separate piece of the
# original return and not the largest
comps = components(bm)
big = comps[0]
dropped = 0
for c in comps[:8]:
    xs = [v.co for v in c]
    print('SHELLCOMP', len(c), [round(min(p[i] for p in xs), 3) for i in range(3)], [round(max(p[i] for p in xs), 3) for i in range(3)],
          'boundary', sum(1 for v in c for e in v.link_edges if e.is_boundary) // 2, 'main' if any(v in main for v in c) else 'piece')


def boundary_loops(vset):
    es = {e for v in vset for e in v.link_edges if e.is_boundary}
    out, seen = [], set()
    for e in es:
        if e in seen:
            continue
        lp, st = [], [e]; seen.add(e)
        while st:
            x = st.pop(); lp.append(x)
            for v in x.verts:
                for y in v.link_edges:
                    if y.is_boundary and y not in seen:
                        seen.add(y); st.append(y)
        out.append(lp)
    return out


def centre(lp):
    vs = {v for e in lp for v in e.verts}
    return sum((v.co for v in vs), Vector()) / len(vs)


# limbs cut off by the deletion (Meshy joined the cow's front legs to the body through the inner layer only):
# bridge each detached main-body part's open loop to the nearest hole of the largest part
bridged = []
for c in comps[1:]:
    if not any(v in main for v in c):
        continue
    if len(c) >= 60:
        body_loops = boundary_loops(set(components(bm)[0]))
        for lp in boundary_loops(set(c)):
            cc = centre(lp)
            tgt = min(body_loops, key=lambda l: (centre(l) - cc).length)
            dist = (centre(tgt) - cc).length
            try:
                r = bmesh.ops.bridge_loops(bm, edges=lp + tgt)
                bridged.append((len(c), len(lp), len(tgt), round(dist, 4), len(r['faces'])))
                body_loops.remove(tgt)
            except Exception as ex:
                bridged.append((len(c), len(lp), len(tgt), round(dist, 4), str(ex)[:60]))
    else:
        bmesh.ops.delete(bm, geom=c, context='VERTS'); dropped += len(c)
print('SHELL bridged', bridged)
bnd = [e for e in bm.edges if e.is_boundary and e.verts[0] in main]
# boundary loops
loops, seen = [], set()
for e in bnd:
    if e in seen:
        continue
    loop, st = [], [e]; seen.add(e)
    while st:
        x = st.pop(); loop.append(x)
        for v in x.verts:
            for y in v.link_edges:
                if y.is_boundary and y not in seen:
                    seen.add(y); st.append(y)
    loops.append(loop)
sizes = sorted((len(l) for l in loops), reverse=True)
print('SHELL interior', len(interior), 'dropped verts', dropped, 'holes', len(loops), 'hole edges', sizes[:12])
before = set(bm.faces)
bmesh.ops.holes_fill(bm, edges=bnd, sides=0)
new = [f for f in bm.faces if f not in before]
bmesh.ops.triangulate(bm, faces=new)
new = [f for f in bm.faces if f not in before]
bmesh.ops.recalc_face_normals(bm, faces=[f for f in bm.faces if f.verts[0] in main or True])
# relax the filled patches (their inner vertices only: none for plain n-gon fills; the rim one ring)
rim = {v for f in new for v in f.verts}
for _ in range(3):
    pos = {v: sum((e.other_vert(v).co for e in v.link_edges), Vector()) / len(v.link_edges) for v in rim}
    for v, p in pos.items():
        v.co = v.co.lerp(p, 0.3)
me = bpy.data.meshes.new('Body'); bm.to_mesh(me)
ob = bpy.data.objects.new('Body', me); bpy.context.scene.collection.objects.link(ob)
bpy.data.objects.remove(src)
for p in me.polygons:
    p.use_smooth = True
for o in bpy.data.objects:
    o.select_set(o == ob)
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', export_yup=True, export_materials='NONE',
                          use_selection=True)
bm2 = bmesh.new(); bm2.from_mesh(me)
print('SHELL out faces', len(me.polygons), 'boundary', sum(1 for e in bm2.edges if e.is_boundary),
      'nonmanifold', sum(1 for e in bm2.edges if not e.is_manifold), 'filled', len(new), 'pieces', pieces_n)
