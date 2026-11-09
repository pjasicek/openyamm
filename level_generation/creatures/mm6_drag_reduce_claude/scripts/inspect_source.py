import os, bpy, bmesh
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'source.blend'))
for o in bpy.data.objects:
    s = f'{o.type} {o.name} parent={o.parent.name if o.parent else None}'
    if o.type == 'MESH':
        b = bmesh.new(); b.from_mesh(o.data)
        s += f' tris={sum(len(f.verts)-2 for f in b.faces)} open={sum(1 for e in b.edges if e.is_boundary)} mats={[m.name for m in o.data.materials]} uv={len(o.data.uv_layers)} vg={len(o.vertex_groups)} mods={[m.type for m in o.modifiers]} hidden={o.hide_render}'
    print('OBJ', s)
print('ACT', [(a.name, tuple(a.frame_range)) for a in bpy.data.actions])
