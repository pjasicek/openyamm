"""Bake base colour and tangent normals from the Meshy detail source onto the Peasant atlas (selected-to-active)."""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
DY = 0.019
outdir = os.path.join(common.PROJECT, 'texturing')
rig = bpy.data.objects['Peasant_Rig']; rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
with bpy.data.libraries.load(os.path.join(common.WORK, 'meshy_fitted.blend')) as (src, dst):
    dst.objects = ['MeshyDetail']
meshy = dst.objects[0]; bpy.context.scene.collection.objects.link(meshy); meshy.location.y -= DY
target = bpy.data.objects['Peasant']
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
prefs = bpy.context.preferences.addons['cycles'].preferences
for kind in ('OPTIX', 'CUDA'):
    try:
        prefs.compute_device_type = kind; prefs.get_devices()
        for d in prefs.devices: d.use = True
        scene.cycles.device = 'GPU'; break
    except Exception:
        continue
scene.cycles.samples = 16
mat = bpy.data.materials.new('BakeTarget'); mat.use_nodes = True
target.data.materials.clear(); target.data.materials.append(mat)
nodes = mat.node_tree.nodes
tex = nodes.new('ShaderNodeTexImage')
for o in bpy.data.objects: o.select_set(o in (meshy, target))
bpy.context.view_layer.objects.active = target
for kind, colourspace in (('DIFFUSE', 'sRGB'), ('NORMAL', 'Non-Color')):
    img = bpy.data.images.new(f'bake_{kind.lower()}', 2048, 2048, alpha=False, float_buffer=False)
    img.colorspace_settings.name = colourspace
    tex.image = img; nodes.active = tex
    kwargs = dict(type=kind, use_selected_to_active=True, cage_extrusion=0.025, max_ray_distance=0.06, margin=8)
    if kind == 'DIFFUSE':
        kwargs['pass_filter'] = {'COLOR'}
    bpy.ops.object.bake(**kwargs)
    img.filepath_raw = os.path.join(outdir, f'bake_{kind.lower()}.png'); img.file_format = 'PNG'; img.save()
    print('BAKED', kind)
