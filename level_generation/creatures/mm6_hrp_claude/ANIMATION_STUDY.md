# Native motion and rig plan
Sources: ../mm6_hrp/manifest.json, source/native_flight_contact.png and native_actions_contact.png.
48 distinct native images: 6 flight frames × 5 views, 6 attack, 6 hit, 6 death/remains.
Views 5/6/7 mirror 3/2/1. Actions use Image1 (front reused for all views).
Flight/standing/walk/fidget: 6 × 0.1875 = 1.125 s. Wings rise outward (a), pass level (b/c),
sweep down and feather tips angle back (d/e), fold upward (f). Body mostly upright with small
pitch/bob; legs dangle with bent knees. Rig requires independent wing root/elbow/tip plus feather
fan control and short tail. Keep actor origin low; no artificial permanent hover lift.
Attack: 1.125 s native. a hover, b knees spread/lift, c both feet forward claws open,
d draw feet back, e lower legs, f return. Arms balance asymmetrically; native is a TALON attack.
Author smooth phase-based airborne double kick using those observed anchors. Runtime impact
must land near native action end: add a ready beat before the fast claw release, mark release.
Hit: 1.125 s; one hand raises toward head, torso recoils, one knee draws up, then settle.
Death: five × .1875 = .9375 s native plus final held corpse frame. Recoil, backward/side roll,
one leg high, wings collapse, settle on side with claws extending and folded wings on body.
Cast: native Attack2 reuses attack image sequence. Tier C casts Mass Curse; author distinct Cast
clip using recoil/screech/head and hand release, keeping the same flight/wing rhythm.
Required exported roles: Standing,Walking,Running,Attack,Cast,Hit,Death,Dead,Fidget.
Local anim_library checked: Floating/Flying, Flying Bicycle Kick/Flying Back Death candidates exist;
humanoid-only motions lack wings and paired avian talon strike. Native procedural flyer route
chosen per non-humanoid playbook; no animation purchases needed.
Rig mesh-measured joints, connectivity-owned feathers/digits, inspect extremes and exports.
