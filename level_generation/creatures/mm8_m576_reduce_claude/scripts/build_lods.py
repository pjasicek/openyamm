"""work/ke_r64_lod0.glb -> work/ke_r64_lods_raw.glb with LOD1-3 and shadow LODs, like mm8_m576_claude/scripts/build_lods.py:
both whole hands (hand + finger weight > 0.3: the gripping left hand, and the right hand, which stretched over the
hand gate in shadow LOD3 when free) and the sole band (foot/toe vertices in the lowest 12 mm, REA_SOLE_M; 6 mm let
the LOD3 left foot fail the running foot-yaw gate) the Dead-pose floor contact and the top 3 cm of the crest spike (picking bounds use the coarsest LOD) are protected points, 4 influences. The trident is already a separate attachment, so its grip section
needs no protection here. Ratios of the reduced LOD0 (REA_LOD_RATIOS, default 0.5 / 0.37 / 0.27, inside the gate caps 0.51 / 0.38 / 0.28 of gates.json): the installed
body kept 0.5 / 0.365 / 0.264 of 10,656 because protecting the hand at generic budgets overcollapsed torso and legs.
Usage: blender -b -P build_lods.py"""
import os, sys, bpy
from pathlib import Path
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate  # noqa: E402
SRC, DST = P / os.environ.get('REA_LOD0', 'work/ke_r64_lod0.glb'), P / os.environ.get('REA_LODS', 'work/ke_r64_lods_raw.glb')
HANDS = tuple(f'B_{s}_' for s in os.environ.get('REA_HANDS', 'L'))
CREST = os.environ.get('REA_CREST', '1') == '1'
SOLE = float(os.environ.get('REA_SOLE_M', '0.012'))
ratios = tuple(float(x) for x in os.environ.get('REA_LOD_RATIOS', '0.5,0.375,0.275').split(','))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(SRC))
body = bpy.data.objects['Triton']; names = {g.index: g.name for g in body.vertex_groups}
def w(v, pred):
    return sum(g.weight for g in v.groups if pred(names[g.group]))
pts = [body.matrix_world @ v.co for v in body.data.vertices]
hand = [p for v, p in zip(body.data.vertices, pts) if w(v, lambda n: n[:4] in HANDS and (n[4:] == 'Hand' or n[4:].startswith('Finger'))) > .3]
protected = list(hand)
for side in 'LR':
    feet = [(v, p) for v, p in zip(body.data.vertices, pts) if w(v, lambda n: n.startswith((f'B_{side}_Foot', f'B_{side}_Toe'))) > .5]
    zmin = min(p.z for _, p in feet)
    protected += [p for _, p in feet if p.z < zmin + SOLE]
# corpse contact: vertices within 1 cm of the lowest point of the final Dead pose (LOD3 floated 2.1 cm without them)
import bmesh
rig = next(x for x in bpy.data.objects if x.type == 'ARMATURE'); act = bpy.data.actions['Dead']
rig.animation_data.action = act; bpy.context.scene.frame_set(int(act.frame_range[1]))
bm = bmesh.new(); bm.from_object(body, bpy.context.evaluated_depsgraph_get()); bm.transform(body.matrix_world); bm.verts.ensure_lookup_table()
dz = [q.co.z for q in bm.verts]; bm.free(); floor = min(dz)
corpse = [p for p, z in zip(pts, dz) if z < floor + .01]; protected += corpse; print('CORPSE contact vertices', len(corpse), flush=True)
zmax = max(p.z for p in pts)
protected += [p for p in pts if p.z > zmax - .03] if CREST else []  # crest spike tip: LOD3 lost 5.4 cm of height without it
protected = sorted({tuple(round(c, 6) for c in p) for p in protected})
print('PROTECTED', len(hand), 'hand vertices,', len(protected), 'points', flush=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
generate(SRC, DST, 'Triton', ratios=ratios, max_influences=4, protected_points=protected)
