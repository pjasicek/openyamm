"""Guardian rig on work/clean_v2.blend -> work/rig_v1.blend. Forward -Y, up +Z, the skull's left +X.

Bones (all rigid, one influence per vertex, by the face attribute 'part' of clean.py):
  Body   hover root at the skull centre (moves, bobs, tilts the whole skull)
  Cranium  cranium, upper teeth, gem bezel (parts 0, 2, 4); pivot at the skull centre (not 'Skull': the mesh node
         is called Skull, and glTF node names must not collide)
  Jaw    mandible and lower teeth (parts 1, 3); pivot at the condyles (the hinge under the cheekbones)
  Gem    the faceted ruby (part 5); pivot at its centre, scaled for the flare
  EyeL / EyeR   the green eye cores (parts 6 / 7); pivots at their centres, scaled for the flare
Sockets (non-deform bones, exported as nodes): Socket_Gem 1.5 cm in front of the gem's table (charge and release of
the ranged attack), Socket_Eye_Left / Socket_Eye_Right just in front of the eye cores (eye glow, attack glow)."""
import bpy, os, json
import numpy as np
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'clean_v2.blend'))
mesh = bpy.data.objects['Skull']; me = mesh.data
info = json.load(open(os.path.join(HERE, 'work', 'gem_info.json')))
co = np.array([tuple(v.co) for v in me.vertices])
fp = np.zeros(len(me.polygons), np.int32); me.attributes['part'].data.foreach_get('value', fp)
vpart = -np.ones(len(co), np.int32)
for p, k in zip(me.polygons, fp):
    for v in p.vertices:
        vpart[v] = k
jaw = co[vpart == 1]
tops = []
for side in (1, -1):
    s_ = jaw[jaw[:, 0] * side > 0.18]
    tops.append(s_[s_[:, 2] > s_[:, 2].max() - 0.03].mean(0))
hinge = Vector((0.0, float((tops[0][1] + tops[1][1]) / 2), float(jaw[:, 2].max() - 0.02)))
chin = Vector((0.0, float(jaw[:, 1].min()) + 0.02, float(jaw[:, 2].min()) + 0.03))
cran = co[vpart == 0]
centre = Vector(((cran.min(0) + cran.max(0)) / 2).tolist())
gem_c = Vector(info['gem_centre']); gem_n = Vector(info['gem_axis']); gem_top = Vector(info['gem_top'])
eyes = {'L': Vector(info['eye_left']), 'R': Vector(info['eye_right'])}

arm = bpy.data.armatures.new('Guardian_Rig')
rig = bpy.data.objects.new('Guardian_Rig', arm)
bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects: o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.edit_bones


def bone(name, head, tail, parent=None, deform=True):
    b = eb.new(name); b.head = head; b.tail = tail; b.parent = parent; b.use_deform = deform
    d = (tail - head).normalized()
    b.align_roll(Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((0, -1, 0)))
    return b


body = bone('Body', centre, centre + Vector((0, 0, 0.2)))
skull = bone('Cranium', centre, centre + Vector((0, -0.25, 0)), body)
bone('Jaw', hinge, chin, skull)
gem = bone('Gem', gem_c, gem_c + gem_n * 0.05, skull)
for s in 'LR':
    e = bone(f'Eye{s}', eyes[s], eyes[s] + Vector((0, -0.04, 0)), skull)
    sock = eyes[s] + Vector((0, -0.016, 0))
    bone(f'Socket_Eye_{"Left" if s == "L" else "Right"}', sock, sock + Vector((0, -0.03, 0)), e, deform=False)
sg = gem_top + gem_n * 0.015
bone('Socket_Gem', sg, sg + gem_n * 0.03, gem, deform=False)
bpy.ops.object.mode_set(mode='OBJECT')

BONE_OF = {0: 'Cranium', 2: 'Cranium', 4: 'Cranium', 1: 'Jaw', 3: 'Jaw', 5: 'Gem', 6: 'EyeL', 7: 'EyeR'}
groups = {n: mesh.vertex_groups.new(name=n) for n in set(BONE_OF.values())}
for i, k in enumerate(vpart):
    groups[BONE_OF[int(k)]].add([i], 1.0, 'REPLACE')
mod = mesh.modifiers.new('Armature', 'ARMATURE'); mod.object = rig
mesh.parent = rig
out = {'centre': list(centre), 'hinge': list(hinge), 'chin': list(chin), 'socket_gem': list(sg),
       'height': float(co[:, 2].max()), 'unweighted': int((vpart < 0).sum())}
json.dump(out, open(os.path.join(HERE, 'work', 'rig_info.json'), 'w'), indent=1)
print('RIGGED bones', len(arm.bones), json.dumps(out))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v1.blend'))
