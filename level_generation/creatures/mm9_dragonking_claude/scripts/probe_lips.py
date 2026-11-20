import bpy, sys, bmesh
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
ob = bpy.data.objects['Body']; me = ob.data
UPPER = {'Xheadpiv', 'Xhead', 'Xjawbase', 'Xtopfinpiv', 'Xtopfinpiv01', 'Xfinpiv', 'Xfinpiv01', 'XneckD'}
LOWER = {'Xjaw', 'Xjawpivot', 'Xchinfinpiv', 'Xchinfinpiv01', 'Xbotfinpiv', 'Xbotfinpiv01', 'Xtong', 'Xtongpiv'}
vg = {g.index: g.name for g in ob.vertex_groups}
def lw(v):
    return sum(g.weight for g in v.groups if vg[g.group] in LOWER)
w = np.array([lw(v) for v in me.vertices])
piece = np.array([d.value for d in me.attributes['piece'].data])
P = np.array([tuple(v.co) for v in me.vertices])
hw = np.array([sum(g.weight for g in v.groups if vg[g.group] in UPPER | LOWER) for v in me.vertices])
head = hw > 0.5
print('HEAD verts', head.sum(), 'lower>0.5', ((w > 0.5) & head).sum(), 'mixed 0.2-0.8', ((w > 0.2) & (w < 0.8)).sum())
mix = (w > 0.2) & (w < 0.8) & (piece == 0)
print('MIX bounds', P[mix].min(0).round(2), P[mix].max(0).round(2))
low = (w > 0.5) & (piece == 0)
print('LOWER bounds', P[low].min(0).round(2), P[low].max(0).round(2))
arm = bpy.data.objects['MM9_Rig']
for b in ('Xjawpivot', 'Xjaw', 'Xjawbase', 'Xhead', 'Xchinfinpiv'):
    print('BONE', b, [round(c, 2) for c in arm.data.bones[b].head_local])
