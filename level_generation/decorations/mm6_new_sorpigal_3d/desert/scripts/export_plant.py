"""work/<id>/plant.blend + impostor maps -> work/<id>/plant_export.glb (+ export.blend) with Plant, Plant_LOD1,
Plant_LOD2 and Plant_LOD3: one quad in Blender's XZ plane (glTF XY), x -W/2..W/2, z 0..H, facing -Y (glTF +Z),
material Impostor (openyamm_billboard, the plant's wind, openyamm_specular), white COLOR_0. Usage: -- <id>"""
import bpy, bmesh, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import desert_common as dc
import desert_lib as dl
SID = sys.argv[sys.argv.index('--') + 1]
WORK = dc.work(SID)
bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, 'plant.blend'))
info = json.load(open(os.path.join(WORK, 'impostor.json')))
w, h = info['width_m'], info['height_m']
me = bpy.data.meshes.new('Plant_LOD3'); bm = bmesh.new(); uv = bm.loops.layers.uv.new('UVMap')
vs = [bm.verts.new(p) for p in ((-w / 2, 0, 0), (w / 2, 0, 0), (w / 2, 0, h), (-w / 2, 0, h))]
f = bm.faces.new(vs)
for loop, t in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
    loop[uv].uv = t
bm.normal_update()
if f.normal.y > 0:
    f.normal_flip()
bmesh.ops.triangulate(bm, faces=bm.faces[:]); bm.to_mesh(me); bm.free()
obj = bpy.data.objects.new('Plant_LOD3', me); bpy.context.scene.collection.objects.link(obj)
white = me.color_attributes.new('Color', 'FLOAT_COLOR', 'POINT')
white.data.foreach_set('color', [1.0] * 4 * len(me.vertices)); me.color_attributes.active_color = white
wind = bpy.data.materials['Leaves']['openyamm_wind']
m = dl.material('Impostor', os.path.join(WORK, 'impostor_basecolor.png'), os.path.join(WORK, 'impostor_normal.png'),
                wind, True, 0.9)
del m['openyamm_translucency']
m['openyamm_billboard'] = True
me.materials.append(m)
names = ['Plant', 'Plant_LOD1', 'Plant_LOD2', 'Plant_LOD3']
for o in bpy.data.objects:
    o.select_set(o.name in names)
bpy.context.view_layer.objects.active = bpy.data.objects['Plant']
out = os.path.join(WORK, 'plant_export.glb')
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True, export_extras=True,
                          export_normals=True, export_vertex_color='ACTIVE', export_tangents=False,
                          export_animations=False, export_skins=False, export_morph=False, export_image_format='AUTO',
                          export_apply=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'export.blend'))
print('EXPORTED', out)
