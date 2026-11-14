"""Per-kind settings shared by prep.py, the Codex briefs and post.py (README.md "Route").

pieces: the upload's pieces, as Blender-Z ranges of face centres (top first); prep.py stands them side by side so a
long weapon fills the Meshy guides at three to four times the resolution of one full-length view (original UVs: the
paint lands on the assembled model). head_z: faces above it are the head (denser UVs). views: the guide views.
"""

KINDS = {
    'spear': {'pieces': [(77.0, 999.0), (42.0, 77.0), (6.0, 42.0), (-999.0, 6.0)], 'head_z': 77.0,
              'views': ('front', 'back'), 'template': 'w_spear',
              # Built 140 units long and painted so; held 118 long (README.md "Held length"): the plain wood between
              # the wrap's top band (z 12) and the socket (z 77) shortened to 0.66 in export_mesh.py, same UVs.
              'compress': (12.0, 77.0, 0.66)},
    'halberd': {'pieces': [(36.0, 999.0), (4.0, 36.0), (-999.0, 4.0)], 'head_z': 36.0,
                'views': ('front', 'back'), 'template': 'w_halberd'},
    'trident': {'pieces': [(48.0, 999.0), (14.0, 48.0), (-999.0, 14.0)], 'head_z': 48.0,
                'views': ('front', 'back'), 'template': 'w_trident'},
    'wand': {'pieces': [(-999.0, 999.0)], 'head_z': 999.0, 'views': ('front', 'back', 'left'), 'template': 'w_wand'},
    'blaster': {'pieces': [(-999.0, 999.0)], 'head_z': 999.0, 'views': ('front', 'back', 'top'),
                'template': 'w_blaster',
                # Built muzzle along -X as the Gun mount's comment says; in game the muzzle then points at the eye, so
                # the runtime copy is turned half a turn about the vertical (export_mesh.py).
                'turn': True,
                # The fist closes around the grip (README.md "Blaster"): built with the palm 1.5 units below the body,
                # the index and middle fingers sat inside it and the fist read as closing below the gun. Lifted 2.3
                # units up the fist (the body's underside just above the index finger, the trigger at its tip, the
                # pommel below the little finger) and the muzzle raised 10 degrees about the palm (the grip's rake
                # along the fist's axis).
                'shift': 2.3, 'aim': 10.0},
    'crossbow': {'pieces': [(-999.0, 999.0)], 'head_z': 999.0, 'views': ('top', 'front', 'back'),
                 'template': 'w_crossbow',
                 # Built in the left hand's Torch frame (the foregrip in the left fist); held since the crossbow set
                 # (crossbow_set_20261114) in the right hand's Weapon node, the wrist of the stock through the fist:
                 # the runtime copy is placed rigidly by weapon_from_build (export_mesh.py), which the set's clip bake
                 # uses too. grip: the stock's wrist (Blender build coordinates) at the fist's centre; roll: a turn
                 # about the stock (degrees, positive: the top toward the back of the hand; at 0 the hand hangs over
                 # the stock like a suitcase's, at -115 it cradles the wrist from below and behind, the elbow down);
                 # tilt: the stock's nose raised in the fist (degrees).
                 'mount': {'grip': (-11.5, 0.0, 3.95), 'roll': -115.0, 'tilt': 0.0}},
    # Two pieces (knob and handle, cut in the plain shaft at z 18) for the upload: 55 units long and 12 across. Tiers
    # 1 and 2 only: every club is below the 150 value band (held_tiers.yml max_tier 2).
    'club': {'pieces': [(18.0, 999.0), (-999.0, 18.0)], 'head_z': 26.0, 'views': ('front', 'back'),
             'template': 'w_club',
             # Built with the palm at the wrap's middle; the runtime copy moved 4.5 units down the hand
             # (export_mesh.py): butt 15 below the palm as on the mace, the knob's neck at the top of the idle frame.
             'shift': -4.5},
}


def weapon_from_build(mount):
    """The crossbow's placement in the right hand's Weapon node (kinds.py 'mount'): a rigid 4x4 in glTF coordinates
    from the build frame (the left hand's Torch frame: bolt +X, up +Y, right +Z) to the Weapon frame, where a held
    weapon runs along +Y out of the fist's thumb side, the knuckles face +X and the back of the hand +Z. The stock runs
    along +Y (the bolt forward), its top toward -X, its right side toward the back of the hand; the stock's wrist at
    the fist's centre. numpy is imported here only, so the table above stays plain data."""
    import numpy as np

    to_gltf = np.array([[1.0, 0.0, 0.0], [0.0, 0.0, 1.0], [0.0, -1.0, 0.0]])
    base = np.array([[0.0, -1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 1.0]])
    roll, tilt = np.radians(mount['roll']), np.radians(mount['tilt'])
    about_y = np.array([[np.cos(roll), 0.0, np.sin(roll)], [0.0, 1.0, 0.0], [-np.sin(roll), 0.0, np.cos(roll)]])
    about_z = np.array([[np.cos(tilt), -np.sin(tilt), 0.0], [np.sin(tilt), np.cos(tilt), 0.0], [0.0, 0.0, 1.0]])
    rotation = about_z @ about_y @ base
    out = np.eye(4)
    out[:3, :3] = rotation
    out[:3, 3] = -rotation @ (to_gltf @ np.array(mount['grip'], float))
    return out
