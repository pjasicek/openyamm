"""MM9 true-handed source -> work/mm9_true.npz (Blender coords): joint names/positions, mesh A/FA, for Blender scripts. Args: glb out.npz"""
import sys, numpy as np
sys.path.insert(0, __import__('os').path.dirname(__file__))
import demon_common as C
J = C.joints(sys.argv[1]); A, FA, _ = C.load_mesh(sys.argv[1])
np.savez(sys.argv[2], jn=np.array(list(J)), jp=np.array(list(J.values())), A=A, FA=FA)
print('saved', len(J), A.shape)
