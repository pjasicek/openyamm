"""Ring of textured head renders (12 azimuths x 3 elevations, ortho, Standing frame 0, flat emission of the base colour
so lighting does not differ) of the per-LOD GLBs written by lod_check.py. Usage: blender -b -P green_ring.py -- <label> <level>
-> work/ring/<label>_<level>_<az>_<el>.png"""
import math, os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
label, level = sys.argv[sys.argv.index('--') + 1:][:2]
out = os.path.join(HERE, 'work', 'ring'); os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'work', f'lodcheck_{label}_{level}.glb'))
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
rig.animation_data.action = bpy.data.actions['Standing']; sc.frame_set(0)
for m in bpy.data.materials:
    if not m.use_nodes:
        continue
    nt = m.node_tree; bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    outn = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
    if bsdf and bsdf.inputs['Base Color'].links:
        em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(bsdf.inputs['Base Color'].links[0].from_socket, em.inputs['Color'])
        nt.links.new(em.outputs[0], outn.inputs['Surface'])
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = .3
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (0, 0, 0, 1)
sc.view_settings.view_transform = 'Standard'; sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x = sc.render.resolution_y = 400
c = rig.matrix_world @ rig.pose.bones['B_Head'].head + Vector((0, 0, .07))
for az in range(0, 360, 30):
    for el in (-20, 10, 40):
        d = Vector((math.sin(math.radians(az)) * math.cos(math.radians(el)), -math.cos(math.radians(az)) * math.cos(math.radians(el)), math.sin(math.radians(el))))
        cam.location = c + d * 2; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = os.path.join(out, f'{label}_{level}_{az:03d}_{el:+03d}.png'); bpy.ops.render.render(write_still=True)
print('RING done')
