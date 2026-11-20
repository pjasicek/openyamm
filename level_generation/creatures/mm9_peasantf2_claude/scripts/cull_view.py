"""Back-face-culled Workbench views of a GLB (LOD0 only) on magenta: holes show magenta. Args: <glb> <out prefix> <cx,cy,cz> <ortho> <views name=dx,dy,dz:...> [clip:seconds]"""
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=a[0])
for o in bpy.data.objects:
    if o.type == 'MESH' and ('LOD' in o.name or 'Shadow' in o.name): o.hide_render = True
if len(a) > 5:
    clip, t = a[5].split(':'); rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE'); act = next(x for x in bpy.data.actions if x.name.startswith(clip))
    rig.animation_data_create(); rig.animation_data.action = act
    try: rig.animation_data.action_slot = act.slots[0]
    except Exception: pass
    bpy.context.scene.frame_set(int(float(t) * 24))
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'MATERIAL'; sh.show_backface_culling = True
sc.render.resolution_x = sc.render.resolution_y = 700; sc.world = bpy.data.worlds.new('W'); sc.world.color = (1, 0, 1); sh.background_type = 'WORLD'
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'; cd.ortho_scale = float(a[3]); cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
ce = Vector([float(x) for x in a[2].split(',')])
for v in a[4].split(':'):
    nm, d = v.split('='); d = Vector([float(x) for x in d.split(',')]).normalized(); cam.location = ce + d * 5; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[1]}_{nm}.png'; bpy.ops.render.render(write_still=True)
