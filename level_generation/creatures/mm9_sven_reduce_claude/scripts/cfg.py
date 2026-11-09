"""This project's model: Sven Svenssen (installed mm9_sven.glb, node Sven, prims Sven (body) / SvenHead (face shell with the
painted beard, hair shell, side braids, eyes, lips, MPFB hands)). Pieces = connected components welded by position, numbered as
scripts/probe_pieces.py / glb_parts.py number them (scipy connected_components order).
Part codes: body 1 tunic/vest, 2 bare arms + bracers, 3 belt, 5 trousers, 6 boots, 9 small (necklace plaques, brooches, boot
pieces); head 0 hands, 20 face shell, 21 hair shell, 23 side braids, 22 small (eyes, lips, bits)."""
GLB = 'mm9_sven.glb'
NODE = 'Sven'
PR = ['Sven', 'SvenHead']
BODY_PIECES = {2: 1, 13: 2, 0: 2, 5: 3, 3: 5, 11: 6, 1: 6}   # others -> 9
HEAD_PIECES = {3: 20, 1: 21, 11: 23, 2: 23}                  # hands by joints -> 0, others -> 22
# ear box (skin-coloured hair-shell faces here are kept exact with a pad, as on Tryggva)
EAR_X, EAR_Y, EAR_Z = 0.05, (1.56, 1.72), (-0.08, 0.05)
