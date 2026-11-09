"""Record a source-driven attack plan. This does not key or modify the Blender rig."""
import csv
import base64
import hashlib
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

STAGE = Path(__file__).resolve().parent
ROOT = STAGE.parents[3]
AUDIT = json.loads((STAGE / 'native_reference_audit.json').read_text())
RIG = json.loads((STAGE / 'rig_control_study.json').read_text())

# Manual image landmarks, not recovered 3D joints. X right, Y down, full native canvas.
# Long-claw tips are SCREEN ORDER ONLY; hidden anatomy and digit identities are not invented.
POSES = [
    dict(letter='a', phase='Ready',
         right=[(141, 120), (119, 156), (87, 189), (78, 209)],
         left=[(209, 120), (221, 165), (241, 213), (246, 235)],
         right_tips=[(94, 210), (96, 224), (93, 236)], right_thumb=(92, 181),
         left_tips=[(223, 248), (224, 264), (231, 272)], left_thumb=(232, 219),
         eyes=(177, 84), chin=(177, 108), clasp=(174, 131), tail=(157, 275), tail_confidence='low',
         observed='Right hand low and slightly out; both hands hooked; head frontal and snarling; feet planted.'),
    dict(letter='b', phase='Open and lift',
         right=[(142, 120), (111, 143), (76, 143), (65, 139)],
         left=[(209, 121), (219, 155), (215, 172), (218, 181)],
         right_tips=[(38, 121), (31, 135), (31, 147)], right_thumb=(71, 118),
         left_tips=[(201, 171), (206, 194), (206, 209)], left_thumb=None,
         eyes=(177, 84), chin=(177, 110), clasp=(173, 130), tail=None, tail_confidence='occluded',
         observed='Right upper arm lifts outward, elbow bends; open palm faces camera. Left hand rises; mouth opens.'),
    dict(letter='c', phase='High open claw',
         right=[(141, 122), (101, 139), (55, 105), (41, 94)],
         left=[(209, 124), (216, 155), (202, 165), (182, 162)],
         right_tips=[(5, 73), (5, 56), (20, 48)], right_thumb=(47, 66),
         left_tips=[(142, 148), (151, 170), (172, 184)], left_thumb=None,
         eyes=(177, 84), chin=(177, 116), clasp=(172, 129), tail=(194, 283), tail_confidence='moderate',
         observed='Right forearm rotates up about a bent elbow, claw fanned high left. Left hand guards abdomen; jaw widest.'),
    dict(letter='d', phase='Lower before sweep',
         right=[(142, 124), (101, 151), (71, 140), (58, 133)],
         left=[(211, 128), (222, 176), (235, 199), (240, 211)],
         right_tips=[(31, 106), (22, 122), (20, 134)], right_thumb=(68, 110),
         left_tips=[(237, 216), (238, 231), None], left_thumb=None,
         eyes=(177, 91), chin=(177, 119), clasp=(175, 142), tail=(195, 289), tail_confidence='moderate',
         observed='Open right hand lowers outward toward chest height. Left guard drops; head and chest dip; mouth remains open.'),
    dict(letter='e', phase='Across-body stroke',
         right=[(143, 127), (149, 165), (188, 163), (211, 166)],
         left=[(210, 126), (245, 192), (271, 211), (290, 226)],
         right_tips=[(255, 150), (257, 164), (253, 176)], right_thumb=(227, 142),
         left_tips=[(306, 216), (299, 238), (287, 246)], left_thumb=None,
         eyes=(183, 97), chin=(181, 119), clasp=(181, 146), tail=(162, 281), tail_confidence='moderate',
         observed='Right forearm and open fingers sweep across chest toward screen right. Left arm counterbalances down/out; torso and head tilt.'),
    dict(letter='f', phase='Recover',
         right=[(141, 120), (121, 165), (94, 210), (91, 232)],
         left=[(209, 121), (222, 170), (247, 229), (248, 251)],
         right_tips=[(110, 222), (112, 237), (110, 248)], right_thumb=(97, 196),
         left_tips=[(226, 265), (228, 279), (237, 286)], left_thumb=(240, 237),
         eyes=(177, 84), chin=(177, 108), clasp=(174, 131), tail=(168, 270), tail_confidence='low',
         observed='Both arms return low, hands recurl, head and torso return frontal; feet remain planted. F differs from A and standing.'),
]

# These are restrained fitting seeds, not measurements or executable bone-local Euler angles.
SEEDS = {
    'torso_world_yaw_deg': [0, -3, -6, 0, 16, 0],
    'torso_nose_down_pitch_deg': [0, 0, 2, 7, 8, 0],
    'head_world_yaw_deg': [0, 0, -4, 0, 10, 0],
    'head_world_nose_down_pitch_deg': [0, 0, -2, 4, 6, 0],
    'head_screen_clockwise_roll_deg': [0, 0, 2, 0, -6, 0],
    'mouth_open_fraction': [0, .3, 1, .95, .55, .05],
    'clean_jaw_hinge_open_deg': [0, 5, 18, 17, 10, 0],
    'right_palm_front_facing_weight': [.25, .95, 1, .95, .45, .25],
    'right_clavicle_elevation_deg': [0, 2, 4, 2, 0, 0],
    'left_clavicle_elevation_deg': [0, 0, 1, 0, 0, 0],
    'right_proximal_finger_straightening_fraction': [.1, .75, 1, .9, .9, .15],
    'right_fan_half_angle_deg': [5, 14, 18, 15, 12, 5],
    'right_thumb_spread_deg': [10, 22, 28, 24, 20, 10],
    'left_proximal_finger_straightening_fraction': [.1, .15, .25, .1, .1, .1],
    'tail_total_world_z_yaw_deg': [10, -4, -12, -14, 12, 4],
}

CHECKS = {
    'J': 'Fixed real joint lengths; no bone/object scale, elbow flip or wrist discontinuity.',
    'S': 'Shoulder horns follow shoulder, forearm spines follow forearm; harness/clasp remain attached.',
    'C': 'Three main digits plus thumb retain order; hard tips rigid; no digit intersections; measure all six tip pairs.',
    'B': 'Hand/forearm surfaces clear chest, harness and opposite arm in front AND profile.',
    'H': 'Skull/upper teeth remain rigid; lower jaw hinges independently; no muzzle shortening or mouth collision.',
    'F': 'Both sole patches stay planted with fixed footprint; no toe curl, sideways roll or floor penetration.',
    'T': 'Tail lengths fixed; root does not pull belly; no thigh/floor intersections or kink.',
    'P': 'One fixed comparison camera; approximate source landmark fit and silhouette; inspect all views and subframes.',
}


def projected_arm(points):
    shoulder, elbow, wrist, palm = points
    upper = [elbow[0] - shoulder[0], shoulder[1] - elbow[1]]
    lower = [wrist[0] - elbow[0], elbow[1] - wrist[1]]
    hand = [palm[0] - wrist[0], wrist[1] - palm[1]]
    angles = [math.degrees(math.atan2(v[1], v[0])) for v in (upper, lower, hand)]
    dot = sum(a * b for a, b in zip(upper, lower))
    bend = math.degrees(math.acos(max(-1, min(1, dot / (math.hypot(*upper) * math.hypot(*lower))))))
    return dict(upper_heading_deg=round(angles[0], 3), forearm_heading_deg=round(angles[1], 3),
                hand_heading_deg=round(angles[2], 3), projected_elbow_bend_deg=round(bend, 3))


def lerp(a, b, u):
    if a is None or b is None:
        return None
    return [round(x * (1 - u) + y * u, 4) for x, y in zip(a, b)]


def smooth(u):
    return u * u * (3 - 2 * u)


anchors = []
for index, pose in enumerate(POSES):
    anchors.append({**pose, 'source_frame': 'dmnatk' + pose['letter'] + '0',
                    'time_ms': index * 125, 'planned_sample': index * 6,
                    'arm_landmark_order': ['shoulder', 'elbow', 'wrist', 'palm'],
                    'landmark_uncertainty_px': {'joint_centers': 6, 'visible_tips_eyes_clasp': 4},
                    'long_claw_tip_identity': 'screen order only; does not assign native digits to rig labels',
                    'projected_right_arm': projected_arm(pose['right']),
                    'projected_left_arm': projected_arm(pose['left']),
                    'inferred_control_seeds': {key: values[index] for key, values in SEEDS.items()}})

actions = [
    ('Lift right upper arm outward; bend elbow and turn palm forward; open proximal knuckles.',
     'Bend left elbow and raise hooked hand beside torso.',
     'Keep gaze forward; start opening lower jaw; subtle backward torso anticipation.'),
    ('Raise right forearm around elbow; retain elbow bend; fan fingers high without straightening the whole arm.',
     'Bring left hooked hand across low chest/abdomen, in front of body.',
     'Open lower jaw to maximum; keep upper face rigid; slight head tilt only.'),
    ('Lower right wrist and open palm outward toward chest height; elbow remains bent.',
     'Release guard and lower left elbow/hand.',
     'Dip chest and head through spine/neck rotations; jaw remains open.'),
    ('Sweep right forearm across front of chest; turn upper arm inward; retain separated extended fingers.',
     'Extend left arm down/out as counterbalance; retain hooked fingers.',
     'Small torso yaw/forward dip and head compensation; begin closing jaw; tail reverses behind legs.'),
    ('Retract right hand away from chest, lower arm and recurl proximal joints; avoid body intersection.',
     'Lower left arm toward source F guard.',
     'Return head/torso toward front; close jaw toward snarl; let tail settle.'),
    ('Hold source F low right guard; do not snap to A or A-pose.',
     'Hold source F left guard.',
     'Hold recovered head/torso until 750 ms; standing blend belongs outside this clip.'),
]

frames = []
for sample in range(37):
    segment = min(sample // 6, 5)
    next_segment = min(segment + 1, 5)
    u = (sample - segment * 6) / 6
    p, q = POSES[segment], POSES[next_segment]
    # Screen-space guides only. The eventual rig uses fixed-length rotations/IK, not joint translations.
    guides = {side: [lerp(a, b, u) for a, b in zip(p[side], q[side])] for side in ('right', 'left')}
    controls = {key: round(values[segment] * (1 - smooth(u)) + values[next_segment] * smooth(u), 5)
                for key, values in SEEDS.items()}
    guide_points = {key: lerp(p[key], q[key], u) for key in ('eyes', 'chin', 'clasp', 'tail')}
    frame = dict(sample=sample, time_ms=round(sample * 1000 / 48, 6),
                 source_hold_frame='dmnatk' + POSES[min(sample // 6, 5)]['letter'] + '0',
                 exact_source_anchor=sample in (0, 6, 12, 18, 24, 30),
                 source_anchor_or_endpoint=sample in (0, 6, 12, 18, 24, 30, 36),
                 transition=f"{p['letter'].upper()} -> {q['letter'].upper()}", transition_fraction=round(u, 6),
                 screen_guide_only=guides, other_screen_guides=guide_points,
                 projected_arm_guides={side: projected_arm(guides[side]) for side in ('right', 'left')},
                 inferred_control_seeds=controls,
                 movement=dict(zip(('right_arm_hand', 'left_arm_hand', 'head_body_tail'), actions[segment])),
                 feet='Both fixed footprint/sole targets; solve knees/hips without bone scaling.',
                 check_ids=list(CHECKS),
                 priority_checks=['B', 'C', 'J'] if 12 < sample < 30 else ['H', 'C', 'F'])
    frames.append(frame)

tracked_paths = [ROOT / frame['source_path'] for frame in AUDIT['attack_frames']]
tracked_paths += [STAGE.parent / 'meshy_rig_review' / name for name in
                  ('mm6_demon_rig_corrected.glb', 'mm6_demon_rig_corrected.blend')]
tracked_paths += [Path('/home/pjasicek/Downloads/Meshy_AI_mm6_demon_cleaned_All_Animations.glb')]
hashes = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in tracked_paths}
for source_frame in AUDIT['attack_frames']:
    assert hashes[str(ROOT / source_frame['source_path'])] == source_frame['sha256']
expected_rig_hashes = {
    'mm6_demon_rig_corrected.glb': '08b092138084c0541f40b03905f55ac448a8718fcd641f43d06a588932007eab',
    'mm6_demon_rig_corrected.blend': '466ef259aca9805b3219b9316c433c6538b97d86ac8d4733865b9b0888d9b0c1',
}
for name, expected in expected_rig_hashes.items():
    assert hashes[str(STAGE.parent / 'meshy_rig_review' / name)] == expected
assert hashes['/home/pjasicek/Downloads/Meshy_AI_mm6_demon_cleaned_All_Animations.glb'] == (
    'f7631fca2e11a01740035028b507584a6f1c4f2fd7251529918495b8bdaa9996')
spec = dict(status='Study complete; no authored attack, no final deformation acceptance',
            native=dict(sprite_group='danatka0', sprite_id=18794, descriptor_id=502, palette_id=688,
                        duration_ms=750, frames=6, hold_ms=125, genuine_views=1, aliases=['attack2'],
                        timing_evidence='assets_dev/engine/rendering/sprite_frame_data_common.yml',
                        other_octants='Image1 repeats the frontal view; standing has five genuine stored views'),
            proposed_clip=dict(name='Attack_Native_Study', fps=48, samples_including_endpoint=37,
                               duration_ms=750, loop=False, anchor_samples=[0, 6, 12, 18, 24, 30],
                               endpoint_sample=36, endpoint='Hold F; subsequent standing blend is separate',
                               anchors_are_observed=True, intermediate_motion_is_inferred=True,
                               impact_event='No gameplay event inferred from the visual sweep pose'),
            coordinates=dict(native='354x330 canvas; x right, y down; anatomical right is screen left',
                             blender='Z up, front -Y, anatomical right -X',
                             angle_guides='Screen headings: 0 right, 90 up. Projected bends are not 3D elbow angles.',
                             seeds='Semantic world targets, NOT executable bone-local Euler angles. +Z yaw turns front toward +X.',
                             comparison='Fit one camera and model transform to standing; keep fixed for all poses'),
            solver=dict(arm_chain_lengths=RIG['arm_chain_lengths'],
                        wrist_landmark='Hand.head; ForeArm.tail is about 0.098 units short of the wrist',
                        rotations='Quaternion interpolation + fixed-length arm IK with persistent elbow pole',
                        screen_guides='Interpolated 2D guides are fitting references only; do not translate skeleton joints to them',
                        depth='Infer from standing/profile anatomy and front-most hand overlap; enforce surface clearance. D-to-E and E-to-F guides can foreshorten: retain real length in depth.',
                        head='Solve world target after torso; use local compensation rather than adding world angles twice',
                        fingers='Proximal knuckles/fan only; preserve terminal claw local shape; mark semantic tip vertices',
                        tail='Keep Bone_020 root fixed initially; distribute target over 019..015; add restrained distal lag'),
            prerequisites=[
                'Repair Bone_025 hinge/weights: existing opening moves upper face and skull.',
                'Resolve Pinky distal-region stretch and establish semantic hard-tip masks including thumb.',
                'Fit six source anchors and validate chest clearance before interpolating the full clip.',
            ],
            checks=CHECKS,
            thresholds=dict(bone_length_relative_error=1e-5, semantic_hard_claw_edge_relative_error=.01,
                            planted_foot_drift_units=.002, floor_penetration_units=.002,
                            jaw_test_upper_skull_displacement_units=.0001,
                            source_joint_fit_px=6, source_visible_feature_fit_px=4,
                            surface_clearance_goal_units=.003,
                            thresholds_are_review_targets_not_measured_final_results=True),
            required_review=dict(output_samples=37, quarter_sample_inbetween_poses=145,
                                 views=['front', 'left profile', 'right profile', 'rear', 'both three-quarter'],
                                 independent_features=['shoulder and elbow centers', 'wrist center and palm normal',
                                                       'semantic claw tips and all pair distances', 'upper face and lower jaw',
                                                       'harness clasp', 'sole contact patches', 'tail contour'],
                                 actual_glb_reimport=True, acceptance='Pending authoring and complete visual review'),
            anchors=anchors, planned_frames=frames, preserved_file_sha256=hashes)
(STAGE / 'attack_motion_spec.json').write_text(json.dumps(spec, indent=2) + '\n')

with (STAGE / 'planned_frames.csv').open('w', newline='') as output:
    fields = ['sample', 'time_ms', 'transition', 'transition_fraction', 'source_anchor_or_endpoint',
              'right_upper_heading', 'right_forearm_heading', 'right_projected_elbow_bend',
              'left_upper_heading', 'left_forearm_heading', 'left_projected_elbow_bend', *SEEDS,
              'right_arm_hand', 'left_arm_hand', 'head_body_tail', 'checks']
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    for frame in frames:
        row = {key: frame[key] for key in fields[:5]}
        for side in ('right', 'left'):
            angles = frame['projected_arm_guides'][side]
            row[side + '_upper_heading'] = angles['upper_heading_deg']
            row[side + '_forearm_heading'] = angles['forearm_heading_deg']
            row[side + '_projected_elbow_bend'] = angles['projected_elbow_bend_deg']
        row.update(frame['inferred_control_seeds'])
        row.update(frame['movement'])
        row['checks'] = ','.join(frame['check_ids'])
        writer.writerow(row)

# Explicitly annotated diagnostic plate; source PNGs remain untouched.
font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
font = ImageFont.truetype(font_path, 18)
small = ImageFont.truetype(font_path, 14)
cell_width, cell_height = 708, 735
sheet = Image.new('RGB', (cell_width * 3, cell_height * 2), (27, 32, 38))
draw = ImageDraw.Draw(sheet)
for index, pose in enumerate(POSES):
    ox, oy = index % 3 * cell_width, index // 3 * cell_height
    source_path = ROOT / AUDIT['attack_frames'][index]['source_path']
    native = Image.open(source_path).convert('RGBA').resize((708, 660), Image.Resampling.NEAREST)
    sheet.paste(native, (ox, oy + 40), native)
    draw.text((ox + 12, oy + 8), f"{pose['letter'].upper()} | {index * 125} ms | {pose['phase']}", font=font, fill='white')
    for side, color in (('right', '#ffad56'), ('left', '#63d6eb')):
        points = [(ox + 2 * x, oy + 40 + 2 * y) for x, y in pose[side]]
        draw.line(points, fill=color, width=3)
        for point, label in zip(points, ('S', 'E', 'W', 'P')):
            x, y = point
            draw.ellipse((x - 4, y - 4, x + 4, y + 4), fill=color)
            draw.text((x + 5, y - 8), label, fill=color, font=small)
        for tip in pose[side + '_tips']:
            if tip is not None:
                x, y = ox + 2 * tip[0], oy + 40 + 2 * tip[1]
                draw.ellipse((x - 4, y - 4, x + 4, y + 4), outline=color, width=2)
    draw.line((ox, oy + 698, ox + 708, oy + 698), fill='#66717e')
    draw.text((ox + 12, oy + 708), 'Orange: anatomical R | Cyan: L | Approximate screen guides only', font=small, fill='#d8e1e9')
sheet.save(STAGE / 'annotated_native_attack.png')

art = {frame['frame']: 'data:image/png;base64,' + base64.b64encode((ROOT / frame['source_path']).read_bytes()).decode()
       for frame in AUDIT['attack_frames']}
template = (STAGE / 'review_template.html').read_text()
(STAGE / 'index.html').write_text(template.replace('__SPEC_DATA__', json.dumps(spec))
                                .replace('__NATIVE_IMAGES__', json.dumps(art)))

# Focused bookkeeping validation. This is not a pose/deformation pass.
assert len(frames) == 37 and frames[-1]['time_ms'] == 750
assert [f['sample'] for f in frames if f['exact_source_anchor']] == [0, 6, 12, 18, 24, 30]
assert all(frame['check_ids'] == list(CHECKS) for frame in frames)
assert anchors[3]['left_tips'][2] is None and anchors[1]['tail'] is None
assert frames[-1]['screen_guide_only']['right'] == [list(point) for point in POSES[-1]['right']]
for name, digest in hashes.items():
    assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == digest
print('Saved six annotated source anchors and 37 planned samples; preserved input hashes; no Blender mutation.')
