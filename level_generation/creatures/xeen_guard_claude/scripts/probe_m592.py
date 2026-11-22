"""Import the installed stand-in mm8_m592.glb (the clip source, D-19), report its rest skeleton (heads, tails, world
rest rotations) and every clip's length, and render clay key frames of each clip (front and side) into
work/m592_probe/. Writes work/m592_rest.json."""
import bpy, os, sys, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
OUT = os.path.join(HERE, 'work', 'm592_probe'); os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(REPO, 'assets_source/worlds/mm8/models/mm8_m592.glb'))
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
print('OBJECTS', [(o.name, o.type, o.parent.name if o.parent else None) for o in bpy.data.objects])
rest = {}
for b in rig.data.bones:
    m = rig.matrix_world @ b.matrix_local
    rest[b.name] = {'head': list(rig.matrix_world @ b.head_local), 'tail': list(rig.matrix_world @ b.tail_local),
                    'parent': b.parent.name if b.parent else None,
                    'rot': [list(r) for r in m.to_3x3()]}
    print('BONE', b.name, 'parent', rest[b.name]['parent'], 'head', [round(x, 3) for x in rest[b.name]['head']],
          'tail', [round(x, 3) for x in rest[b.name]['tail']])
json.dump(rest, open(os.path.join(HERE, 'work', 'm592_rest.json'), 'w'), indent=1)
sc = bpy.context.scene
print('FPS', sc.render.fps)
for a in bpy.data.actions:
    print('ACTION', a.name, [round(x, 3) for x in a.frame_range])
# keep only the LOD0 colour mesh visible
lod0 = max(meshes, key=lambda o: len(o.data.polygons))
for o in meshes:
    o.hide_render = o is not lod0
C.MESH = lod0.name
co = [lod0.matrix_world @ v.co for v in lod0.data.vertices]
print('LOD0', lod0.name, len(lod0.data.polygons), 'zmin', round(min(c.z for c in co), 3), 'zmax', round(max(c.z for c in co), 3),
      'x', round(min(c.x for c in co), 3), round(max(c.x for c in co), 3), 'y', round(min(c.y for c in co), 3), round(max(c.y for c in co), 3))
if '--render' in sys.argv:
    for a in bpy.data.actions:
        rig.animation_data.action = a
        f0, f1 = a.frame_range
        for k in range(6):
            f = f0 + (f1 - f0) * k / 5
            sc.frame_set(int(round(f)))
            for v, (loc, tgt) in {'front': ((2.6, 0, 1.0), (0, 0, 0.8)), 'side': ((0, -2.6, 1.0), (0, 0, 0.8))}.items():
                C.render(loc, tgt, 2.6, os.path.join(OUT, f'{a.name}_{k}_{v}.png'), res=(300, 300), floor=False)
