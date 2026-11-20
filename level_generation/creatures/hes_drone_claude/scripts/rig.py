"""Drone rig on the UV-mapped master (work/body_v2.blend from build_body.py; env HDR_SRC=uv_v1.blend for the v1 Meshy shell) -> work/rig_v1.blend. Forward -Y, up +Z, left +X.

Bones (every body vertex 100 % on one bone; only the tendons blend along their chains):
  Body                 root; pivot at the casing's centre; carries the casing, resin, ribs, vents
  Lens                 child of Body at the lens dome's base; the dome (part 4), for the shot's recoil
  Socket_Muzzle        non-deforming child of Lens, 3 cm in front of the dome's apex: the bolt leaves here
  Thrust               child of Body under the vent ring, pointing down: the thrust glow (gear.py) and its pulse
  Tendon<k>_1..3       chains of the three tendons (parent Body), from the buried root to the claw
  GearEmitter, GearRing  children of Body: the tier gear (gear.py), split into attachments at export
  GearEmitterGlow, GearRingGlow  the same pivots: the gear's glowing disc / cells (glow material)
Writes work/rig_info.json (pivots)."""
import bpy, os, json
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', os.environ.get('HDR_SRC', 'body_v2.blend')))
mesh = bpy.data.objects['HDR']
info = json.load(open(os.path.join(HERE, 'work', 'clean_info.json')))
co = np.array([tuple(v.co) for v in mesh.data.vertices])
part_f = np.zeros(len(mesh.data.polygons), int); mesh.data.attributes['part'].data.foreach_get('value', part_f)
part = np.zeros(len(co), int)
for p in mesh.data.polygons:
    for v in p.vertices:
        part[v] = part_f[p.index]
body = co[part == 0]
centre = Vector(((body.min(0) + body.max(0)) / 2).tolist()); centre.x = 0.0
lens = co[part == 4]
lens_base = Vector((float(lens[:, 0].mean()), float(lens[:, 1].max()), float(lens[:, 2].mean())))
apex = Vector((lens_base.x, float(lens[:, 1].min()), lens_base.z))
under = body[(np.abs(body[:, 0]) < 0.08) & (body[:, 1] > -0.17) & (body[:, 1] < 0.08)]
thrust = Vector((0.0, float(under[:, 1].mean()), float(under[:, 2].min())))
print('PIVOTS centre', tuple(round(c, 3) for c in centre), 'lens', tuple(round(c, 3) for c in lens_base),
      'apex', tuple(round(c, 3) for c in apex), 'thrust', tuple(round(c, 3) for c in thrust))

arm = bpy.data.armatures.new('HDR_Rig'); rig = bpy.data.objects.new('HDR_Rig', arm)
bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects:
    o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.edit_bones


def bone(name, head, tail, parent=None, deform=True):
    b = eb.new(name); b.head = head; b.tail = tail; b.parent = parent; b.use_deform = deform
    d = (Vector(tail) - Vector(head)).normalized()
    b.align_roll(Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((0, -1, 0)))
    return b


b_body = bone('Body', centre, centre + Vector((0, 0, 0.15)))
b_lens = bone('Lens', lens_base, apex, b_body)
bone('Socket_Muzzle', apex + Vector((0, -0.03, 0)), apex + Vector((0, -0.08, 0)), b_lens, deform=False)
bone('Thrust', thrust, thrust + Vector((0, 0, -0.08)), b_body)
bone('GearEmitter', centre, centre + Vector((0, -0.1, 0)), b_body)
bone('GearRing', centre, centre + Vector((0, 0, 0.1)), b_body)
# the gear's glowing parts use the glow material: one material per attachment, so they get bones of their own
bone('GearEmitterGlow', centre, centre + Vector((0, -0.1, 0)), b_body)
bone('GearRingGlow', centre, centre + Vector((0, 0, 0.1)), b_body)
chains = []
for t in info['tendons']:
    pts = [Vector(p) for p in t['points']] + [Vector(t['claw'][-1])]
    n = len(t['points']) - 1
    joints = [pts[0], pts[n // 3], pts[2 * n // 3], pts[-1]]
    prev = b_body; names = []
    for j in range(3):
        nm = f"Tendon{t['tendon']}_{j + 1}"
        prev = bone(nm, joints[j], joints[j + 1], prev); prev.use_connect = j > 0; names.append(nm)
    chains.append((t['tendon'], names, [list(j) for j in joints], pts))
bpy.ops.object.mode_set(mode='OBJECT')

groups = {b.name: mesh.vertex_groups.new(name=b.name) for b in arm.bones if b.use_deform}
groups['Body'].add(np.nonzero(part == 0)[0].tolist(), 1.0, 'REPLACE')
groups['Lens'].add(np.nonzero(part == 4)[0].tolist(), 1.0, 'REPLACE')
BLEND = 0.06   # of the chain's length, either side of a joint
for k, names, joints, pts in chains:
    idx = np.nonzero(part == k)[0]
    J = np.array(joints)
    seglen = np.linalg.norm(np.diff(J, axis=0), axis=1); total = seglen.sum()
    cum = np.concatenate([[0], np.cumsum(seglen)]) / total
    # arc parameter of each vertex: projection onto the joint polyline
    tpar = np.zeros(len(idx))
    for n_, vi in enumerate(idx):
        p = co[vi]; best = (1e9, 0.0)
        for s in range(3):
            a, b = J[s], J[s + 1]; d = b - a
            u = float(np.clip(np.dot(p - a, d) / np.dot(d, d), 0, 1))
            dist = np.linalg.norm(a + u * d - p)
            if dist < best[0]:
                best = (dist, cum[s] + u * (cum[s + 1] - cum[s]))
        tpar[n_] = best[1]
    w = np.zeros((len(idx), 3))
    for s in range(3):
        lo, hi = cum[s], cum[s + 1]
        rise = np.clip((tpar - (lo - BLEND)) / (2 * BLEND), 0, 1) if s > 0 else np.ones(len(idx))
        fall = np.clip(((hi + BLEND) - tpar) / (2 * BLEND), 0, 1) if s < 2 else np.ones(len(idx))
        w[:, s] = np.minimum(rise, fall)
    w /= w.sum(1, keepdims=True)
    for s, nm in enumerate(names):
        for vi, ww in zip(idx, w[:, s]):
            if ww > 1e-4:
                groups[nm].add([int(vi)], float(ww), 'REPLACE')
mesh.parent = rig
mod = mesh.modifiers.new('Armature', 'ARMATURE'); mod.object = rig
unweighted = sum(1 for v in mesh.data.vertices if not v.groups)
print('WEIGHTS unweighted', unweighted)
json.dump({'centre': list(centre), 'lens_base': list(lens_base), 'apex': list(apex), 'thrust': list(thrust),
           'tendon_joints': {k: j for k, _, j, _ in chains}},
          open(os.path.join(HERE, 'work', 'rig_info.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v1.blend'))
print('SAVED rig_v1.blend')
