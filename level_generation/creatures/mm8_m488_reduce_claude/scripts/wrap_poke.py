"""Leg/wrap poke-through over a clip, straight from GLBs: per 48 fps frame, body vertices weighted mostly to the thighs
or pelvis that lie outside the wrap skirt's surface (along the nearest wrap face's outward normal) within 6 cm of it.
Prints per frame counts and the deepest poke for each GLB. Usage: blender -b -P wrap_poke.py -- <clip> <label=glb,...>"""
import bpy, bmesh, os, sys
import numpy as np
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
clip, items = sys.argv[sys.argv.index('--') + 1:][:2]
for item in items.split(','):
    label, glb = item.split('=')
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb))
    sc = bpy.context.scene; rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    body = bpy.data.objects['Minotaur']; act = bpy.data.actions[clip]; rig.animation_data.action = act
    names = {g.index: g.name for g in body.vertex_groups}
    legw = np.array([sum(g.weight for g in v.groups if names[g.group].endswith(('Thigh', 'Pelvis'))) for v in body.data.vertices])
    # pieces by welded connectivity: the wrap is the second largest
    bm = bmesh.new(); bm.from_mesh(body.data)
    co = {}
    for v in bm.verts:
        co.setdefault(tuple(round(c, 6) for c in v.co), []).append(v.index)
    parent = list(range(len(bm.verts)))
    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]; a = parent[a]
        return a
    for ids in co.values():
        for i in ids[1:]:
            parent[find(i)] = find(ids[0])
    for e in bm.edges:
        parent[find(e.verts[0].index)] = find(e.verts[1].index)
    root = np.array([find(i) for i in range(len(bm.verts))]); bm.free()
    roots, counts = np.unique(root, return_counts=True); order = roots[np.argsort(-counts)]
    bodyv = root == order[0]; wrapv = root == order[1]
    tris = [list(p.vertices) for p in body.data.polygons]; wtri = [t for t in tris if wrapv[t[0]]]
    rz = np.array([v.co.z for v in body.data.vertices]) if abs(body.matrix_world[2][2]) > .5 else None
    cand = np.where(bodyv & (legw > .6) & (np.array([(body.matrix_world @ v.co).z for v in body.data.vertices]) < float(os.environ.get('POKE_ZMAX', '1.0'))))[0]
    fps = sc.render.fps / sc.render.fps_base; f0, f1 = act.frame_range; n = int(round((f1 - f0) / fps * 48)) + 1
    res = []
    for i in range(n):
        fr = f0 + i / 48 * fps; sc.frame_set(int(fr), subframe=fr - int(fr))
        dg = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(dg).data
        P = np.array([body.matrix_world @ v.co for v in ev.vertices])
        tree = BVHTree.FromPolygons([tuple(x) for x in P], wtri)
        cnt, deep = 0, 0.0
        for vi in cand:
            hit, nrm, _, d = tree.find_nearest(P[vi], .06)
            if hit is not None:
                s = float(np.dot(P[vi] - np.array(hit), np.array(nrm)))
                if s > .002:
                    cnt += 1; deep = max(deep, s)
        res.append((cnt, deep))
    print('POKE', label, clip, 'frames with pokes', sum(1 for c, _ in res if c), 'max count', max(c for c, _ in res),
          'deepest %.1f mm' % (max(d for _, d in res) * 1000))
    print('POKEF', label, ' '.join(f'{i}:{c}/{d*1000:.0f}' for i, (c, d) in enumerate(res) if c))
