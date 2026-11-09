# MM8 Dragon Turtle — native study and production decisions

Native sources and hashes: `references/native_inventory.json`. Evidence: native anatomy and all action strips in `references/`. Descriptor 136–138 / palettes 581–583 / sprite aliases m581–m583 reference m580 bitmaps. The original gameplay height is 400, radius 80, movement speed 200; preserve these. Native frame scale is 4.0. Native views 0–4 are observations; 5–7 mirror 3–1 and do not supply new anatomy. The bottom-center canvas anchor is not a visible floor.

## Anatomy and reference pose

Broad domed oval green/ochre carapace with strong tan seams, swept dorsal spines and a pale underside. The shell is a single rigid volume. Long grey/olive neck, flattened blunt dragon muzzle, yellow eyes, swept paired horns and pale cheek plates. Two large tapering front paddles, two smaller rear steering flippers, thin central tail. No hands, feet, wings, weapon or other equipment. Front flippers have leathery membranes and pale branching support ribs. Palette variants alter the shell; protect skin, horns, eyes and flippers. B is darker teal, C ochre/olive; use native ACT differences rather than invented whole-body hue shifts.

Neutral modeling pose: horizontal glide, neck gently extended, four flippers spread with clear gaps, tail separated, jaw slightly parted. View unseen construction is inferred; preserve observed proportions and silhouette. Shell spine count obscured in views: use the three prominent swept ridge peaks visible in side view, no decorative additional rows. Interior mouth and underside topology are inferred.

## Rig and motion

Dedicated local rig: root plus rigid shell/body driver; neck chain, head, lower jaw; root and distal flex controls for each of four flippers; tail chain. Shell and shell spikes receive only the shell transform. Blend soft joints locally; protect head horns and upper jaw from lower-jaw motion. No humanoid rig/library action matches this anatomy. Snake contributes only neck-chain/bite principles, not topology, poses or timings.

| Role | Native source / duration | Driver and phases | Validation |
|---|---|---|---|
| Swim / idle | wa–wh, 8 × .125 = 1 s, loop | Front paddles extend, power-stroke down/back, turn edge-on, recover forward. Rear flippers steer with reduced delayed stroke. Shell has small pitch/heave; neck and tail lag. Idle uses restrained swim, locomotion full stroke. | Front/profile paddles remain distinct; dense loop seam and no shell deformation. |
| Bite | aa–af, 6 × .125 = .75 s | 0 neutral; .125 shell pitches up with neck raised, front paddles brace; .250 jaw opens and neck coils; .375 body drives forward/down and neck extends, jaw closes; .500 follow-through; .625–.750 recover. Contact near .375–.438, finalize from exported mouth trajectory. | Profile jaw hinge; no skull collapse; front shows symmetrical bracing; body, neck and jaw contribute in sequence. |
| Hit | na–nf, 6 × .125 = .75 s | Neutral; .125 recoil starts; .250 strongest nose-up shell pitch and raised neck; .375–.625 lower and recover. Flippers flare then settle, tail lags. | Shell remains rigid; head/flippers clear shell through maximum recoil. |
| Death | na,nb,nc,da,db, 5 × .125 = .625 s | Recoil rises into nose-up whole-body pitch, then rolls onto side/back. Flippers lose stroke and trail. Endpoint matches xa corpse: rolled rigid shell, slack lateral neck and flippers. | Held corpse and death last pose agree; no endless sinking or cycling. |
| Corpse | xa, .125 s hold | Same settled terminal death pose. | Stable endpoint and full visible anatomy. |
| Fidget | fa–fd, 4 × .125 = .5 s | Small neck/head extension and glance, restrained continuous paddles, recover to glide. | No abrupt stop at each source key; head/horn clearance. |

All times above are native holds, not recovered continuous 3D motion. Continuous acceleration, depth, distal flex and secondary lag are restrained inferences. Rig probes: jaw open with skull fixed, neck raised/extended, both front paddles at power/recovery extrema, rear flipper steering, tail sweep, shell roll into corpse. Check evaluated geometry in front/side/rear and normal/half-speed playback, then exported GLB. No ground-leg walking or invented casting action. Standing and movement share native swim group; clips may share source rhythm with distinct amplitude.

## Production reach

Five generated HD masters → Smart Topology body → dedicated rig and all native roles → Meshy PBR texture → shared base/normal/MR/region maps and three native palette tiers → four LODs → exported browser playback → source installation/cooking, actor bindings, focused regression and native outdoor/indoor captures. Preserve prior 2D restoration and unrelated creatures. Meshy budget 100 credits; no equipment jobs. User art acceptance remains separate from agent validation.

Production timing refinement: the MM8 runtime applies melee damage at the native action end (.75s). The 3D Bite therefore has a .75s windup/closure plus .35s recovery (1.10s total), avoiding a 2× slowed windup from marking the native .375s illustrated contact. Death settles over .875s; runtime finishes it before corpse hold. Swim, hit and fidget retain native durations. These are presentation adaptations, not changes to native gameplay or claims of recovered continuous motion.

## Final reviewed reconstruction

The initial 112-degree death roll was rejected after textured playback: it perched on an extended flipper.
The selected death rolls 28 degrees, folds the paddles and lowers to a side rest; Dead is its exact terminal pose.
The native corpse is dark and low, so the side rest retains the visible shell rather than exposing an upright belly.
Eight-frame area calibration gives scale 662.31; installed 650 differs by only 3.68% in mean area.
