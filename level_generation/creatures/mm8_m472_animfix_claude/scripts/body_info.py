"""Leg length, Standing hip height and Froude numbers of the package's bodies at their chase speeds (diagnostic)."""
import sys
import numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gaitlib
from gaitlib import glb_pose

for m, speeds in (('cle', (2.91, 3.64)), ('dru1', (2.90, 3.62)), ('lch', (3.23, 3.94)), ('sor1', (3.77, 4.52)),
                  ('arc1', (2.63, 3.01))):
    glb = gaitlib.open_glb(f'work/mm6_{m}_pre_gait.glb')
    M = glb_pose.Model(glb)
    I = {n['name']: i for i, n in enumerate(glb.json['nodes'])}
    W = M.world(M.sample('Standing', 0.0))
    p = lambda n: W[I[n], :3, 3]
    L = float(np.linalg.norm(p('B_L_Calf') - p('B_L_Thigh')) + np.linalg.norm(p('B_L_Foot') - p('B_L_Calf')))
    head = p('B_Head')[1]
    fr = [v * v / (9.81 * L) for v in speeds]
    print(m, 'leg', round(L, 3), 'hip', round(float(p('B_Pelvis')[1]), 3), 'head joint', round(float(head), 3),
          'Froude', [round(f, 2) for f in fr], 'clips', list(M.clips))
