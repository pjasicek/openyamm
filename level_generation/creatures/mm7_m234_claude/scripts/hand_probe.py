"""Print the right/left hand vertex spread around the composed wrist joint: depth along the forearm direction and the
farthest skin vertices (debug for fit_fingers.py on the clawed hands). Args: -- <blend>"""
import bpy, sys, os, json
import numpy as np
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(sys.argv[sys.argv.index('--') + 1]))
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
J = json.load(open(os.path.join(HERE, 'work', 'joints_final.json')))['joints']
b = bpy.data.objects['Body']; co = np.array([tuple(b.matrix_world @ v.co) for v in b.data.vertices])
for s in 'RL':
    wr, fa = np.array(J[f'{s}_Hand']), np.array(J[f'{s}_Forearm']); d = (wr - fa) / np.linalg.norm(wr - fa)
    near = (np.linalg.norm(co - wr, axis=1) < 0.25) & (np.sign(co[:, 0]) == np.sign(wr[0]))
    dep = (co[near] - wr) @ d
    far = co[near][np.argmax(np.linalg.norm(co[near] - wr, axis=1))]
    low = co[near][np.argmin(co[near][:, 2])]
    print('HANDPROBE', s, 'wrist', np.round(wr, 3), 'dir', np.round(d, 2), 'depth range', round(float(dep.min()), 3), round(float(dep.max()), 3),
          'farthest', np.round(far, 3), 'lowest', np.round(low, 3), 'n', int(near.sum()))
