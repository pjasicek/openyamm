"""List objects, materials, modifiers, actions of a .blend. Usage: blender -b <file> -P list_blend.py"""
import bpy
for o in bpy.data.objects:
    extra = ''
    if o.type == 'MESH':
        me = o.data
        extra = f'tris={sum(len(p.vertices)-2 for p in me.polygons)} verts={len(me.vertices)} mats={[m.name if m else None for m in me.materials]} uv={[u.name for u in me.uv_layers]} vg={len(o.vertex_groups)} mods={[m.type for m in o.modifiers]} attrs={[a.name for a in me.attributes if not a.name.startswith(".")]}'
    if o.type == 'ARMATURE':
        extra = f'bones={len(o.data.bones)} action={o.animation_data.action.name if o.animation_data and o.animation_data.action else None}'
    print('OBJ', o.name, o.type, 'parent=', o.parent.name if o.parent else None, 'dims=', tuple(round(d,3) for d in o.dimensions), extra)
print('ACTIONS', [(a.name, tuple(a.frame_range)) for a in bpy.data.actions])
print('IMAGES', [(i.name, tuple(i.size)) for i in bpy.data.images])
print('FPS', bpy.context.scene.render.fps)
