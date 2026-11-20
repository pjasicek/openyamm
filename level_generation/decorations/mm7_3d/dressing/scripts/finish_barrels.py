"""Finish table of the barrels and bones (build_barrel.py, build_cask.py, build_skeleton.py, build_bones.py)."""
NET = {'alpha': 'MASK', 'cutoff': 0.5, 'double': True}
TABLE = {
    # 208 placements: the hundreds band, 300-1500 LOD0.
    '7dec32': {'output': 'mm7_deco_7dec32.glb', 'budget': [1500, 800, 300, 200], 'materials': {'Net': NET}},
    # One placement: a one-off prop.
    '7dec21': {'output': 'mm7_deco_7dec21.glb', 'budget': [2000, 900, 300, 120], 'materials': {}},
    # 36 placements (tens band 1500-4000): the posed Meshy skeleton.
    'dec19': {'output': 'mm7_deco_dec19.glb', 'budget': [4000, 1700, 650, 250], 'materials': {}},
    # One placement: the full Meshy skull (one-off, up to 6000).
    '7dec20': {'output': 'mm7_deco_7dec20.glb', 'budget': [5500, 2300, 850, 300], 'materials': {}},
    # 13 placements (tens band 1500-4000): skull on a bone pile.
    '7dec18': {'output': 'mm7_deco_7dec18.glb', 'budget': [4000, 1900, 750, 300], 'materials': {}},
}
