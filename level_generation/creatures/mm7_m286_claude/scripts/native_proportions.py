#!/usr/bin/env python3
"""Native silhouette proportions of the MM7 Minotaur from the restored x2 standing frames.

Landmark rows were picked on gridded crops of ../mm7_m286/aligned_2x/m286sa0 (front), sa2 (right profile) and sa4
(back); widths come from the alpha runs at those rows where the silhouette separates, and from the marked anatomical
edges where the arms touch the torso (chest, waist). Everything is divided by H = sole to skull top (horns excluded).

Writes review/native_proportions.json.
"""
import json
from pathlib import Path

import numpy as np
from PIL import Image

P = Path(__file__).resolve().parents[1]
X2 = P.parent / 'mm7_m286/aligned_2x'


def runs(alpha, y):
    row = np.r_[0, (alpha[y] > 100).astype(int), 0]
    xs = np.flatnonzero(np.diff(row))
    return [(int(a), int(b) - 1) for a, b in zip(xs[::2], xs[1::2])]


def main():
    front = np.array(Image.open(X2 / 'm286sa0.png'))[..., 3]
    side = np.array(Image.open(X2 / 'm286sa2.png'))[..., 3]
    back = np.array(Image.open(X2 / 'm286sa4.png'))[..., 3]
    ys = np.flatnonzero(front.max(axis=1) > 100)
    horn_tip, sole = int(ys[0]), int(ys[-1])

    # Landmark rows (front frame, y down), by inspection.
    rows = {
        'horn_tip': horn_tip,
        'skull_top': 146,      # fur crown between the horn roots
        'eyes': 176,
        'chin': 212,           # lower jaw / nose-ring bottom
        'acromion': 225,       # top of the deltoids (shoulder line)
        'deltoid': 240,        # widest deltoid
        'armpit': 262,
        'waist': 300,          # narrowest torso above the belt
        'belt': 315,
        'kilt_hip': 364,       # fur kilt at the hip (below the left fist, right of the axe haft)
        'kilt_hem': 385,
        'crotch': 398,         # first row where the legs separate below the kilt
        'thigh': 412,
        'knee': 418,           # side view: knee most forward
        'hock': 455,           # side view: hock most backward
        'shin': 460,
        'fist_bottom': 365,
        'sole': sole,
    }
    H = sole - rows['skull_top']

    def central(alpha, y, cx):
        for a, b in runs(alpha, y):
            if a <= cx <= b:
                return a, b
        raise ValueError((y, runs(alpha, y)))

    # Widths in px (front unless stated). Edges where arm and torso touch are the marked anatomical edges.
    sternum_x = 257.5
    widths = {
        'shoulder_width': (182.5, 340.0),          # outer deltoids at the deltoid row
        'upper_arm_span': runs(front, 280)[0][0], # filled below
        'chest_width': (208.5, 306.5),             # pec/lat edges at the armpit, symmetric about the sternum
        'waist_width': (217.5, 297.5),
        'belt_width': (225.0, 299.0),
        'kilt_hip_width': (212.0, 320.0),          # row 364: the haft ends the run at 212 on the left
        'leg_outer_span_thigh': None,
        'thigh_width_single': None,
        'shin_width_single': None,
        'hoof_width_single': None,
        'hoof_outer_span': None,
        'head_width_no_ears': central(front, 184, sternum_x),
        'ear_span': central(front, 172, sternum_x),
        'horn_span': (runs(front, 130)[0][0], runs(front, 130)[-1][1]),
        'upper_arm_width': (302.5, 342.5),         # creature's left arm at y 270 (front)
        'upper_arm_width_back': runs(back, 280)[0],
        'forearm_band_width': (322.0, 359.0),      # wrist band without spikes, y 310
        'fist_width': (312.0, 347.0),
    }
    r280 = runs(front, 280)
    widths['upper_arm_span'] = (r280[0][0], r280[-1][1])
    r412 = runs(front, rows['thigh'])
    widths['leg_outer_span_thigh'] = (r412[0][0], r412[-1][1])
    widths['thigh_width_single'] = r412[-1]
    widths['shin_width_single'] = runs(front, rows['shin'])[-1]
    r508 = runs(front, sole - 8)
    widths['hoof_width_single'] = r508[-1]
    widths['hoof_outer_span'] = (r508[0][0], r508[-1][1])
    # Side view (faces +x): chest depth to the back skin under the mane, head length occiput -> snout.
    widths['chest_depth_side'] = (218.0, 298.0)
    widths['chest_depth_with_mane_side'] = central(side, 256, 250)
    widths['head_length_side'] = (235.0, 320.0)                # occiput hidden by the mane: informational only
    widths['eye_to_snout_side'] = (284.8, 324.0)               # red eye pixels' centre -> snout tip (ring excluded)

    px = {k: float(b - a + (0 if isinstance(a, float) else 1)) for k, (a, b) in widths.items()}
    heights = {k: (sole - v) / H for k, v in rows.items()}
    ratios = {k: round(v / H, 4) for k, v in px.items()}
    derived = {
        'head_height': round((rows['chin'] - rows['skull_top']) / H, 4),
        'skull_top_to_acromion': round((rows['acromion'] - rows['skull_top']) / H, 4),
        'chin_above_acromion': round((rows['acromion'] - rows['chin']) / H, 4),
        'horn_rise': round((rows['skull_top'] - rows['horn_tip']) / H, 4),
        'torso_acromion_to_crotch': round((rows['crotch'] - rows['acromion']) / H, 4),
        'leg_crotch_height': round((sole - rows['crotch']) / H, 4),
        'arm_acromion_to_fist_bottom': round((rows['fist_bottom'] - rows['acromion']) / H, 4),
        'shoulder_to_waist': round(px['shoulder_width'] / px['waist_width'], 3),
        'shoulder_to_kilt_hip': round(px['shoulder_width'] / px['kilt_hip_width'], 3),
    }
    out = {
        'source': {'front': 'mm7_m286/aligned_2x/m286sa0.png', 'side': 'mm7_m286/aligned_2x/m286sa2.png',
                   'back': 'mm7_m286/aligned_2x/m286sa4.png'},
        'method': __doc__.strip(),
        'H_px': H,
        'H_definition': 'sole to skull top (horns excluded); total to horn tip = %.3f H' % ((sole - horn_tip) / H),
        'landmark_rows_px': rows,
        'landmark_heights_over_H': {k: round(v, 4) for k, v in heights.items()},
        'widths_px': px,
        'widths_over_H': ratios,
        'derived': derived,
        'gate_ratios': {
            # The ratios the HD masters and the final mesh are gated on (target within ~10 %).
            'head_height': derived['head_height'],
            'skull_top_to_acromion': derived['skull_top_to_acromion'],
            'shoulder_width': ratios['shoulder_width'],
            'chest_width': ratios['chest_width'],
            'waist_width': ratios['waist_width'],
            'kilt_hip_width': ratios['kilt_hip_width'],
            'leg_crotch_height': derived['leg_crotch_height'],
            'leg_outer_span_thigh': ratios['leg_outer_span_thigh'],
            'thigh_width_single': ratios['thigh_width_single'],
            'shin_width_single': ratios['shin_width_single'],
            'upper_arm_width': ratios['upper_arm_width'],
            'forearm_band_width': ratios['forearm_band_width'],
            'arm_acromion_to_fist_bottom': derived['arm_acromion_to_fist_bottom'],
            'head_width_no_ears': ratios['head_width_no_ears'],
            'horn_rise': derived['horn_rise'],
            'chest_depth_side': ratios['chest_depth_side'],
            'eye_to_snout_side': ratios['eye_to_snout_side'],
        },
        'notes': [
            'Shoulder width is about 2x the waist (%.2f) and 1.5x the kilt at the hip.' % derived['shoulder_to_waist'],
            'The legs separate only below the kilt hem; the true crotch is hidden, so leg_crotch_height is a minimum.',
            'Arm length is measured on the hanging arm with a slightly bent elbow (fist at the hip).',
            'Human reference (stature units): crotch ~0.47, biacromial ~0.23, chin above acromion ~0.05.',
        ],
    }
    path = P / 'review/native_proportions.json'
    path.write_text(json.dumps(out, indent=2) + '\n')
    for k, v in out['gate_ratios'].items():
        print(f'{k:32s} {v:.4f}')


if __name__ == '__main__':
    main()
