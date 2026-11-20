"""Author the reviewed family-specific anatomy and choreography, keeping inference explicit."""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from motion_notes import ARMS, HANDS, NOTES, CURVES, FAMILY_CHECKS

ROOT = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text())


def write(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')


ANATOMY = {
    'pmn2': {
        'identity': 'MM6 staff-carrying mage, pmn2; Apprentice/Journeyman/Mage descriptors 610–612',
        'head': 'Broad adult male skull, strong brow, square nose and jaw; full dark beard/moustache and nape-length dark hair. Ears emerge through side hair. No hat or hood.',
        'body': 'Sturdy broad shoulders and compact torso; bare upper arms; short green shoulder mantle, brown sleeveless leather tunic to upper thighs, rope waist tie and two green lateral hip pouches.',
        'legs': 'Green trousers ending at dark knee-high leather boots; knees stay separate. Rounded long toes, low heel, flat sole and ankle bend; no pointed metal sabatons.',
        'materials': '802 green mantle/trousers/pouches; 801 red and 803 blue variants. Protect dark hair/beard, natural skin, brown leather tunic, ochre rope, dark blue-black bracers/boots and wood.',
        'props': 'Separate long wooden staff with an irregular thickened upper end; right-hand grip. Native side view shows its true length. The body submission omits the whole staff. Do not replace it with a sword or add spell effects to native attack.',
        'secondary': 'Mantle remains short and follows shoulders with small delayed hem motion; rope knot fixed to waist, rope tips and pouches lag hip acceleration by a little. Boots/bracers remain firm while joints flex at their ends.',
        'stress': ['right elbow 90–130 degrees with staff grip', 'both hands above brow under horizontal staff',
                   'left palm opens in attack b/e; overhead shaft contact c/d needs fitting', 'left leg lift during hit', 'backward fall and supine corpse'],
        'measurements': {'head_including_beard_over_H': [.17,.20], 'shoulder_width_over_H': [.34,.40],
                         'tunic_hem_height_above_floor_over_H': [.36,.42], 'boot_top_height_over_H': [.19,.25],
                         'profile_shoe_length_over_H': [.13,.18]},
        'H': 257, 'top': 15, 'sole': 272,
        'boxes': [('head, beard, ears', [145,15,181,63]), ('short mantle', [111,54,210,94]),
                  ('rope and two hip pouches', [128,123,204,166]), ('openable free hand', [212,149,232,174]),
                  ('knee boots and soles', [124,207,217,272])],
        'special': 'Keep two pouches at the lateral hips: apparent front/back positions are projection, not four separate pouches. Match native head size before refining face. The AI weave/grain is illustrative surface detail, not new embossed ornament.'},
    'pman': {
        'identity': 'MM6 male town peasant, pman; descriptors 607–609',
        'head': 'Adult clean-shaven angular face, ordinary rounded skull, short reddish-brown hair; exposed ears, plain brow, modest projecting nose, defined chin. No headgear.',
        'body': 'Slim ordinary shoulders, green short V-neck tunic with short sleeves and brown elbow cuffs, wide brown waist belt with round front buckle; tunic notch/splits to upper thighs. Bare forearms.',
        'legs': 'Long relatively slim beige trouser legs, cloth folds at knees/ankles, brown low closed shoes with rounded toes and low heels. No boots, leg armor or bare toes.',
        'materials': '798 green tunic, 799/800 native alternate garments/palette ramps retained in native_variants.png. Preserve brown belt/cuffs/shoes, beige trousers, skin and reddish hair.',
        'props': 'Separate small straight dagger/knife used by the right hand only during native attack. Standing/walk/hit/fidget are empty-handed. Whole blade and grip omitted from body submission; do not model an always-present sword or knife fused to fingers.',
        'secondary': 'Short tunic hem lags hip turn slightly; belt buckle stays on waist, cuffs follow upper arm and clear elbow. Trouser folds deform at knee without changing limb length.',
        'stress': ['right shoulder cross-body thrust', 'right forearm across eyes, left palm out',
                   'deep asymmetrical protective crouch', 'side fall with one straight leg', 'wide prone corpse'],
        'measurements': {'head_over_H': [.13,.17], 'shoulder_width_over_H': [.27,.33],
                         'belt_height_above_floor_over_H': [.57,.64], 'tunic_hem_height_over_H': [.40,.45],
                         'profile_shoe_length_over_H': [.12,.16]},
        'H': 253, 'top': 1, 'sole': 254,
        'boxes': [('skull, ear, jaw', [127,0,162,43]), ('neck, shoulders, cuffs', [103,38,185,96]),
                  ('belt, round buckle, short hem', [112,94,178,151]), ('hands and finger chains', [101,123,185,145]),
                  ('trousers, low shoes', [112,145,178,255])],
        'special': 'Keep this a plain peasant: no leather breastplate, cape, pouch, beard or heroic shoulder expansion. AI seam stitching and grain clarify manufacture; they do not authorize new clothing coverage.'},
    'pfem': {
        'identity': 'MM6 female town peasant, pfem; descriptors 595–597',
        'head': 'Adult oval face, modest nose/chin, brown hair with low nape tie/braid; narrow forehead band. Side and rear art establish nape hair, not a tall bun or long loose mane. Ears partly exposed.',
        'body': 'Green square-neck bodice over pale short puff sleeves, modest proportions, narrow brown belt with small rectangular front buckle. Long pale pleated skirt with two green bands separated by pale stripe around hem.',
        'legs': 'Most thighs and knees are hidden by skirt. Visible ankles and simple brown closed shoes with thin ankle fastening; rounded toes and low heel. Ordinary two legs/five toes per foot are construction inferences, not resolved sprite digits.',
        'materials': '786 green bodice/hem bands; 787/788 native alternate ramps retained in native_variants.png. Preserve pale sleeves/skirt, brown belt/shoes, natural skin and hair. No apron, lacing, lace ornaments or jewelry.',
        'props': 'Separate small right-hand dagger appears during native attack and is absent in standing/walk/fidget. Omit it entirely from body submission. The attack grip must later be poseable without welding fingers to blade.',
        'secondary': 'Bodice follows ribcage; puff sleeves fold where shoulders rotate. Skirt is a separate hollow cloth surface with room for independent leg swing and kneeling; hem lags hips and broadens on collapse. Nape hair has restrained lag.',
        'stress': ['both hands folded in front without merging', 'right-hand cross-body blade reach',
                   'forward abdominal recoil', 'deep kneeling fall and hands toward floor', 'spread skirt in prone corpse'],
        'measurements': {'head_over_H': [.13,.17], 'shoulder_width_over_H': [.24,.29],
                         'belt_height_above_floor_over_H': [.61,.66], 'skirt_hem_height_over_H': [.08,.13],
                         'profile_shoe_length_over_H': [.12,.16]},
        'H': 251, 'top': 0, 'sole': 251,
        'boxes': [('headband, skull and nape hair', [89,0,127,43]), ('square-neck bodice, puff sleeves', [73,40,139,96]),
                  ('two separate folded hands', [95,98,126,123]), ('pleats and two green hem bands', [53,96,159,231]),
                  ('exposed ankle, closed shoes', [74,228,135,252])],
        'special': 'Long dress is essential identity. Never shorten it, add a thigh slit, invent tight trousers, or fuse both hidden legs into a single skirt pillar for auto-rigging. Inspect model underside and hip topology before sending for a rig.'},
    'gua': {
        'identity': 'MM6 New Sorpigal Guard A, gua; descriptor 553, palette 748; lieutenant/captain 554–555 are variants',
        'head': 'Compact rounded dark iron helmet with narrow nasal bar; small eye/face opening, mail around jaw/chin and nape. Side view retains nose/face clearance. No horns, plume or broad visor.',
        'body': 'Average solid human frame; warm bronze/brown short-sleeve mail hauberk to upper thighs, navy cloth sleeves to elbows, bare forearms/hands, brown waist belt and round front buckle.',
        'legs': 'Dark teal trousers, plain low brown closed shoes with rounded toes and low heels. No plate greaves, knee plates or knee-high boots.',
        'materials': '748 navy sleeves/teal trousers/warm mail. Native 749/750 alter sleeves, trousers, mail and other material ramps: inspect retained palettes rather than recolor the whole body with one tint. Helmet dark metal; wood and blade protected as separate prop.',
        'props': 'Separate long halberd: wood shaft, dark broad axe blade with projecting points/spike and blue binding near head. Side view reveals full length obscured by frontal foreshortening. Right carries it; left joins the shaft during attack. Body input omits shaft/blade completely. No shield or sword in this native family.',
        'secondary': 'Mail hauberk behaves as one flexible garment surface, belt follows pelvis, coif follows skull with small neck compliance; helmet and nasal bar are rigid. Blue sleeves deform at shoulders/elbows, not as rigid plate.',
        'stress': ['two-hand polearm grip with fixed shaft', 'right overhead lift', 'left open palm above head in hit',
                   'backward knee buckle', 'curled side/back corpse with head/coif clearance'],
        'measurements': {'helmet_plus_coif_over_H': [.17,.22], 'shoulder_width_over_H': [.28,.33],
                         'belt_height_above_floor_over_H': [.56,.62], 'mail_hem_height_over_H': [.38,.44],
                         'profile_shoe_length_over_H': [.12,.17]},
        'H': 253, 'top': 43, 'sole': 296,
        'boxes': [('helmet, nasal bar, coif', [157,43,192,93]), ('mail and blue sleeves', [131,86,214,140]),
                  ('belt and mail hem', [141,139,210,197]), ('bare hands, separate halberd grip', [125,160,214,185]),
                  ('teal trousers, low shoes', [146,194,198,296])],
        'special': 'Budget the body at approximately 15000 triangles; tiny mail rings belong to normal/base-color surface detail, not thousands of disconnected physical rings. Keep nasal bar away from the nose and coif clear of shoulder/neck pivots.'}
}

COMMON_REGIONS = {
    'skull_face_ears': ('head', 'Retain front width and profile depth together; verify brow, eye spacing, nose projection, jaw/chin and ear location in front/left/right. Native pupils, teeth and ear interior are unresolved; choose restrained human construction. Inspect the selected render, do not treat a written prompt as evidence.', 'Head follows neck; eyes/gaze and jaw separate if supported. Hair/beard/coif must not weld jaw to chest.'),
    'torso_shoulders_neck': ('body', 'Keep distinct clavicle, shoulder ball, elbow and wrist chain. Avoid arm-to-torso bridges, neck spikes, inverted armpits or flattened rear volume. Match torso depth in both side views and shoulder width in native standing.', 'Shoulder rotation must preserve torso volume; garment flex around armpit, neck remains clear.'),
    'hands_fingers_thumb': (None, 'Ordinary human hand construction selected: four fingers plus opposed thumb, four knuckle chains, broad palm tapering at wrist. Preserve individual tips/web gaps, thumb base, palm thickness and enough edge flow for grip/open fan. Native pixels cannot prove exact phalanx shapes. No extra/missing/fused digits.', 'Separate forearm roll from wrist flex; fingers curl around prop or touch other hand, never pass through palm. Test closed grip, open palm, pronation/supination and thumb opposition.'),
    'pelvis_hips_knees': (None, 'Keep an actual pelvis and two separate fixed-length leg chains under clothing. Native visible groin/foot seeds can guide fitting; hidden femurs, knee centers and hip depth remain inferred. Inspect underside, crossings and disconnected inside shells.', 'Hip flex, knee flex and foot plant must work together. Cloth has its own weights; trousers follow legs, skirt never locks both legs as one limb.'),
    'feet_ankles_soles': ('legs', 'Match profile toe reach, heel length, low heel height, ankle placement and sole thickness. Closed footwear hides anatomical toes; do not add toe cutouts. Both shoes need complete underside and flat support surfaces, not melted heels or razor soles.', 'Ankle dorsiflexion/plantarflexion and toe-off must preserve shoe volume. Test heel contact, flat foot, toe contact and clear swing without sliding.'),
    'clothing_fasteners_props': ('props', 'Keep body and handheld prop geometry separate. Attach belt/knot/buckle to waist, not abdomen skin stretching; match strap/pouch count and native coverage. Make broad silhouette folds geometry, tiny weave/mail grain surface detail.', 'Rigid prop/socket follows grip; fixed shaft/blade length. Secondary hand constrains same shaft, not an independently animated copy.'),
    'secondary_surfaces': ('secondary', 'Preserve clothing/hair coverage while keeping joints and negative spaces readable. Never simulate away a native silhouette mismatch. Check front/side/back and both extreme and intermediate poses.', 'Use restrained lag and damped settling; exact simulation parameters are not recovered from six sprites.'),
    'palette_material_boundaries': ('materials', 'Retain clear cloth/leather/skin/metal boundaries and compare all native variants. Generated unseen detail is inference. Do not bake studio highlights, invented embossing or color spill into final geometry.', 'Material boundaries remain stable as surfaces deform; texture and UV authoring follows accepted geometry and animations.')
}


def anatomy(family):
    p=ROOT/family; data=ANATOMY[family]; inv=read(p/'source_inventory.json')
    targets={'schema_version':1,'identity':data['identity'],'body_submission':'Empty-handed neutral A-pose; original handheld weapons/staff omitted. Attached clothing and accessories retained.',
             'measurement_contract':'Native logical pixels, body height H from crown/helmet to visible standing sole, excluding prop. Approximate projected ranges for comparison, not recovered 3D anthropometry. Keep one bottom-center pivot and comparison scale; do not independently normalize each native frame.',
             'native_body_H_px':data['H'],'native_crown_y_px':data['top'],'native_sole_y_px':data['sole'],
             'projected_ratio_ranges':data['measurements'],'regions':[], 'special_model_checks':data['special'],
             'rig_stress_poses':data['stress'],'priority_order':['silhouette and proportions','head and garment coverage','hands, feet, attachments','joint topology and hidden surfaces','surface detail'],
             'confidence_contract':'Observed = visible native silhouette/materials. Inferred = hidden construction and 3D depth. Selected = reviewed AI detail/A-pose. User choice = weapon-free body submission. None establishes original hidden topology.'}
    for region,(field,checks,deformation) in COMMON_REGIONS.items():
        observed=data[field] if field else ('Visible human palms/knuckles; held/fisted native poses obscure digit count.' if region=='hands_fingers_thumb' else 'Visible leg/foot silhouettes; hip/knee depth and covered joints partly or fully hidden.')
        targets['regions'].append({'id':region,'priority':'high' if region!='palette_material_boundaries' else 'medium',
                                   'observed':observed,'inferred_or_selected':checks,'deformation':deformation,
                                   'confidence':'High visible coverage; medium proportions; low hidden depth/fine anatomy.'})
    write(p/'anatomy_targets.json',targets)
    lines=['# '+data['identity']+': anatomy guide','',targets['measurement_contract'],'',
           '**Submission:** '+targets['body_submission'],'',
           '[Reviewed AI views](guides/selected_views_review.png) · [Native anatomy callouts](guides/anatomy_native.png) · '
           '[Native coordinates](guides/anatomy_coordinate_review.png) · [All native palette views](source/generation_inputs/native_variants.png)','',
           '## Proportions','',f"Standing body H ≈ {data['H']} native pixels; crown/helmet y≈{data['top']}, visible sole y≈{data['sole']}. The prop is excluded.",'',
           '| Projected measurement / H | Fitting range |','| --- | --- |']
    lines += [f"| {k.replace('_',' ')} | {v[0]}–{v[1]} |" for k,v in data['measurements'].items()]+['']
    for r in targets['regions']:
        lines += ['## '+r['id'].replace('_',' ').title(),'','**Native observation:** '+r['observed'],'',
                  '**Construction/model checks:** '+r['inferred_or_selected'],'','**Deformation:** '+r['deformation'],'',
                  '**Confidence:** '+r['confidence'],'']
    lines += ['## Family-specific ingest check','',data['special'],'','## Rig stress poses','']+['- '+s for s in data['stress']]+['',
              'Compare each with native action contacts before approving the rig. Repair anatomical shape/topology before weight tuning; an intact low-triangle mesh can still have wrong anatomy. '
              'Stock walking/running are diagnostic only; no native running sequence exists.','']
    (p/'ANATOMY_GUIDE.md').write_text('\n'.join(lines))
    cw,ch=inv['native_canvas']; sheet=Image.new('RGB',((cw*2+20)*3,ch*2+250),'#343839');draw=ImageDraw.Draw(sheet)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',17)
    names=inv['clips'][0]['frames'][0]['names']
    for col,v in enumerate([0,2,4]):
        x=col*(cw*2+20);im=Image.open(p/'source/frames'/(names[v]+'.png')).convert('RGBA');bg=Image.new('RGBA',im.size,'#343839');bg.alpha_composite(im)
        sheet.paste(bg.resize((cw*2,ch*2),Image.Resampling.NEAREST).convert('RGB'),(x,35));draw.text((x+6,8),names[v],font=font,fill='white')
        if v==0:
            for i,(label,box) in enumerate(data['boxes']):
                color=['#ffcf6a','#65d9fa','#e99def','#91e7a4','#ffa581'][i]
                draw.rectangle((x+box[0]*2,35+box[1]*2,x+box[2]*2,35+box[3]*2),outline=color,width=2)
                draw.text((x+5,ch*2+50+i*27),label,font=font,fill=color)
        else:
            draw.text((x+5,ch*2+55),'Profile/back are genuine source views.',font=font,fill='white')
            draw.text((x+5,ch*2+85),'Joint depth and fine anatomy inferred.',font=font,fill='white')
    sheet.save(p/'guides/anatomy_native.png')


def motion(family):
    p=ROOT/family; inv=read(p/'source_inventory.json'); landmarks=read(p/'source/native_landmarks.json')['frames']
    contract={
        'native_pixels':'x right, y down, full shared native logical canvas; frame offsets/pivot preserved. Character right appears image LEFT in frontal view. Existing original 2D seeds have provenance/confidence; restored-only seeds are excluded.',
        'body_space':'Semantic anatomical X = character right, Y = forward, Z = up. Angles describe anatomy, never executable bone-local Euler channels. Map to actual bind matrices only after geometry and rig return.',
        'angle_signs':'Elbow/knee 0 = straight, positive flexion; shoulder abduction 0 = arm down, 90 = side horizontal; forward elevation positive toward/front and overhead, negative behind. Trunk tilt positive forward, negative backward relative WORLD upright; lying tilt belongs mainly to root orientation, not local spine. Yaw positive toward character right. Wrist flex positive palm toward forearm; forearm axial roll solved from palm normal rather than assigning a sign without a bind pose.',
        'seed_uncertainty':'All 3D values are inferred INITIAL fitting seeds/ranges: shoulder ±20°, elbow/knee ±15°, trunk/yaw ±10°, pelvis height delta ±0.03H. Hidden skirt joints may need a wider search. Native silhouettes and all genuine views override seeds. Seeds are not automated pass/fail tolerances or recovered forces.',
        'hands':'Palm normal AND extended finger direction are constraints. Finger curl is proximal-flexion range, fan is separation; thumb opposed for grip. Preserve fixed segment lengths. Forearm roll changes palm plane, wrist flex remains modest. Depth/roll unresolved by frontal-only art stays low-confidence.',
        'support':'Incoming contact windows and support-side assignment are extrapolation unless a shoe/sole clearly establishes contact. Logical canvas bottom is not automatically floor. Solve shoe trajectories against fitted body floor, then inspect profile/back with stable root progression.'}
    spec={'schema_version':1,'identity':ANATOMY[family]['identity'],'coordinate_contract':contract,
          'source_inventory':'source_inventory.json','anatomy_targets':'anatomy_targets.json',
          'inventory_rule':'Every descriptor-referenced frame entry is an anchor, including repeated holds. attack2 aliases attack; no second clip, native run, spell effect or invented idle cycle.',
          'interpolation_rule':'Keep native anchor times/holds and duration. Construct continuous 3D curves through constrained poses; a 125 ms native hold is a timing interval, not permission to retime the action. Proposed midpoints are review/curve keys, not additional observed frames.',
          'family_verification':FAMILY_CHECKS[family],
          'implementation_order':['geometry/anatomy accepted','Meshy auto-rig returned and inspected','stock walking/running diagnostics only','native walking and weight corrections','all remaining native actions','every anchor plus midpoints, loops and endpoints','UV after accepted animation and deformations','Meshy texture return and final consistency review'],
          'clips':[]}
    md=['# '+spec['identity']+': complete native animation study','',
        '[All-action native overview](guides/animation_overview.png) · [Anatomy guide](ANATOMY_GUIDE.md) · '
        '[Structured motion specification](motion_spec.json) · [Native inventory](source_inventory.json)','',
        'The native image is evidence; the hidden 3D reconstruction is a constrained hypothesis. These are semantic '
        'targets to fit after the actual mesh/rig exists. They are not animation files or measured original joint angles.','',
        '## Coordinate, timing and confidence contract','']
    for name,text in contract.items(): md += ['**'+name.replace('_',' ').title()+':** '+text,'']
    md += ['All raw frame lengths here are 2: **125 ms per entry**, using 62.5 ms per raw unit. Standing/corpse metadata '
           'is 125 ms but the pose holds for the state duration. Walk/fidget loop at 750 ms; once-actions recover '
           'to standing except death, which reaches separate corpse at 625 ms. Male hit is only 625 ms.','',
           'Attack and hit/death/fidget supply one frontal bitmap per pose reused for all directions. Only standing '
           'and walking supply five genuine views. Directions 5/6/7 are mirrors of 3/2/1 and cannot establish new depth. '
           'A 3D rig preserves anatomical handedness when turned; do not imitate a mirrored sprite by swapping weapon hands.','',
           '## Family priorities','']+['- '+c for c in FAMILY_CHECKS[family]]+['','## Native playback coverage','',
           '| Action | Entries | Duration | Behavior |','| --- | --- | --- |']
    md += [f"| {c['name']} | {len(c['frames'])} | {c['native_duration_ms']:g} ms | {c['mode']} |" for c in inv['clips']]
    md += ['','Unused artwork remains in the source inventory, not playback: '+(', '.join(inv['unused_artwork']) or 'none')+'.',
           'Pixel-identical images/holds are retained exactly: '+json.dumps(inv['pixel_aliases'])+'.','']
    for native_clip in inv['clips']:
        name=native_clip['name']; notes=NOTES[family][name]; assert len(notes)==len(native_clip['frames'])
        clip={'name':name,'native_group':native_clip['group'],'duration_ms':native_clip['native_duration_ms'],
              'mode':native_clip['mode'],'genuine_views':native_clip['genuine_views'],
              'direction_reuse':native_clip['direction_reuse'],'curve_plan':CURVES[name],
              'verification_times_ms':sorted(set([f['time_ms'] for f in native_clip['frames']]+[
                  f['time_ms']+f['duration_ms']/2 for f in native_clip['frames']]+[native_clip['native_duration_ms']])),
              'endpoint':'hold current pose indefinitely' if name in ['standing','corpse'] else
                         'loop to first pose at 750 ms, keeping velocity/contact continuity' if name in ['walk','fidget'] else
                         'reach separate corpse at 625 ms; last death anchor remains at 500 ms' if name=='death' else
                         f"return to native standing at {native_clip['native_duration_ms']:g} ms",
              'anchors':[]}
        md += ['## '+name.title(),'','[Unannotated native contacts](source/'+name+'_native.png) · '
               '[Existing original 2D landmark overlay](guides/'+name+'_landmarks.png)','',
               '**Source views:** '+', '.join(clip['genuine_views'])+'. '+clip['direction_reuse']+'.','',
               '**Motion spacing:** '+clip['curve_plan'],'','**End rule:** '+clip['endpoint']+'.','']
        image_hashes={Path(im['png']).stem:im['png_sha256'] for im in inv['images']}
        seen_poses={}
        for i,(frame,note) in enumerate(zip(native_clip['frames'],notes)):
            phase,evidence,driver,r,rh,l,lh,body,support,head,prop,bodyseed=note
            lean,yaw,kr,kl,bob=bodyseed
            def arm(code):
                abd,fwd,elbow,roll,wrist,chain=ARMS[code]
                return {'chain':chain,'abduction_seed_deg':abd,'forward_elevation_seed_deg':fwd,
                        'elbow_flex_seed_deg':elbow,'wrist_flex_seed_deg':wrist,
                        'forearm_roll':'Solve anatomical axial rotation from palm/shaft constraint; allow initial ±90° search. No bind-relative roll sign is asserted.'}
            native_seeds={n:landmarks.get(n,{}).get('original',{}) for n in frame['names']}
            native_seeds={n:s for n,s in native_seeds.items() if s}
            next_phase=notes[i+1][0] if i+1<len(notes) else clip['endpoint']
            transition=f"{frame['time_ms']:g}–{frame['time_ms']+frame['duration_ms']:g} ms: {phase} → {next_phase}. "+clip['curve_plan']
            if name=='fidget' and family!='gua' and i==0:
                transition='0–250 ms is a repeated native rest-pose hold. Do not add an intermediate gesture merely because playback has two entries.'
            if name=='death' and i==len(notes)-1:
                transition+=' Keep last observed pose at 500 ms and fit the hidden path to actual corpse at 625 ms; do not replace or skip either endpoint.'
            hand_right=HANDS[rh]; hand_left=HANDS[lh]
            if name=='fidget' and family=='gua' and i==4:
                hand_left+=' Possible shaft approach/touch, not an observed firm grip; do not curl all digits around wood automatically.'
            checks=['Render front at exact anchor with common camera/scale/pivot; compare crown/head, shoulders, elbows/wrists, hand silhouettes, belt/hem and shoe positions.',
                    'For standing/walk also render genuine front-right/right/back-right/back at same time; fit one shared 3D pose, never independently fit each view.',
                    'Inspect required palm normal/finger direction, thumb opposition, wrist continuity, both arm-chain lengths and clothing/prop clearance.',
                    'Check fixed-length legs, support/contact window, root drift, underside and mid-interval penetrations; source occlusion is not proof of no collision.',
                    'Review indicated next transition at half interval; match driver and secondary response without stopping the whole pose at every key.']
            secondary=ANATOMY[family]['secondary']+' '+('Lag is quiet here; do not invent cloth flutter or hair cycles.' if name in ['standing','fidget','corpse'] else
                       'Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.')
            anchor={'time_ms':frame['time_ms'],'native_hold_ms':frame['duration_ms'],'native_names':frame['names'],
                    'phase':phase,'evidence':{'observed':evidence,'original_2d_seeds':native_seeds,
                    'confidence':'High frame identity/order/visible silhouette; medium described overlaps; low hidden depth, palm plane, exact contact/joint centers.',
                    'inferred':'3D limb angles, axial roll, root/contact depth and physical line of action; fit against native silhouette and reject inconsistent seeds.'},
                    'driver':driver,'right_arm':arm(r),'right_hand':hand_right,'left_arm':arm(l),'left_hand':hand_left,
                    'body':body,'support':support,'head':head,'secondary':secondary,'prop_and_visibility':prop,
                    'transition':transition,'seeds':{'space':'semantic anatomy; inferred ranges, not local Euler',
                    'world_trunk_forward_tilt_deg':{'center':lean,'range':[lean-10,lean+10]},
                    'torso_yaw_toward_right_deg':{'center':yaw,'range':[yaw-10,yaw+10]},
                    'pelvis_yaw_note':'Keep smaller than rib yaw during attack; gait ±4–8° opposing ribcage. Corpse root orientation fitted to native remains.',
                    'right_knee_flex_deg':{'center':kr,'range':[max(0,kr-15),min(150,kr+15)]},
                    'left_knee_flex_deg':{'center':kl,'range':[max(0,kl-15),min(150,kl+15)]},
                    'pelvis_height_delta_over_standing_body_H':{'center':bob,'range':[bob-.03,bob+.03]},
                    'ankle_note':'During support keep fitted sole on floor, modest dorsiflexion; swing may plantarflex. Shoe/heel evidence overrides seeds; ankle center unseen.'},
                    'checks':checks}
            signature=tuple(image_hashes[n] for n in frame['names'])
            if signature in seen_poses:
                earlier=seen_poses[signature]
                anchor['same_native_pose_as_ms']=earlier
                anchor['evidence']['observed']+=f' All supplied native views are pixel-identical to the {earlier:g} ms anchor; retain the same constrained pose.'
                anchor['transition']+=' Preserve identical source-pose constraints; no invented limb change between identical holds.'
            else:
                seen_poses[signature]=frame['time_ms']
            clip['anchors'].append(anchor)
            md += [f"### {chr(97+i)} — {frame['time_ms']:g} ms: {phase}",'',
                   '**Native frames:** '+', '.join(frame['names'])+f". Hold {frame['duration_ms']:g} ms. "+anchor['evidence']['observed'],'',
                   '**Main driver:** '+driver,'',
                   '**Right chain:** '+anchor['right_arm']['chain']+f" Initial abduction/forward elevation/elbow flex ≈ {ARMS[r][0]}/{ARMS[r][1]}/{ARMS[r][2]}°; ±20/20/15° fitting ranges.",'',
                   '**Right palm/fingers:** '+hand_right,'',
                   '**Left chain:** '+anchor['left_arm']['chain']+f" Initial abduction/forward elevation/elbow flex ≈ {ARMS[l][0]}/{ARMS[l][1]}/{ARMS[l][2]}°; ±20/20/15° fitting ranges.",'',
                   '**Left palm/fingers:** '+hand_left,'',
                   '**Trunk/hips:** '+body+f" World trunk tilt {lean}°, rib yaw {yaw}°, pelvis height delta {bob:+.3f}H (all inferred centers).",'',
                   '**Support/legs:** '+support+f" Initial R/L knee flex {kr}/{kl}° (±15°; hidden knees uncertain).",'',
                   '**Head:** '+head,'','**Prop/visibility:** '+prop,'','**Secondary surfaces:** '+secondary,'',
                   '**Next interval:** '+anchor['transition'],'',
                   '**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. '
                   'Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.','']
        spec['clips'].append(clip)
    md += ['## Rig and animation acceptance','',
           'Start with geometry comparison and the family stress poses in the anatomy guide. After receiving the rig, '
           'use stock walk/run only to diagnose weight collapse, crossed joints, arm-to-torso attachment and foot volumes. '
           'Then build native walking first, verify all five genuine views and the seam, repair weights, and construct '
           'the other six native states. Review every observed anchor and proposed midpoint, not only contact sheets.','',
           'A later review should retain native/3D side-by-side screenshots with the mismatched region highlighted, '
           'the time/view, cause (geometry, rig, weight, animation, prop or cloth) and fix/recheck evidence. Match camera '
           'and scale before declaring a shape defect. Do not tweak topology to conceal a wrong pose or retime the source '
           'to conceal failed interpolation. UVs and Meshy texturing follow accepted animation/deformation.','',
           'Numeric seeds and ambiguities are deliberately reviewable. Palms, hidden knees, contacts and corpse depth '
           'cannot be certified before a 3D model exists. No human artistic acceptance or model deformation pass is claimed here.','']
    write(p/'motion_spec.json',spec); (p/'ANIMATION_STUDY.md').write_text('\n'.join(md))


if __name__=='__main__':
    for family in ANATOMY:
        anatomy(family); motion(family)
        print(f'{family}: anatomy and {sum(len(n) for n in NOTES[family].values())} timed motion anchors authored')
