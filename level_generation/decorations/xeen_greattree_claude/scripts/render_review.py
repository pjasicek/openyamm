"""Eevee review renders of a crown blend (sun + sky, alpha-clipped leaves, Standard view). Materials get the
engine's vertex-colour rule (base colour x COLOR_0 'Color'); mode 'occlusion' renders the vertex colour alone.
Args: <id> out_prefix blend views [mode] [resolution_height] [noshadow] [framing height].

Views (adapted from the MM8 batch's render_review.py):
 - crown alone, framed by its height as the MM8 review cameras: eye (front), three_quarter, back, side, close,
   under (below the crown, looking up into it);
 - in context (16:9, with a stand-in for A6's trunk: 16-sided, xdbark, radius 760 -> 547 units, the root foot, the
   ground; the crown placed `placement.overlap` units below the trunk top): green4k / green6k (the party's eye, 180
   units up, 4,000 / 6,000 units from the trunk axis), far (14,000 units), foot (at the trunk's foot, looking up
   65 degrees: the crown fills the screen). Context views render LOD0 only, except `far`, which renders every LOD."""
import bpy, bmesh, sys, os, math
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
spec = common.load()
args = sys.argv[sys.argv.index('--') + 2:]       # after the species id
prefix, blend, views = args[0], args[1], args[2].split(',')
mode = args[3] if len(args) > 3 else 'lit'
res = int(args[4]) if len(args) > 4 else 540
bpy.ops.wm.open_mainfile(filepath=blend)
sc = bpy.context.scene
for engine in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
    try:
        sc.render.engine = engine; break
    except TypeError:
        continue
sc.view_settings.view_transform = 'Standard'
sc.render.film_transparent = True
world = sc.world or bpy.data.worlds.new('W'); sc.world = world; world.use_nodes = True
bg = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND')
bg.inputs['Color'].default_value = (0.55, 0.6, 0.68, 1); bg.inputs['Strength'].default_value = 0.5
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 3.6; sun.data.color = (1.0, 0.95, 0.86)
sun.rotation_euler = (math.radians(40), 0, math.radians(-35))
if len(args) > 5 and args[5] == 'noshadow':     # like the engine: no shadow maps, no screen-space occlusion or GI
    sun.data.use_shadow = False
    sc.eevee.use_shadows = False; sc.eevee.use_fast_gi = False; sc.eevee.use_raytracing = False
for m in bpy.data.materials:
    if not m.use_nodes:
        continue
    nt = m.node_tree; bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if bsdf is None or not bsdf.inputs['Base Color'].links:
        continue
    tex = bsdf.inputs['Base Color'].links[0].from_node
    bsdf.inputs['Specular IOR Level'].default_value = 0.15
    attr = nt.nodes.new('ShaderNodeAttribute'); attr.attribute_type = 'GEOMETRY'; attr.attribute_name = 'Color'
    if mode == 'occlusion':
        out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
        em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(attr.outputs['Color'], em.inputs['Color'])
        surface = em.outputs[0]
        if bsdf.inputs['Alpha'].links:
            clip = bsdf.inputs['Alpha'].links[0].from_node
            tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
            nt.links.new(clip.outputs[0], mx.inputs[0]); nt.links.new(tr.outputs[0], mx.inputs[1])
            nt.links.new(em.outputs[0], mx.inputs[2]); surface = mx.outputs[0]
        nt.links.new(surface, out.inputs['Surface'])
    elif mode == 'lit':
        mul = nt.nodes.new('ShaderNodeVectorMath'); mul.operation = 'MULTIPLY'
        nt.links.new(tex.outputs['Color'], mul.inputs[0]); nt.links.new(attr.outputs['Color'], mul.inputs[1])
        nt.links.new(mul.outputs[0], bsdf.inputs['Base Color'])
for m in bpy.data.materials:                   # the engine culls back faces of single-sided (opaque) materials
    if m.name in ('Bark', 'Shell'):
        m.use_backface_culling = True
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 50
lods = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('Tree')]
Hh = max((o.matrix_world @ Vector(c)).z for o in lods for c in o.bound_box)
if len(args) > 6:
    Hh = float(args[6])
# the crown is wider than tall: crown-alone views frame the larger of its height and its width (in the 480 x 540
# portrait frame), aimed at half the height as before
Wd = max(max(abs((o.matrix_world @ Vector(c))[i]) for o in lods if o.name == 'Tree' for c in o.bound_box) for i in (0, 1)) * 2
FRAME = max(Hh, Wd * 540 / 480)
target = Vector((0, 0, Hh * 0.5))
CAMS = {'eye': (0.0, 1.6), 'three_quarter': (45.0, 5.5), 'back': (180.0, 1.6), 'side': (90.0, 1.6),
        'under': (0.0, 1.5), 'close': (30.0, 3.5)}
# ---------------------------------------------------------------- context: trunk stand-in and ground
P = spec['placement']; U = common.UNITS_PER_METRE
GROUND = -(P['trunk_top'] - P['overlap']) / U                 # ground height in the model's frame (m)
EYE = GROUND + P['eye'] / U
CONTEXT = {  # name: (distance from the axis in units, lens mm, aim point z m, pitch override degrees)
    'green4k': (4000, 18, 6.0, None), 'green6k': (6000, 22, 4.0, None), 'far': (14000, 40, 0.0, None),
    'foot': (P['trunk_r_base'] + 120, 14, None, 62.0)}
for _name in list(CONTEXT):                      # <view>_bare: the same camera, crown alone on a transparent film
    CONTEXT[_name + '_bare'] = CONTEXT[_name]
context_objs = []
if any(v in CONTEXT for v in views):
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    n = 16; ta, tl = common.BARK_TILE_M
    levels = [(GROUND - 0.5, P['trunk_r_base'] / U), (GROUND + P['foot'] / U, P['trunk_r_base'] / U),
              ((P['overlap'] / U), P['trunk_r_top'] / U)]
    rings = [[bm.verts.new((r * math.cos(2 * math.pi * (j + 0.5) / n), r * math.sin(2 * math.pi * (j + 0.5) / n), z))
              for j in range(n)] for z, r in levels]
    for (ra, (za, rA)), (rb, (zb, rB)) in zip(zip(rings, levels), zip(rings[1:], levels[1:])):
        for j in range(n):
            j2 = (j + 1) % n
            f = bm.faces.new((ra[j], ra[j2], rb[j2], rb[j]))
            side_a = 2 * rA * math.sin(math.pi / n) / ta; side_b = 2 * rB * math.sin(math.pi / n) / ta
            for loop, uv in zip(f.loops, ((j * side_a, za / tl), ((j + 1) * side_a, za / tl),
                                          ((j + 1) * side_b, zb / tl), (j * side_b, zb / tl))):
                loop[uvl].uv = uv
    top = bm.faces.new(rings[-1])
    for loop in top.loops:
        loop[uvl].uv = (loop.vert.co.x / ta, loop.vert.co.y / tl)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new('TrunkProxy'); bm.to_mesh(me); bm.free()
    attr = me.color_attributes.new('Color', 'FLOAT_COLOR', 'POINT')
    attr.data.foreach_set('color', [1.0] * 4 * len(me.vertices))
    me.materials.append(bpy.data.materials['Bark'])
    trunk = bpy.data.objects.new('TrunkProxy', me); sc.collection.objects.link(trunk)
    bpy.ops.mesh.primitive_plane_add(size=600, location=(0, 0, GROUND))
    ground = bpy.context.active_object; ground.name = 'GroundProxy'
    gm = bpy.data.materials.new('GroundProxy'); gm.use_nodes = True
    gb = next(n for n in gm.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    gb.inputs['Base Color'].default_value = (0.035, 0.05, 0.03, 1); gb.inputs['Roughness'].default_value = 1.0
    ground.data.materials.append(gm)
    context_objs = [trunk, ground]
    for o in context_objs:
        o.hide_render = True


def shoot(view, o):
    sc.render.filepath = f'{prefix}_{o.name}_{view}.png'
    bpy.ops.render.render(write_still=True)
    print('RENDERED', sc.render.filepath)


for o in lods:
    for x in lods:
        x.hide_render = x is not o
    for view in views:
        if view in CONTEXT:
            if o.name != 'Tree' and view != 'far':
                continue
            dist, lens, aim_z, pitch = CONTEXT[view]
            bare = view.endswith('_bare')
            for c in context_objs:
                c.hide_render = bare
            sc.render.film_transparent = bare
            sc.render.resolution_y = res; sc.render.resolution_x = int(res * 16 / 9)
            cam.data.sensor_fit = 'HORIZONTAL'; cam.data.lens = lens; cam.data.clip_end = 2000
            cam.location = (0.0, -dist / U, EYE)
            if pitch is not None:
                cam.rotation_euler = (math.radians(90 + pitch), 0.0, 0.0)
            else:
                cam.rotation_euler = (Vector((0, 0, aim_z)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
            shoot(view, o)
            for c in context_objs:
                c.hide_render = True
            sc.render.film_transparent = True
            cam.data.sensor_fit = 'AUTO'
            continue
        if o.name != 'Tree' and 'close' in views:
            continue
        sc.render.resolution_y = res; sc.render.resolution_x = int(res * 480 / 540)
        cam.data.lens = 50; cam.data.clip_end = 1000
        yaw, height = CAMS[view]
        scale = FRAME / 6.69                      # framing as for the 6.69 m MM6 tree, whatever the size
        d = (2.6 if view == 'under' else 5.2 if view == 'close' else 10.5) * scale; height *= scale
        if view == 'under':                       # looking up into the crown from below its rim
            cam.data.lens = 24
        cam.location = (math.sin(math.radians(yaw)) * d, -math.cos(math.radians(yaw)) * d, height)
        aim = Vector((0, 0, Hh * 0.62)) if view in ('under', 'close') else target
        cam.rotation_euler = (aim - cam.location).to_track_quat('-Z', 'Y').to_euler()
        shoot(view, o)
