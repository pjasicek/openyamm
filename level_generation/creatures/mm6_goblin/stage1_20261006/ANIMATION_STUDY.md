# MM6 Goblin A: native motion study

Extrapolated authoring brief; no new rig or animation has been authored or verified in this run.

This is a 3D authoring and review contract, not a recovered original skeleton. Read the unannotated source beside the approximate landmark overlays. All native timestamps come from descriptors; smooth subkeys, depth and numerical angle ranges are extrapolations.

## Coordinate, timing and confidence contracts

**world**: +X anatomical right, +Y creature forward, +Z up. Front camera is on +Y looking toward creature; anatomical right appears image-left. Convert this basis explicitly on rig ingestion.

**source**: 355x289 logical pixels, x right and y down, no crop/recenter per frame; native bottom billboard pivot is at canvas bottom y=289. World joint positions cannot be recovered uniquely from these pixels.

**height**: H=256 standing silhouette pixels. Normalize anatomical distances by standing height, not per-frame bounding box. Native frame scale 0.649994 and actor scale remain separate from this study.

**points order**: ['face_center', 'neck', 'shoulder_R', 'elbow_R', 'wrist_R', 'shoulder_L', 'elbow_L', 'wrist_L', 'pelvis', 'knee_R', 'ankle_R', 'knee_L', 'ankle_L', 'sword_tip']

**points accuracy**: Manually placed 2D fitting seeds, corrected against coordinate grids: typically +/-6 pixels for visible face/wrist, +/-10-15 for inferred joint centers under plates. Face center is a tracking point, not skull center of mass or a bone joint. Null means occluded or too uncertain. These are neither tracked ground truth nor solved bone transforms. Source alpha bounds remain exact.

**rotations**: All degree ranges are semantic anatomical fitting seeds, not Blender local Euler keys. Elbow flex=0 straight; head pitch positive looks down; spine lean positive forward; hip flex positive knee forward. Forearm roll is relative to baseline grip around shoulder-to-wrist chain, not accumulated turns.

**hands**: Describe a hand with wrist position, palm outward normal, wrist-to-middle-finger direction and thumb side. A grip uses handle axis along the closed finger stack and palm normal into the handle; a guard uses palm normal toward the incoming hit. Solve a continuous orthonormal orientation, unwrap shortest sensible twist, and verify visible thumb/guard/claw silhouettes.

**timing**: One native raw unit=62.5 ms. Each frame raw length=2 ->125 ms. Keys at frame starts are a suggested sprite-match authoring convention; intervals are native holds, and the last interval is still part of clip duration. Smooth motion passes anchors without stopping at every bitmap. Standing/corpse are indefinite held states, not 125 ms loops with invented motion.

## Rules shared by every action

- Native physical goblin uses AttackMelee and AttackRanged as the same gobata0 animation; no separate magic/ranged choreography is observed.
- No native running clip. Any stock walk/run is only a later rig stress test and cannot replace Walk_Native.
- Standing/walk have five genuine views, plus Mirror5/6/7 reuse; action frames have Image1 single-view reuse. Mirrored sword-side swaps are a billboard shortcut, not 3D anatomy.
- Use one rigid right-hand sword grip through standing/walk/attack/hit/fidget; sword moves through shoulder, elbow and forearm orientation, never stretches or slides in grip.
- Foot grounding outranks exact projected pixel position where perspective obscures depth. Fit frontal reach and profile stride together before correcting weights.
- Secondary motion is restrained, generally 20-50 ms behind primary body changes as an inferred starting range, not an observed original timing. Keep overall native durations.
- Skin shoulder/elbow/wrist chains must remain plausible. Inspect forearm pronation before interpreting palm errors as a weighting defect.
- Freeze held standing/corpse; no added breathing, glance, theatrical bounce or extra death roll without an explicit artistic decision.

## Native action inventory

| Action | Anchors | Native duration | Views | Playback |
| --- | ---: | ---: | --- | --- |
| Standing | 1 | 125.0 ms | 5 genuine | hold |
| Walk | 6 | 750.0 ms | 5 genuine | loop |
| Attack | 6 | 750.0 ms | 1 genuine | one_shot |
| Hit | 6 | 750.0 ms | 1 genuine | one_shot |
| Death | 5 | 625.0 ms | 1 genuine | one_shot |
| Corpse | 1 | 125.0 ms | 1 genuine | hold |
| Fidget | 6 | 750.0 ms | 1 genuine | one_shot |

AttackMelee and AttackRanged alias Attack. Standing and Corpse durations are metadata for one held frame; their visible hold is indefinite. Native running is absent. Death d and Corpse have identical original bytes; Death e is a small settling variation.

## Standing

Stable armed ready stance, not the unarmed modeling A pose.

**Continuous motion**: One constant pose. A transition from another clip may blend into it, but the held pose itself is static.

**Confidence**: High silhouette and held timing; medium grip depth and hidden finger joints.

[Unannotated native sheet](source/standing_native.png) · [Approximate landmark overlay](guides/standing_landmarks.png)

### a — 0 ms: held ready

**Native evidence**: gobsta0.bmp, gobsta1.bmp, gobsta2.bmp, gobsta3.bmp, gobsta4.bmp; native interval 125.0 ms.

**Driver**: Upright body supported evenly by both feet; sword held low in right hand.

**Right Arm**: Shoulder relaxed down/out, elbow slightly flexed; wrist near right waist/upper thigh. Forearm and blade project mostly forward in 3D, explaining short frontal sword.

**Right Hand**: Closed power grip with thumb opposed over fingers; palm faces into hilt, fingers wrap rather than hang open. Wrist nearly neutral, roll establishes gold guard and blade plane seen in gobsta2.

**Left Arm**: Shoulder lower than shoulder cap silhouette; elbow relaxed, forearm down beside left hip.

**Left Hand**: Relaxed three fingers plus thumb point down/forward, palm inward/obliquely forward. Slight finger curl; do not fist or rigidly fan as in modeling pose.

**Body**: Pelvis level and centered; chest upright, neck long but not stretched; weight balanced, no artificial lean.

**Support**: Both complete soles down; knees unlocked. No floating heel or foot shuffle.

**Head**: Forward stare, compact chin projected, jaw almost closed with teeth showing; no breathing or head turn.

**Secondary**: Pouch and skirt hang under gravity; all held. Shoulder spikes are rigid.

**Anatomical fitting ranges, not local Euler keys**: elbow_R_deg=[15, 35]; elbow_L_deg=[5, 25]; head_pitch_deg=[0, 8]; spine_forward_deg=[0, 5]; knee_R_deg=[0, 12]; knee_L_deg=[0, 12].

**Verify**:

- Match gobsta0 head/shoulders/belt/feet without recentering.
- Match long sword and heel/toe profile in gobsta2; check bare back and right pouch in gobsta4.

Compare each listed genuine view at the same anchor; preserve handedness despite source mirror shortcuts.

## Walk

Alternating legs carry body forward; arms oppose leg swing with a rigid sword in right grip.

**Continuous motion**: R swing/heel lead in a-b, R landing/support in c, L swing/heel lead in d-e, L landing/support in f. Wrap f into a without duplicated hold. In-place hip motion is allowed, but pin stance foot using compensating root/IK; for travelling playback choose stride from profile and match velocity so planted foot does not skate.

**Confidence**: High alternating swing order from genuine profiles; medium exact ground depth and joint rotations. Native left/right half-cycles are not perfect mirror copies.

[Unannotated native sheet](source/walk_native.png) · [Approximate landmark overlay](guides/walk_landmarks.png)

### a — 0 ms: right swing / left support

**Native evidence**: gobwaa0.bmp, gobwaa1.bmp, gobwaa2.bmp, gobwaa3.bmp, gobwaa4.bmp; native interval 125.0 ms.

**Driver**: Right knee lifts and comes forward; left leg bears weight.

**Right Arm**: Right shoulder extends behind torso and slightly outward; elbow partly flexed; right wrist swings behind/right of waist.

**Right Hand**: Fixed power grip, blade trailing/down from wrist. Palm remains toward hilt; fingers and thumb do not change ownership. Wrist close to neutral, small flex rather than a flapping joint.

**Left Arm**: Left arm comes forward to counter right thigh; elbow flexes gently with forearm reaching forward/out.

**Left Hand**: Open relaxed fingers, palm partly up/forward and thumb visible; low fan with 15-30 degree loose curl.

**Body**: Pelvis moving over left stance foot, small lateral shift; chest counters pelvis yaw. Body near upper bob, shoulders not level copies of rest.

**Support**: Left sole supports; right sole clear, right knee forward. Do not plant raised right toes just because front view is compressed.

**Head**: Looks forward, approximately upright; preserve high crown and subtle turn, not full head lock to chest.

**Secondary**: Sword trails because shoulder is back; skirt panels follow advancing right thigh, pouch lags pelvis lightly.

**Anatomical fitting ranges, not local Euler keys**: elbow_R_deg=[15, 35]; elbow_L_deg=[25, 50]; hip_R_deg=[20, 40]; knee_R_deg=[35, 65]; knee_L_deg=[5, 20]; head_pitch_deg=[0, 8]; pelvis_bob_h=[-0.02, 0.01].

**Verify**:

- Right foot is raised in front and moving forward in gobwaa2.
- Left open hand is forward; sword trails without changing grip. Compare all five genuine views.

Compare each listed genuine view at the same anchor; preserve handedness despite source mirror shortcuts.

### b — 125.0 ms: right heel leads / body lowers

**Native evidence**: gobwab0.bmp, gobwab1.bmp, gobwab2.bmp, gobwab3.bmp, gobwab4.bmp; native interval 125.0 ms.

**Driver**: Right lower leg extends forward toward landing; left stance moves toward toe-off.

**Right Arm**: Right wrist stays behind with a small elbow bend; shoulder does not jerk forward just to match dark blade silhouette.

**Right Hand**: Grip unchanged; blade down/back with tip low. Continuous forearm roll exposes another blade plane; preserve thumb/guard relationship.

**Left Arm**: Left elbow bends more; forearm/hand lift slightly toward chest and reach ahead of left shoulder.

**Left Hand**: Palm up/oblique forward, fingers loosely cupped with thumb separated; do not close into a sword-like grip.

**Body**: Pelvis/chest lower into stride; torso gently inclines forward with counter-yaw; shoulder asymmetry visible.

**Support**: Left stance near toe support; right heel reaches forward, right toes up and sole visible in front. Contact time is between b and c, not fully solved at b.

**Head**: Crown lower than a, slight pitch/nod; face still watches forward.

**Secondary**: Skirt advances around right leg; arms near swing extrema decelerate smoothly, not stop at frame boundary.

**Anatomical fitting ranges, not local Euler keys**: elbow_R_deg=[15, 35]; elbow_L_deg=[50, 85]; hip_R_deg=[25, 45]; knee_R_deg=[5, 25]; knee_L_deg=[10, 30]; head_pitch_deg=[4, 12]; pelvis_bob_h=[-0.045, -0.015].

**Verify**:

- Right heel-leading toe-up foot, not toe-down landing.
- Lower crown/chest and raised free hand agree across gobwab0/1/2; root must compensate planted left foot.

Compare each listed genuine view at the same anchor; preserve handedness despite source mirror shortcuts.

### c — 250.0 ms: right landing / weight transfer

**Native evidence**: gobwac0.bmp, gobwac1.bmp, gobwac2.bmp, gobwac3.bmp, gobwac4.bmp; native interval 125.0 ms.

**Driver**: Right foot receives weight; rear left leg prepares to swing.

**Right Arm**: Right shoulder begins returning from extension; wrist remains outside right hip with elbow unlocked.

**Right Hand**: Rigid grip; blade still points down/back but begins follow-through. Avoid extra full forearm turn between b and c.

**Left Arm**: Left shoulder begins moving back; elbow opens, wrist lowers past left hip.

**Left Hand**: Palm rotates inward/down, fingers point toward ground with more relaxed curl than b; wrist roll continuous.

**Body**: Weight transfers from left to right; pelvis rises after landing while chest remains slightly pitched. Head pitch is stronger than a.

**Support**: Right heel/sole lands and settles; left heel unloads. Brief double support is plausible, inferred from side view. No two fully pinned feet during continued root travel.

**Head**: Chin dips and gaze briefly down/forward; do not infer a deep bow from shading alone.

**Secondary**: Skirt trails completing right swing; pouch settles after pelvic drop.

**Anatomical fitting ranges, not local Euler keys**: elbow_R_deg=[15, 40]; elbow_L_deg=[5, 30]; hip_R_deg=[10, 25]; knee_R_deg=[10, 30]; knee_L_deg=[20, 40]; head_pitch_deg=[10, 20]; pelvis_bob_h=[-0.02, 0.01].

**Verify**:

- Both front feet appear low, but profile must distinguish right landing from left unloading.
- Free hand now down beside hip; neck must follow nod without shortening skull.

Compare each listed genuine view at the same anchor; preserve handedness despite source mirror shortcuts.

### d — 375.0 ms: left swing / right support

**Native evidence**: gobwad0.bmp, gobwad1.bmp, gobwad2.bmp, gobwad3.bmp, gobwad4.bmp; native interval 125.0 ms.

**Driver**: Left knee lifts; right leg carries body, beginning opposite half-stride.

**Right Arm**: Right shoulder flexes forward, elbow slightly bent; wrist travels toward front/right hip.

**Right Hand**: Blade now projects more forward and foreshortens in front. Roll follows shoulder/forearm, not a change of blade length or grip.

**Left Arm**: Left shoulder extends back/out, elbow mostly open; wrist swings behind left hip.

**Left Hand**: Relaxed palm inward/down; fingers trail and fan slightly, wrist near neutral.

**Body**: Pelvis shifts toward right support; chest yaw counterbalances. Do not mechanically mirror a because sword and pouch are asymmetric.

**Support**: Right sole down; left foot clear and knee advancing. Keep right toe contact stable while heel can roll.

**Head**: Small down/forward pitch carried over from c; recover smoothly rather than abrupt reset.

**Secondary**: Sword carried ahead, skirt changes which leg drives it; left hand lags shoulder slightly.

**Anatomical fitting ranges, not local Euler keys**: elbow_R_deg=[15, 40]; elbow_L_deg=[5, 25]; hip_L_deg=[20, 40]; knee_L_deg=[35, 65]; knee_R_deg=[5, 20]; head_pitch_deg=[8, 16]; pelvis_bob_h=[-0.02, 0.01].

**Verify**:

- Raised foot is anatomical LEFT now.
- Short front sword is forward foreshortening; compare full blade in gobwad2.

Compare each listed genuine view at the same anchor; preserve handedness despite source mirror shortcuts.

### e — 500.0 ms: left heel leads / sword forward peak

**Native evidence**: gobwae0.bmp, gobwae1.bmp, gobwae2.bmp, gobwae3.bmp, gobwae4.bmp; native interval 125.0 ms.

**Driver**: Left leg extends toward contact while sword arm reaches its forward swing peak.

**Right Arm**: Right shoulder forward/adducted; elbow flexed, wrist nearer front midline at belt height.

**Right Hand**: Fixed grip with forearm roll presenting broad blade across front/upward. Wrist modestly extended/ulnar angled, not bent 90 degrees to force blade orientation.

**Left Arm**: Left arm near rear swing, elbow slightly flexed and wrist low/back.

**Left Hand**: Loose open hand, palm back/inward; fingertips down with restrained curl.

**Body**: Pelvis lowers into left stride, chest follows forward energy with opposite yaw. Right bracer must not collide with belly or pouch.

**Support**: Right stance approaches toe-off; left heel leads and toes rise, sole visible in front. Left contact occurs between e and f.

**Head**: Head rises slightly from d pitch but remains steady toward travel.

**Secondary**: Blade arc is smooth and rigid; pouch/skirt trail torso, do not mirror right hip attachment.

**Anatomical fitting ranges, not local Euler keys**: elbow_R_deg=[45, 75]; elbow_L_deg=[10, 30]; hip_L_deg=[25, 45]; knee_L_deg=[5, 25]; knee_R_deg=[10, 30]; head_pitch_deg=[3, 10]; pelvis_bob_h=[-0.045, -0.015].

**Verify**:

- Left heel-leading foot must agree in gobwae2 and rear view.
- Blade crosses chest but hand remains near waist; no blade through gorget or left fingers.

Compare each listed genuine view at the same anchor; preserve handedness despite source mirror shortcuts.

### f — 625.0 ms: left landing / return toward right swing

**Native evidence**: gobwaf0.bmp, gobwaf1.bmp, gobwaf2.bmp, gobwaf3.bmp, gobwaf4.bmp; native interval 125.0 ms.

**Driver**: Left foot receives weight; right foot unloads for next cycle.

**Right Arm**: Right shoulder returns from forward peak; elbow opens as wrist moves outside waist.

**Right Hand**: Grip stable, sword rotates toward its trailing arc through shortest sensible roll. No discontinuity in thumb or gold guard at loop wrap.

**Left Arm**: Left shoulder begins forward swing again, elbow opens slightly and hand moves outward.

**Left Hand**: Palm partly forward/inward, fingers relaxed and spread enough to avoid fused outline; no abrupt fist.

**Body**: Pelvis/chest rise into transfer, counter-yaw returns toward a. Preserve asymmetric head and shoulder heights.

**Support**: Left sole settles; right heel unloads. Transition to a lifts right foot after left support is established.

**Head**: Forward gaze, crown high; smooth pitch return and small bob, no extra glancing motion.

**Secondary**: Cloth and pouch settle without stopping between f and a; contact velocity stays continuous.

**Anatomical fitting ranges, not local Euler keys**: elbow_R_deg=[15, 40]; elbow_L_deg=[15, 40]; hip_L_deg=[10, 25]; knee_L_deg=[10, 30]; knee_R_deg=[20, 40]; head_pitch_deg=[0, 8]; pelvis_bob_h=[-0.01, 0.015].

**Verify**:

- No foot-swap or root teleport at f-to-a wrap.
- Head, free wrist and sword arc have continuous tangents; inspect profile for sliding.

Compare each listed genuine view at the same anchor; preserve handedness despite source mirror shortcuts.

## Attack

Right-hand diagonal sword slash powered by shoulder and torso turn; free arm balances and protects. Not an overhead club chop.

**Continuous motion**: a sets guard; a-b-c raise/coil, decelerating briefly near c; c-d is fastest cross-body/downward cut; d-e follows through, then e-f decelerates/recover. Do not put zero tangents at d or e. Add subkeys inside c-d only if needed for continuous blade path, keeping 750 ms native duration. Blend f back to armed standing during last interval if desired and label that inference.

**Confidence**: High screen-space sword/hand path and raised left foot in b/c; medium body twist; low-medium exact depth, roll and contact pivots because only Image1 action exists.

[Unannotated native sheet](source/attack_native.png) · [Approximate landmark overlay](guides/attack_landmarks.png)

### a — 0 ms: initial guard / wind-up

**Native evidence**: gobata0.bmp; native interval 125.0 ms.

**Driver**: Sword draws diagonally across front from right waist, building shoulder/torso coil.

**Right Arm**: Right shoulder forward/down, elbow bent, wrist near right belt; shoulder-to-elbow then elbow-to-wrist stay connected without locking.

**Right Hand**: Firm grip; blade runs image-left lower to image-right upper across belly/chest. Palm into hilt, thumb fixes guard side; near-neutral wrist, begin moderate pronation rather than accumulated spin.

**Left Arm**: Left shoulder relaxed, elbow flexed gently, wrist down at left thigh before coming up to balance.

**Left Hand**: Fingers relaxed/open, palm inward; no two-handed sword grip.

**Body**: Weight initially between feet, chest starts turning toward image-right, hips lag slightly. No large root stride.

**Support**: Both feet low/grounded; unlock knees for loading.

**Head**: Eyes look toward anticipated cut with small turn; jaw modestly open, not a scream.

**Secondary**: Left hand and pouch begin to lag torso, skirt still hanging.

**Anatomical fitting ranges, not local Euler keys**: elbow_R_deg=[40, 70]; elbow_L_deg=[10, 35]; spine_forward_deg=[0, 10]; torso_yaw_magnitude_deg=[10, 25]; head_pitch_deg=[0, 10].

**Verify**:

- Right wrist low with blade diagonal across front.
- Maintain left hand low and separate, fixed grip and native feet.

No genuine side/back action evidence. Side/back motion is inferred and must be checked for anatomy, balance and collisions on the returned rig.

### b — 125.0 ms: diagonal lift / coil

**Native evidence**: gobatb0.bmp; native interval 125.0 ms.

**Driver**: Right shoulder elevates and adducts, lifting sword toward image-right/up with torso turn.

**Right Arm**: Shoulder rotates forward/up, upper arm crosses front; elbow opens somewhat, wrist rises to upper-chest height on image-right. Avoid shoulder hiking into neck.

**Right Hand**: Grip closed; palm/knuckles rotate with forearm so blade broad face is visible. Wrist extension small, forearm roll roughly 20-60 degrees from guard as fitting range, not a full rotation.

**Left Arm**: Left elbow flexes to bring free hand up in front at lower-chest height, lagging right lift and helping balance.

**Left Hand**: Loose partially curled fingers, palm oblique inward/up. It hovers behind/below weapon hand and never grips the blade.

**Body**: Chest turns toward image-right and rises, hips retain support; right leg bears more load.

**Support**: Right foot grounded; left foot visibly rises. Prefer left knee/hip lift with a small right-foot pivot over an invented long lunge.

**Head**: Chin slightly up, face follows lift toward image-right; maintain neck-to-skull alignment.

**Secondary**: Skirt/pouch respond after pelvic turn; shoulder caps remain rigid clear of head.

**Anatomical fitting ranges, not local Euler keys**: elbow_R_deg=[25, 55]; elbow_L_deg=[55, 90]; shoulder_R_front_elevation_deg=[65, 90]; forearm_R_roll_from_guard_deg=[20, 60]; knee_L_deg=[25, 50]; head_pitch_deg=[-10, 0].

**Verify**:

- Sword wrist at upper chest, tip high image-right; not over the crown.
- Left foot lifted, right support stable; free hand below weapon hand.

No genuine side/back action evidence. Side/back motion is inferred and must be checked for anatomy, balance and collisions on the returned rig.

### c — 250.0 ms: lift apex / cut begins

**Native evidence**: gobatc0.bmp; native interval 125.0 ms.

**Driver**: Hands continue toward image-right high side while torso completes coil; begin cutting impulse without stopping all joints.

**Right Arm**: Right wrist reaches furthest cross-body/high position, elbow still flexed; shoulder elevation near b or slightly higher.

**Right Hand**: Thumb stays over fingers, palm into handle. Blade plane begins rolling edge toward cutting direction; fit about 35-80 degrees roll from guard with wrist bend under 20 degrees.

**Left Arm**: Left forearm lifts toward weapon arm with elbow bent, counterbalancing and preparing to sweep across torso.

**Left Hand**: Open/fanning fingers briefly visible near right hand; palm oblique inward/forward. Do not merge fingers with sword guard.

**Body**: Torso loaded and turned; pelvis begins uncoiling while sword arm is still high, creating drive instead of isolated wrist swing.

**Support**: Right support remains; left foot still lifted, knees soft. Contact/pivot depth is inferred and must be side-checked on rig.

**Head**: Face rotates back toward front and slightly up, following intended slash; jaw slightly parted.

**Secondary**: Free arm follows main arm with short delay; pouch at right hip trails uncoil.

**Anatomical fitting ranges, not local Euler keys**: elbow_R_deg=[25, 55]; elbow_L_deg=[65, 100]; forearm_R_roll_from_guard_deg=[35, 80]; knee_L_deg=[20, 45]; torso_yaw_magnitude_deg=[20, 40]; head_pitch_deg=[-8, 3].

**Verify**:

- Native left foot remains raised; do not choose two-flat-feet key just for easier rig.
- Blade and guard orient coherently, no 360-degree forearm wind-up.

No genuine side/back action evidence. Side/back motion is inferred and must be checked for anatomy, balance and collisions on the returned rig.

### d — 375.0 ms: fast crossing cut

**Native evidence**: gobatd0.bmp; native interval 125.0 ms.

**Driver**: Torso uncoils, shoulder drives right wrist rapidly across/down toward image-left; elbow supports arc.

**Right Arm**: Right wrist drops from chest to upper waist and moves image-left, elbow bends around torso; shoulder leads, wrist follows without disconnecting or sweeping through ribcage.

**Right Hand**: Grip locked; blade strongly foreshortens as plane rotates through cut. Palm remains into hilt; continuous pronation/supination solving rather than extra elbow twist; wrist bends only enough to align edge.

**Left Arm**: Left elbow/forearm crosses chest toward image-left, hand near center/chest as balance and protection.

**Left Hand**: Palm inward/oblique toward chest, fingers open and slightly bent, thumb spread. It must clear weapon wrist and blade path.

**Body**: Pelvis uncoils first then chest follows with forward/down impulse; shoulder heights tilt as load changes. Force comes from whole chain, not a frozen torso and spinning hand.

**Support**: Left foot returns toward contact; right heel may unload as support transfers, seen right foot slightly higher in front. Exact toe pivot uncertain: use contact-safe small turn rather than skate.

**Head**: Head turns toward slash/image-left and chin starts dipping, slightly lagging chest.

**Secondary**: Free arm balances cut; pouch and skirt lag torso briefly, then follow. Sword remains rigid through maximum angular speed.

**Anatomical fitting ranges, not local Euler keys**: elbow_R_deg=[55, 95]; elbow_L_deg=[65, 105]; spine_forward_deg=[8, 20]; head_pitch_deg=[5, 15]; knee_R_deg=[15, 35]; knee_L_deg=[5, 25].

**Verify**:

- Wrist crosses down/image-left at maximum speed, with free hand across chest.
- Review several subframes c-d-e for blade clipping, palm inversion and foot skating.

No genuine side/back action evidence. Side/back motion is inferred and must be checked for anatomy, balance and collisions on the returned rig.

### e — 500.0 ms: low outward follow-through

**Native evidence**: gobate0.bmp; native interval 125.0 ms.

**Driver**: Right arm extends out toward image-left/down as torso leans into completed slash, then starts braking.

**Right Arm**: Shoulder reaches forward/out on right side, elbow opens markedly; wrist remains low and outside body, not locked straight.

**Right Hand**: Blade extends far image-left with narrow edge-on silhouette. Keep grip closure; wrist neutral to slightly ulnar bent and forearm roll continuous. Edge-on blade must not be replaced by a shorter blade.

**Left Arm**: Left forearm sweeps down/forward across belly, elbow opens while shoulder counterbalances right reach.

**Left Hand**: Palm oblique up/inward, loose fingers pointing image-left/down and thumb separated; no rigid identical pose to c.

**Body**: Chest bends forward and toward image-left with restrained pelvic rotation; decelerate broad arm/body arc after power phase.

**Support**: Both feet low/near ground, knees flexed; lock actual support contact and allow only justified pivot rotation.

**Head**: Strongest downward/side following gaze, chin toward cutting hand. Neck bends smoothly rather than face rotating alone.

**Secondary**: Free hand and skirt finish delayed sweep; pouch may move slightly, but heavy spikes do not wobble like rubber.

**Anatomical fitting ranges, not local Euler keys**: elbow_R_deg=[10, 35]; elbow_L_deg=[20, 55]; spine_forward_deg=[15, 30]; head_pitch_deg=[15, 30]; knee_R_deg=[10, 30]; knee_L_deg=[10, 30].

**Verify**:

- Long blade reaches far image-left, right wrist low; native head/chest visibly lean down.
- Do not freeze all joints at impact; follow-through carries real motion and decelerates.

No genuine side/back action evidence. Side/back motion is inferred and must be checked for anatomy, balance and collisions on the returned rig.

### f — 625.0 ms: recovery

**Native evidence**: gobatf0.bmp; native interval 125.0 ms.

**Driver**: Right shoulder retracts and torso rises toward ready stance after slash.

**Right Arm**: Elbow bends again, wrist moves back toward right thigh/waist; upper arm returns from extension.

**Right Hand**: Grip remains closed, blade near-low/front and foreshortened. Roll returns toward standing through shortest path, without releasing hilt or hiding orientation snap.

**Left Arm**: Free arm relaxes down across front/left thigh; elbow opens gently after balancing sweep.

**Left Hand**: Palm inward/down, fingers loosen; smooth recovery from e rather than immediate modeling hand fan.

**Body**: Pelvis centered again, chest partly recovers but remains tilted compared with held standing. Last 125 ms can finish a small inferred settle.

**Support**: Both feet reestablish stable ground, knees soften rather than snapping straight.

**Head**: Downward gaze begins returning to forward target, jaw returns to restrained snarl.

**Secondary**: Pouch/skirt settle after body, with no extra motion cycle outside native 750 ms.

**Anatomical fitting ranges, not local Euler keys**: elbow_R_deg=[25, 60]; elbow_L_deg=[20, 50]; spine_forward_deg=[5, 15]; head_pitch_deg=[8, 20].

**Verify**:

- Sword hand remains anatomical right and grip does not slide during return.
- f-to-standing blend preserves ground contacts and intentionally records any added settle.

No genuine side/back action evidence. Side/back motion is inferred and must be checked for anatomy, balance and collisions on the returned rig.

## Hit

Recoil and protective reach of free LEFT arm; right hand keeps sword. Not a second attack.

**Continuous motion**: a begins recoil; a-b is fast outward protective reach, b-c closes guard across face, c-d bows into cover, d-e-f lowers guard and recovers. Rapid onset, delayed head/hand recovery, no uniform easing at all frames. Keep 750 ms duration.

**Confidence**: High left-hand face-covering and right grip; medium head turn; low-medium hit direction/depth and exact support pivot because action has one genuine view.

[Unannotated native sheet](source/hit_native.png) · [Approximate landmark overlay](guides/hit_landmarks.png)

### a — 0 ms: recoil onset

**Native evidence**: gobwia0.bmp; native interval 125.0 ms.

**Driver**: Chest and head recoil while free left forearm rises across upper torso.

**Right Arm**: Right shoulder down, elbow partly opens; wrist low/outside right hip, keeping sword away from covering arm.

**Right Hand**: Stable grip, blade low and foreshortened; palm into hilt, wrist near-neutral with small roll beginning as sword arm counterbalances.

**Left Arm**: Left shoulder protracts and lifts, elbow bends to move wrist from hip to upper chest/image-left.

**Left Hand**: Open fingers, palm oblique forward/toward incoming hit; thumb separated. Avoid fully closed fist or a palm facing inward when reaching outward.

**Body**: Chest rotates toward image-left with a small backward recoil, pelvis stays supported and knees unlock.

**Support**: Right sole supports; left heel/foot begins unloading. Exact force vector unknown, so no large backward step is asserted.

**Head**: Head turns image-left, chin slightly lifted; neck responds after chest onset, jaw partly open.

**Secondary**: Sword arm counterbalances rather than performs slash; pouch/skirt lag recoil slightly.

**Anatomical fitting ranges, not local Euler keys**: elbow_R_deg=[15, 40]; elbow_L_deg=[55, 85]; spine_forward_deg=[-12, 0]; head_pitch_deg=[-8, 5].

**Verify**:

- Left wrist rises across chest while right wrist stays low.
- Head turns away/sideways and sword remains rigid in grip.

No genuine side/back action evidence. Side/back motion is inferred and must be checked for anatomy, balance and collisions on the returned rig.

### b — 125.0 ms: protective outward reach

**Native evidence**: gobwib0.bmp; native interval 125.0 ms.

**Driver**: Left hand reaches furthest across/up toward image-left to block, with torso turn.

**Right Arm**: Elbow partly bent, wrist holds low/out; shoulder rolls to orient sword upright and clear body.

**Right Hand**: Power grip unchanged, blade tip up/image-left. Forearm roll aligns guard and blade; wrist bend kept under about 20 degrees instead of compensating with an impossible kink.

**Left Arm**: Left shoulder reaches forward across chest, elbow opens, wrist near face height but far image-left. Do not shorten forearm to fit.

**Left Hand**: Palm normal mostly toward incoming hit/front with fingers fanned and extended horizontally across face direction; thumb opposes but does not grip.

**Body**: Strongest backward/side recoil, chest yaw leads pelvis; small ribcage tilt and shoulder height difference.

**Support**: Right leg supports; left knee lifts and left sole is clear, shown image-right. Avoid false bilateral grounding.

**Head**: Face turns image-left and slightly away from palm; neck not stretched to make hand reach.

**Secondary**: Head and loose fingertips lag body onset; skirt panel follows lifted left thigh, pouch stays right.

**Anatomical fitting ranges, not local Euler keys**: elbow_R_deg=[25, 60]; elbow_L_deg=[15, 45]; shoulder_L_front_elevation_deg=[75, 100]; knee_L_deg=[25, 55]; spine_forward_deg=[-18, -3]; head_pitch_deg=[-5, 10].

**Verify**:

- Maximum free-hand reach is image-left at face/shoulder height.
- Fan palm faces blocking direction; lifted left foot stays clear, right support stable.

No genuine side/back action evidence. Side/back motion is inferred and must be checked for anatomy, balance and collisions on the returned rig.

### c — 250.0 ms: guard closes over face

**Native evidence**: gobwic0.bmp; native interval 125.0 ms.

**Driver**: Left elbow flexes to pull protective palm from extension back toward brow/eyes.

**Right Arm**: Right elbow bends more, wrist comes slightly inward/up while shoulder remains low to leave room for guard.

**Right Hand**: Grip fixed; blade upright with broad face visible. Continuous roll from b and unchanged thumb/guard relation; no hand swap.

**Left Arm**: Left elbow folds, wrist nearer head center; shoulder stays elevated/protracted, preserving shoulder-elbow-wrist lengths.

**Left Hand**: Open hand covers face with palm facing outward/oblique to hit. Fingers splay over brow, thumb below/inside; keep palm just off face, not embedded in eye sockets.

**Body**: Torso starts centering from recoil, pelvis follows after chest; mild forward compression begins.

**Support**: Left foot returns toward ground; right stance remains dominant. Small contact transition inferred, not a jump.

**Head**: Chin tucks and face turns back toward front behind shielding hand; jaw starts closing.

**Secondary**: Head follows protective arm, pouch continues small lag; bracer stays out of skull.

**Anatomical fitting ranges, not local Euler keys**: elbow_R_deg=[40, 70]; elbow_L_deg=[70, 105]; spine_forward_deg=[0, 12]; head_pitch_deg=[10, 25]; knee_L_deg=[10, 30].

**Verify**:

- Palm near brow, fingers visibly cover face rather than drift above crown.
- Swords/arm plates avoid head and free fingers during guard closure.

No genuine side/back action evidence. Side/back motion is inferred and must be checked for anatomy, balance and collisions on the returned rig.

### d — 375.0 ms: bow into cover

**Native evidence**: gobwid0.bmp; native interval 125.0 ms.

**Driver**: Head/chest tuck beneath left palm as recoil resolves into protective crouch.

**Right Arm**: Right upper arm low/outside torso; wrist low at right waist with bent elbow, counterbalancing tuck.

**Right Hand**: Sword nearly upright/narrow edge-on in front; rigid grip, small forearm roll. Do not alter blade thickness to match changing highlight.

**Left Arm**: Elbow flexed near chest, wrist remains in front of face at lower height as head bows.

**Left Hand**: Palm covers brow/upper face, fingers partly curl around guard shape without clipping nose; wrist flexion modest and continuous.

**Body**: Forward torso flex and small pelvic lowering replace backward recoil; shoulder line tilts naturally.

**Support**: Both feet low with soft knees; restore support before lowering center. Toe pivots small and contact-safe.

**Head**: Strongest chin tuck/downward pitch; face mostly behind hand, neck bends with upper spine.

**Secondary**: Free fingertips relax from maximum fan; skirt hangs into slight crouch with no artificial wide swing.

**Anatomical fitting ranges, not local Euler keys**: elbow_R_deg=[25, 60]; elbow_L_deg=[75, 110]; spine_forward_deg=[10, 25]; head_pitch_deg=[20, 35]; knee_R_deg=[10, 30]; knee_L_deg=[10, 30].

**Verify**:

- Head goes down under hand; hand stays in front rather than sliding through skull.
- Upright sword remains beside body, no blade through left forearm.

No genuine side/back action evidence. Side/back motion is inferred and must be checked for anatomy, balance and collisions on the returned rig.

### e — 500.0 ms: guard lowers

**Native evidence**: gobwie0.bmp; native interval 125.0 ms.

**Driver**: Left wrist lowers from face to chest while body begins recovery.

**Right Arm**: Elbow/shoulder settle toward ready but keep sword arm outside torso.

**Right Hand**: Grip remains closed, blade upright but begins lowering by forearm/shoulder motion; thumb orientation continuous.

**Left Arm**: Left elbow opens gently, wrist comes to chest height, shoulder lowers after head starts clearing hand.

**Left Hand**: Palm rotates inward/down from outward guard, fingers loosen into soft open curl; avoid instant 180-degree wrist flip.

**Body**: Pelvis centered, torso slowly straightens with restrained remaining forward lean.

**Support**: Both feet support, knee extension gradual. No root shift to hide hand/head error.

**Head**: Head still down, beginning to look forward again; jaw restrained.

**Secondary**: Free arm recovery lags torso; cloth/pouch settle without oversized jiggle.

**Anatomical fitting ranges, not local Euler keys**: elbow_R_deg=[25, 60]; elbow_L_deg=[55, 85]; spine_forward_deg=[5, 18]; head_pitch_deg=[12, 25].

**Verify**:

- Free hand below eyes, not still shielding at maximum height.
- Head and wrist trajectories both descend/recover continuously.

No genuine side/back action evidence. Side/back motion is inferred and must be checked for anatomy, balance and collisions on the returned rig.

### f — 625.0 ms: return to ready

**Native evidence**: gobwif0.bmp; native interval 125.0 ms.

**Driver**: Left arm relaxes to hip and sword lowers while torso/head recover.

**Right Arm**: Right wrist returns near right waist, elbow slight bend; shoulder no longer recoils.

**Right Hand**: Blade lowers and foreshortens toward standing projection; roll follows shortest continuous return, fingers retain grip.

**Left Arm**: Left wrist beside left upper thigh, elbow nearly relaxed, shoulder down.

**Left Hand**: Palm inward/oblique forward, loose fingers downward; preserve natural grip-free asymmetry with right hand.

**Body**: Near-ready upright pose with residual gentle forward tilt; complete small inferred blend in final interval if needed.

**Support**: Both soles stable, knees unlocked, center balanced.

**Head**: Face recovers toward front, chin not yet forced to exact standing angle at f.

**Secondary**: Pouch/skirt settle; held standing must become static after transition.

**Anatomical fitting ranges, not local Euler keys**: elbow_R_deg=[15, 40]; elbow_L_deg=[10, 30]; spine_forward_deg=[0, 10]; head_pitch_deg=[3, 15].

**Verify**:

- Left hand returns near hip, sword hand keeps handle.
- Blend to standing without extra dramatic flourish or foot reset.

No genuine side/back action evidence. Side/back motion is inferred and must be checked for anatomy, balance and collisions on the returned rig.

## Death

Loss of support: head and torso bow, knees fold, left hand reaches ground, body collapses prone. Sword descends with right hand.

**Continuous motion**: a-b progressively lose height; b-c accelerates into collapse; c-d is fastest fall/contact; d is already pixel-identical to held corpse, e is a small settling variation; end at 625 ms on Corpse. No added sideways roll, explosion or kneeling final state. Ground contact must be solved at several subframes before editing weights.

**Confidence**: High overall collapse and visible head/hands/sword; low hidden pelvic roll, legs and support under body. Null points must not be interpreted as limb disappearance.

[Unannotated native sheet](source/death_native.png) · [Approximate landmark overlay](guides/death_landmarks.png)

### a — 0 ms: bow / strength fails

**Native evidence**: gobdya0.bmp; native interval 125.0 ms.

**Driver**: Head drops and upper torso pitches forward while knees begin to soften.

**Right Arm**: Right elbow flexes slightly, wrist low/front right of waist, bringing sword broadside across abdomen.

**Right Hand**: Grip retained, palm into hilt; blade horizontal/diagonal forward with broad face visible. Wrist modestly bent, shoulder movement drives lowering.

**Left Arm**: Left elbow bends, wrist drops inward over abdomen/thigh as body starts folding.

**Left Hand**: Open/loose fingers with palm inward/down, starting to seek ground rather than grabbing sword.

**Body**: Pelvis still high and centered, spine flex starts at hips/chest; do not shrink torso to lower head.

**Support**: Both feet grounded, knees begin flexion, weight moves forward.

**Head**: Chin down, crown forward, neck flex distinct from spine, teeth partly obscured by bow.

**Secondary**: Skirt moves with initial hip fold, pouch stays right; blade and plates remain rigid.

**Anatomical fitting ranges, not local Euler keys**: spine_forward_deg=[15, 30]; head_pitch_deg=[20, 40]; knee_R_deg=[10, 30]; knee_L_deg=[10, 30]; elbow_R_deg=[25, 55]; elbow_L_deg=[35, 65].

**Verify**:

- Head bows before root collapses, sword low across front.
- Feet still support; no sudden whole-body translation through ground.

No genuine side/back action evidence. Side/back motion is inferred and must be checked for anatomy, balance and collisions on the returned rig.

### b — 125.0 ms: deep fold / knees yield

**Native evidence**: gobdyb0.bmp; native interval 125.0 ms.

**Driver**: Hips/knees yield and chest folds downward; head descends sharply.

**Right Arm**: Right forearm folds inward at lower chest/knee height, bringing grip near front center.

**Right Hand**: Grip closed; sword broad face extends toward image-right/up relative to lowered hand. Avoid reading tip rise as active attack; hand/body descend together.

**Left Arm**: Left elbow bent with hand nearer center/thigh, starting to uncross for ground brace.

**Left Hand**: Palm rotates from inward toward down, fingers open in preparation for bracing, wrist not yet load-bearing.

**Body**: Large forward bend with knee flexion and pelvic drop; hips still above final ground, chest compresses without scaled bones.

**Support**: Both feet still near original ground but load shifts to toes; knee and toe pivots need geometry-aware fitting.

**Head**: Head deeply down, neck folded with visible crown toward viewer; do not insert face through gorget.

**Secondary**: Skirt overlaps flexed thighs and hangs downward; right pouch compresses against hip but remains separate.

**Anatomical fitting ranges, not local Euler keys**: spine_forward_deg=[40, 65]; head_pitch_deg=[30, 50]; knee_R_deg=[35, 65]; knee_L_deg=[35, 65]; elbow_R_deg=[60, 95]; elbow_L_deg=[60, 100].

**Verify**:

- Crown/chest lower strongly from a, pelvis and knees contribute to loss of height.
- Right sword hand stays rigid; left hand prepares support rather than fusing into hilt.

No genuine side/back action evidence. Side/back motion is inferred and must be checked for anatomy, balance and collisions on the returned rig.

### c — 250.0 ms: left hand ground brace / falling

**Native evidence**: gobdyc0.bmp; native interval 125.0 ms.

**Driver**: Left palm reaches ground image-right while knees fold and body falls forward.

**Right Arm**: Right shoulder reaches down/out, elbow opens toward ground with sword hand near lower image-left.

**Right Hand**: Grip may remain loose but attached; sword lies low across front. Do not let blade penetrate terrain while lowering wrist.

**Left Arm**: Left shoulder abducts/protracts, elbow extends, wrist reaches far image-right and down to brace. Arm cannot shorten to keep both head and hand low.

**Left Hand**: Palm normal downward toward ground, fingers splayed across floor. Wrist extends about 35-60 degrees as load builds; claws must sit above/contact floor without stabbing deeply through it.

**Body**: Pelvis drops and chest moves forward/down, hips/knees deeply flexed. A brief crouch is transitional, not death endpoint.

**Support**: Left palm becomes a contact, knees/feet transition from support; hidden leg configuration is inferred, keep joint lengths and floor clearance.

**Head**: Head hangs low between arms, crown toward viewer, neck flexed; leave room between forehead and terrain until impact.

**Secondary**: Skirt falls around bent hips; pouch swings down with gravity. Sword follows hand with no independent windmill.

**Anatomical fitting ranges, not local Euler keys**: spine_forward_deg=[65, 90]; head_pitch_deg=[20, 45]; knee_R_deg=[80, 125]; knee_L_deg=[80, 125]; elbow_R_deg=[25, 60]; elbow_L_deg=[10, 40]; wrist_L_extension_deg=[35, 60].

**Verify**:

- Left palm contacts image-right ground, sword hand low image-left, knees deeply folded.
- No wrist/bracer ground penetration or forehead teleport; inspect acceleration into d.

No genuine side/back action evidence. Side/back motion is inferred and must be checked for anatomy, balance and collisions on the returned rig.

### d — 375.0 ms: prone ground impact

**Native evidence**: gobdyd0.bmp; native interval 125.0 ms.

**Driver**: Chest/head finish falling to ground; arms spread with sword beside right hand.

**Right Arm**: Right shoulder low, arm extends outward toward image-left with elbow bent enough to stay plausible and not lock.

**Right Hand**: Hand low on ground near guard; loosened grip or maintained attachment is ambiguous, use minimum grip-preserving arrangement first. Blade rests rigidly alongside/front, not through palm.

**Left Arm**: Left arm extends sideways along floor toward image-right; elbow soft, shoulder lies with body.

**Left Hand**: Palm down/oblique floor, fingers relaxed and spread along contact; wrist extension reduces after load transfer.

**Body**: Torso lies prone with slight inferred roll only to match visible shoulder/back plates. Pelvis/legs mostly hidden: do not claim exact stance from invisible pixels.

**Support**: Torso/head/forearms contact ground, lower limbs occluded. Set plausible floor-safe legs, no standing pelvis or final kneeling pose.

**Head**: Head low and turned/down into floor silhouette; ear/jaw must remain volumetric with floor clearance.

**Secondary**: Pouch/leather strips settle downward; optional tiny contact compression, no exaggerated rebound. This bitmap is identical to Corpse.

**Anatomical fitting ranges, not local Euler keys**: torso_prone_from_upright_deg=[80, 100]; elbow_R_deg=[15, 50]; elbow_L_deg=[5, 35]; wrist_L_extension_deg=[0, 25].

**Verify**:

- Match shallow wide ground silhouette and spread hands in gobdyd0.
- Do not invent recovered hidden knee/foot positions; verify plausible legs in new side/back renders.

No genuine side/back action evidence. Side/back motion is inferred and must be checked for anatomy, balance and collisions on the returned rig.

### e — 500.0 ms: small impact settle

**Native evidence**: gobdye0.bmp; native interval 125.0 ms.

**Driver**: Very small final head/torso/arm settle from prone impact, then held corpse.

**Right Arm**: Same floor-spread configuration as d, minute elbow/wrist relaxation, no big sweep.

**Right Hand**: Sword/hand stay low together, grip state consistent with d. Guard and blade cannot hover or jump at corpse transition.

**Left Arm**: Extended along floor, small easing of elbow/shoulder load; keep wrist contact stable.

**Left Hand**: Palm down, loose fingers; no fresh gesture or grasp.

**Body**: Tiny settling variation compared with d; remain prone and finish at Corpse pose at clip end, not a new dramatic roll.

**Support**: Maintain floor contacts, hidden legs kept plausible and unchanged except small relaxation.

**Head**: Small settling only, crown and chin stay near floor, ears retain shape.

**Secondary**: Pouch and skirt finish settling under gravity, then stop completely in Corpse.

**Anatomical fitting ranges, not local Euler keys**: torso_prone_from_upright_deg=[80, 100]; elbow_R_deg=[15, 50]; elbow_L_deg=[5, 35]; settle_rotation_amplitude_deg=[0, 3].

**Verify**:

- e differs slightly from d/f; do not omit it merely because impact already looks like corpse.
- End at held gobdyf0 at 625 ms with stable sword and floor contacts.

No genuine side/back action evidence. Side/back motion is inferred and must be checked for anatomy, balance and collisions on the returned rig.

## Corpse

Held prone terminal pose, pixel-identical to Death frame d.

**Continuous motion**: Constant pose; Death last interval interpolates tiny e variation back to this pose by 625 ms. Remains held indefinitely.

**Confidence**: High visible shape and exact d/f pixel equality; low hidden pelvis/leg placement.

[Unannotated native sheet](source/corpse_native.png) · [Approximate landmark overlay](guides/corpse_landmarks.png)

### a — 0 ms: held prone corpse

**Native evidence**: gobdyf0.bmp; native interval 125.0 ms.

**Driver**: No motion; preserve ground-resting wide shallow silhouette.

**Right Arm**: Arm spread along ground image-left, elbow soft; no independent drift.

**Right Hand**: Ground-resting hand beside gold guard, same grip/release decision as Death d/e, rigid sword beside it.

**Left Arm**: Arm spread along ground image-right; shoulder/elbow maintain floor-safe anatomical lengths.

**Left Hand**: Palm down, fingers relaxed on terrain; static.

**Body**: Prone chest/back, slight inferred roll matching native visibility; pelvis and legs hidden, reconstruct plausibly without claiming certainty.

**Support**: Body/arms/head rest on ground; hidden limbs must remain solid and floor-safe in new viewpoints.

**Head**: Low/down/side as native, no rise or breathing; jaw and ears clear floor enough to avoid slicing.

**Secondary**: All leather, pouch, hoops, spikes and sword held after settle.

**Anatomical fitting ranges, not local Euler keys**: torso_prone_from_upright_deg=[80, 100]; elbow_R_deg=[15, 50]; elbow_L_deg=[5, 35].

**Verify**:

- Compare gobdyf0 and gobdyd0: exact source pixel equality.
- A new side view must show prone body and coherent hidden legs, not an upright lower half.

No genuine side/back action evidence. Side/back motion is inferred and must be checked for anatomy, balance and collisions on the returned rig.

## Fidget

Small stationary ready-stance variation, principally chest/shoulder and free-hand relaxation; no dramatic glance or extra flourish.

**Continuous motion**: Tiny a-b-c rise/tension, c-d-e release, f approaches initial ready. Preserve six 125 ms frames over 750 ms. Foot contacts remain constant. Exact 3D amplitude is inferred: fit native silhouettes with 0-0.01H chest translation and 0-3 degree body rotations before adding detail.

**Confidence**: High stationary feet and small extent of motion; medium shoulder/hand changes; low exact tiny wrist/jaw rotations. Sparse image changes do not justify an invented long breathing loop.

[Unannotated native sheet](source/fidget_native.png) · [Approximate landmark overlay](guides/fidget_landmarks.png)

### a — 0 ms: ready baseline

**Native evidence**: gobfia0.bmp; native interval 125.0 ms.

**Driver**: Small ready stance variation begins without stepping.

**Right Arm**: Relaxed near standing; elbow slightly bent, wrist beside right hip.

**Right Hand**: Power grip retained, sword low and front-foreshortened; palm into hilt, no finger release.

**Left Arm**: Elbow loose, wrist at left hip/thigh.

**Left Hand**: Relaxed slightly curved fingers, palm inward/down; thumb loose.

**Body**: Pelvis level, shoulders quiet, chest at baseline.

**Support**: Both soles fully planted for entire fidget; no hip translation that creates skate.

**Head**: Front gaze and restrained snarl, no extra sideways turn.

**Secondary**: Pouch/skirt almost still; any lag below visibly significant scale.

**Anatomical fitting ranges, not local Euler keys**: body_rotation_amplitude_deg=[0, 3]; elbow_R_deg=[15, 35]; elbow_L_deg=[5, 25]; wrist_rotation_amplitude_deg=[0, 5].

**Verify**:

- Preserve standing foot locations and sword grip.
- Do not start a two-second procedural breathing cycle.

No genuine side/back action evidence. Side/back motion is inferred and must be checked for anatomy, balance and collisions on the returned rig.

### b — 125.0 ms: small chest/shoulder tension

**Native evidence**: gobfib0.bmp; native interval 125.0 ms.

**Driver**: Slight chest expansion/shoulder rise, with arms responding softly.

**Right Arm**: Upper arm rises minimally with shoulder, elbow remains loose and wrist almost unchanged.

**Right Hand**: Grip/palm frame stable; subtle blade orientation change only from arm, not autonomous sword wobble.

**Left Arm**: Shoulder rises subtly, elbow/forearm relax without a large reach.

**Left Hand**: Small change of finger curl, thumb remains separated; palm orientation near baseline.

**Body**: Tiny chest lift; pelvis/root stable. Match native surface silhouette rather than large volume inflation.

**Support**: Both soles planted, knees unchanged.

**Head**: Front gaze, crown nearly unchanged; neck counteracts tiny chest lift to avoid head bob.

**Secondary**: Only restrained equipment response, no visible plate flex or pouch bounce.

**Anatomical fitting ranges, not local Euler keys**: body_rotation_amplitude_deg=[0, 3]; chest_translation_h=[0, 0.01]; finger_curl_change_deg=[0, 8].

**Verify**:

- Head/feet remain almost unchanged, chest shift small.
- No extra hand motion invented from metallic highlight changes.

No genuine side/back action evidence. Side/back motion is inferred and must be checked for anatomy, balance and collisions on the returned rig.

### c — 250.0 ms: tiny peak / free fingers relax

**Native evidence**: gobfic0.bmp; native interval 125.0 ms.

**Driver**: Stationary chest/shoulder variation reaches small peak; free fingers loosen.

**Right Arm**: Right shoulder/elbow remain close to b; wrist stable near waist.

**Right Hand**: Closed grip unchanged; no guard sliding or opening thumb.

**Left Arm**: Free forearm lowers/relaxes marginally relative to shoulder.

**Left Hand**: Fingers a little longer/opener in silhouette, palm still inward/down; use gentle distal curl variation rather than hand scale.

**Body**: Chest near slight peak, abdomen shape may vary subtly; pelvis stable.

**Support**: Both feet fixed, knees soft and unchanged.

**Head**: Forward and nearly fixed; small jaw/face changes are uncertain, leave neutral unless silhouette demands them.

**Secondary**: No extra cloth swing; very slight response follows chest.

**Anatomical fitting ranges, not local Euler keys**: body_rotation_amplitude_deg=[0, 3]; chest_translation_h=[0, 0.01]; finger_curl_change_deg=[-8, 0].

**Verify**:

- Fingers change curl, not digit count or length.
- Small amplitude stays within native stationary outline; no theatrical chest heave.

No genuine side/back action evidence. Side/back motion is inferred and must be checked for anatomy, balance and collisions on the returned rig.

### d — 375.0 ms: small release

**Native evidence**: gobfid0.bmp; native interval 125.0 ms.

**Driver**: Shoulders/chest return gradually, left hand follows with slight delay.

**Right Arm**: Shoulder lowers minimally, elbow loose, wrist nearly fixed.

**Right Hand**: Rigid grip and low sword; shortest small orientation return.

**Left Arm**: Forearm settles beside hip, elbow opens by only a small amount.

**Left Hand**: Relaxed fingers partly open, palm inward; wrist does not swing across body.

**Body**: Chest eases downward toward baseline; no pelvic bob or torso twist beyond tiny inferred fitting range.

**Support**: Both complete soles stable.

**Head**: Front gaze with compact jaw silhouette, no new head nod.

**Secondary**: Free fingertips lag chest slightly; pouch/skirt effectively still.

**Anatomical fitting ranges, not local Euler keys**: body_rotation_amplitude_deg=[0, 3]; chest_translation_h=[-0.005, 0.005]; finger_curl_change_deg=[-5, 5].

**Verify**:

- Hands remain near baseline locations, foot contacts exact.
- Do not convert subtle texture differences into shoulder jerks.

No genuine side/back action evidence. Side/back motion is inferred and must be checked for anatomy, balance and collisions on the returned rig.

### e — 500.0 ms: settling to ready

**Native evidence**: gobfie0.bmp; native interval 125.0 ms.

**Driver**: Small body release completes, free fingers regain relaxed curve.

**Right Arm**: At near-standing shoulder/elbow positions; wrist stable.

**Right Hand**: Grip and blade plane close to initial pose; no hand roll snap.

**Left Arm**: Elbow/wrist near baseline beside left hip.

**Left Hand**: Loose downward fingers regain slight curl; thumb remains free.

**Body**: Chest and shoulders near baseline, pelvis/root fixed.

**Support**: Both soles remain pinned, knees unchanged.

**Head**: Same forward attention and jaw, no added blink asserted from sparse pixels.

**Secondary**: No new equipment motion as body finishes.

**Anatomical fitting ranges, not local Euler keys**: body_rotation_amplitude_deg=[0, 2]; chest_translation_h=[-0.005, 0.005]; finger_curl_change_deg=[0, 5].

**Verify**:

- Approach standing smoothly without changing feet.
- No added visible glance, sword flourish or skirt bounce.

No genuine side/back action evidence. Side/back motion is inferred and must be checked for anatomy, balance and collisions on the returned rig.

### f — 625.0 ms: ready restored

**Native evidence**: gobfif0.bmp; native interval 125.0 ms.

**Driver**: Finish small stationary variation and blend into held ready stance.

**Right Arm**: Relaxed near standing, elbow unlocked.

**Right Hand**: Closed right grip, sword same low foreshortened arrangement.

**Left Arm**: Relaxed left arm down beside hip.

**Left Hand**: Loose three fingers and thumb, slight natural curl, palm inward/down.

**Body**: Stable level pelvis and quiet chest; remaining tiny settle must fit final native interval.

**Support**: Both soles fixed through transition to Standing.

**Head**: Forward stare, held snarl and no new breathing cycle.

**Secondary**: Everything settles to static held state.

**Anatomical fitting ranges, not local Euler keys**: body_rotation_amplitude_deg=[0, 2]; elbow_R_deg=[15, 35]; elbow_L_deg=[5, 25].

**Verify**:

- Final interval blends to native held standing, not a perpetual looping idle.
- Keep tiny intentional variation separate from noise in later frame comparisons.

No genuine side/back action evidence. Side/back motion is inferred and must be checked for anatomy, balance and collisions on the returned rig.

## Review on the returned rig

First inspect walking and the sword-grip/high-cross/face-guard/deep-knee/prone stress poses. Render each native anchor plus intermediate frames through the fastest attack and collapse intervals. Use one locked camera, scale and ground, compare head/shoulder/wrist/pelvis/sole heights, hand plane/visible thumb, blade plane, support contacts and the unannotated silhouette. Approximate 2D seeds suggest where to look, not an automatic pass/fail threshold. Check front plus genuine native walk views; review inferred action sides/back for plausible chains and clearance. Repair geometry, bone axis, orientation, contact or weights according to the demonstrated cause; record annotated before/after images and rerun affected clips. Do not author the rest over a known pilot defect.
