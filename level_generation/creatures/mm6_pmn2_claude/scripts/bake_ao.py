"""Bake ambient occlusion of the rest-pose mage (work/rig_v8.blend, body mesh only; the staff casts no AO into the
atlas) into work/ao_wide.png (15 cm reach: shade under the mantle, armpits, between legs) and work/ao_tight.png (3 cm:
creases, knuckles, rope/pouch contact), 2048, linear."""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'rig_v8.blend'))
rig = bpy.data.objects['Mage_Rig']; rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
m = bpy.data.objects['Mage']
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
scene.world = scene.world or bpy.data.worlds.new('W')
mat = bpy.data.materials.new('AO'); mat.use_nodes = True
m.data.materials.clear(); m.data.materials.append(mat)
for o in bpy.data.objects:
    o.select_set(o == m)
bpy.context.view_layer.objects.active = m
for name, reach in (('ao_wide', 0.15), ('ao_tight', 0.03)):
    scene.world.light_settings.distance = reach
    img = bpy.data.images.new(name, 2048, 2048, alpha=False, float_buffer=False); img.colorspace_settings.name = 'Non-Color'
    t = mat.node_tree.nodes.new('ShaderNodeTexImage'); t.image = img; mat.node_tree.nodes.active = t
    bpy.ops.object.bake(type='AO', margin=8)
    img.filepath_raw = os.path.join(common.WORK, name + '.png'); img.file_format = 'PNG'; img.save()
    print('AO baked', name)
