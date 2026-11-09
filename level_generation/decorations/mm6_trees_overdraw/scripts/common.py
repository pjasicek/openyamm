"""Paths and per-tree settings for the MM6 leaf overdraw pass (system Python and Blender's Python).

species/<id>.json lists what differs from DEFAULTS. <id> is the short model id (tree01 -> mm6_deco_tree01.glb)."""
import copy, json, os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
MM6_TREES = os.path.join(HERE, '..', 'mm6_new_sorpigal_3d', 'trees')      # read only
BLENDER = '/snap/bin/blender'

DEFAULTS = {
    # crown shell per LOD (shell.py): 'star' = sphere grid around the crown centre at the far crossing of the clump
    # ellipsoids (scale x clump radius, axes from the spread of the clump's cards), capped at (1 - inset) x the card
    # envelope; 'nets' = surface-nets mesh of the smooth ellipsoid union decimated to `tris` (separate pads)
    # (tree01 values, 2026-10-16). Colour: ao (sky term), jitter (per-vertex value), normal_out (shading normals
    # lean up), dark_under (the underside keeps downward normals), texture ('impostor' or 'white'), value (tune.py)
    'shell': {'mode': 'star', 'scale': [0.8, 0.8, 0.8], 'inset': [0.35, 0.35, 0.35], 'inset_down': 0.25,
              'grid': [[16, 10], [14, 8], [10, 6]], 'smooth': 1, 'resolution': 0.08, 'tris': [260, 200, 90],
              'skip_inner': False, 'value': 1.0, 'ao': 0.4, 'jitter': 0.35, 'normal_out': 0.6,
              'dark_under': False, 'texture': 'impostor', 'floor': 0.8, 'uv_fold': True},
    # cards (shell.py): those wholly inside the shell (corners pulled `inside_shrink` toward the centre) are marked;
    # select_cards.py then keeps the cards that matter until the view layers reach `layers`; `grow` scales kept
    # cards about their centres; `fringe` / `depth` / `under_weight`: select_cards.py's pixel values and view weight
    'cards': {'inside_shrink': 0.7, 'keep': [1.0, 1.0, 1.0], 'grow': [1.0, 1.0, 1.08], 'margin': 0.0,
              'layers': [2.7, 2.7, 2.4], 'fringe': 2.0, 'depth': 0.15, 'under_weight': 0.6,
              'vc_floor': 0.15, 'dark_bias': [0.5, 0.5, 0.0]},
}


def _merge(base, extra):
    for key, value in extra.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _merge(base[key], value)
        else:
            base[key] = value
    return base


def load(tid):
    spec = _merge(copy.deepcopy(DEFAULTS), json.load(open(os.path.join(HERE, 'species', f'{tid}.json'))))
    spec['id'] = tid
    spec.setdefault('glb', f'mm6_deco_{tid}.glb')
    spec['work'] = os.path.join(HERE, 'work', tid)
    spec['review'] = os.path.join(HERE, 'review', tid)
    os.makedirs(spec['work'], exist_ok=True)
    os.makedirs(spec['review'], exist_ok=True)
    return spec
