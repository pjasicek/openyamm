"""Job 7 diagnosis: one low 3/4 close-up of a static textured export rendered three ways - full material, normal map
off, base colour only (emission, unlit) - to tell paint lines from shading lines. Args: <glb> <out prefix> [side 1|-1]
[cam distance 0.35] [target x,y,z (Blender frame)]"""
import bpy, sys, math
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
glb, out = a[0], a[1]; SX = float(a[2]) if len(a) > 2 else 1.0; DIST = float(a[3]) if len(a) > 3 else 0.35
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
for o in bpy.data.objects:
    if o.type == 'MESH' and ('LOD' in o.name or 'hadow' in o.name): o.hide_render = True
sc = bpy.context.scene
try: sc.render.engine = 'BLENDER_EEVEE_NEXT'
except TypeError: sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x, sc.render.resolution_y = 1000, 700
sc.world = bpy.data.worlds.new('W'); sc.world.use_nodes = True
bg = next(n for n in sc.world.node_tree.nodes if n.type == 'BACKGROUND'); bg.inputs['Color'].default_value = (0.3, 0.32, 0.35, 1)
for nm, rot, en in (('key', (50, 0, 30 * SX), 3.0), ('fill', (60, 0, 160), 1.0)):
    ld = bpy.data.lights.new(nm, 'SUN'); ld.energy = en; lo = bpy.data.objects.new(nm, ld); sc.collection.objects.link(lo)
    lo.rotation_euler = [math.radians(x) for x in rot]
cd = bpy.data.cameras.new('C'); cd.lens = 50; cd.clip_start = 0.01
cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
tgt = Vector(tuple(float(x) for x in a[4].split(','))) if len(a) > 4 else Vector((SX * 0.035, -0.03, 0.985))
d = Vector((SX * 0.75, -0.6, -0.35)).normalized()
cam.location = tgt + d * DIST
cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
def render(tag):
    sc.render.filepath = f'{out}_{tag}.png'; bpy.ops.render.render(write_still=True)
render('full')
saved = []
for m in bpy.data.materials:
    if not m.use_nodes: continue
    nt = m.node_tree
    for n in nt.nodes:
        if n.type == 'NORMAL_MAP':
            for l in list(n.outputs[0].links): saved.append((m, l.from_socket, l.to_socket)); nt.links.remove(l)
render('nonormal')
for m in bpy.data.materials:
    if not m.use_nodes: continue
    nt = m.node_tree
    bs = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if bs is None: continue
    src = bs.inputs['Base Color'].links[0].from_socket if bs.inputs['Base Color'].links else None
    em = nt.nodes.new('ShaderNodeEmission'); o_ = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
    if src: nt.links.new(src, em.inputs[0])
    nt.links.new(em.outputs[0], o_.inputs[0])
render('albedo')
print('SHADESPLIT done')
