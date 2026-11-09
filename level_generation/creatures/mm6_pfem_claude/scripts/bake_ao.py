"""Bake ambient occlusion of the rest-pose Peasant into the UV atlas (work/ao.png, 2048, linear)."""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
rig = bpy.data.objects['Peasant_Rig']; rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
bpy.context.view_layer.update()
m = bpy.data.objects['Peasant']
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o != m:
        bpy.data.objects.remove(o, do_unlink=True)
scene = bpy.context.scene; scene.render.engine = 'CYCLES'
prefs = bpy.context.preferences.addons['cycles'].preferences
for kind in ('OPTIX', 'CUDA'):
    try:
        prefs.compute_device_type = kind; prefs.get_devices()
        for d in prefs.devices: d.use = True
        scene.cycles.device = 'GPU'; break
    except Exception:
        continue
scene.cycles.samples = 128
scene.world = scene.world or bpy.data.worlds.new('W'); scene.world.light_settings.distance = 0.06
mat = bpy.data.materials.new('AO'); mat.use_nodes = True
m.data.materials.clear(); m.data.materials.append(mat)
img = bpy.data.images.new('ao', 2048, 2048, alpha=False, float_buffer=False); img.colorspace_settings.name = 'Non-Color'
t = mat.node_tree.nodes.new('ShaderNodeTexImage'); t.image = img; mat.node_tree.nodes.active = t
for o in bpy.data.objects: o.select_set(o == m)
bpy.context.view_layer.objects.active = m
bpy.ops.object.bake(type='AO', margin=8)
img.filepath_raw = os.path.join(common.WORK, 'ao.png'); img.file_format = 'PNG'; img.save()
print('AO baked')
