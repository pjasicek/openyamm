"""Shared Blender helpers for the New Sorpigal props: procedural mesh builders (lathe, tube, box, quad), textured
materials from props/textures/, per-vertex canopy-style occlusion into the 'Color' attribute (glTF COLOR_0), LOD export
and review renders. Blender is Z-up; the glTF export converts to Y-up. Every prop is built around its base centre on
the ground (z = 0)."""
import bpy, bmesh, math, os
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

PROPS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(PROPS, 'textures')
REPO = os.path.abspath(os.path.join(PROPS, '..', '..', '..', '..'))
NATIVE = os.path.join(REPO, 'level_generation', 'decorations', 'mm6_new_sorpigal', 'native')


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


# ---------------------------------------------------------------- materials
_images = {}


def image(name, colorspace):
    key = (name, colorspace)
    if key not in _images:
        img = bpy.data.images.load(os.path.join(TEX, name)); img.colorspace_settings.name = colorspace
        _images[key] = img
    return _images[key]


def material(name, texture, alpha=False, extras=None):
    """Principled material from props/textures/<texture>_{basecolor,normal,mr}.png (mr: G rough, B metal). Alpha
    (base colour alpha) is wired when the material is cut out or blended; the alpha mode itself is set in finish.py."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    base = nt.nodes.new('ShaderNodeTexImage'); base.image = image(f'{texture}_basecolor.png', 'sRGB')
    nt.links.new(base.outputs['Color'], bsdf.inputs['Base Color'])
    if alpha:
        nt.links.new(base.outputs['Alpha'], bsdf.inputs['Alpha'])
        m.surface_render_method = 'BLENDED'
    normal_path = os.path.join(TEX, f'{texture}_normal.png')
    if os.path.exists(normal_path):
        tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = image(f'{texture}_normal.png', 'Non-Color')
        nm = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(tn.outputs['Color'], nm.inputs['Color'])
        nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    mr_path = os.path.join(TEX, f'{texture}_mr.png')
    if os.path.exists(mr_path):
        tr = nt.nodes.new('ShaderNodeTexImage'); tr.image = image(f'{texture}_mr.png', 'Non-Color')
        sep = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(tr.outputs['Color'], sep.inputs['Color'])
        nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness'])
        nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
    for key, value in (extras or {}).items():
        m[key] = value
    return m


# Fire flipbook shared by every fire decoration: the CC0 Unity Labs Flame02 recoloured to the MM torch flame
# (mm6_dungeons_3d/textures/FLAMES.md: 16 x 4 frames at 30 fps; show a frame's lower 80 %, the flame spans about 60 %
# of the card width with its flat base just above the card's bottom edge).
FLAME_TEXTURES = os.path.join(REPO, 'level_generation', 'decorations', 'mm6_dungeons_3d', 'textures')
FLAME_FLIPBOOK = [16, 4, 30]
FLAME_FRAME_TOP = 0.8


def flame_material(name='Fire', texture='flame02'):
    """Camera-facing flipbook material on the shared flame (finish.py makes it blended, double-sided and unlit)."""
    global TEX
    props = TEX
    TEX = FLAME_TEXTURES
    try:
        return material(name, texture, alpha=True, extras={'openyamm_billboard': True,
                                                           'openyamm_flipbook': list(FLAME_FLIPBOOK),
                                                           'openyamm_specular': 0.0})
    finally:
        TEX = props


# Graded Poly Haven (CC0) sets of the fire props (make_pbr_textures.py), same file naming as props/textures/.
PBR_TEXTURES = os.path.join(PROPS, 'textures_pbr')


def pbr_material(name, texture, alpha=False, extras=None):
    """material() on props/textures_pbr/<texture>_{basecolor,normal,mr}.png."""
    global TEX
    props = TEX
    TEX = PBR_TEXTURES
    try:
        return material(name, texture, alpha=alpha, extras=extras)
    finally:
        TEX = props


# ---------------------------------------------------------------- mesh builders (all return bmesh-built objects)
def to_object(name, bm, mat=None, smooth=True):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    obj = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(obj)
    if mat is not None:
        me.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = smooth
    return obj


def _uv_layer(bm):
    return bm.loops.layers.uv.verify()


def lathe(name, profile, segments, mat=None, u_repeat=1.0, v_scale=1.0, centre=(0, 0, 0), cap_top=False,
          cap_bottom=False, smooth=True):
    """Surface of revolution of profile [(radius, z), ...] (bottom to top) about the vertical axis through centre.
    u runs around (u_repeat times), v along the profile (v_scale per metre of profile length)."""
    bm = bmesh.new(); uv = _uv_layer(bm)
    cx, cy, cz = centre
    rings = []
    for r, z in profile:
        ring = []
        for s in range(segments):
            a = 2 * math.pi * s / segments
            ring.append(bm.verts.new((cx + r * math.cos(a), cy + r * math.sin(a), cz + z)))
        rings.append(ring)
    lengths = [0.0]
    for (r0, z0), (r1, z1) in zip(profile, profile[1:]):
        lengths.append(lengths[-1] + math.hypot(r1 - r0, z1 - z0))
    for i in range(len(profile) - 1):
        for s in range(segments):
            s2 = (s + 1) % segments
            f = bm.faces.new((rings[i][s], rings[i][s2], rings[i + 1][s2], rings[i + 1][s]))
            for loop, (uu, vv) in zip(f.loops, ((s, i), (s + 1, i), (s + 1, i + 1), (s, i + 1))):
                loop[uv].uv = (uu / segments * u_repeat, lengths[vv] * v_scale)
    for cap, ring in ((cap_bottom, rings[0]), (cap_top, rings[-1])):
        if cap:
            f = bm.faces.new(ring if ring is rings[-1] else list(reversed(ring)))
            for loop in f.loops:
                loop[uv].uv = (0.5 + (loop.vert.co.x - cx) * 0.5, 0.5 + (loop.vert.co.y - cy) * 0.5)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    return to_object(name, bm, mat, smooth)


def tube(name, a, b, radius_a, radius_b, sides, mat=None, u_repeat=1.0, v_scale=1.0, caps=True, twist=0.0):
    """Tapered cylinder from point a to point b (u around, v along: v_scale per metre)."""
    a, b = Vector(a), Vector(b); axis = (b - a); length = axis.length; axis.normalize()
    side = axis.orthogonal().normalized(); other = axis.cross(side)
    bm = bmesh.new(); uv = _uv_layer(bm)
    rings = []
    for end, centre, radius in ((0, a, radius_a), (1, b, radius_b)):
        ring = []
        for s in range(sides):
            angle = 2 * math.pi * s / sides + twist * end
            ring.append(bm.verts.new(centre + (side * math.cos(angle) + other * math.sin(angle)) * radius))
        rings.append(ring)
    for s in range(sides):
        s2 = (s + 1) % sides
        f = bm.faces.new((rings[0][s], rings[0][s2], rings[1][s2], rings[1][s]))
        for loop, (uu, vv) in zip(f.loops, ((s, 0), (s + 1, 0), (s + 1, 1), (s, 1))):
            loop[uv].uv = (uu / sides * u_repeat, vv * length * v_scale)
    if caps:
        for ring, flip in ((rings[0], True), (rings[1], False)):
            f = bm.faces.new(list(reversed(ring)) if flip else ring)
            for loop in f.loops:
                d = loop.vert.co - (a if flip else b)
                loop[uv].uv = (0.5 + d.dot(side) * 2, 0.5 + d.dot(other) * 2)
    return to_object(name, bm, mat, True)


def box(name, centre, size, mat=None, uv_scale=1.0):
    bm = bmesh.new(); uv = _uv_layer(bm)
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2])) + Vector(centre)
    for f in bm.faces:
        n = f.normal
        for loop in f.loops:
            co = loop.vert.co
            if abs(n.z) > 0.5:
                loop[uv].uv = (co.x * uv_scale, co.y * uv_scale)
            elif abs(n.x) > 0.5:
                loop[uv].uv = (co.y * uv_scale, co.z * uv_scale)
            else:
                loop[uv].uv = (co.x * uv_scale, co.z * uv_scale)
    return to_object(name, bm, mat, False)


def join(name, objects):
    # One shared texture-coordinate layer: imported meshes and built ones name theirs differently, and join would
    # otherwise keep them as separate layers (exporting zeros for the parts that only have the second one).
    for o in objects:
        while len(o.data.uv_layers) > 1:
            o.data.uv_layers.remove(o.data.uv_layers[-1])
        if o.data.uv_layers:
            o.data.uv_layers[0].name = 'UVMap'
    for o in bpy.data.objects:
        o.select_set(o in objects)
    bpy.context.view_layer.objects.active = objects[0]
    if len(objects) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active; obj.name = name; obj.data.name = name
    return obj


def triangles(obj):
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


def decimate_to(obj, target):
    """Collapse-decimate a copy-in-place until within the triangle budget."""
    bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True); bpy.context.view_layer.objects.active = obj
    start = triangles(obj)
    if start <= target:
        return start
    ratio = target / start
    for _ in range(12):
        mod = obj.modifiers.new('Decimate', 'DECIMATE'); mod.decimate_type = 'COLLAPSE'
        mod.ratio = ratio; mod.use_collapse_triangulate = True
        depsgraph = bpy.context.evaluated_depsgraph_get()
        count = sum(len(p.vertices) - 2 for p in obj.evaluated_get(depsgraph).data.polygons)
        if count <= target:
            bpy.ops.object.modifier_apply(modifier=mod.name)
            return count
        obj.modifiers.remove(mod); ratio *= target / count * 0.995
    raise RuntimeError(f'cannot decimate {obj.name} to {target}')


# ---------------------------------------------------------------- occlusion
def vertex_occlusion(obj, rays=48, distance=0.6, strength=0.75, floor=True, alpha=None, seed=5):
    """Ambient occlusion per vertex (rays over the normal's hemisphere against the object itself and, optionally, the
    ground plane z = 0) into the 'Color' point attribute, linear rgb = 1 - strength x occluded fraction.
    alpha: optional per-vertex callable (co) -> value for the colour alpha (flag flutter weight); default 1."""
    depsgraph = bpy.context.evaluated_depsgraph_get()
    bvh = BVHTree.FromObject(obj, depsgraph)
    rng = np.random.default_rng(seed)
    dirs = rng.normal(size=(rays, 3)); dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
    me = obj.data
    colours = []
    for v in me.vertices:
        n = v.normal; p = v.co + n * 0.002
        hit = 0
        for d in dirs:
            d = Vector(d)
            if d.dot(n) < 0:
                d = -d
            if floor and d.z < 0 and p.z + d.z * distance < 0:
                hit += 1; continue
            loc, *_ = bvh.ray_cast(p, d, distance)
            if loc is not None:
                hit += 1
        o = 1.0 - strength * hit / rays
        colours.append((o, o, o, alpha(v.co) if alpha else 1.0))
    attr = me.color_attributes.new('Color', 'FLOAT_COLOR', 'POINT')
    attr.data.foreach_set('color', np.array(colours, np.float32).ravel())
    me.color_attributes.active_color = attr
    return float(np.mean([c[0] for c in colours]))


def white_colour(obj, alpha=None):
    me = obj.data
    colours = [(1.0, 1.0, 1.0, alpha(v.co) if alpha else 1.0) for v in me.vertices]
    attr = me.color_attributes.new('Color', 'FLOAT_COLOR', 'POINT')
    attr.data.foreach_set('color', np.array(colours, np.float32).ravel())
    me.color_attributes.active_color = attr


# ---------------------------------------------------------------- export and review
def export(objects, path):
    """objects: [LOD0, LOD1, LOD2(, LOD3)] already named Base, Base_LOD1, ..."""
    for o in bpy.data.objects:
        o.select_set(o in objects)
    bpy.ops.export_scene.gltf(filepath=path, use_selection=True, export_format='GLB', export_yup=True,
                              export_extras=True, export_normals=True, export_vertex_color='ACTIVE',
                              export_tangents=False, export_animations=False, export_skins=False,
                              export_morph=False, export_image_format='AUTO', export_apply=True)
    print('EXPORTED', path, 'tris', [triangles(o) for o in objects])


def setup_render(resolution=(512, 512)):
    scene = bpy.context.scene
    for engine in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
        try:
            scene.render.engine = engine; break
        except TypeError:
            continue
    scene.eevee.taa_render_samples = 32
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.film_transparent = True
    scene.view_settings.view_transform = 'Standard'
    world = scene.world or bpy.data.worlds.new('World'); scene.world = world; world.use_nodes = True
    bg = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND')
    bg.inputs['Color'].default_value = (0.55, 0.62, 0.72, 1.0); bg.inputs['Strength'].default_value = 0.9
    sun = bpy.data.lights.new('Sun', 'SUN'); sun.energy = 3.2; sun.angle = math.radians(3)
    so = bpy.data.objects.new('Sun', sun); scene.collection.objects.link(so)
    so.rotation_euler = (math.radians(40), 0, math.radians(-35))
    return scene


def bounds(objects):
    pts = [o.matrix_world @ Vector(c) for o in objects for c in o.bound_box]
    return (Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))),
            Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts))))


def render_views(objects, out_dir, prefix, views=((0, 8), (40, 22)), lens=50):
    """Render the given objects alone from (yaw, elevation) views; returns the written paths."""
    scene = bpy.context.scene
    hidden = [o for o in bpy.data.objects if o.type == 'MESH' and o not in objects]
    for o in hidden:
        o.hide_render = True
    for o in objects:
        o.hide_render = False
    lo, hi = bounds(objects); centre = (lo + hi) / 2; radius = (hi - lo).length / 2
    cam = scene.camera
    if cam is None:
        cam = bpy.data.objects.new('Camera', bpy.data.cameras.new('Camera'))
        scene.collection.objects.link(cam); scene.camera = cam
    cam.data.lens = lens
    fov = 2 * math.atan(cam.data.sensor_width / (2 * lens))
    paths = []
    for yaw, elevation in views:
        y, e = math.radians(yaw), math.radians(elevation)
        d = Vector((math.sin(y) * math.cos(e), -math.cos(y) * math.cos(e), math.sin(e)))
        cam.location = centre + d * radius * 1.1 / math.sin(fov / 2)
        cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
        path = os.path.join(out_dir, f'{prefix}_y{yaw:03d}.png')
        scene.render.filepath = path; bpy.ops.render.render(write_still=True); paths.append(path)
    for o in hidden:
        o.hide_render = False
    return paths
