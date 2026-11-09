"""Join reviewed parts, preserve provenance, and export the provisional rig upload."""
import bpy, json
from pathlib import Path
P = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P / 'work/anatomy_v2_parts.blend'))
parts = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('P')]
bpy.ops.object.select_all(action='DESELECT')
for o in parts:
    attr = o.data.attributes.new('piece', 'INT', 'POINT')
    attr.data.foreach_set('value', [int(o.name[1:])] * len(o.data.vertices))
    o.data.materials.clear()
    o.select_set(True)
bpy.context.view_layer.objects.active = bpy.data.objects['P00']
bpy.ops.object.join()
body = bpy.context.object
body.name = body.data.name = 'Body'
body.data.attributes.new('orig_co', 'FLOAT_VECTOR', 'POINT').data.foreach_set(
    'vector', [c for v in body.data.vertices for c in v.co])
mat = bpy.data.materials.new('Provisional clay for rigging')
mat.use_nodes = True
im = bpy.data.images.new('Provisional_clay', width=1, height=1, alpha=True)
im.pixels = [0.55, 0.55, 0.55, 1.0]
im.pack()
tex = mat.node_tree.nodes.new('ShaderNodeTexImage')
tex.image = im
mat.node_tree.links.new(tex.outputs['Color'], mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
body.data.materials.append(mat)
if not body.data.uv_layers:
    body.data.uv_layers.new(name='ProvisionalUV')
for p in body.data.polygons:
    p.material_index = 0
    p.use_smooth = True
assert len(parts) == 17 and len(body.data.vertices) > 20000
bpy.ops.wm.save_as_mainfile(filepath=str(P / 'work/step1.blend'))
(P / 'export').mkdir(exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(P / 'export/m424_clean_v1.glb'), export_format='GLB',
    use_selection=True, export_animations=False, export_yup=True, export_extras=True)
s = json.loads((P / 'creature_3d_progress.json').read_text())
s['stages']['references_and_motion']['note'] = 'All five body and four selected head views complete; corrected head three-quarter is 01_three_quarter_v2.png.'
s['stages']['model_and_rig']['substep'] = 'Reviewed corrected geometry; provisional textured GLB ready for rig joint/weight estimates.'
s['geometry_corrections'] = {'ears': 'Locally extended ear tips to match native pointed anatomy.', 'hands': 'Restored missing ring fingers; four separated long fingers and preserved thumbs, both sides. Closed repaired hand surfaces.', 'evidence': 'work/anatomy_v2_report.json', 'remaining': 'Reduce dense interim hand surfaces after weighting and check deformation; inspect scalp coverage under textured hair.'}
s['next_action']['action'] = 'Submit rig estimate, compare measured joint rings, fit source frames and finger chains.'
(P / 'creature_3d_progress.json').write_text(json.dumps(s, indent=2) + '\n')
(P / 'requests/rig_v1.json').write_text(json.dumps({'model_url': '@file:export/m424_clean_v1.glb', 'height_meters': 1.7}, indent=2) + '\n')
print('RIG_UPLOAD', len(body.data.vertices), sum(len(p.vertices)-2 for p in body.data.polygons))
