"""Can the waist backstop tube be seen from outside? (Peasant boy reduction check, 2026-11-05.) The tube is one-texel and dark: if a
reduced tube's chord pushed it through the cloth it would show as dark patches, which the see-through gate (background holes) does
not count. LOD0 only; every clip at every STEP-th frame; the tube's face centroids and edge midpoints; per point a ray toward each of
16 cameras (8 azimuths x level / 20 deg down, the see-through gate's views). The ray passes back faces (culled in game) and stops at
the first front face of a non-tube face: a point whose ray escapes to any camera is visible. Reports per clip the most visible
points in one frame and the frames with any.
Args (Blender): <glb> <out json> [step 3]"""
import bpy, bmesh, sys, json, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
GLB, OUT = a[0], a[1]; STEP = int(a[2]) if len(a) > 2 else 3
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
o = bpy.data.objects['PeasantBoy']; rig = next(m.object for m in o.modifiers if m.type == 'ARMATURE')
for x in bpy.data.objects:
    if x.type == 'MESH' and x is not o:
        bpy.data.objects.remove(x)
me = o.data; uv = me.uv_layers.active.data
# the tube: one-texel faces of the body material whose texel is the tube's (the largest one-texel island of the body material
# sitting on one UV: waist_backstop.py samples one dark vest texel)
tex = {}
for p in me.polygons:
    us = {(round(uv[l].uv[0], 6), round(uv[l].uv[1], 6)) for l in p.loop_indices}
    if len(us) == 1 and me.materials[p.material_index].name.startswith('PeasantBoy_A'):
        tex.setdefault(us.pop(), []).append(p.index)
# tube faces: the one-texel faces forming the connected component of more than 600 faces on one texel
cand = max(tex.values(), key=len)
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
cs = set(cand); seen, comps = set(), []
for f in cand:
    if f in seen:
        continue
    stack, comp = [f], []
    seen.add(f)
    while stack:
        g = stack.pop(); comp.append(g)
        for e in bm.faces[g].edges:
            for h in e.link_faces:
                if h.index in cs and h.index not in seen:
                    seen.add(h.index); stack.append(h.index)
    comps.append(comp)
tube = set(max(comps, key=len)); bm.free()
print('TUBE faces', len(tube), 'of texel islands', sorted(len(c) for c in comps)[-3:])
dirs = []
for el in (0.0, 20.0):
    for az in range(0, 360, 45):
        e, z = math.radians(el), math.radians(az)
        dirs.append(Vector((math.sin(z) * math.cos(e), -math.cos(z) * math.cos(e), math.sin(e))))
sc = bpy.context.scene; rep = {}
for act in bpy.data.actions:
    rig.animation_data_create(); rig.animation_data.action = act
    if act.slots:
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range); most, frames = 0, 0
    for fr in range(f0, f1 + 1, STEP):
        sc.frame_set(fr); dg = bpy.context.evaluated_depsgraph_get()
        b = bmesh.new(); b.from_object(o, dg); b.transform(o.matrix_world); b.faces.ensure_lookup_table()
        verts = [v.co.copy() for v in b.verts]; polys = [[v.index for v in f.verts] for f in b.faces]
        tree = BVHTree.FromPolygons(verts, polys)
        pts = []
        for i in tube:
            f = b.faces[i]; c = f.calc_center_median(); pts.append(c)
            for e in f.edges:
                pts.append((e.verts[0].co + e.verts[1].co) / 2)
        vis = 0
        for p in pts:
            seen_any = False
            for d in dirs:
                start = p + d * 1e-4
                for _ in range(12):
                    hit, n, idx, dist = tree.ray_cast(start, d)
                    if hit is None:
                        seen_any = True; break
                    fn = b.faces[idx].normal
                    if idx not in tube and fn.dot(d) > 0:
                        break                     # a front face toward the camera: occluded
                    start = hit + d * 1e-4        # a back face (culled) or the tube itself: keep going
                if seen_any:
                    break
            vis += seen_any
        most = max(most, vis); frames += vis > 0; b.free()
    rep[act.name] = {'most_visible_points': most, 'frames_with_visible': frames}
    print('TUBEVIS', act.name, json.dumps(rep[act.name]), flush=True)
json.dump(rep, open(OUT, 'w'), indent=1)
