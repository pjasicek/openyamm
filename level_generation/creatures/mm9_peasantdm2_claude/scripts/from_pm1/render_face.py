"""Unlit (albedo) orthographic front render of the head of an export GLB, rest pose, for the Codex face repaint and its
back-projection (project_face.py uses the same camera). Blender space: the face looks to -Y.
Args: -- <glb> <out png> <cx> <cz> <ortho m> <size px> [view: front|high]   (high: 20 deg from above, review only)"""
import bpy, sys, math
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
glb, out, cx, cz, ortho, size = a[0], a[1], float(a[2]), float(a[3]), float(a[4]), int(a[5])
view = a[6] if len(a) > 6 else 'front'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
for o in bpy.data.objects:
    if o.type == 'ARMATURE':
        if o.animation_data:
            o.animation_data.action = None
        for pb in o.pose.bones:
            pb.matrix_basis.identity()
    if o.type == 'MESH' and ('LOD' in o.name or 'Shadow' in o.name):
        o.hide_render = True
for m in bpy.data.materials:
    if not m.use_nodes:
        continue
    nt = m.node_tree
    bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    outn = next((n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'), None)
    if bsdf is None or outn is None:
        continue
    link = bsdf.inputs['Base Color'].links
    em = nt.nodes.new('ShaderNodeEmission')
    if link:
        nt.links.new(link[0].from_socket, em.inputs['Color'])
    nt.links.new(em.outputs['Emission'], outn.inputs['Surface'])
sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE'
sc.view_settings.view_transform = 'Standard'
sc.render.resolution_x = sc.render.resolution_y = size
sc.render.film_transparent = True
sc.world = bpy.data.worlds.new('W')
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'; cd.ortho_scale = ortho
cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
c = Vector((cx, 0.0, cz))
d = Vector((0, -1, 0)) if view == 'front' else Vector((0, -math.cos(math.radians(20)), math.sin(math.radians(20))))
cam.location = c + d * 5
cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
cd.clip_end = 20
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print('FACE', out)
