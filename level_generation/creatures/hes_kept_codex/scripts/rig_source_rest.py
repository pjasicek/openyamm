"""Dump the source set's rest skeleton (T-pose) in our convention: armature turned 180 degrees about Z (faces -Y,
character left = +X), unit scale. Per B_* bone: parent, world head, world rotation (3x3, scale removed), and the
segment direction to its main child head (the imported tails are unusable). Writes work/source_rest.json.
Args: -- <set glb>"""
import bpy, sys, os, json, math
BODY_KIND = os.environ['KEPT_BODY']
assert BODY_KIND in ('male', 'female')
BODY_ID = 'm' if BODY_KIND == 'male' else 'f'
BODY_VERSION = 'v2' if BODY_ID == 'm' else 'v1'
from mathutils import Matrix
glb = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.render.fps = 30
bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
arm.animation_data.action = None
for pb in arm.pose.bones:
    pb.matrix_basis.identity()
TURN = Matrix.Rotation(math.pi, 4, 'Z')
W = TURN @ arm.matrix_world
CHILD = {'B_Pelvis': 'B_Spine', 'B_Spine': 'B_Spine1', 'B_Spine1': 'B_Spine2', 'B_Spine2': 'B_Neck', 'B_Neck': 'B_Head'}
for s in ('L', 'R'):
    CHILD.update({f'B_{s}_Clavicle': f'B_{s}_UpperArm', f'B_{s}_UpperArm': f'B_{s}_Forearm', f'B_{s}_Forearm': f'B_{s}_Hand',
                  f'B_{s}_Hand': f'B_{s}_Finger2', f'B_{s}_Thigh': f'B_{s}_Calf', f'B_{s}_Calf': f'B_{s}_Foot',
                  f'B_{s}_Foot': f'B_{s}_Toe0'})
    for i in range(5):
        a = f'B_{s}_Finger{i}'
        kids = [b.name for b in arm.data.bones if b.parent and b.parent.name == a]
        CHILD[a] = kids[0] if kids else None
        if kids:
            gk = [b.name for b in arm.data.bones if b.parent and b.parent.name == kids[0]]
            CHILD[kids[0]] = gk[0] if gk else None
out = {}
for b in arm.data.bones:
    if not b.name.startswith('B_'):
        continue
    M = W @ b.matrix_local
    R = M.to_3x3().normalized()
    head = M.translation
    c = CHILD.get(b.name)
    seg = None
    if c:
        ch = (W @ arm.data.bones[c].matrix_local).translation
        seg = list((ch - head))
    out[b.name] = {'parent': b.parent.name if b.parent else None, 'head': list(head), 'rot': [list(r) for r in R],
                   'child': c, 'seg': seg}
path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'work', BODY_KIND, 'source_rest.json')
json.dump(out, open(path, 'w'), indent=1)
print('SOURCE_REST', len(out), 'bones; R_UpperArm head', [round(x, 3) for x in out['B_R_UpperArm']['head']],
      'R_Finger2 head', [round(x, 3) for x in out['B_R_Finger2']['head']])

sys.stdout.flush();sys.stderr.flush();os._exit(0)
