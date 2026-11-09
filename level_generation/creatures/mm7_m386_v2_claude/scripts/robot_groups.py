"""Per-face labels for the robot ladder (work/source.blend Body = work/mesh_in.npz triangle order):
- protect (work/protect_head.npy): Head/Jaw-dominated faces (armoured head, jaw, teeth, green optics), own ratio
  (REA_PROTECT_RATIO);
- keep (work/keep_spikes.npy): the four spikes with their rod tops (Spike_* dominated), kept exactly: low-poly
  cones whose tips shortened by up to 12 mm at the first cuts, and the floor contacts of every clip;
- groups (work/groups.npy): 1 = the articulated neck and tail (Neck*/Tail* dominated: ring segments, fins, neck
  cables), 2 = small separate pieces elsewhere (< 60 faces: bolts, connectors, rails, gun coils), 3 = the gun (ball,
  barrel, housing), each with its own ratio (REA_GROUP_RATIOS); 0 = chassis, sleeves, arm plates and cables take the
  rest of the budget.
Usage: blender -b -P robot_groups.py"""
import os, bpy
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'source.blend'))
o = bpy.data.objects['Body']; me = o.data; me.calc_loop_triangles()
names = {g.index: g.name for g in o.vertex_groups}
dom = np.array([names[max(v.groups, key=lambda g: g.weight).group] if v.groups else '' for v in me.vertices])
f = np.array([t.vertices[:] for t in me.loop_triangles])
d = np.load(os.path.join(HERE, 'work/mesh_in.npz')); assert (d['faces'] == f).all()
n = len(me.vertices); parent = np.arange(n)
def find(i):
    while parent[i] != i:
        parent[i] = parent[parent[i]]; i = parent[i]
    return i
for a, b, c in f:
    for u, v in ((a, b), (b, c)):
        ru, rv = find(u), find(v)
        if ru != rv: parent[ru] = rv
lab = np.array([find(i) for i in range(n)]); fl = lab[f[:, 0]]; size = np.bincount(fl, minlength=n)[fl]
fd = dom[f]                      # dominant bone of each corner
head = np.isin(fd, ['Head', 'Jaw']).sum(1) >= 2
chain = (np.char.startswith(fd.astype(str), 'Tail') | np.char.startswith(fd.astype(str), 'Neck')).sum(1) >= 2
small = size < 60
spike = np.char.startswith(fd.astype(str), 'Spike').sum(1) >= 2
gun = (fd == 'Gun').sum(1) >= 2
g = np.zeros(len(f), int); g[chain & ~head] = 1; g[gun & ~head] = 3; g[small & ~head & ~chain & ~gun] = 2
g[spike | head] = 0
np.save(os.path.join(HERE, 'work/protect_head.npy'), head & ~spike); np.save(os.path.join(HERE, 'work/groups.npy'), g)
np.save(os.path.join(HERE, 'work/keep_spikes.npy'), spike)
rest = (g == 0) & ~head & ~spike
print('FACES', len(f), 'head', int((head & ~spike).sum()), 'spikes kept', int(spike.sum()), 'chain', int((g == 1).sum()),
      'small', int((g == 2).sum()), 'gun', int((g == 3).sum()), 'rest', int(rest.sum()))
