"""Gate copy attributes for the source project's gates (g6_contacts.py, stretch_all.py read the point attribute
'garment' of the hes_villager_f_claude master: 0 skin, 1 teeth, 2 tail spikes, 3 eyes). The master's rest frame is the
working frame (the export moved the origin 0.626 m), so the labels are rebuilt on the gate copy from its own pieces
(gate_import.py's 'piece', 0 = the closed skin): 0 for the skin, 2 for small pieces weighted to the tail, 1 for the
other small pieces (teeth and eyes; the gates only tell the skin from the rest). Args: -- <gate blend>"""
import bpy, sys, os
import numpy as np
gate = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(gate))
gb = bpy.data.objects['Body']; me = gb.data
piece = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', piece)
names = {g.index: g.name for g in gb.vertex_groups}
tail = np.array([sum(e.weight for e in v.groups if names[e.group].startswith('B_Tail')) > 0.5 for v in me.vertices])
garment = np.where(piece == 0, 0, 1)
for p in np.unique(piece[piece > 0]):
    m = piece == p
    if tail[m].mean() > 0.5:
        garment[m] = 2
at = me.attributes.get('garment') or me.attributes.new('garment', 'INT', 'POINT')
at.data.foreach_set('value', garment.tolist())
print('GATEATTRS garment', {int(k): int((garment == k).sum()) for k in np.unique(garment)}, 'pieces', len(np.unique(piece)))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(gate))
