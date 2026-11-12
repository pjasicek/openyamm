import bpy, sys
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--')+1])
for o in bpy.data.objects:
    s = f'OBJ {o.name} {o.type}'
    if o.type == 'MESH':
        me = o.data
        s += f' polys={len(me.polygons)} verts={len(me.vertices)} attrs={[a.name for a in me.attributes]} uv={[u.name for u in me.uv_layers]} mats={[m.name if m else None for m in me.materials]} vg={len(o.vertex_groups)}'
    print(s)
