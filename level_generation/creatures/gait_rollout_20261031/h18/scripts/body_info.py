"""Leg length, Standing hip height and Froude numbers of the package's bodies at their chase speeds (diagnostic)."""
import sys
import numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gaitlib
from gaitlib import glb_pose

# chase speeds (model units/s) from gait_gate.py: Standard A..C (MAW where it differs)
for m, speeds in (('m424', (2.43,)), ('m428', (2.36,)), ('m432', (3.99, 4.65, 7.31)), ('m604', (2.94, 3.74, 5.88)),
                  ('m460', (2.89, 3.62))):
    glb = gaitlib.open_glb(f'work/mm8_{m}_pre_gait.glb')
    M = glb_pose.Model(glb)
    I = {n['name']: i for i, n in enumerate(glb.json['nodes'])}
    W = M.world(M.sample('Standing', 0.0))
    p = lambda n: W[I[n], :3, 3]
    L = float(np.linalg.norm(p('B_L_Calf') - p('B_L_Thigh')) + np.linalg.norm(p('B_L_Foot') - p('B_L_Calf')))
    head = p('B_Head')[1]
    fr = [v * v / (9.81 * L) for v in speeds]
    print(m, 'leg', round(L, 3), 'hip', round(float(p('B_Pelvis')[1]), 3), 'head joint', round(float(head), 3),
          'Froude', [round(f, 2) for f in fr], 'clips', list(M.clips))
