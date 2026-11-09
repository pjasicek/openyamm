"""Rest-pose landmarks for the armour spec: B_* bone heads and body cross-sections (x/y extent per z band,
skin of the torso only = vertices dominated by spine/pelvis/clavicle/neck bones). Args: -- <rig blend>"""
import bpy, sys, os
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
for b in rig.data.bones:
    if b.name.startswith('B_') and 'Finger' not in b.name and 'Toe' not in b.name:
        print('BONE', b.name, [round(x, 3) for x in b.head_local], 'parent', b.parent.name if b.parent else None)
GI = {g.index: g.name for g in body.vertex_groups}
CO = np.array([v.co[:] for v in me.vertices]); DOM = np.array([GI[max(v.groups, key=lambda g: g.weight).group] if v.groups else '' for v in me.vertices])
PIECE = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', PIECE)
torso = np.isin(DOM, ['B_Spine', 'B_Spine1', 'B_Spine2', 'B_Pelvis', 'B_Neck', 'B_L_Clavicle', 'B_R_Clavicle', 'B_Groin']) & (PIECE == 0)
for z in np.arange(0.80, 1.62, 0.04):
    m = torso & (np.abs(CO[:, 2] - z) < 0.02)
    if m.any():
        print('TORSO z', round(z, 2), 'x', round(CO[m, 0].min(), 3), round(CO[m, 0].max(), 3), 'y', round(CO[m, 1].min(), 3), round(CO[m, 1].max(), 3), 'bones', sorted(set(DOM[m]))[:5])
for s in 'LR':
    for bn in (f'B_{s}_Thigh', f'B_{s}_Calf', f'B_{s}_Foot'):
        m = (DOM == bn) & (PIECE == 0)
        print('LIMB', bn, 'n', int(m.sum()), 'z', round(CO[m, 2].min(), 3), round(CO[m, 2].max(), 3), 'x', round(CO[m, 0].min(), 3), round(CO[m, 0].max(), 3), 'y', round(CO[m, 1].min(), 3), round(CO[m, 1].max(), 3))
print('PIECES', {int(p): int((PIECE == p).sum()) for p in np.unique(PIECE)})
