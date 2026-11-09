"""G1: preview library clips on the winged body before authoring. Each candidate = a library clip's trunk and arms
over the native flight (wings, legs, pelvis), a stand-in prop on a hand socket; frames rendered as a strip per
candidate (workbench, three-quarter front from the party's side). Writes review/g1/<set>_<clip>.png tiles list
review/g1/<set>.json for sheet assembly.
Args: -- <set name> <glb> <clip,clip,...> [prop: R|L|LR|2H] [frames per strip]"""
import bpy, sys, os, json, math
from pathlib import Path
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import clips_lib as cl
P = Path(__file__).resolve().parents[1]; ROOT = P.parents[2]
a = sys.argv[sys.argv.index('--') + 1:]
setname, glb, clips = a[0], a[1], a[2].split(',')
prop = a[3] if len(a) > 3 else 'R'; nfr = int(a[4]) if len(a) > 4 else 6
bpy.ops.wm.open_mainfile(filepath=str(P / 'work' / 'source.blend'))
scene = bpy.context.scene; rig = bpy.data.objects['Rig']
src = cl.load_sources(ROOT, {glb: clips}, scene)
flight = bpy.data.actions['Overseer_Flight']


def stand_in(bone, length, back, name):
    me = bpy.data.meshes.new(name); w = 0.02
    v = [(-w, -w, -back), (w, -w, -back), (w, w, -back), (-w, w, -back), (-w * 0.3, -w * 3, length), (w * 0.3, -w * 3, length),
         (w * 0.3, w * 3, length), (-w * 0.3, w * 3, length)]
    me.from_pydata(v, [], [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)])
    ob = bpy.data.objects.new(name, me); scene.collection.objects.link(ob)
    # bone-parented: the object's frame = the bone's (rest) frame; the handle axis is the socket bone's local Z
    ob.parent = rig; ob.parent_type = 'BONE'; ob.parent_bone = bone
    b = rig.data.bones[bone]
    ob.matrix_world = rig.matrix_world @ b.matrix_local
    return ob


if 'R' in prop or prop == '2H': stand_in('CollarRod', 0.55, 0.12, 'PropR')
if 'L' in prop: stand_in('PulsePistol', 0.45, 0.10, 'PropL')
sc = scene
sc.render.engine = 'BLENDER_WORKBENCH'; sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'MATERIAL'
sc.render.resolution_x = 320; sc.render.resolution_y = 400
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.3, 0.3, 0.32)
cam = bpy.data.objects.new('C', bpy.data.cameras.new('C')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 2.4
d = Vector((0.55, -0.83, 0.12)).normalized(); cam.location = Vector((0, 0, 0.95)) + d * 6
cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
out = P / 'review' / 'g1'; out.mkdir(parents=True, exist_ok=True)
tiles = []
for ci, clip in enumerate(clips):
    dur = src[clip][0]
    act = cl.author(rig, scene, src, f'G1_{clip}', flight, dur, [
        {'bones': cl.TRUNK[1:] + cl.CLAV, 'src': clip, 't': lambda t: t, 'w': lambda t: 1.0},
        {'bones': cl.ARM['L'] + cl.ARM['R'], 'src': clip, 't': lambda t: t, 'w': lambda t: 1.0, 'rel_clav': True}])
    cl.set_action(rig, act)
    for k in range(nfr):
        t = dur * k / (nfr - 1); cl.frame_at(scene, t * cl.FPS)
        f = str(out / f'{setname}_{clip}_{k}.png'); sc.render.filepath = f; bpy.ops.render.render(write_still=True)
        tiles.append((ci, k, f))
json.dump({'rows': len(clips), 'cols': nfr, 'w': 320, 'h': 400, 'tiles': tiles, 'labels': clips}, open(out / f'{setname}.json', 'w'))
print('G1', setname, len(tiles)); sys.stdout.flush(); os._exit(0)
