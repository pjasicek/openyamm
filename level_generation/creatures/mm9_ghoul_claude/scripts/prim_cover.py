"""Does collapse_gate.py see every LOD0 primitive? Lists the mesh primitives of the first mesh per material, and what glb_pose hands the gate. Args: glb"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
m = Model(Glb(sys.argv[1])); doc = m.glb.json
print('nodes with meshes', [(n.get('name'), len(doc['meshes'][n['mesh']]['primitives'])) for n in doc['nodes'] if 'mesh' in n])
print('primitives seen by the gate', len(m.primitives), [(p['node'], len(p['positions']), len(p['triangles'])) for p in m.primitives])
print('tris gate', sum(len(p['triangles']) for p in m.primitives))
