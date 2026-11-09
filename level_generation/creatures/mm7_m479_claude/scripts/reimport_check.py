"""Re-import the runtime GLB in a clean Blender and list meshes, triangles, materials, actions and rest bounds.
Args: -- <glb>"""
import bpy, sys, os
glb = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
for o in bpy.data.objects:
    if o.type == 'MESH':
        me = o.data
        print('REIMPORT mesh', o.name, 'tris', sum(len(p.vertices) - 2 for p in me.polygons), 'uv', len(me.uv_layers),
              'mats', [m.name for m in me.materials], 'groups', len(o.vertex_groups))
print('REIMPORT actions', sorted(a.name for a in bpy.data.actions))
print('REIMPORT bones', [b.name for b in bpy.data.armatures[0].bones] if bpy.data.armatures else None)
