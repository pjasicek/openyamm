"""Close-ups for the review fixes (Standing frame 0, model faces -Y): both upper arms at the cuffs (front/side/back),
hairline (front/3-4 both sides/side/top-back), tunic chest. Usage: blender -b -P detail_views.py -- <glb> <label>"""
import os, sys, math, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
glb, label = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
sc = bpy.context.scene; rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
rig.animation_data.action = bpy.data.actions['Standing']; sc.frame_set(0)
B = lambda n: rig.matrix_world @ rig.pose.bones[n].head
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.type = 'ORTHO'
for name, rot, e in [('Key', (math.radians(55), 0, math.radians(-30)), 3.0), ('Fill', (math.radians(70), 0, math.radians(140)), 1.2)]:
    s = bpy.data.objects.new(name, bpy.data.lights.new(name, 'SUN')); s.data.energy = e; s.rotation_euler = rot; sc.collection.objects.link(s)
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs['Color'].default_value = (.35, .35, .38, 1)
if os.environ.get('EMIT'):   # base colour only (no lighting): separates texture from shading problems
    for m in bpy.data.materials:
        if not m.use_nodes: continue
        nt = m.node_tree; bs = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if bs is None or not bs.inputs['Base Color'].is_linked: continue
        src = bs.inputs['Base Color'].links[0].from_socket; out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
        em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(src, em.inputs['Color']); nt.links.new(em.outputs['Emission'], out.inputs['Surface'])
sc.view_settings.view_transform = 'Standard'; sc.render.engine = 'BLENDER_EEVEE'; sc.render.resolution_x = sc.render.resolution_y = 560
elbowL, elbowR = B('B_L_Forearm'), B('B_R_Forearm'); armL, armR = B('B_L_UpperArm'), B('B_R_UpperArm')
head = B('B_Head') + Vector((0, 0, .1))
spots = {'armL': ((armL * .45 + elbowL * .55), .22, {'front': (0, -1, .05), 'side': (1, 0, .05), 'back': (0, 1, .05), 'under': (.2, -.3, -1)}),
         'armR': ((armR * .45 + elbowR * .55), .22, {'front': (0, -1, .05), 'side': (-1, 0, .05), 'back': (0, 1, .05), 'under': (-.2, -.3, -1)}),
         'hair': (head, .22, {'front': (0, -1, .1), 'q34r': (.65, -.75, .15), 'q34l': (-.65, -.75, .15), 'side': (1, 0, .1), 'sidel': (-1, 0, .1), 'back': (0, 1, .1)}),
         'tunic': (B('B_Spine1'), .45, {'front': (0, -1, .05), 'back': (0, 1, .05)})}
out = os.path.join(HERE, 'review', 'fix'); os.makedirs(out, exist_ok=True)
for spot, (c, size, views) in spots.items():
    for view, d in views.items():
        dv = Vector(d).normalized(); cam.location = c + dv * 4; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.ortho_scale = size
        sc.render.filepath = os.path.join(out, f'{label}_{spot}_{view}.png'); bpy.ops.render.render(write_still=True)
