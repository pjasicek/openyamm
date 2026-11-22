import bpy, sys
for o in bpy.data.objects:
    extra = ''
    if o.type == 'MESH':
        extra = f' polys={len(o.data.polygons)} attrs={[a.name for a in o.data.attributes]} mods={[m.type for m in o.modifiers]} dims={tuple(round(x,3) for x in o.dimensions)}'
    print('OBJ', o.name, o.type, extra)
