"""Build native animation plans and inspection plates; never open or modify the 3D model."""
import base64
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

STAGE = Path(__file__).resolve().parent
ROOT = STAGE.parents[3]
SOURCE = STAGE.parent.parent / 'mm6_dmn'
FPS = 48

# Hand estimates in the complete 354x330 source canvas, not recovered bone positions.
# Front: anatomical right is screen left. Profile: near/far traces have no digit/side assignment.
def front(right, left, legs, head, clasp, tail=None):
    return dict(right_arm=right, left_arm=left, right_leg=legs[:3], left_leg=legs[3:],
                head=[head], clasp=[clasp], tail=[] if tail is None else [tail])


STAND = front([[141, 120], [122, 168], [98, 216], [96, 239]],
              [[209, 120], [225, 171], [250, 221], [250, 243]],
              [[158, 208], [154, 262], [149, 316], [191, 208], [195, 262], [199, 316]],
              [177, 84], [176, 130], [177, 284])
WALK_FRONT = [
    front([[141, 120], [119, 165], [96, 207], [94, 232]],
          [[209, 120], [227, 166], [245, 205], [245, 228]],
          [[158, 207], [153, 259], [147, 312], [191, 207], [196, 262], [201, 318]],
          [177, 84], [176, 126], [187, 280]),
    front([[141, 133], [117, 179], [88, 225], [88, 244]],
          [[209, 133], [227, 176], [241, 218], [241, 243]],
          [[158, 219], [149, 272], [143, 316], [191, 219], [197, 268], [201, 318]],
          [177, 97], [176, 140], [188, 285]),
    front([[141, 117], [118, 153], [91, 188], [87, 213]],
          [[209, 117], [228, 157], [247, 199], [246, 220]],
          [[158, 204], [153, 256], [146, 317], [191, 204], [191, 242], [194, 272]],
          [177, 80], [176, 122], [174, 286]),
    front([[141, 120], [120, 159], [99, 195], [96, 218]],
          [[209, 120], [226, 163], [242, 205], [243, 226]],
          [[158, 207], [156, 261], [151, 317], [191, 207], [195, 257], [199, 310]],
          [177, 84], [176, 126], [163, 281]),
    front([[141, 133], [120, 172], [101, 215], [98, 239]],
          [[209, 133], [234, 179], [261, 225], [263, 244]],
          [[158, 219], [152, 268], [148, 318], [191, 219], [196, 272], [201, 316]],
          [177, 97], [176, 140], [166, 285]),
    front([[141, 117], [119, 156], [94, 199], [92, 221]],
          [[209, 117], [231, 153], [261, 188], [265, 213]],
          [[158, 204], [159, 242], [161, 272], [191, 204], [197, 256], [203, 317]],
          [177, 80], [176, 122], [179, 286]),
]
WALK_PROFILE = [
    dict(near_arm=[[181, 117], [199, 167], [232, 203], [247, 221]],
         near_leg=[[181, 201], [173, 258], [168, 314]],
         far_leg=[[165, 201], [158, 259], [129, 314]], head=[[203, 83]], tail=[[134, 280]]),
    dict(near_arm=[[181, 130], [200, 181], [239, 210], [250, 230]],
         near_leg=[[181, 214], [160, 265], [117, 312]],
         far_leg=[[165, 214], [195, 264], [220, 313]], head=[[204, 97]], tail=[[138, 282]]),
    dict(near_arm=[[181, 113], [205, 156], [243, 191], [258, 209]],
         near_leg=[[181, 196], [176, 252], [169, 313]],
         far_leg=[[165, 196], [139, 254], [100, 247]], head=[[204, 79]], tail=[[134, 280]]),
    dict(near_arm=[[181, 117], [202, 164], [237, 199], [253, 218]],
         near_leg=[[181, 201], [176, 258], [173, 314]],
         far_leg=[[165, 201], [155, 258], [132, 314]], head=[[203, 83]], tail=[[135, 280]]),
    dict(near_arm=[[181, 130], [212, 176], [252, 202], [271, 217]],
         near_leg=[[181, 214], [207, 264], [235, 311]],
         far_leg=[[165, 214], [145, 264], [104, 312]], head=[[204, 97]], tail=[[137, 282]]),
    dict(near_arm=[[181, 113], [201, 159], [237, 194], [252, 211]],
         near_leg=[[181, 196], [155, 254], [114, 247]],
         far_leg=[[165, 196], [174, 252], [169, 313]], head=[[204, 79]], tail=[[134, 280]]),
]
HIT_FRONT = [
    STAND,
    front([[141, 120], [123, 164], [98, 198], [96, 218]],
          [[209, 120], [229, 164], [252, 201], [255, 222]],
          [[158, 207], [154, 262], [149, 316], [191, 207], [198, 260], [201, 309]],
          [177, 82], [176, 130], [175, 281]),
    front([[142, 120], [119, 166], [79, 190], [67, 194]],
          [[209, 120], [240, 157], [261, 156], [272, 163]],
          [[158, 207], [153, 262], [149, 316], [191, 207], [201, 257], [217, 305]],
          [181, 82], [179, 131], [192, 280]),
    front([[141, 119], [120, 137], [105, 125], [88, 116]],
          [[209, 115], [235, 116], [245, 86], [254, 64]],
          [[158, 199], [154, 261], [151, 316], [191, 199], [201, 257], [221, 306]],
          [170, 79], [177, 116], [257, 181]),
]
HIT_FRONT += [HIT_FRONT[2], HIT_FRONT[1]]
FIDGET_FRONT = [
    STAND,
    front([[141, 125], [121, 171], [99, 212], [97, 231]],
          [[209, 125], [229, 171], [252, 212], [254, 233]],
          [[158, 210], [154, 263], [149, 316], [191, 210], [195, 263], [199, 316]],
          [177, 89], [176, 136], [177, 284]),
    front([[141, 129], [115, 169], [84, 185], [78, 203]],
          [[209, 129], [237, 169], [266, 184], [272, 202]],
          [[158, 211], [154, 263], [149, 316], [191, 211], [195, 263], [199, 316]],
          [177, 93], [176, 139], [177, 284]),
    front([[141, 136], [113, 166], [84, 170], [75, 173]],
          [[209, 136], [238, 166], [268, 170], [277, 173]],
          [[158, 217], [154, 265], [149, 316], [191, 217], [195, 265], [199, 316]],
          [177, 102], [176, 148], [177, 284]),
]
FIDGET_FRONT += [FIDGET_FRONT[2]]
DEATH_FRONT = [
    STAND,
    front([[141, 121], [124, 161], [104, 193], [98, 211]],
          [[209, 121], [231, 161], [257, 196], [261, 213]],
          [None] * 6, [177, 87], [176, 134]),
    front([[142, 127], [116, 156], [86, 179], [70, 183]],
          [[208, 128], [239, 150], [253, 126], [267, 120]],
          [None] * 6, [181, 101], [180, 149]),
] + [{} for _ in range(6)]

# Each row distinguishes the observed bitmap from proposed continuous 3D motion.
NOTES = {
    'standing': [
        ('Held ready stance',
         'One pose per stored view: upright body, low long arms, hooked hands, broad splayed feet and hanging tail.',
         'Fit a single ready pose in all five stored views. Keep jaw at its small snarl and hands low.',
         'Keep both feet supported; no step, breath cycle or tail sway is evidenced by this one-frame group.'),
    ],
    'walk': [
        ('Right swing begins',
         'Front: right foot (screen left) is lifted; left is lower. Profile: both feet are near the low pass position.',
         'Continue the right-leg swing into B while the left leg supports. Carry restrained opposite arm swing.',
         'Infer continuous contact from front and profile together; source bottom row alone is not a floor.'),
        ('Right forward / low body',
         'Right sole turns toward the viewer in front. Profile shows a long forward/rear split; head and clasp are lower.',
         'Bring the right foot forward to contact, accommodate through hip/knee flex, and retain the low torso phase.',
         'Do not independently curl talons to expose the sole. Use ankle orientation and whole-foot motion.'),
        ('Left trailing foot raised',
         'Left foot is high with claws pointing down; right foot is low. Profile shows the trailing leg bent up.',
         'Let the left leg leave support and fold into swing as the body rises; hold real thigh/shin lengths.',
         'Use a bent knee and ankle to match the raised trailing foot; do not shorten the limb.'),
        ('Left swing begins',
         'Left foot is lifted; right is lower. Arms and tail are in the opposite half-cycle to A.',
         'Pass the left leg into the forward swing, with right support and the opposing arm phase.',
         'Match actual D, rather than mirroring A blindly; native hands/feet are not perfectly symmetric.'),
        ('Left forward / low body',
         'Left sole faces the viewer in front; profile shows the opposite long stride and lower head/clasp.',
         'Bring the left foot forward to contact, accommodate through fixed-length legs, and retain the low phase.',
         'Keep planted claws rigid and choose contact intervals from the reviewed geometry.'),
        ('Right trailing foot raised',
         'Right foot is high with claws pointing down; left foot is low. Profile shows the opposite trailing leg folded.',
         'Fold the right trailing leg and raise the torso, then continue into A over the final 250 ms.',
         'F→A is the loop closure. Join pose and motion smoothly at 1125 ms; do not add a pause.'),
    ],
    'hit': [
        ('Ready', 'Upright snarl, arms low; no recoil yet.',
         'Start from the observed A pose, then raise both hands toward B without an added anticipation.',
         'Keep support steady; incoming gameplay blends are outside the native 750 ms action.'),
        ('Hands rise', 'Both hands rise slightly; the left foot changes orientation and becomes higher in front.',
         'Lift forearms and open hands slightly, carrying a restrained torso/head reaction.',
         'Allow the visible left-foot change; do not lock both footprints or invent a traveling step.'),
        ('Asymmetric recoil', 'Right arm opens down/out; left forearm lifts outward. Head tilts and left foot remains raised.',
         'Rotate the left forearm upward and right arm outward with continuous wrist twist; preserve claw order.',
         'Keep the right foot supporting; hidden depth and any heel motion require fitting.'),
        ('Maximum recoil', 'Left hand is high, right hand out; head tips back and tail extends toward screen right.',
         'Reach the raised left-hand extreme through elbow/shoulder articulation; counterbalance through the spine.',
         'Review left wrist/claws above the shoulder, upper-face rigidity, raised foot and tail/body clearance.'),
        ('Return through C', 'E is pixel-identical to C on this aligned canvas.',
         'Retrace toward C with a short quaternion path; do not wind the forearm through a full revolution.',
         'Recover support consistently; the repeated art does not uniquely determine the reverse 3D path.'),
        ('Return through B', 'F is pixel-identical to B; it is not the standing A pose.',
         'Return to B, then hold it from 625 to 750 ms. Blend to Standing after the clip.',
         'Do not append A inside the native duration or erase the remaining left-foot difference.'),
    ],
    'fidget': [
        ('Ready', 'Low hooked hands, small snarl, frontal head and torso.',
         'Use the observed ready stance and begin the small dip and hand opening.',
         'Both feet remain low; no clear step or large body turn appears.'),
        ('Small dip', 'Head/clasp dip and hands rise a little; the mouth opens.',
         'Flex through hips/spine, start opening the repaired jaw, and lift forearms gently.',
         'Keep shoulder spikes attached and skull/upper teeth rigid.'),
        ('Open forearms', 'Elbows bend, hands spread outward, head/clasp lower further and mouth stays open.',
         'Turn palms outward with a modest proximal finger fan; keep the same foot support.',
         'Preserve curved hard claw tips, including the supplied fourth long claw and thumb.'),
        ('Maximum dip / open hands', 'Lowest head/clasp, both hands open out near lower chest height.',
         'Fit the widest symmetric gesture and body dip without using body or bone scale.',
         'Inspect both palms, claw spacing, harness attachment, knees and floor clearance.'),
        ('Partial recovery to C', 'E repeats C exactly; the descriptor does not play the stored F/B alias.',
         'Return to C and hold it from 500 to 625 ms. Recover to Standing in a separate outgoing blend.',
         'Do not invent a sixth playback frame or turn this one-shot fidget into a breathing loop.'),
    ],
    'death': [
        ('Ignition at feet', 'Body is upright; small warm plumes appear around the feet.',
         'Begin from the visible ready pose and introduce an effect around the feet while retaining body scale.',
         'Separate intact anatomy from the effect; no falling body or lying corpse is shown.'),
        ('Plume climbs legs', 'Warm fragments/flame obscure shins and thighs; hands lift and open slightly.',
         'Lift hands slightly while the effect climbs. Hide geometry only as the observed disintegration requires.',
         'Leg landmarks are occluded; do not manufacture a uniquely measured knee/ankle pose.'),
        ('Last clear upper body', 'Head tilts back, left hand rises, right opens out; torso/lower body break into the plume.',
         'Fit the last visible upper-body reaction, then transition into disappearance with warm and dark fragments.',
         'Keep visible skull, shoulders and claws rigid until removal; no skeleton shrinking.'),
        ('Body obscured', 'Full head/torso are no longer readable; partial dark limb forms remain within the plume.',
         'Complete disappearance as a separate visibility/effect treatment; hidden skeletal posture is unconstrained.',
         'Do not assign joint landmarks to flame tips or treat missing pixels as compressed anatomy.'),
        ('Residual limb / plume', 'A dark forearm/hand silhouette remains near the left side of the dense plume.',
         'Let the remaining visible fragment vanish without reconstructing an unsupported whole-body pose.',
         'Avoid a surviving intact arm popping out after the body has disappeared.'),
        ('Full plume', 'Warm plume and dark fragments dominate; no complete creature silhouette is readable.',
         'Continue plume motion and fragment loss in an effect layer; skeletal bones no longer explain this image.',
         'Inspect the full plume envelope and empty gaps, not only bone transforms.'),
        ('Plume persists', 'Tall irregular plume persists; the creature is no longer intact.',
         'Keep the effect tall through G, then reduce its envelope into H.',
         'Retain the native 125 ms G hold in source playback; intermediate effect motion is inferred.'),
        ('Plume falls away', 'Plume becomes much shorter and lower; H has a longer 187.5 ms hold.',
         'Reduce the plume and settle fragments over H→I without resurrecting body geometry.',
         'Keep the extended H interval; do not flatten all death frames to 125 ms.'),
        ('Low remaining flames', 'Only low warm fragments remain; I also has a 187.5 ms hold.',
         'Hold the I endpoint to 1250 ms, then hand off to separate ash remains.',
         'A portable skeletal GLB alone cannot prove this appearance; declare effect export support.'),
    ],
    'corpse': [
        ('Held ash remains', 'A small dark ash pile; all five stored direction images have identical RGBA pixels.',
         'Use a separate ash asset/pose and keep the demon body absent. Hold indefinitely until gameplay removes it.',
         'Respect Center and scale 1.75; body scale is 0.699997. Asset-canvas alignment is not runtime placement.'),
    ],
}

CLIPS = {
    'standing': dict(label='Standing / idle', clip='Standing', loop=True, landmarks={'0': [STAND]},
                     summary='A held ready pose, with five stored views. No breathing cycle is present.'),
    'walk': dict(label='Walk', clip='Walk_Native', loop=True,
                 landmarks={'0': WALK_FRONT, '2': WALK_PROFILE},
                 summary='Alternating broad-foot strides, body bob and low opposing arm swing; 1125 ms loop.'),
    'hit': dict(label='Hit / wince', clip='Hit', loop=False, landmarks={'0': HIT_FRONT},
                summary='Asymmetric recoil: left hand rises high, right opens outward, then C and B repeat.'),
    'fidget': dict(label='Fidget', clip='Fidget', loop=False, landmarks={'0': FIDGET_FRONT},
                   summary='Small dip, jaw opening and two-handed outward gesture; ends at repeated C.'),
    'death': dict(label='Death / disintegration', clip='Death', loop=False, landmarks={'0': DEATH_FRONT},
                  summary='1250 ms upright disintegration, rising plume and settling fragments; separate effect work.'),
    'corpse': dict(label='Ash remains', clip='Ash_Remains', loop=False, landmarks={},
                   summary='Separate static ash pile, held indefinitely; no prone demon corpse.'),
}

CHECKS = {
    'J': 'Fixed limb lengths and persistent IK poles; continuous forearm twist; no bone/object scale.',
    'C': 'All four supplied long claws plus thumb retain order and rigid tips; inspect all tip pairs and both palms.',
    'H': 'Use repaired Bone_025 jaw hinge; upper skull, face and teeth stay rigid; no mouth collisions.',
    'S': 'Retain shoulder spike parenting, six forearm twist helpers, repaired weights and harness attachment.',
    'F': 'Inspect evaluated sole/claw height and support at keys AND subframes; allow evidenced swing, not toe curl.',
    'T': 'Tail chain has fixed lengths and no kink, belly pull, thigh or floor intersection.',
    'P': 'One camera/scale per native view, fixed across the action; front, profiles, back and three-quarter review.',
    'E': 'Death appearance includes visibility, plume/fragments and ash; inspect actual exported effect support.',
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def interpolate(p, q, u):
    if p is None or q is None:
        return None
    return [round(a * (1 - u) + b * u, 3) for a, b in zip(p, q)]


def main():
    manifest = json.loads((SOURCE / 'manifest.json').read_text())
    sources = json.loads((SOURCE / 'sources.json').read_text())
    bindings = manifest['native_group_bindings']['688']['actions']
    images, audit = {}, []
    for name, record in sources['sources'].items():
        if name.startswith('dmnatk'):
            continue
        path = SOURCE / 'native' / (name + '.png')
        images[name] = Image.open(path).convert('RGBA')
        entry = dict(name=name, png_path=str(path.relative_to(ROOT)), png_sha256=sha(path),
                     bmp_sha256_recorded=record['sha256'], native_offset=record['native_offset'],
                     alpha_bbox=images[name].getbbox(), referenced=record['referenced'])
        if name == 'dmnfgtf0':
            entry['original_bmp_check'] = 'Unavailable; unused F PNG checked against pixel-identical B only'
        else:
            bmp = ROOT / record['path'] if name.startswith('m496') else (
                ROOT / 'reference/mmerge_data_forus/Data/mmmerge.sprites.lod' / (name + '.bmp'))
            assert sha(bmp) == record['sha256'], bmp
            palette = record.get('fixed_palette', 688)
            palette_path = ROOT / sources['palette_paths'][str(palette)]
            assert sha(palette_path) == sources['palette_sources'][str(palette)]['sha256']
            indices = np.array(Image.open(bmp))
            colors = np.frombuffer(palette_path.read_bytes()[:768], np.uint8).reshape(256, 3)
            decoded = Image.new('RGBA', (354, 330))
            decoded.paste(Image.fromarray(np.dstack([colors[indices], (indices != 0).astype(np.uint8) * 255])),
                          tuple(record['native_offset'][:2]))
            assert decoded.tobytes() == images[name].tobytes(), name
            entry.update(original_bmp_check='Hash and exact aligned RGBA verified',
                         bmp_path=str(bmp.relative_to(ROOT)), palette=palette, palette_sha256=sha(palette_path))
        audit.append(entry)
    for name, alias in sources['pixel_aliases'].items():
        if name in images:
            assert images[name].tobytes() == images[alias].tobytes(), (name, alias)

    rows = []
    for action, config in CLIPS.items():
        native = manifest['animations'][action]
        binding = bindings[action]
        duration = native['sequence_ms']
        endpoint = round(duration * FPS / 1000)
        config.update(native_group=native['native_group'], native_binding=binding,
                      views=native['views'], single_view=native['single_view'],
                      duration_ms=duration, endpoint_sample=endpoint, fps=FPS,
                      next_action=native['next_action'], hold_indefinitely=action == 'corpse')
        config['endpoint_rule'] = ('Join A without a pause; endpoint duplicates the start for authoring only'
                                   if action == 'walk' else 'Constant pose; no newly evidenced motion'
                                   if action == 'standing' else 'Static hold indefinitely; 125 ms is frame metadata'
                                   if action == 'corpse' else 'Hold last native pose to duration; outgoing blend is separate'
                                   if action != 'death' else 'Hold I to 1250 ms, then switch to separately placed ash')
        anchors, time = [], 0
        for i, entry in enumerate(native['views']['0']):
            phase, observed, movement, support = NOTES[action][i]
            sample = round(time * FPS / 1000)
            assert abs(sample * 1000 / FPS - time) < 1e-8
            anchors.append(dict(index=i, source=entry['frame'], phase=phase, time_ms=time,
                                hold_ms=entry['duration_ms'], sample=sample, observed=observed,
                                movement=movement, support_and_checks=support,
                                pixel_alias=sources['pixel_aliases'].get(entry['frame'])))
            time += entry['duration_ms']
        assert time == duration == binding['animation_length_raw'] * 62.5
        assert [a['hold_ms'] for a in anchors] == [f['frame_length_raw'] * 62.5 for f in binding['frames']]
        config['anchors'] = anchors
        config['planned_frames'] = []
        for sample in range(endpoint + 1):
            time = sample * 1000 / FPS
            segment = max(i for i, a in enumerate(anchors) if a['time_ms'] <= time + 1e-8)
            a = anchors[segment]
            following = segment + 1 if segment + 1 < len(anchors) else 0 if config['loop'] else segment
            b = anchors[following]
            fraction = min(1, (time - a['time_ms']) / a['hold_ms'])
            u = fraction * fraction * (3 - 2 * fraction)
            guides = {}
            for view, landmarks in config['landmarks'].items():
                p, q = landmarks[segment], landmarks[following]
                # Unknown or occluded endpoints stay unknown; never extrapolate a flame into a limb.
                guides[view] = p if u == 0 else {
                    key: [interpolate(x, y, u) for x, y in zip(value, q[key])]
                    for key, value in p.items() if key in q}
            frame = dict(sample=sample, time_ms=round(time, 6), anchor_index=segment, next_index=following,
                         transition_fraction=round(fraction, 6), source_anchor=any(sample == x['sample'] for x in anchors),
                         movement=a['movement'], support_and_checks=a['support_and_checks'], screen_guides=guides)
            config['planned_frames'].append(frame)
            rows.append(dict(action=action, sample=sample, time_ms=frame['time_ms'], source=a['source'],
                             next_source=b['source'], transition_fraction=frame['transition_fraction'],
                             source_anchor=frame['source_anchor'], movement=a['movement'], support=a['support_and_checks']))
        config['plume_colour_bounds'] = []
        if action == 'death':
            for a in anchors:
                rgba = np.array(images[a['source']]).astype(np.int16)
                mask = ((rgba[:, :, 0] > rgba[:, :, 1] + 25) & (rgba[:, :, 0] > rgba[:, :, 2] + 15)
                        & (rgba[:, :, 0] > 180) & (rgba[:, :, 3] > 0))
                if a['index'] < 3:
                    mask[:100] = False
                if a['index'] == 2:
                    mask[90:130, 150:205] = False
                # Bright warm envelope only; exclude the visible face, retain the later full-height plume.
                yy, xx = np.where(mask)
                config['plume_colour_bounds'].append([int(xx.min()), int(yy.min()), int(xx.max()+1), int(yy.max()+1)])

        names = [f['frame'] for view in native['views'].values() for f in view]
        assert all(name in images for name in names)
        stored_views = [0] if native['single_view'] else range(5)
        cols = 3 if len(anchors) > 1 else 5
        panels = [(view, a) for view in stored_views for a in anchors]
        sheet = Image.new('RGB', (354 * cols, 362 * ((len(panels) + cols - 1) // cols)), (34, 42, 50))
        draw = ImageDraw.Draw(sheet)
        for i, (view, a) in enumerate(panels):
            name = native['views'][str(view)][a['index']]['frame']
            x, y = i % cols * 354, i // cols * 362
            draw.text((x + 8, y + 5), f"{name} | {a['time_ms']:g} ms | {a['hold_ms']:g} ms hold", fill='white')
            sheet.paste(images[name], (x, y + 26), images[name])
        sheet.save(STAGE / f'native_{action}_aligned.png')

    preservation = {str((STAGE.parent / 'attack_animation_v3' / name).relative_to(ROOT)):
                    sha(STAGE.parent / 'attack_animation_v3' / name)
                    for name in ('mm6_demon_attack.blend', 'mm6_demon_attack.glb', 'acceptance.json')}
    preservation[str((STAGE.parent / 'attack_study/index.html').relative_to(ROOT))] = sha(
        STAGE.parent / 'attack_study/index.html')
    data = dict(status='Plans only; no new 3D clips or effects authored', fps=FPS, clips=CLIPS, checks=CHECKS,
                landmark_uncertainty_px=8, coordinates='354x330 native canvas; anatomical right is screen left in front',
                guides='Estimated 2D image features, smoothstep interpolation only; not a solved or accepted skeleton',
                source_inventory=dict(descriptor_id=502, palette=688, raw_unit_ms=62.5, checked_bmps=60,
                                      native_pngs=61, unused_fidget_file='dmnfgtf0', attack2='Alias of existing Attack v3',
                                      running='No separate native Running group; existing Meshy Running retained'),
                preserved_file_sha256=preservation)
    (STAGE / 'animation_motion_spec.json').write_text(json.dumps(data, indent=2) + '\n')
    (STAGE / 'native_reference_audit.json').write_text(json.dumps(audit, indent=2) + '\n')
    with (STAGE / 'planned_frames.csv').open('w', newline='') as out:
        writer = csv.DictWriter(out, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    art = {name: 'data:image/png;base64,' + base64.b64encode((SOURCE / 'native' / (name + '.png')).read_bytes()).decode()
           for name in images}
    html = (STAGE / 'viewer.html').read_text().replace('/* STUDY_DATA */', 'const spec=' + json.dumps(data) +
                                                     ';\nconst art=' + json.dumps(art) + ';')
    (STAGE / 'index.html').write_text(html)
    assert sum(len(c['planned_frames']) for c in CLIPS.values()) == 198
    for path, digest in preservation.items():
        assert sha(ROOT / path) == digest
    print('Built six native plans, 198 sample instructions, 61 native PNGs and six aligned contact sheets.')
    print('Verified 60 original BMPs; unused Fidget F is an explicitly documented PNG-only alias check.')


if __name__ == '__main__':
    main()
