"""Radius profile and hand weight along the forearm axis, final blend, both arms. Args: blend"""
import bpy, sys, json, numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--') + 1]); b = bpy.data.objects['Body']; me = b.data
P = np.array([v.co[:] for v in me.vertices]); pa = np.zeros(len(P), int); me.attributes['part'].data.foreach_get('value', pa)
gid = {g.index: g.name for g in b.vertex_groups}
Fr = json.load(open('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm9_trellborg_claude/work/hands_v1.json'))['frames']
for S, sg in (('R', -1), ('L', 1)):
    W = np.array(Fr[S]['W']); d = np.array(Fr[S]['d']); d /= np.linalg.norm(d); al = (P - W) @ d; r = np.linalg.norm(P - W - np.outer(al, d), axis=1)
    m = (np.sign(P[:, 0]) == sg) & (pa == 0) & (r < .2)
    for a in np.arange(-.08, .14, .02):
        k = np.nonzero(m & (np.abs(al - a) < .01))[0]
        if not len(k): continue
        wh = [sum(g.weight for g in me.vertices[int(i)].groups if 'Hand' in gid[g.group] and gid[g.group].endswith('Hand')) for i in k]
        wh2 = [sum(g.weight for g in me.vertices[int(i)].groups if gid[g.group].endswith('Hand_h')) for i in k]
        print('PROF', S, round(a, 2), len(k), 'r', np.round(np.percentile(r[k], [50, 100]), 3).tolist(), 'hand', round(float(np.mean(wh)), 2), 'h_', round(float(np.mean(wh2)), 2))
