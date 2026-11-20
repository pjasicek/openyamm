"""Export work/step1_uv.blend (cleaned, UV'd, unrigged) as export/pmn2_clean_uv.glb for Meshy auto-rigging.
1.578 m tall, soles at z=0, facing -Y in Blender (= +Z in glTF), one mesh, no material/texture."""
import bpy, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'step1_uv.blend'))
for o in list(bpy.data.objects):
    if o.type != 'MESH':
        bpy.data.objects.remove(o, do_unlink=True)
m = bpy.data.objects['Mage']; m.data.materials.clear()
for o in bpy.data.objects:
    o.select_set(o == m)
bpy.context.view_layer.objects.active = m
out = os.path.join(common.PROJECT, 'export', 'pmn2_clean_uv.glb')
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_normals=True,
                          export_materials='NONE', export_yup=True)
me = m.data; me.calc_loop_triangles()
lo = [min(v.co[i] for v in me.vertices) for i in range(3)]; hi = [max(v.co[i] for v in me.vertices) for i in range(3)]
print('EXPORT', out, 'tris', len(me.loop_triangles), 'verts', len(me.vertices), 'bounds', [round(x, 3) for x in lo], [round(x, 3) for x in hi])
