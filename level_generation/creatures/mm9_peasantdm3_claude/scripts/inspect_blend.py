import bpy, sys, bmesh
from collections import Counter
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
for o in bpy.data.objects:
    if o.type == 'MESH':
        me = o.data
        bm = bmesh.new(); bm.from_mesh(me)
        # loose parts
        bm.verts.ensure_lookup_table()
        seen = set(); parts = []
        for v in bm.verts:
            if v.index in seen: continue
            st = [v]; comp = []
            seen.add(v.index)
            while st:
                x = st.pop(); comp.append(x)
                for e in x.link_edges:
                    y = e.other_vert(x)
                    if y.index not in seen: seen.add(y.index); st.append(y)
            zs = [(o.matrix_world @ p.co).z for p in comp]; xs = [(o.matrix_world @ p.co).x for p in comp]; ys = [(o.matrix_world @ p.co).y for p in comp]
            parts.append((len(comp), round(min(zs),3), round(max(zs),3), round(min(xs),3), round(max(xs),3), round(min(ys),3), round(max(ys),3)))
        print('OBJ', o.name, 'v', len(me.vertices), 'f', len(me.polygons), 'mats', [m.name for m in me.materials if m], 'uv', [u.name for u in me.uv_layers], 'vg', len(o.vertex_groups), 'parent', o.parent.name if o.parent else None)
        for i, p in enumerate(sorted(parts, key=lambda p: -p[0])[:20]): print('  PART', i, p)
    elif o.type == 'ARMATURE':
        print('ARM', o.name, len(o.data.bones), [b.name for b in o.data.bones][:50])
        for b in o.data.bones:
            if 'Head' in b.name or 'Neck' in b.name or 'Pony' in b.name or 'Bone03' in b.name:
                print('  BONE', b.name, [round(x,3) for x in (o.matrix_world @ b.head_local)], [round(x,3) for x in (o.matrix_world @ b.tail_local)])
