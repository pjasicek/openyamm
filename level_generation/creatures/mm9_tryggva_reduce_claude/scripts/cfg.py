"""This project's model: Tryggva Ravenlocks (installed mm9_tryggva.glb, node Tryggva, prims Tryggva (body) / TryggvaHead
(face shell, hair shell with the fused ears and fur lapels, braids, MPFB hands)). Pieces = connected components welded by
position, numbered as scripts/probe_pieces.py / glb_parts.py number them (scipy connected_components order).
Part codes (glb_parts.py format of the PeasantM1 project): body 1 tunic + sleeves, 3 belt, 4 collar, 5 trousers + boots
(one piece), 7 shoulder fur, 9 small; head 0 hands, 20 face shell, 21 hair shell, 23 braids, 22 small (mouth, braid ends)."""
GLB = 'mm9_tryggva.glb'
NODE = 'Tryggva'
PR = ['Tryggva', 'TryggvaHead']
HEIGHT = None  # measured by the ladder (standing height)
BODY_PIECES = {0: 1, 3: 3, 4: 4, 2: 5, 6: 7, 1: 7}          # others -> 9
HEAD_PIECES = {6: 20, 1: 21, 10: 23, 5: 23, 4: 23, 9: 23}   # hands by joints -> 0, others -> 22
# ears fused into the hair shell (../mm9_tryggva_claude/scripts/fix_ear_try.py box, widened 1-2 cm): hair-shell faces with the
# centroid here are kept exact (the ear and the hair framing it)
EAR_X, EAR_Y, EAR_Z = 0.035, (1.55, 1.72), (-0.10, 0.065)
