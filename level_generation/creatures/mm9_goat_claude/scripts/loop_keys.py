"""For an MM9 action: per key time, the largest bone rotation difference to a reference key (find the true cycle).
Args: <mm9 glb> <action> [reference key, default 0]"""
import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import clips_mm9 as C
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=argv[0])
sc = bpy.context.scene
fps = sc.render.fps / sc.render.fps_base
rec = C.read_keys(bpy.data.actions[argv[1]], fps)
REF = int(argv[2]) if len(argv) > 2 else 0
n = len(next(iter(rec.values()))['t'])
for k in range(n):
    worst, wb = 0, ''
    for b, r in rec.items():
        d = r['q'][REF].rotation_difference(r['q'][k])
        a = math.degrees(d.angle if d.angle <= math.pi else 2 * math.pi - d.angle)
        if a > worst:
            worst, wb = a, b
    print('KEY %2d t %.3f maxdiff %.1f %s' % (k, next(iter(rec.values()))['t'][k], worst, wb))
