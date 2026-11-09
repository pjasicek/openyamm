"""Close the open boundaries of the crow's body shell (2026-10-30, between graft_head.py and neck_fair.py).

Args: <in blend> <out blend> <report json>

The review viewer showed a lens of background through the -X wing root. The material is single sided and the wing is a
closed shell, so a hole in the upper surface looks straight through the culled lower one. That opening came from
graft_head.py: the bisect at the neck plane also caught the wing leading edge beside the neck (its seed is a cylinder
around the neck) and clear_outer cut that piece away, on one side only because the Meshy wings are not symmetric. Eight
other openings on the wings and the body are older, from the Meshy mesh and its reduction.

Every boundary loop that touches no head face is filled (a few one-edge remnants of pinched loops stay; they enclose
no area) and triangulated, without new vertices (weights, the paints and
the atlas keep their meaning), wound against its rim. The filled triangles reuse the rim's painted UVs: each one is
folded over its rim edge (the two rim corners keep their UVs, the third takes the rim face's opposite corner), so it
samples the plumage next to the hole in every map and never an unpainted gutter. The boundaries at the mouth stay.
"""
import bpy, bmesh, sys, json
import numpy as np

a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REP = a[:3]
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']
bm = bmesh.new()
bm.from_mesh(body.data)
uvl = bm.loops.layers.uv.active
hl = bm.faces.layers.int['head']
# a loop can be two chains whose ends only coincide: weld those ends first
ends = list({v for e in bm.edges if e.is_boundary for v in e.verts})
rep_weld = len(bm.verts)
bmesh.ops.remove_doubles(bm, verts=ends, dist=2e-5)
rep_weld -= len(bm.verts)
bm.edges.ensure_lookup_table()

rep = {'welded_verts': rep_weld, 'open_edges': sum(1 for e in bm.edges if e.is_boundary), 'loops': []}
for round_ in range(1):
    open_edges = [e for e in bm.edges if e.is_boundary]
    loops, seen = [], set()
    for e in open_edges:
        if e in seen:
            continue
        comp, st = [], [e]
        seen.add(e)
        while st:
            x = st.pop()
            comp.append(x)
            for v in x.verts:
                for y in v.link_edges:
                    if y.is_boundary and y not in seen:
                        seen.add(y)
                        st.append(y)
        loops.append(comp)

    for comp in loops:
        rim = [e.link_faces[0] for e in comp]
        centre = np.mean([tuple(v.co) for e in comp for v in e.verts], 0).round(3).tolist()
        item = {'edges': len(comp), 'centre': centre}
        rep['loops'].append(item)
        if any(f[hl] == 1 for f in rim):
            item['state'] = 'left (head)'
            continue
        item['round'] = round_
        made = bmesh.ops.holes_fill(bm, edges=comp, sides=len(comp) + 1)['faces'] or \
            bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=comp)['geom']
        made = [f for f in made if isinstance(f, bmesh.types.BMFace)]
        if not made:
            item['state'] = 'not filled'
            continue
        tris = bmesh.ops.triangulate(bm, faces=made, quad_method='BEAUTY', ngon_method='BEAUTY')['faces']
        bm.normal_update()
        new = set(tris)
        # winding against the rim, then outwards through the fill
        done = {}
        for f in tris:
            for l in f.loops:
                others = [x for x in l.edge.link_faces if x not in new]
                if others:
                    o = others[0]
                    same = next(k for k in o.loops if k.edge == l.edge).vert == l.vert
                    if same:
                        f.normal_flip()
                    done[f] = o
                    break
        todo = [f for f in tris if f not in done]
        while todo:
            rest = []
            for f in todo:
                hit = None
                for l in f.loops:
                    for x in l.edge.link_faces:
                        if x is not f and x in done and x in new:
                            hit = x
                            same = next(k for k in x.loops if k.edge == l.edge).vert == l.vert
                            if same:
                                f.normal_flip()
                            break
                    if hit:
                        break
                if hit:
                    done[f] = hit
                else:
                    rest.append(f)
            if len(rest) == len(todo):
                break
            todo = rest
        # UVs: fold over the rim edge, or over the already mapped neighbour inside the fill
        assigned = set()
        order = [f for f in tris if done.get(f) is not None and done[f] not in new] + \
                [f for f in tris if done.get(f) is not None and done[f] in new]
        for f in order:
            src = done[f]
            shared = [v for v in f.verts if v in src.verts]
            far = next(v for v in src.verts if v not in shared)
            uv_of = {k.vert: k[uvl].uv.copy() for k in src.loops}
            for k in f.loops:
                k[uvl].uv = uv_of[k.vert] if k.vert in uv_of else uv_of[far]
            f[hl] = 0
            f.smooth = True
            f.material_index = src.material_index
            assigned.add(f)
        item['state'] = 'filled'
        item['tris'] = len(tris)
        item['area_cm2'] = round(sum(f.calc_area() for f in tris) * 1e4, 2)

bm.normal_update()
rep['open_edges_after'] = sum(1 for e in bm.edges if e.is_boundary)
rep['tris'] = sum(len(f.verts) - 2 for f in bm.faces)
bm.to_mesh(body.data)
bm.free()
body.data.update()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('CLOSED', json.dumps(rep))
