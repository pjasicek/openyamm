"""Close-up stills of a runtime GLB (LOD0) at clip frames, back faces culled as in the game (Workbench, textured, studio
light, viewer-grey background). Optional red twin: a normal-flipped copy drawn in flat red shows where the view meets the
inside of the cloth (back faces nearest); background = a see-through hole.
Args (Blender): <glb> <out dir> <tier a|b> <spec> [spec ...]
  spec = name|clip (or bind)|frame30|target|az|el|ortho[|twin][|cut]   (cut: the near half in front of the target is clipped
  away, a section through the target)
  target = bone name, or 'Bone@t' (lerp from the bone's head to its first child's head), or 'x,y,z'
  az/el in degrees (az 0: camera on -Y looking +Y; el > 0 from above), ortho in metres (frame width).
Writes <out dir>/<name>.png (512 px)."""
import bpy, bmesh, sys, os, math
from mathutils import Vector

a = sys.argv[sys.argv.index('--') + 1:]
GLB, OD, TIER = a[0], a[1], a[2]
SPECS = a[3:]
RES = 512
os.makedirs(OD, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
mesh = next(o for o in bpy.data.objects if o.type == 'MESH' and o.parent == rig and 'LOD' not in o.name
            and 'Shadow' not in o.name)
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o is not mesh:
        bpy.data.objects.remove(o)
if TIER == 'b':
    mats = {m.name: m for m in bpy.data.materials}
    for slot in mesh.material_slots:
        if slot.material is None:
            continue
        n = slot.material.name
        cand = [k for k in mats if k != n and k.startswith(n.rsplit('_', 1)[0]) and (k.endswith('_B') or k.endswith('_b')
                                                                                  or '_b' in k[len(n):])]
        if n.endswith('_A') and n[:-2] + '_B' in mats:
            slot.material = mats[n[:-2] + '_B']
        elif cand:
            slot.material = mats[cand[0]]
    print('CLOSEUP tier b materials', [s.material.name for s in mesh.material_slots if s.material])
twin = mesh.copy(); twin.data = mesh.data.copy(); twin.name = 'Twin'
bpy.context.scene.collection.objects.link(twin)
bm = bmesh.new(); bm.from_mesh(twin.data)
bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
bm.to_mesh(twin.data); bm.free()
red = bpy.data.materials.new('RedInside'); red.diffuse_color = (1, 0, 0, 1)
twin.data.materials.clear(); twin.data.materials.append(red)
for p in twin.data.polygons:
    p.material_index = 0
sc = bpy.context.scene
FPS = sc.render.fps / sc.render.fps_base
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.light = 'STUDIO'; sh.color_type = 'TEXTURE'; sh.show_backface_culling = True
sh.show_specular_highlight = False
sc.display.render_aa = '8'
sc.render.film_transparent = False
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.33, 0.34, 0.36)
sc.view_settings.view_transform = 'Standard'
sc.render.resolution_x = sc.render.resolution_y = RES
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'
cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
rig.animation_data_create()
for spec in SPECS:
    f = spec.split('|')
    name, clip, f30, tgt, az, el, ortho = f[0], f[1], int(f[2]), f[3], float(f[4]), float(f[5]), float(f[6])
    use_twin = 'twin' in f[7:]
    cd.clip_start = 4.0 if 'cut' in f[7:] else 0.1
    if clip == 'bind':                  # PeasantDM4: rest pose (MM9's converted models have no Standing clip)
        rig.animation_data.action = None
        for pb in rig.pose.bones:
            pb.matrix_basis.identity()
    else:
        act = bpy.data.actions[clip]
        rig.animation_data.action = act
        if getattr(act, 'slots', None) is not None and len(act.slots):
            rig.animation_data.action_slot = act.slots[0]
        fr = act.frame_range[0] + f30 / 30.0 * FPS
        sc.frame_set(int(fr), subframe=fr % 1.0)
    bpy.context.view_layer.update()
    if ',' in tgt:
        T = Vector([float(x) for x in tgt.split(',')])
    else:
        bn, t = (tgt.split('@') + ['0'])[:2]
        pb = rig.pose.bones[bn]
        h = rig.matrix_world @ pb.head
        nxt = rig.matrix_world @ (pb.children[0].head if pb.children else pb.tail)
        T = h.lerp(nxt, float(t))
    d = Vector((math.sin(math.radians(az)) * math.cos(math.radians(el)),
                -math.cos(math.radians(az)) * math.cos(math.radians(el)), math.sin(math.radians(el))))
    cam.location = T + d * 4.0
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    cd.ortho_scale = ortho
    twin.hide_render = not use_twin
    sc.render.filepath = os.path.join(OD, name + '.png')
    bpy.ops.render.render(write_still=True)
    print('CLOSEUP', name)
