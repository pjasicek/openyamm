"""finish.py table for the leftover trees and flowers (build_plants.sh). Trees: four levels (LOD3 the camera-facing
impostor, cut to a 6-vertex outline); foliage MASK 0.5 double-sided with openyamm_specular 0.1 (set by the copied
post_process.py and kept here), bark opaque. Flowers: three levels, one MASK material."""
FOLIAGE = {'alpha': 'MASK', 'cutoff': 0.5, 'double': True}
TREE = {'Bark': {}, 'Leaves': FOLIAGE, 'LeavesFar': FOLIAGE, 'Impostor': FOLIAGE, 'Moss': FOLIAGE}


def tree(sid, budget):
    return {'output': f'mm6_deco_{sid[1:]}.glb', 'export': f'work/plants/{sid}/tree_tinted.glb', 'budget': budget,
            'materials': TREE}


def flower(sid, budget):
    return {'output': f'mm6_deco_{sid[1:]}.glb', 'export': f'work/plants/{sid}/plant_cut.glb', 'budget': budget,
            'materials': {'Plant': FOLIAGE}}


TABLE = {
    '6tree09': tree('6tree09', [6000, 2400, 900, 8]),
    '6tree22': tree('6tree22', [6000, 2400, 900, 8]),
    '6tree26': tree('6tree26', [6000, 2400, 900, 8]),
    '6tree30': tree('6tree30', [4000, 1600, 600, 8]),
    '6flower01': flower('6flower01', [1500, 600, 200]),
    '6flower11': flower('6flower11', [1500, 600, 200]),
}
