#!/usr/bin/env python3
"""Shoulder skin kept exactly (Ebora round 2 lesson): faces with any vertex whose dominant bone is a Clavicle or UpperArm
(the vertex set the jitter gate's shoulder-skin term reads), so that term follows the installed mesh.
-> work/keep_shoulder.npy"""
import numpy as np
d = np.load('work/mesh_in.npz'); f = d['faces']; names = [str(n) for n in d['names']]; W = d['W']
dom = np.array([names[i] for i in W.argmax(1)])
sv = np.array([x.endswith(' Clavicle') or x.endswith(' UpperArm') for x in dom])
keep = sv[f].any(1) & (d['mat'] == 0)
np.save('work/keep_shoulder.npy', keep); print('SHOULDER', int(keep.sum()), 'faces,', int(sv.sum()), 'vertices')
