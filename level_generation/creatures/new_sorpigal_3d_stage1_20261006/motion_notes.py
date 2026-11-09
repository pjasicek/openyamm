"""Manually reviewed native choreography. Angles are fitting seeds, never measurements."""

# Arm code: shoulder abduction, forward elevation, elbow flexion, forearm roll, wrist flexion, chain description.
ARMS = {
    'down': (5,0,10,0,0,'Clavicle quiet; upper arm beside ribs, elbow points back/out slightly, wrist below hip.'),
    'back': (8,-18,20,-10,0,'Shoulder travels back; elbow stays low beside ribs; wrist trails hip, away from clothing.'),
    'forward_low': (8,22,25,10,0,'Clavicle advances slightly; upper arm reaches forward low, elbow soft, wrist ahead of hip.'),
    'staff_ready': (25,20,90,0,0,'Upper arm low/out, elbow below hand; forearm forward to waist/lower chest; wrist aligned to shaft.'),
    'staff_back': (20,-5,100,-15,5,'Shoulder retracts; elbow beside waist, wrist near abdomen; grip remains continuous as shaft trails.'),
    'staff_front': (20,45,45,15,0,'Shoulder advances, elbow opens toward target, wrist ahead of chest; keep full upper-arm/forearm lengths.'),
    'temple': (55,60,120,25,5,'Clavicle rises; elbow out below shoulder; forearm folds up beside temple, wrist clear of face.'),
    'overhead': (65,120,95,35,-5,'Shoulder elevates with clavicle/scapula; elbow out/up, forearm above brow, wrist follows overhead arc.'),
    'overhead_support': (55,110,100,-25,-5,'Upper arm raises beside head; elbow points outward, forearm almost upright; wrist approaches overhead shaft.'),
    'side_open': (40,25,45,45,5,'Upper arm opens away from torso; elbow soft, wrist out and forward as a counterweight.'),
    'out_high': (70,60,30,55,0,'Clavicle rotates upward; upper arm out/front; elbow opens, wrist near shoulder-height reach.'),
    'draw_low': (35,-25,30,-25,0,'Shoulder retracts and turns outward; elbow low, wrist drawn behind/outside hip without overstretching.'),
    'thrust': (20,75,40,25,0,'Clavicle protracts; upper arm points toward viewer; elbow opens, forearm foreshortens, wrist ahead of torso.'),
    'cross': (25,80,20,35,5,'Shoulder reaches across chest toward opposite side; elbow nearly opens; wrist traces lateral attack arc at chest/shoulder height.'),
    'cross_retract': (20,55,75,30,0,'Shoulder remains turned across body; elbow folds to retract wrist toward opposite chest, without crossing forearm through ribs.'),
    'waist_grip': (12,30,75,15,0,'Upper arm lowers near ribs; elbow remains bent, wrist returns in front of belt/waist.'),
    'face_guard': (55,55,115,65,10,'Clavicle hunches; elbow out at shoulder height; forearm crosses brow, wrist passes outside face rather than through nose.'),
    'open_guard': (40,65,100,-35,-10,'Shoulder raises forward/out; elbow bends below hand, wrist beside face/chest as open protective palm.'),
    'abdomen': (15,30,105,60,0,'Shoulder folds inward; elbow low, forearm crosses abdomen, wrist close to opposite waist.'),
    'elbow_out': (60,20,100,20,20,'Upper arm abducts sideways; elbow high/out, forearm hangs down/forward; wrist below elbow.'),
    'floor_reach': (20,80,30,70,15,'Shoulder reaches forward/down as torso lowers; elbow opens softly, wrist approaches floor without arm extension beyond length.'),
    'folded': (15,20,40,35,0,'Upper arm close to ribs; elbow bends slightly outward, forearm diagonally inward to joined hands below belt.'),
    'pole_ready': (5,0,15,20,0,'Upper arm hangs near ribs; elbow nearly straight, wrist at thigh/low hip; rigid polearm supported by right grip.'),
    'pole_front': (15,40,45,25,0,'Shoulder advances with forearm; elbow bends low, wrist rises in front of waist; polearm blade sweeps forward/up.'),
    'pole_up': (35,55,90,15,0,'Clavicle lifts; elbow out and bent, wrist chest/shoulder high; shaft rises beside body.'),
    'pole_high': (50,75,105,40,0,'Right shoulder rotates up/back; elbow out, wrist near temple/shoulder; blade above and outside head.'),
    'pole_second': (20,50,90,-35,0,'Left clavicle advances; elbow folded near ribs, wrist reaches lower part of same shaft across chest/waist.'),
    'pole_down': (15,45,45,55,5,'Upper arm drives down/across; elbow opens toward lower chest, wrist moves through centerline while remaining on shaft.'),
    'pole_pull': (10,30,70,-45,0,'Left elbow draws back/down; forearm guides lower shaft toward left hip, complementing right-hand push.'),
    'pole_recover': (25,55,100,40,0,'Right elbow folds and lifts in front of chest; wrist brings shaft across upper torso for recovery.'),
    'fall_spread': (65,20,25,45,0,'Shoulder opens as trunk falls; elbow mostly open, wrist out from body. Root rotation carries arm, not an impossible spine bend.'),
    'corpse_out': (65,0,30,70,0,'Arm rests out from trunk; elbow/wrist settle near floor. Occluded depth must be chosen from collision-free anatomy.'),
}

HANDS = {
    'relaxed': 'Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.',
    'loose_fist': 'Fingers point/curl into palm (proximal curl 50–80°, tips flex), palm normal inward/back, thumb outside index rather than buried. Keep fist silhouette but preserve separate digits.',
    'staff': 'Palm normal toward shaft; fingers wrap tangentially around wood (curl 65–95°), thumb opposed across index. Wrist nearly straight; forearm roll follows shaft axis. Fixed grip offset, no sliding or changing shaft length.',
    'pole': 'Palm normal toward wood shaft, fingers curved around it (65–95°), opposed thumb closes grip. Wrist stays within about ±15° flex; use forearm rotation to roll blade, not a wrist kink or blade morph.',
    'pole_second': 'Left palm normal toward same shaft, fingers encircle lower grip station, opposed thumb; finger curl 65–95°. Maintain finite grip spacing and align forearm roll to shaft; do not weld hands together.',
    'knife': 'Palm normal inward toward knife handle; four fingers curl 70–95°, opposed thumb supports handle. Finger direction follows curled grip; blade is rigid extension of hand/socket. Forearm roll sets edge orientation; wrist near neutral, not snapped sideways.',
    'open_up': 'Palm normal up (+Z, with modest forward component), fingers extend outward/forward, fan 10–20°, curl 0–20°; thumb abducted/opposed. Supinate forearm; do not obtain palm-up with extreme wrist bend.',
    'open_front': 'Palm normal forward (+Y), fingers upward/outward along hand, fan 10–20°, curl 0–15°; thumb spread. Adjust forearm roll for palm plane; wrist within ±15°.',
    'open_down': 'Palm normal down (−Z), fingers forward/down along reach, fan 8–18°, curl 0–20°; thumb separated. Pronation travels through forearm, wrist softly extended for contact.',
    'face_guard': 'Palm normal toward face/partly down, fingers extend sideways above brow with curl 15–40°; thumb outside face. Protect facial clearance; rotation comes from shoulder and forearm before wrist.',
    'folded': 'Fingers diagonally down/inward, palm normal toward skirt/other hand; curl 15–35°, fan 0–8°, thumb slightly opposed. Retain two palms/digit sets and light contact without fused or interpenetrating hands.',
    'shaft_ambiguous': 'Overhead hand lies close to shaft. Native pixels do not resolve a closed grip: begin with supporting palm normal up/toward wood, fingers partly curled 20–60°, thumb separated. Test supporting-contact and near-contact fits; do not invent a firm second grip without matching the silhouette.',
}

# phase | native observation | driver | right arm/hand | left arm/hand | trunk/support/head | prop
# Body seed: world trunk forward tilt, torso yaw toward character right, R/L knee flex, pelvis height delta / H.
NOTES = {
 'pmn2': {
  'standing': [
   ('held ready','Upright staff at character right; left hand below hip, feet apart, beard faces front.','Quiet torso supports right elbow and shaft, no breathing cycle.', 'staff_ready','staff','down','relaxed','Broad chest upright; shoulders level.','Both boots apparently supported; knees soft, exact depth inferred.','Face forward, chin neutral; no compulsory jaw motion.','Staff upright, upper end above right shoulder; tip near floor, not evidence of cane weight.',(0,0,5,5,0))],
  'attack': [
   ('ready/open','Right staff extends out, left fingers open near hip; feet remain broadly spaced.','Small knee softening and right-shoulder preparation.','staff_ready','staff','side_open','open_front','Chest front, pelvis quiet.','Both feet support; begin small knee bend.','Eyes toward target, chin slightly down.','Staff near vertical; right grip continuous.',(3,0,10,10,-.01)),
   ('draw and free-hand lift','Right hand near temple with staff strongly foreshortened; left palm rises in front of shoulder.','Knees lower pelvis while right shoulder draws shaft back; left palm counters toward target.','temple','staff','open_guard','open_front','Ribs hunch slightly; no large backward step.','Feet stay spaced; knees bend together.','Chin down, gaze under brows.','Shaft depth/axial angle uncertain; keep length, fit end projection.',(8,8,25,25,-.03)),
   ('overhead brace','Staff diagonal above brow; both forearms raised, crouch visible.','Clavicles elevate and elbows guide staff overhead; knee flex makes clearance.','overhead','staff','overhead_support','shaft_ambiguous','Trunk slightly forward, shoulders raised; pelvis lowered.','Both knees flex; apparent contact retained unless side fit requires small pivot.','Duck chin under shaft, eyes still target.','Diagonal in frontal plane; left support/contact unresolved, shaft never cuts skull.',(12,5,35,35,-.05)),
   ('horizontal overhead passage','Staff nearly horizontal across eyes, hands high; lowest guarded posture.','Right elbow/forearm carries a continuous overhead arc; left forearm accompanies near shaft.','overhead','staff','overhead_support','shaft_ambiguous','Deepest short crouch; avoid separate torso bounce.','Both feet close to original standing positions; knee flex peaks.','Brow under staff, head dips, beard clear of forearms.','Horizontal projection at brow; avoid interpreting this as a ground slam.',(15,0,40,40,-.06)),
   ('release across body','Staff diagonal across chest; left open palm reaches character left, head/shoulders turn that way.','Right shoulder lowers/rotates shaft; left arm opens as opposing balance, knees extend.','temple','staff','out_high','open_up','Ribcage turns character left, pelvis turns less; rising.','Both feet support, slight sole pivot inferred.','Head turns left modestly with chest, no independent spin.','Diagonal down across chest; right grip fixed, free left clears arc.',(5,-20,20,20,-.025)),
   ('restore upright staff','Staff upright again, left arm low/out, body near ready.','Right elbow lowers to ready; free arm settles last.','staff_ready','staff','side_open','open_down','Chest returns front and upright.','Knees relax toward standing, boots remain grounded.','Face returns front, beard settles.','Upright right-hand carry; recovery ends at 750 ms.',(0,-3,8,8,-.005))],
  'hit': [
   ('recoil begins','Chin lifts, ribs recoil; right staff arm out, left knee starts lifting.','Upper trunk recoils first, hip counterbalance retains support.','staff_ready','staff','down','loose_fist','Short backward rib tilt, pelvis mostly below trunk.','Right boot carries more weight; left heel/contact uncertain.','Chin up/back, gaze briefly above target.','Staff tips away with arm, does not detach.',(-10,0,5,20,-.005)),
   ('recoil and lifted knee','Staff diagonal outward, head tilted back/side; left knee visibly raised.','Rib recoil and left hip flex; right arm widens for balance.','out_high','staff','back','loose_fist','Back/side lean restrained; right shoulder pulled out.','Right support, left knee/foot in swing; no left-foot pin.','Head up and sideways, neck not elongated.','Shaft diagonal away from body, tip sweep stays clear of boot.',(-18,8,8,50,-.01)),
   ('fold staff near face','Right staff near face, left knee still raised; left arm begins opening.','Right elbow folds as trunk changes from recoil toward crouch.','temple','staff','side_open','relaxed','Backward lean reduces, rib yaw slight.','Right supports; left leg begins lowering.','Head tilts away from right hand, chin begins descending.','Staff near vertical beside face; bracer/nose clearance.',(-3,-5,15,40,-.025)),
   ('low forward recovery','Head/chest low, left hand opens outward, boots near floor.','Hip/knee flex absorbs recoil; arms balance the fold.','staff_ready','staff','side_open','open_down','Forward fold with lower pelvis.','Left lands softly; both knees bend, no sudden leg-length change.','Chin down, head follows chest.','Shaft leans slightly; tip may approach floor without automatic plant.',(20,0,35,35,-.05)),
   ('rise','Body rises, head still down, staff upright, left hand lowers.','Knee extension raises pelvis before full head recovery.','staff_ready','staff','side_open','relaxed','Ribs unfold, shoulders descend.','Both boots support, knees extend gradually.','Head still modestly bowed.','Staff upright; grip never resets.',(10,0,20,20,-.025)),
   ('ready restoration','Head/front shoulders return, staff vertical, left arm lower/out.','Torso/head recover after legs; left hand settles.','staff_ready','staff','side_open','relaxed','Upright, slight residual hand widening.','Both feet supported, soft knees.','Face forward, chin neutral.','Return to standing at 750 ms.',(0,0,8,8,0))],
  'death': [
   ('backward recoil','Chin up, staff upright/out; left knee rises as balance breaks.','Ribs/head recoil while right hip briefly supports.','staff_ready','staff','side_open','relaxed','Back tilt begins; pelvis below ribs.','Right support predominates, left foot lifting.','Chin up, no neck stretch.','Staff upright outside right shoulder.',(-10,0,10,25,-.005)),
   ('lose support','Chest arches back, right staff raised diagonally, free hand opens.','Center of mass leaves support; root begins fall while knees buckle.','out_high','staff','side_open','open_up','Whole-body backward tilt increases; local spine modest.','Right foot may pivot; left remains loose, neither both feet pinned.','Head follows backfall, face upward.','Staff rotates with right grip, no brace planted.',(-30,5,25,45,-.08)),
   ('fall back','Torso approaches horizontal above ground, knees draw, left palm open to side.','Root falls backward; arms spread, knees flex to preserve leg lengths.','fall_spread','staff','fall_spread','open_up','Root rotation drives near-horizontal trunk; do not bend spine 70°.','Foot contacts release/roll as body drops; occluded depth inferred.','Head follows torso, face up.','Shaft near horizontal outside body, fixed grip retained.',(-65,8,45,65,-.25)),
   ('floor arrival','Body supine, two boot soles toward viewer; free hand by head, staff at ground left.','Back/hips arrive at floor, small limb/cloth lag.','corpse_out','staff','corpse_out','open_up','Trunk horizontal, pelvis low; floor contacts collision fitted.','Boots separate, knees partly bent; support now back/hips/limbs.','Head depth obscured by mantle/body; choose clear neck pose.','Staff rests low to side, does not pass through ground.',(-90,10,35,45,-.40)),
   ('settle','Nearly same supine silhouette; boot spacing and hand near head remain.','Small settling after impact, no additional roll or flourish.','corpse_out','staff','corpse_out','open_up','Keep floor body silhouette; damp residual rotation.','Back/hips rest, boots settle without sliding.','Head held with only inferred settling.','Shaft stays low/grounded by same grip.',(-90,10,35,45,-.40))],
  'corpse': [
   ('held supine remains','Native pmn2def0 lies supine with separated boots, free hand near head, staff low to side.','None; static remains rather than animated breathing.','corpse_out','staff','corpse_out','open_up','Match corpse silhouette, root/pelvis low.','Floor-supported back/hips/limbs; hidden contacts inferred.','Head near ground, maintain beard/mantle clearance.','Shaft remains fixed and floor-clear; no spontaneous release.',(-90,10,35,45,-.40))],
 },
 'pman': {
  'standing': [
   ('held neutral','Both hands low in loose fists; feet apart, tunic/belt front, chin upright.','No cyclic driver; quiet held stance.','down','loose_fist','down','loose_fist','Chest upright, shoulders modestly square.','Both shoes supported, knees almost straight but unlocked.','Face front, ordinary jaw relaxed.','No handheld knife visible.',(0,0,5,5,0))],
  'attack': [
   ('knife ready','Right knife low by thigh; left arm opens slightly, body front.','Right hand acquires knife visibility and shoulder prepares.','down','knife','side_open','relaxed','Torso quiet, small forward readiness.','Both shoes planted, no invented advance.','Look toward target.','Knife at right side; separate rigid prop.',(2,0,8,8,-.005)),
   ('draw and left guard','Right blade drawn back/out low; left open palm rises toward face/chest; knees flex.','Right shoulder retracts while pelvis lowers, left arm reaches as counterbalance.','draw_low','knife','out_high','open_front','Ribs wind toward character right slightly; pelvis less.','Both knees bend; stance width roughly retained.','Chin down, eyes target below brow.','Blade low/outside right hip, grip does not open.',(5,15,25,30,-.03)),
   ('forward thrust passage','Right forearm foreshortens toward viewer near belt/chest; left palm opens to side.','Clavicle protraction starts reach; elbow opens, knife follows.','thrust','knife','side_open','open_up','Ribs begin turning left, pelvis counters modestly.','Both feet support, knees begin extending.','Gaze ahead, head follows shoulder gently.','Depth of blade inferred from short projected reach; no hand scaling.',(5,0,20,20,-.02)),
   ('cross-body reach','Right arm extends across to character left at shoulder height; knife points diagonally up.','Torso yaw and right shoulder carry lateral blade arc; elbow opens last.','cross','knife','back','relaxed','Chest turns left, pelvis turns less, shoulders oblique.','Left support can carry slightly more weight; minimal sole pivot inferred.','Head turns with blade/chest, chin modestly tilted.','Blade tip upper-left body side (image right); fixed length/edge roll.',(2,-30,10,10,-.005)),
   ('retract cross-body','Right forearm folds across upper chest, blade up/diagonal; left low/back.','Right elbow folds to decelerate distal reach, chest remains turned.','cross_retract','knife','back','relaxed','Yaw holds then starts returning, no new windup.','Feet remain near original stance, soft knees.','Head remains slightly left, target maintained.','Knife outside chest, keep wrist near neutral.',(0,-25,8,8,0)),
   ('lower to waist','Right hand/knife returns near waist/front, left arm down.','Shoulder lowers after elbow recovery; body re-centers.','waist_grip','knife','down','relaxed','Chest returns front, pelvis level.','Both shoes support, knees relax.','Head front.','Knife still visible here; disappearance belongs after attack at 750 ms.',(0,-5,5,5,0))],
  'hit': [
   ('start protective fold','Right hand rises to abdomen/chest, left low; head inclines.','Abdominal fold starts, hands react afterward.','abdomen','loose_fist','forward_low','relaxed','Small forward rib fold, shoulders round.','Both feet support, knees start bending.','Chin down toward chest.','No knife in native hit.',(10,0,12,12,-.01)),
   ('forearm guard','Right forearm crosses face; left palm opens in front at waist/chest.','Shoulder hunch and elbow lift protect head while knees lower pelvis.','face_guard','face_guard','open_guard','open_up','Forward fold, pelvis drops.','Both knees flex; right knee begins angling outward.','Duck behind right forearm.','Hands clear nose/eyes and each other.',(20,0,35,35,-.06)),
   ('deep squat guard','Lowest crouch, right forearm over eyes, left palm fanned beside face; right knee out.','Hip/knee flex absorbs recoil; two arms make asymmetric guard.','face_guard','face_guard','open_guard','open_front','Short deep fold, avoid shrinking torso.','Right knee flex/out, left knee also bent; both shoes near ground.','Head down, shoulders raised protectively.','Right forearm above brow; left fingers independently open.',(25,3,70,65,-.15)),
   ('guard recovery','Protected crouch persists but starts lifting; open left palm remains high.','Knee extension begins below held guard, then elbows loosen.','face_guard','face_guard','open_guard','open_front','Forward fold reduces slightly, pelvis starts up.','Both feet grounded, knee angles decrease a little.','Chin stays low, eyes behind forearm.','Guard fingers/palms do not suddenly swap orientation.',(20,0,60,55,-.12)),
   ('arms lower','Hands separate/lower to either side, chest lifts but still crouched.','Legs restore height while arms release the guard.','side_open','relaxed','side_open','open_down','Ribs unfold and shoulders descend.','Both knees extend toward standing over final 125 ms.','Face begins looking ahead.','Native unused pmanwif0 is excluded; standing boundary is 625 ms.',(8,0,25,25,-.035))],
  'death': [
   ('defensive reaction','Right hand near chest, left low/front, head inclines.','Torso fold and defensive arm reaction.','abdomen','loose_fist','forward_low','relaxed','Chest folds slightly, pelvis lowers.','Both feet support briefly.','Head down, gaze interrupted.','No weapon visible.',(10,0,15,15,-.015)),
   ('protected crouch','Right forearm guards eyes, left palm near face; knees bent.','Knee/hip flex lowers root while arms shield face.','face_guard','face_guard','open_guard','open_front','Forward fold, shoulders hunch.','Deep knee bend; support about to fail.','Head ducks behind forearm.','Hands clear facial features.',(25,0,65,65,-.14)),
   ('side balance failure','Torso inclines character left (image right), right leg extends image left, left knee sinks.','Root tilts toward left; left knee buckles, right leg opens as counterweight.','face_guard','face_guard','open_guard','open_front','Forward/left side root tilt; maintain modest local spine bend.','Left knee drops; right shoe may slide/release. Do not pin both feet.','Head follows fall, no neck swivel independent of torso.','No props; guard arms begin reaching out.',(35,-10,20,95,-.24)),
   ('side drop','Right leg long/out to image left, left leg folded below; arms flare by head as body falls.','Root translation/roll carries collapse; left leg folds, arms reach.','fall_spread','open_down','open_guard','open_front','Strong side tilt and forward pitch; torso lengths preserved.','Left knee/floor nearing contact, right foot no fixed pin.','Head ahead of shoulder fall, neck flex restrained.','Hands/forearms should not cut through head on descent.',(65,-15,15,110,-.37)),
   ('side floor arrival','Low side-lying body, one leg out; head to image right, arms low.','Hip/side contact halts fall; hands and hem settle.','corpse_out','open_down','corpse_out','relaxed','Root at floor; side orientation differs from native corpse.','Floor supports side/hip/leg, right leg partly extended.','Head close to floor turned sideways, not detached.','Last pose must bridge to separate prone corpse at 625 ms.',(85,-20,30,100,-.42))],
  'corpse': [
   ('held prone remains','Face-down body with arms spread, legs apart; distinct pmandef0 from death e.','No repeated motion; endpoint alignment must be solved once.','corpse_out','open_down','corpse_out','open_down','Prone floor root, torso flat and neck clear.','Chest/hips/limbs supported by floor; contact locations inferred.','Face near floor, no breathing or raised gaze.','No knife/blood effect added.',(90,0,20,20,-.42))],
 },
 'pfem': {
  'standing': [
   ('held folded hands','Two hands overlap in front below belt; upright bodice and long skirt, shoes separate.','Quiet held stance, hands lightly contact.','folded','folded','folded','folded','Chest upright, shoulders relaxed, waist above skirt folds.','Both shoes support; hidden hips/knees inferred.','Face front, chin neutral.','No knife visible; two hands must remain anatomically separate.',(0,0,5,5,0))],
  'attack': [
   ('knife ready','Right knife low at character right; left hand near waist, head/torso incline slightly.','Right arm releases folded-hand rest; modest right-side preparation.','down','knife','waist_grip','relaxed','Small side lean, bodice front.','Shoes remain near standing positions; hidden knees soft.','Look toward blade/target with slight chin down.','Separate right-hand dagger visible; folded rest hand contact released.',(3,3,10,10,-.005)),
   ('low draw','Right arm/blade back and outward; left hand near hip, elbow out; torso leans toward right.','Right shoulder draws back, waist/hips provide small windup; left arm balances.','draw_low','knife','elbow_out','relaxed','Ribcage turns right modestly; pelvis less, skirt begins lag.','Both shoes supported; inferred knees flex, no large lunge.','Head angled down/right toward preparation.','Blade low/down at right side, fixed grip.',(8,15,20,20,-.02)),
   ('foreshortened reach','Right forearm reaches toward viewer at belt/chest; left arm opens low to side.','Clavicle advances and elbow opens; rib turn follows, skirt lags.','thrust','knife','side_open','relaxed','Chest begins turning left, pelvis closer to front.','Both feet support with small forward weight shift; knees hidden.','Gaze toward reach, chin down slightly.','Short frontal wrist/blade projection means depth uncertainty, not shorter arm.',(8,0,20,20,-.02)),
   ('cross-body sweep','Right arm extends character left at chest height, blade up/right in image; head/bodice turn left.','Torso yaw and right shoulder sweep knife laterally, elbow opens to reach.','cross','knife','back','relaxed','Quarter-turn left in ribs; waist less; skirt visibly twisted/full.','Tiny shoe pivot allowed, no unobserved extra stride.','Head turns/tilts with chest, eyes along reach.','Left hand stays out of blade arc, no second-hand grip.',(8,-30,15,15,-.01)),
   ('cross-body retraction','Right elbow folds, blade remains diagonal; torso/head still left, left hand low.','Elbow retracts then torso slows; hem continues slight lag.','cross_retract','knife','back','relaxed','Left rib yaw held then unwinds, pelvis modest.','Both shoes retain support, knee flex inferred.','Head remains down/left, follows torso rather than snapping front.','Knife remains separate from forearm/bodice.',(6,-25,10,10,-.005)),
   ('hands toward waist','Right blade/hand lowered in front; left hand approaches without proven grip; body upright/front.','Right shoulder lowers, left arm returns toward folded-rest region.','waist_grip','knife','folded','folded','Torso re-centers, skirt untwists and settles.','Shoes grounded, knees relax.','Head front, chin neutral.','Knife still visible; disappearance/rest hand contact occurs after 750 ms.',(0,-3,5,5,0))],
  'hit': [
   ('abdomen clutch','Right forearm crosses abdomen; left hand low/front; chin bows.','Abdominal fold starts, right arm guards midsection.','abdomen','loose_fist','forward_low','relaxed','Ribs lean forward, waist lowers slightly.','Both shoes support; knee flex hidden under skirt.','Chin down, head follows trunk.','Empty hands, no blade.',(15,0,15,15,-.015)),
   ('fold with left elbow out','Deeper fold, right hand central; left elbow high/out, wrist hanging forward/down.','Spine/hip flex deepens; left arm lifts elbow for balance.','abdomen','loose_fist','elbow_out','open_down','Ribs fold over waist, shoulder asymmetry.','Infer knee flex from overall height, not a visible knee landmark.','Head bows toward abdomen.','Left wrist flex modest; hanging hand does not imply broken wrist.',(30,5,35,35,-.055)),
   ('deepest abdominal recoil','Head low, right forearm across abdomen, left elbow high; skirt broadens.','Hip/knee fold and trunk flex lower head; arms preserve guard shape.','abdomen','loose_fist','elbow_out','open_down','Deep forward fold, body height reduced by joints/root rather than scaling.','Shoes remain at base; knees hidden, choose collision-free 50–80° fit.','Head down, chin toward ribs, neck still full length.','Skirt bends/broadens independently of leg chains.',(50,5,60,60,-.12)),
   ('begin unfolding','Right forearm still at waist, left elbow/wrist still lifted/dangling; torso starts up.','Knee extension starts under maintained abdominal guard.','abdomen','loose_fist','elbow_out','open_down','Forward fold decreases, shoulder asymmetry retained.','Both supports, knees gradually extend below skirt.','Head remains bowed, no premature gaze lift.','Hem lags rise, no instantaneous rigid skirt reset.',(35,3,45,45,-.085)),
   ('release arms','Hands lower/separate, torso rises; head still partly bowed.','Trunk unfolds and shoulders release guard after leg recovery.','down','relaxed','forward_low','open_down','Forward tilt reduces, shoulders descend.','Both shoes support, knees approach relaxed stance.','Chin rises slowly.','No hand merge against skirt.',(15,0,20,20,-.025)),
   ('upright recovery','Nearly upright, hands low/front, head faces forward.','Body settles; hands return toward folded rest during final interval.','forward_low','relaxed','forward_low','relaxed','Chest upright, waist stable.','Both supports, hidden knees softly bent.','Face front.','Reconnect folded hands at 750 ms only with preserved finger clearance.',(2,0,8,8,-.005))],
  'death': [
   ('abdominal collapse starts','Head bows, right forearm crosses waist, left elbow flares.','Rib/hip flex initiates collapse.','abdomen','loose_fist','elbow_out','open_down','Forward fold, waist slightly lowers.','Both shoes initially support; knees unseen.','Head down toward chest.','No knife; skirt covers both legs.',(25,3,25,25,-.04)),
   ('deep fold','Head lower, right arm guards abdomen, left elbow up/out; skirt expands.','Hip/knee flex lowers body while ribcage folds.','abdomen','loose_fist','elbow_out','open_down','Strong forward bend, shoulders rounded.','Inferred knees flex; shoes need coherent contacts.','Chin toward ribs; nape hair follows head.','Do not draw hidden knees as recovered evidence.',(45,3,55,55,-.10)),
   ('crouched buckle','Body shorter/wider, head low, left elbow out, skirt bulges over knees.','Knees buckle toward kneeling; hip/root descends.','abdomen','loose_fist','elbow_out','open_down','Root lowers as spine stays folded; retain torso volume.','Hidden knees may approach floor; exact side/phase unresolved.','Head down, modest neck flex.','Skirt hem spreads, still a hollow cloth shell.',(55,0,90,90,-.20)),
   ('kneeling descent','Low kneeling silhouette, right arm across lap, left hand moving down/front.','Pelvis drops toward knees; shoulders send hands toward floor.','abdomen','relaxed','floor_reach','open_down','Forward trunk, root low; no leg shortening.','Knee/floor supports inferred; feet shift under skirt collision constraints.','Head follows forward fold.','Hem contacts floor and spreads around leg volumes.',(50,0,115,115,-.30)),
   ('hands to floor','Both hands low toward ground ahead, head between arms, skirt spread wide.','Shoulder/elbow reach catches forward descent; hips/root continue settling.','floor_reach','open_down','floor_reach','open_down','Forward/down root orientation; transition toward prone remains.','Knees and palms can support briefly; hidden contact chosen as inference.','Head near floor between hands, hair stays attached.','Palm normals down, fingertips forward; preserve wrist/forearm continuity.',(65,0,120,120,-.36))],
  'corpse': [
   ('held prone skirted remains','Separate pfemdef0 is face-down low, arms forward/out; pale skirt spreads over legs.','None; align death-to-corpse once, then hold.','corpse_out','open_down','corpse_out','open_down','Prone root near floor, body oriented to match diagonal native remains.','Chest/pelvis/forearms supported; leg arrangement occluded and inferred.','Head near ground turned to visible native side, not a detached hair patch.','Dress covers two folded/extended leg chains; no added exposed legs.',(90,-15,70,80,-.42))],
 },
 'gua': {
  'standing': [
   ('held carry','Right hand low, blade foreshortened front; genuine side shows long shaft across hip, left arm down.','Quiet one-handed carry, no cyclic soldier flourish.','pole_ready','pole','down','relaxed','Torso upright, helmet forward, shoulders level.','Both shoes support, knees relaxed.','Face/helmet front; no required jaw animation.','Polearm low near horizontal in side view; frontal blade size is projection.',(0,0,5,5,0))],
  'attack': [
   ('upright preparation','Right shaft upright, right elbow bent, left hand still down.','Right shoulder raises polearm, small knee readiness.','pole_up','pole','down','relaxed','Chest front, no large crouch.','Both shoes near original stance.','Helmet faces target, chin neutral.','Blade high outside right shoulder, left not gripping yet.',(0,0,8,8,-.005)),
   ('rotate and invite second grip','Shaft diagonal high at right; blade edge narrow/foreshortened, left hand reaches front.','Right forearm rolls shaft while left elbow brings palm toward lower grip.','pole_high','pole','pole_second','relaxed','Modest shoulder counterturn, pelvis quiet.','Both supports; soft knees.','Gaze ahead, helmet clear of blade.','Thin blade projection needs axial roll/depth; blade geometry must remain fixed.',(2,10,10,10,-.005)),
   ('two-hand raised ready','Broad blade above/right side; right grip high, left hand visibly at lower shaft across front.','Right shoulder sets high arc, left palm closes to guide same rigid shaft.','pole_high','pole','pole_second','pole_second','Ribs slightly turned right, left clavicle forward.','Both feet support; minor opposing hip yaw.','Head forward, no neck twist compensating wrong arm reach.','Right upper and left lower grip stations separated; blade rolls broadside.',(3,12,12,12,-.01)),
   ('diagonal downstroke','Blade passes down at image left, right hand pushes across, left pulls lower shaft near left hip.','Proximal right-shoulder descent plus left-elbow pull accelerate polearm head.','pole_down','pole','pole_pull','pole_second','Small forward/left rib turn, pelvis counterbalances; native trunk motion modest.','Both supports with small sole pivot inferred; no added large step.','Eyes toward swing, helmet pitch slightly down.','Shaft diagonal across torso, both grips constrain identical rigid object.',(8,-10,15,15,-.015)),
   ('low passage/foreshortening','Both hands low near waist, blade becomes narrow, shaft projection short.','Arms decelerate sweep through low arc; forearm roll turns blade edge/depth.','waist_grip','pole','pole_pull','pole_second','Torso re-centers slightly, shoulders lowered.','Both feet support, knees relax.','Head front/down a little, follows force path.','Fit axial roll and toward/away depth; never shrink or delete blade.',(4,-5,10,10,-.005)),
   ('cross-chest recovery','Polearm lies across chest diagonally, left hand still at lower station; right forearm bent.','Right elbow folds upward; left guides shaft, then releases into standing carry after this anchor.','pole_recover','pole','pole_second','pole_second','Torso front, arms clear mail/coif.','Both shoes support, standing height returning.','Helmet/gaze front.','At 750 ms return to low one-handed carry; left grip-release curve is inferred.',(0,0,5,5,0))],
  'hit': [
   ('baseline reaction','Low right carry, left down, body near standing.','Start rib recoil without immediate weapon teleport.','pole_ready','pole','down','relaxed','Chest near upright, tiny preparatory recoil.','Both shoes support.','Helmet front.','Shaft begins rise from actual carry angle.',(-2,0,5,5,0)),
   ('open-left recoil','Right blade/shaft rises diagonally; left hand opens low/front, head starts up.','Ribcage recoils, right shoulder lifts weapon away, left opens to balance.','pole_up','pole','side_open','open_front','Short backward tilt, pelvis stabilizes.','Knees soften; no recovered heel-lift timing.','Chin/helmet lifts slightly.','Blade outside right shoulder, right grip persistent.',(-8,0,10,10,-.005)),
   ('head back/palm out','Head/chest lean back, left palm out at chest, right weapon high to side.','Upper-trunk recoil extends neck slightly while free arm catches balance.','out_high','pole','out_high','open_front','Back tilt moderate, no stretched abdomen.','Both supports provisionally retained; hip shift small.','Helmet pitches back, eye opening upward.','Weapon vertical/diagonal outside body, no accidental left grip.',(-15,0,12,12,-.005)),
   ('left hand overhead','Maximum recoil, left palm above head, right shaft upright at side.','Left shoulder elevates from balance reaction; ribs/head reach backward extreme.','pole_up','pole','overhead','open_front','Back tilt peaks; pelvis stays below support.','Soft knees, choose smallest contact change compatible with silhouette.','Helmet back, nasal bar remains rigid to skull.','Left fingers up/fanned, no sword/weapon in left hand.',(-20,0,15,15,-.01)),
   ('recover left reach','Head front again, left arm forward near shoulder level, right shaft drops diagonally.','Trunk recovers first; left arm descends through forward reach rather than straight teleport.','pole_ready','pole','out_high','open_down','Back tilt reduces, shoulders descend.','Both feet support, knees extend gently.','Helmet/gaze front.','Right blade/shaft rotates low with same grip; left palm rotates downward.',(-5,0,8,8,-.005)),
   ('carry restoration','Both arms low, helmet front, weapon near low carry.','Shoulders settle after trunk recovery.','pole_ready','pole','down','relaxed','Upright, no residual body bounce required.','Both supports relaxed.','Head front.','Return to standing low shaft at 750 ms.',(0,0,5,5,0))],
  'death': [
   ('face reaction','Left palm near face, right shaft up with edge-on blade; body near upright.','Head/rib recoil and protective left hand lift.','pole_up','pole','open_guard','face_guard','Small back tilt.','Both feet support briefly, knees loosen.','Chin lifts behind left palm.','Right blade edge-on projection, not a different pole.',(-5,0,10,10,-.01)),
   ('cover face/back sway','Left hand covers face, right weapon upright/out; knees soften.','Ribs recoil while left elbow maintains face guard.','pole_up','pole','open_guard','face_guard','Back sway with minor side yaw.','Both feet support but knees buckling.','Helmet tilted away from hand, no palm clipping nasal bar.','Shaft stays outside right side.',(-15,5,20,20,-.03)),
   ('balance failure','Left palm rises beside head, torso/head back, right hand/weapon out.','Whole-body back tilt leaves support; left arm opens upward.','side_open','pole','overhead','open_front','Root backward tilt increases; local spine small.','Knees start deeper buckle, feet may pivot/release.','Head follows fall, coif bends only at neck.','Weapon remains in right grip, no planted staff assumption.',(-30,8,35,35,-.10)),
   ('backward drop','Body low/back, knees strongly bent, left hand above head, right shaft toward floor.','Root descends/rotates; knees fold, arms lag upward/out.','corpse_out','pole','overhead','open_front','Whole trunk tilts back/side, pelvis drops.','Knees flex, soles/feet may roll; neither both feet fixed.','Helmet/head follows body, chin position partly occluded.','Right shaft approaches floor outside legs; collision checks required.',(-55,10,85,85,-.27)),
   ('curled floor arrival','Body low on side/back, legs drawn, left hand still up; right weapon out on floor.','Hip/back floor contact halts fall; left arm and knees lag.','corpse_out','pole','fall_spread','open_front','Root low, side/back orientation; full supine direction not certain.','Back/side/hip floor support, knees strongly flexed.','Helmet beside torso, neck clear under coif.','Weapon low/outside body, fixed right grip or collision-fitted contact.',(-80,20,110,110,-.40))],
  'corpse': [
   ('held curled remains','Separate guadthf0 is curled on side/back, arm/shaft stretches out on floor, knees drawn.','None after final settling; held remains.','corpse_out','pole','corpse_out','open_down','Match side/back silhouette; exact belly orientation occluded.','Side/back/hips floor supports, feet tucked by bent knees.','Helmet at native side of body, coif/neck not merged with chest.','Polearm lies along floor outside corpse, shaft/blade unchanged.',(-85,25,115,115,-.42))],
  'fidget': [
   ('low carry start','Blade broad/low at right, left arm down; torso/feet near standing.','Small right-wrist/forearm repositioning, not body attack.','pole_ready','pole','down','relaxed','Torso quiet, belt height fixed.','Both feet held.','Helmet forward.','Shaft low/diagonal across hip; right grip fixed.',(0,0,5,5,0)),
   ('roll shaft','Shaft end points down toward image left, blade narrows at waist, body unchanged.','Right forearm rolls and elbow adjusts slightly, blade projection changes.','waist_grip','pole','down','relaxed','Ribs/pelvis quiet.','Both feet held, no gait shift.','Helmet front, tiny glance only if needed to fit pixels.','Shaft tilts, blade edge-on inferred; no blade morph.',(0,0,5,5,0)),
   ('near-horizontal adjustment','Blade head small/foreshortened at right waist, shaft low, left still down.','Right grip rotation continues, elbow brings shaft nearer carry.','pole_ready','pole','down','relaxed','Torso held, shoulders minimally move.','Both feet held.','Head quiet.','Horizontal/depth angle fitted with same long shaft.',(0,0,5,5,0)),
   ('reverse toward carry','Low blade/shaft returns; left hand starts toward waist.','Right forearm reverses roll; left elbow bends slightly as secondary response.','pole_ready','pole','forward_low','relaxed','Torso held; no whole-body oscillation.','Both feet held.','Helmet front.','Blade broadens again; left near-contact not confirmed grip.',(0,0,5,5,0)),
   ('free-hand approach','Left hand approaches shaft near belt, right blade broad at low side.','Left shoulder/elbow reach in response to right adjustment.','waist_grip','pole','pole_second','relaxed','Ribs quiet, belt height fixed.','Both feet held.','Head tiny downward glance only if native fit requires.','Left hand may touch/hover; do not assert firm two-hand grip.',(0,0,5,5,0)),
   ('release/loop carry','Low right carry returns, left hand lowers, body close to first frame.','Left arm releases, right grip settles into loop seam.','pole_ready','pole','forward_low','relaxed','Torso held.','Both feet held.','Helmet front.','Blend to start carry at 750 ms without changing grip station.',(0,0,5,5,0))],
 }
}

WALK_PHASES = [
 ('incoming first foot','Front shows incoming shoe/sole and opposite trailing foot; profile separates stride depth.',
  'Pelvis progression and incoming hip swing lead; opposite arm balances.','First leg reaches forward; heel/flat-foot contact WINDOW, not proven exact plant; other leg trails/toe-off.',(15,25,-.01)),
 ('first support/passing','Feet approach passing alignment; profile trailing heel lifted.',
  'First support leg accepts weight; opposite hip begins forward swing.','First foot supports, opposite heel lifts/pass begins; support assignment fitted across all views.',(8,40,.005)),
 ('opposite knee lift','Opposite knee/shoe forward/up, support leg straighter; profile confirms bent swing leg.',
  'Swing hip/knee flex lifts foot; pelvis modestly rises over support.','First supports; opposite knee bends and shoe clears floor; do not plant lifted foot.',(8,60,.005)),
 ('opposite incoming foot','Opposite leg forward/sole showing; first leg trailing in profile.',
  'Opposite hip completes swing, pelvis advances, arms reverse continuously.','Opposite incoming heel/flat-foot contact WINDOW; first toe-off/trailing, avoid long double-foot pins.',(25,15,-.01)),
 ('opposite support/passing','Feet close again, trailing first heel raised; body crosses support.',
  'Opposite support accepts weight; first hip swings forward.','Opposite supports; first begins swing, lifted heel/toe-off fitted to side/back views.',(40,8,.005)),
 ('first knee lift/loop prep','First leg lifted/bent, opposite support; profile resolves swing shoe behind/under knee.',
  'First hip/knee flex and forward swing prepare next contact, opposite arm travels forward.','Opposite supports, first foot clears; through final 125 ms extend toward first incoming contact without foot slide.',(60,8,.005)),
]


def walk(family):
    first='left' if family in ['pfem','gua'] else 'right'
    other='right' if first=='left' else 'left'
    # Right/left arm codes keyed to each source, not phase copied from a generic gait.
    codes={
      'pmn2': [('staff_back','forward_low'),('staff_ready','down'),('staff_front','back'),
               ('staff_front','back'),('staff_ready','down'),('staff_back','forward_low')],
      'pman': [('back','forward_low'),('down','down'),('forward_low','back'),
               ('forward_low','back'),('down','down'),('back','forward_low')],
      'pfem': [('forward_low','back'),('down','down'),('back','forward_low'),
               ('back','forward_low'),('down','down'),('forward_low','back')],
      'gua': [('pole_front','back'),('pole_front','down'),('waist_grip','forward_low'),
              ('pole_ready','forward_low'),('pole_ready','forward_low'),('pole_ready','down')]}
    props={
      'pmn2':['Staff hand trails waist, shaft sweeps back in right profile.',
              'Staff hand rises, lower shaft slants back in profile.',
              'Staff nearly upright ahead, right elbow opens and hand reaches chest height.',
              'Staff still ahead but slopes forward; grip height starts lowering.',
              'Staff approaches upright/carry, right elbow folds.',
              'Staff retracts/back, shaft tip sweeps behind; no repetitive cane plant.'],
      'gua':['Blade forward/up in profile (~25–40° upward projected shaft); right hand ahead.',
             'Blade still forward/up, right hand remains near waist-front.',
             'Blade/shaft lowers toward near-horizontal; right elbow softens.',
             'Shaft near horizontal through low hip, blade ahead/down.',
             'Blade slopes down/front, shaft rear end rises; right forearm roll keeps grip.',
             'Shaft near horizontal again, ready to lift through loop seam.']}
    result=[]
    for i,(phase,evidence,driver,support,seed) in enumerate(WALK_PHASES):
        k1,k2,bob=seed; kr,kl=(k2,k1) if first=='left' else (k1,k2)
        r,l=codes[family][i]
        skirt=(' Skirt hides knee centers; shoe visibility and genuine profile hem guide inference, not measured knee coordinates.' if family=='pfem' else '')
        body='Pelvis yaw about ±4–8° with step, ribcage counters slightly; restrained forward lean and bob, no torso scaling.'
        prop=props[family][i] if family in props else 'No knife; hands empty. Short arm swing opposes leg phase.'
        result.append((phase,evidence+skirt,driver,r,'staff' if family=='pmn2' else 'pole' if family=='gua' else 'relaxed',
                       l,'loose_fist' if family=='pmn2' else 'relaxed',body,
                       support.replace('First',first.title()).replace('first',first).replace('opposite',other).replace('Opposite',other.title())+skirt,
                       'Head looks along travel, small pitch compensation; crown bob follows pelvis rather than separate head bounce.',
                       prop,(3,[-5,-2,5,5,2,-5][i],kr,kl,bob)))
    return result


def small_fidget(family):
    rest=NOTES[family]['standing'][0]
    phases=['rest hold','duplicate rest hold','small face/head change','held face variation','return expression','loop rest']
    result=[]
    for i,phase in enumerate(phases):
        evidence=('Playback repeats fia0 at 0 and 125 ms; fib0 is unused artwork.' if i<2 else
                  'Small native head/face silhouette change; arms, belt, feet and clothing remain almost identical to rest.')
        head='Fit actual crown/eyes/beard/nape pixels; allow only a small ~0–5° head turn/tilt as inference, not a large look-around. Jaw/expression movement is unresolved.'
        result.append((phase,evidence,'Only subtle head/face variation; no hand gesture or mandatory breathing.',
                       *rest[3:7],rest[7],rest[8],head,rest[10],rest[11]))
    return result


for _family in NOTES:
    NOTES[_family]['walk']=walk(_family)
    if _family!='gua':
        NOTES[_family]['fidget']=small_fidget(_family)

CURVES = {
 'standing': 'Hold indefinitely. Do not turn a single native pose into an invented breathing or weight-shift cycle.',
 'walk': 'Continuous periodic spline/quaternion motion; no easing to a stop at every 125 ms anchor. Contacts are windows: fit heel-to-flat then toe-off from genuine profile/back views, use fixed-length chains. Match opposing arms/shaft, modest pelvis bob and root speed to stride. Inspect 62.5 ms midpoints and 687.5/750 ms loop seam.',
 'attack': 'Preparatory a→b is slower; b→c accelerates toward reach/overhead lift; c→d and d→e form the continuous fastest passage, with no stop at d. e→f decelerates/retracts; final f→standing interval restores rest. Review 187.5, 312.5, 437.5 and 687.5 ms subkeys. These are proposed checks, not recovered impacts; no damage-event time is inferred.',
 'hit': 'Start recoil promptly, peak body/guard deformation in b→d, then recover through remaining anchors. Preserve order of torso/legs/arms and avoid sinusoidal symmetric recoil. Review every 62.5 ms midpoint, facial/hand clearance and final standing boundary.',
 'death': 'Collapse accelerates as support fails; root translation/rotation and knee fold carry motion, never squash/scale the actor. Floor arrival decelerates, limbs/cloth settle. Review 187.5, 312.5, 437.5, 562.5 and 625 ms. The final 125 ms must connect death e to the separate corpse, using explicitly inferred collision-free root roll and arm arcs.',
 'corpse': 'Hold indefinitely at native remains. No twitch, breathing, fading, extra blood or disappearance has source evidence here.',
 'fidget': 'Preserve repeated-pose holds exactly; subtle changes can interpolate, but do not manufacture six independent gestures. Guard shaft/hand roll is continuous and subdued. Match 750 ms loop seam and keep support/whole-body pose stable.',
}

FAMILY_CHECKS = {
 'pmn2': ['Keep right staff grip in every state; compare shaft direction/ends across all five genuine walk views.',
          'Overhead c/d left-hand support is ambiguous: choose collision-free palm contact/hover from projected fingers and record choice.',
          'Beard, mantle and bracers clear forehead/shaft during overhead passage; free left palm opens in b/e.',
          'Hit lifts left knee; do not force both feet to ground. Death ends supine, staff low at side.'],
 'pman': ['Knife grip exists only in attack; compare shoulder-height cross-body reach, blade edge roll and free left guard.',
          'Hit has FIVE entries and returns to standing at 625 ms; unused wif0 must not become a sixth key.',
          'Deep hit guard: right forearm above brows, left open palm near face, right knee outward without leg stretch.',
          'Death is a side fall; separate corpse is prone. Explicitly fit the 500–625 ms transition instead of replacing death e.'],
 'pfem': ['Walk starts LEFT incoming foot, then RIGHT at d; visible shoes/profile hem guide hidden leg fitting.',
          'Folded hands in standing/fidget remain two separate palms; knife only in attack, left never confidently grips it.',
          'Abdominal hit uses right arm across body and left elbow out/wrist hanging; do not copy male face guard.',
          'Kneeling death and prone corpse need two hidden legs plus hollow skirt; contacts/knees are low-confidence inference.'],
 'gua': ['The weapon is a HALBERD, never a sword/shield. Side view establishes full shaft length.',
         'Walk starts LEFT incoming foot (frontal image right), with RIGHT incoming at d; c raises right shoe, f raises left. Confirm against all genuine views.',
         'Attack b/e narrow blade projection is orientation/foreshortening; retain rigid blade and continuous forearm roll.',
         'Left hand closes lower shaft during attack c–f, then releases into right-only carry; finite grip separation mandatory.',
         'Hit left palm rises above helmet; death is backward buckle into curled side/back remains, not peasant prone fall.'],
}
