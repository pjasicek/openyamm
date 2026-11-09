"""Blender: import every prop's raw LOD0 into the asset frame and render front / three-quarter / side / top views with
back faces culled (review/raw/<prop>.png). Usage: blender --background --python inspect_raw.py -- [prop ...]"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blib  # noqa: E402

args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
origins = blib.binding_origins()
props = args or sorted(p for p in os.listdir(os.path.join(blib.WORK, 'raw')) if not p.startswith('ref_'))
out = os.path.join(blib.HERE, 'review', 'raw')
os.makedirs(out, exist_ok=True)
for prop in props:
    blib.reset()
    blib.setup_render((384, 384))
    obj = blib.import_raw(os.path.join(blib.WORK, 'raw', prop, f'{prop}.glb'), prop, origins[prop],
                          apply_armature=prop == 'book')
    print('IMPORT', prop, 'faces', obj['faces_in'], 'flipped', obj['flipped_faces'], 'materials', len(obj.data.materials))
    mat = blib.texture_material(prop, f'{prop}_basecolor.png', alpha=prop == 'cookpot')
    obj.data.materials.clear(); obj.data.materials.append(mat)
    for i, (yaw, el) in enumerate(((0, 10), (40, 25), (90, 10), (200, 30))):
        blib.render([obj], os.path.join(out, f'{prop}_{i}.png'), yaw, el)
