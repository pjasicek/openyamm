"""Head-intersection and floor gate straight from a GLB's LOD0 (the batch I project's check_hydra.py, which needs the
master's 'part' and 'chain_owner' attributes, rebuilt from what the GLB carries): head k = HydraHeads faces whose
dominant bone is Head<k>; the chain owner of a vertex = k when its dominant bone is Neck<k>_* or Head<k>. Per frame
(scene at 30 fps, the clips' own key rate, so frame numbers match check_hydra.py), triangles of each head overlapping
triangles outside head k and neck k (other heads; other necks, the body only above 1.05 m at rest), from BVH trees of
the posed mesh; plus the lowest vertex. Prints per clip the worst frame.
Usage: blender -b -P check_heads_glb.py -- <glb> [step]"""
import bpy, os, sys
import numpy as np
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]; STEP = int(a[1]) if len(a) > 1 else 1
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.render.fps = 30; bpy.context.scene.render.fps_base = 1
bpy.ops.import_scene.gltf(filepath=os.path.abspath(a[0]))
ob = bpy.data.objects['M266']; rig = next(m.object for m in ob.modifiers if m.type == 'ARMATURE'); me = ob.data
gn = {g.index: g.name for g in ob.vertex_groups}
vdom = [gn[max(v.groups, key=lambda g: g.weight).group] if v.groups else '-' for v in me.vertices]
own = np.zeros(len(me.vertices), int)
for i, b in enumerate(vdom):
    for k in range(1, 6):
        if b.startswith(f'Neck{k}_') or b == f'Head{k}':
            own[i] = k
heads_slot = next(i for i, m in enumerate(me.materials) if m.name.startswith('HydraHeads'))
polys = [list(p.vertices) for p in me.polygons]
part = np.zeros(len(polys), int)
for i, p in enumerate(me.polygons):
    if p.material_index == heads_slot:
        votes = [vdom[v] for v in p.vertices]
        b = max(set(votes), key=votes.count)
        part[i] = int(b[4]) if b.startswith('Head') else 0
face_own = np.array([np.bincount(own[p], minlength=6).argmax() for p in polys])
heads = {k: [i for i in range(len(polys)) if part[i] == k] for k in range(1, 6)}
zrest = np.array([me.vertices[p[0]].co.z for p in polys])
others = {k: [i for i in range(len(polys)) if part[i] != k and face_own[i] != k and
              (part[i] > 0 or (face_own[i] > 0 and zrest[i] > 1.05))] for k in range(1, 6)}
print('LABELS', {k: len(v) for k, v in heads.items()}, flush=True)
rig.animation_data_create()
for act in sorted(bpy.data.actions, key=lambda x: x.name):
    rig.animation_data.action = act
    if len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(round(x)) for x in act.frame_range)
    worst = (0, f0, None); low = 9.0; low_at = None; frames_hit = 0
    for f in range(f0, f1 + 1, STEP):
        bpy.context.scene.frame_set(f)
        ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
        co = [tuple(ob.matrix_world @ v.co) for v in m.vertices]; ev.to_mesh_clear()
        zz = np.array([c[2] for c in co]); i = int(zz.argmin())
        if zz[i] < low:
            low = float(zz[i]); low_at = (f, vdom[i])
        fh = 0
        for k in range(1, 6):
            A = BVHTree.FromPolygons(co, [polys[i] for i in heads[k]])
            B = BVHTree.FromPolygons(co, [polys[i] for i in others[k]])
            hits = A.overlap(B); fh += len(hits)
            if hits and os.environ.get('GATE_DEBUG') == f'{act.name}:{f}':  # rest-space centres of the touching faces
                for x, y in hits:
                    fa, fb = polys[heads[k][x]], polys[others[k][y]]
                    ca = sum((me.vertices[v].co for v in fa), me.vertices[fa[0]].co * 0) / 3
                    cb = sum((me.vertices[v].co for v in fb), me.vertices[fb[0]].co * 0) / 3
                    print('TOUCH', k, [round(c, 3) for c in ca], [round(c, 3) for c in cb], flush=True)
            if len(hits) > worst[0]:
                touch = sorted({('H%d' % part[others[k][j]]) if part[others[k][j]] else ('N%d' % face_own[others[k][j]])
                                for _, j in hits})
                worst = (len(hits), f, (k, touch))
        frames_hit += fh > 0
    print(f'GATE {act.name} frames {f0}-{f1}: head overlaps worst {worst[0]} at frame {worst[1]} {worst[2]}, frames with overlaps '
          f'{frames_hit}; lowest vertex {low * 100:.1f} cm {low_at}', flush=True)
