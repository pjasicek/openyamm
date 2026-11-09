"""Close-up shots of a GLB's LOD0 (LODs and shadow meshes dropped), textured, back faces culled as in the game.
Args (Blender): <glb> <shots json> <out dir> [lod=0]
shots json: [{"name", "clip" (or null = bind pose), "f30", "az", "el", "at": bone name | [x, y, z] (Blender world) | "body",
              "size" (ortho m, default 0.5), "mode": "tex" | "red" | "clay", "res" (default 600)}]
tex: texture, background magenta (a hole shows magenta); red: texture plus a normal-flipped red twin (any view onto a back
face is red: inside an opening); clay: flat grey, back faces red. Camera direction as see_through_gate.py (az 0 = -Y)."""
import bpy, bmesh, sys, os, json, math
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
GLB, SPEC, OUTD = a[:3]
opt = dict(x.split('=', 1) for x in a[3:])
LOD = opt.get('lod', '0')
os.makedirs(OUTD, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')


def keep(o):
    n = o.name
    if 'Shadow' in n:
        return False
    if LOD == '0':
        return 'LOD' not in n
    return f'LOD{LOD}' in n


meshes = [o for o in bpy.data.objects if o.type == 'MESH']
for o in meshes:
    if not keep(o) or o.parent != rig:
        bpy.data.objects.remove(o)
mesh = next(o for o in bpy.data.objects if o.type == 'MESH' and o.parent == rig)
twin = mesh.copy(); twin.data = mesh.data.copy(); twin.name = 'Twin'
bpy.context.scene.collection.objects.link(twin)
bm = bmesh.new(); bm.from_mesh(twin.data); bmesh.ops.reverse_faces(bm, faces=bm.faces[:]); bm.to_mesh(twin.data); bm.free()
red = bpy.data.materials.new('Red'); red.diffuse_color = (1, 0, 0, 1)
twin.data.materials.clear(); twin.data.materials.append(red)
for p in twin.data.polygons:
    p.material_index = 0
sc = bpy.context.scene
FPS = sc.render.fps / sc.render.fps_base
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.show_backface_culling = True
sc.display.render_aa = '8'
sc.view_settings.view_transform = 'Standard'
sh.background_type = 'VIEWPORT'
sh.background_color = (1, 0, 1)
sc.world = bpy.data.worlds.new('W')
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'; cd.clip_start = 0.01; cd.clip_end = 20
cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
rig.animation_data_create()
acts = {x.name: x for x in bpy.data.actions}
for s in json.load(open(SPEC)):
    if s.get('clip'):
        act = acts[s['clip']]
        rig.animation_data.action = act
        if getattr(act, 'slots', None) is not None and len(act.slots):
            rig.animation_data.action_slot = act.slots[0]
        f0 = act.frame_range[0]; f = f0 + s.get('f30', 0) / 30.0 * FPS
        sc.frame_set(int(f), subframe=f % 1.0)
    else:
        rig.animation_data.action = None
        for pb in rig.pose.bones:
            pb.matrix_basis.identity()
        sc.frame_set(0)
    bpy.context.view_layer.update()
    at = s.get('at', 'body')
    if isinstance(at, list):
        c = Vector(at)
    elif at == 'body':
        dg = bpy.context.evaluated_depsgraph_get(); ev = mesh.evaluated_get(dg); em = ev.to_mesh()
        pts = [ev.matrix_world @ v.co for v in em.vertices]
        c = sum(pts, Vector()) / len(pts)
        lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
        c = (lo + hi) / 2; ev.to_mesh_clear()
    else:
        pb = rig.pose.bones[at]; c = rig.matrix_world @ pb.head
        if s.get('along'):
            c = rig.matrix_world @ (pb.head + (pb.tail - pb.head) * s['along'])
    az, el = math.radians(s.get('az', 0)), math.radians(s.get('el', 0))
    d = Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))
    cam.location = c + d * 4.0
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    cd.ortho_scale = s.get('size', 0.5)
    res = s.get('res', 600)
    sc.render.resolution_x = sc.render.resolution_y = res
    mode = s.get('mode', 'tex')
    twin.hide_render = mode == 'tex'
    sc.render.film_transparent = mode.startswith('gate')
    sc.display.render_aa = 'OFF' if mode.startswith('gate') else '8'
    if mode == 'gate':
        sh.light = 'FLAT'; sh.color_type = 'OBJECT'; mesh.color = (0.6, 0.6, 0.6, 1); twin.color = (1, 0, 0, 1)
    elif mode == 'gatetex':
        sh.light = 'FLAT'; sh.color_type = 'TEXTURE'; twin.hide_render = True
    elif mode == 'clay':
        sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'
        sh.color_type = 'SINGLE'; sh.single_color = (0.6, 0.6, 0.6)
        twin.hide_render = False
    else:
        sh.light = 'STUDIO'; sh.color_type = 'TEXTURE'
    if mode == 'gate':
        pass
    elif mode == 'clay':
        # twin red through the object colour: single colour applies to every object, so use OBJECT colours
        sh.color_type = 'OBJECT'; mesh.color = (0.6, 0.6, 0.6, 1); twin.color = (1, 0, 0, 1)
    elif mode == 'red':
        # texture for the mesh; the twin's material colour (red) via TEXTURE mode falls back to material colour
        pass
    sc.render.filepath = os.path.join(OUTD, s['name'] + '.png')
    bpy.ops.render.render(write_still=True)
    print('VIEW', s['name'])
