import bpy, os, bmesh
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'source_snapshot.blend'))
for o in bpy.data.objects:
    line = f'{o.type:9s} {o.name:28s} parent={o.parent.name if o.parent else None}'
    if o.type == 'MESH':
        me = o.data
        bm = bmesh.new(); bm.from_mesh(me)
        tris = sum(len(f.verts) - 2 for f in bm.faces)
        # connected components
        seen = set(); comps = []
        for v in bm.verts:
            if v.index in seen: continue
            stack = [v]; n = 0; seen.add(v.index)
            while stack:
                x = stack.pop(); n += 1
                for e in x.link_edges:
                    w = e.other_vert(x)
                    if w.index not in seen: seen.add(w.index); stack.append(w)
            comps.append(n)
        comps.sort(reverse=True)
        line += f' verts={len(me.vertices)} tris={tris} mats={[m.name for m in me.materials]} uvs={[u.name for u in me.uv_layers]} comps={len(comps)} top={comps[:6]} vgroups={len(o.vertex_groups)} mods={[m.type for m in o.modifiers]} dims={tuple(round(d,3) for d in o.dimensions)}'
        bm.free()
    if o.type == 'ARMATURE':
        line += f' bones={len(o.data.bones)}'
    print('OBJ', line)
print('ACTIONS', [(a.name, tuple(a.frame_range)) for a in bpy.data.actions])
for m in bpy.data.materials:
    imgs = [n.image.name for n in (m.node_tree.nodes if m.node_tree else []) if n.type == 'TEX_IMAGE' and n.image]
    print('MAT', m.name, imgs)
