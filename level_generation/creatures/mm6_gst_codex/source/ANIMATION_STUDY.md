# MM6 Ghost: native appearance and motion

Authority: source/native_inventory.json, preserved original frames in ../mm6_gst/native/, and the native reference sheets copied into source/. Descriptors 547/548/549 are BGhost A/B/C, displayed as Ghost / Evil Spirit / Specter. They fly and use melee Dark damage; no projectile or spell is defined. No weapon or other held equipment is required.

Appearance: tall narrow hooded skull, tarnished tan bones, two small glowing eyes, thin skeletal forearms/hands, white-grey coarse shroud, dark sleeveless tabard in front and back. Five digits per hand are the anatomical interpretation of native bony fingers. No visible legs or feet. Palette742 has violet-charcoal cloth and green eyes;743 navy and blue;744 maroon and red. White cloth/bones do not change. Hidden torso and garment backs are inferred from the five stored fly views; other actions reuse front view. Generated details clarify material only.

Native timing: each fly/attack/hit has six2-tick frames, total12/16=0.75s. Death has five2-tick frames (0.625s) then a held cloth-and-skull heap. Standing, walking and fidget all alias the fly loop. Views0–4 are genuinely stored for fly;5–7 mirror. Attack,hit,death reuse their frontal frames around the actor.

Motion selection before modelling: review/source_motion_sheet.jpg compares owned UnarmedCastRAOE1,UnarmedCastRAttack2,UnarmedGetHitF2 on the source mannequin, front/side. The two casts crouch/raise overhead or thrust; neither matches the native lateral right-hand swipe, so author that action from native observations. Retain the upper-body recoil of GetHitF2 (0.5s) with a relaxed approach/recovery inside0.75s. No animation purchase. Source frames, rest matrices and rotation extremes are retained under work/.

Standing/fly: gently bob the whole figure; hands droop at waist level in front of the sleeve edge, forearms angle slightly forward. Shroud trails behind with restrained lag. Walking/Run keep this floating silhouette with more trailing sway, no invented steps. Fidget is a slightly more visible head/hand/cloth variation on the same suspended pose.

Attack observed phases: a starts from idle with right palm turned forward; b raises that hand up/out to the creature right while the left arm crosses toward the chest and the body leans back; c is the open-handed raised wind-up; d extends the right arm outward at shoulder height; e sweeps that hand across the front toward creature left while cloth follows; f relaxes toward idle. Proposed 1.15s presentation: ready0, raise0.18–0.40, shoulder-height out0.55, fastest cross-front sweep near0.75, recover0.9–1.15. Right-hand path must remain in front of the chest and sleeve. Left hand counterbalances, torso sway delivers the swipe; no reach behind the shroud. Actual impact will be measured from the authored hand velocity and checked in playback.

Hit: native recoils with body/head tipping and hands spreading; adapt the short owned GetHitF2 upper body to suspension, without grounded boxer legs.

Death: native arms turn up/out, body arches, cloth billows wide, then skull and hands drop as robe collapses to a small broad heap. Author a smooth1.6–2.0s fall and hold exactly its final pose in Dead; do not substitute a walking-human prone corpse or disappearance. Cloth chains require floor and stretch checks during collapse. No feet to expose.

Verification: arm/hand continuity at60Hz and half-frames, sleeve/hand/body clearance, rigid skull/phalanges, cloth stretch/hem motion and floor, loop joins, Blender/GLB parity, actual viewer normal/slow playback, separate skull/hands close-ups, all palette variants and native indoor/outdoor comparisons. Source maxima are diagnostic ROM, not permission for implausible custom motion.
