#!/usr/bin/env python3
import json, sys
import numpy as np
sys.argv = ['x']
exec(open('hats/mm9_hat_place.py').read().split("g = GLTF2().load('source/mm9/honkm2.glb')")[0])
g = GLTF2().load('v2/work/mm9_honkm_floor1.glb'); W = nodes(g)
hi = next(i for i, n in enumerate(g.nodes) if n.name == 'Bip01 Head')
M = W(hi)
root = next(i for i, n in enumerate(g.nodes) if n.name == 'Scene Root')
print('head world', M[:3, 3].round(3))
json.dump({'head_world': M.tolist(), 'lift': 0.8995}, open('hats/work/head_world.json', 'w'))
