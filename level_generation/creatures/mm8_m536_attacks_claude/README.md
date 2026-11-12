# MM8 Efreeti (m536): attack from an MM9 donor (attacks stream, 2026-11-11)

Part 4 of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/ANIM.md). The `Attack` (local Unarmed library
two-hand cast, motion ratio 0.41 against the audit's "other" bodies, 1.5 s, impact 1.16) is replaced in place by a
clip retargeted from **MM9 BANSHEE `AttackRanged2`** (tools as the [Warlock pilot](../mm7_m426_attacks_claude/README.md);
`job_attack.json`, no Blender). Cast is unchanged.

## Intent

Native `m537a` (8 frames x 125 ms, contact frame 4 = 0.5 s; strip `review/native_attack.png`, built from the archived
BMPs in `assets_legacy/sprites_mm8_monsters_20261019/`): both arms are thrown up high in a burst of sparks, then the
whole body lunges forward driving both hands at the target with the flame tail swinging back, and recovers. The
Banshee (also legless) raises both arms, then lunges forward with the arms thrust out.

## Settings

- The Banshee has its own rig: `XCENTER`, `Xspine/1/2`, `Xneck`, `Xhead`, and per side `Zarmbase` (clavicle),
  `Zarmpiv` (upper arm), `Zarm` (forearm), `Zhand` (`…01` = right), mapped by hand (`map` in the job).
- Travel goes to `BodyRoot` (new `travel_node`), which also carries the flame vortex, so body and tail stay joined;
  horizontal travel x1.3, vertical x0.1 (the Banshee's dip at our 1.7x size dropped the body 33 cm and crushed the
  tail 21 cm under the floor). Vortex_00–07 simulated as a chain from `BodyRoot` (`work/vortex_chain.json`, h11 numpy
  sim toward Standing, leg capsules filtered out), `hem_floor` 1 cm.
- Arms follow the donor's world bone directions for the whole clip (`arm_direction`): the clip starts and ends
  open-armed like the previous attack (the runtime crossfades from the crossed-arm idle); copied rotation changes
  from the crossed idle put the hands over the face.
- Timing 1.15 s (donor 1.0 s), release 0.444 s mapped to 0.5 s; measured `Socket_Palm_Right` at 95 % of its travel
  0.583 s (native 0.5 s, +17 %).

## Results (installed 2026-11-11)

| | Before | After |
|---|---|---|
| Motion ratio ("other" reference) | 0.41 | **0.77** |
| p90 reach / moving share / peak speed | 0.117 / 0.419 / 2.43 | 0.225 / 0.960 / 3.71 |
| Deformation beyond Standing (worst) | arm 2.9 | spine 4.7 |
| Wrist swing / twist | | L 57°/26°, R 58°/32° |
| Hand in body | R 1.8 cm at frame 0 | 0 |
| Floor (flier) | tail tip -14 cm accepted | lowest +1.8 cm |

Bindings (Efreeti A/B/C): `events.attack_melee.impact` and `attack_ranged.impact` 1.162 -> 0.583 (glow, colour and
release unchanged). Checks (`review/finish.txt`): winding 0, glb_diff only the Attack channels, floor audit 0
problems, every-binding regression PASS, viewer no console errors. Shots: `review/attack_viewer_sheet.png`.
Rollback: `work/before_attacks/`. Credits: 0.
