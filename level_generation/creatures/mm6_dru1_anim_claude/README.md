# MM6 Druidess (`dru1`): library Attack (punch, then the installed magic blast; installed 2026-10-14)

User: "attack - I want I think something from library instead, like can be boxing, one handed punch or whatever.
cast is fine now." Only the Attack clip changes; every other clip, the mesh and the textures stay as installed.
`../mm6_dru1_claude/` was only read; its scripts and non-blend work inputs (plus `rig_v2a.blend`, the Relax
retarget) were copied here.

## Choice

Candidates retargeted onto the rig, planted on Standing (`review/cand_three_quarter_sheet.png`, `cand_left_sheet.png`):

| candidate | reading |
|---|---|
| **Mixamo Punching (1)** (0.87 s) | **chosen**: upright, one straight right punch at shoulder height, left hand as a guard; no crouch, no combo |
| Mixamo Standing Melee Punch (1.0 s) | wide sideways swing with a near-straight arm; reads as a slap |
| Mixamo Punching (1.27 s) | boxing guard with both fists up and a short jab |
| Mixamo Uppercut (1.33 s) | big wind-up overhead; too long and flailing |
| humanoid set Unarmed Attack R1 / R3 (0.8 s) | big shoulder wind-up / forward lean with both arms wide |

## Chain (`scripts/rebuild_attack.sh`, about 2 min)

`rebuild.sh` from the Relax retarget on, with: Cast and Hit retargeted as before; Attack = `retarget_mixamo.py`
(`../mm6_bar1_claude/`) `Punching (1).fbx:Attack:plant`; the old Attack-only `arm_offset.py` dropped. Changes:
- `wrist_twist_limit.py` (new, after the retarget): the left guard hand pronated 118 deg against the forearm (the
  accepted druidess clips stay at or below 45 deg in the same trace); clamped to 20 deg about the forearm segment.
- `fingers_relax.py`: `FINGER_K_<ACTION>_L/_R`; the punch keeps the right fist (K 1.0), the left guard 0.45 (G5).
- `clip_timing_dru.py`: `ATTACK_RELEASE=reach` (furthest forward reach); Attack 0.30 s blends in/out of Standing.
- New exporter `export_clips.py` (runtime animation settings), `compare_clips.py`, `splice_attack.py`, `trace_attack.py`.

## Gates (final)

| gate | Attack |
|---|---|
| G4 stretch p99 / max | R 1.83 / 3.31 at full extension (straight arm; the old attack's apex was 2.0); L 1.67 / 2.92 |
| G5 hand stretch | R 2.46x, L 2.50x (limit 2.7x) |
| G6 contacts | 0 (no hand in head, hood, chest or cloak) |
| cloak gate | 0 vertex-frames through the cloth, widest opening 2.7 cm (chest, frame 13) |
| trace (48 fps, linear) | PASS: wrist gap <= 0.4 mm, wrist swing <= 17, wrist twist L 43 / R 22, forearm twist <= 42, hand turn <= 19 deg per half-frame |

Rebuild drift: Standing, Walking, Cast, Hit and Fidget reproduce the installed clips within 0.5 deg; Death's cloak
does not (24 deg, 35 mm), so only Attack is taken from this rebuild.

## Impact

The fist is at full reach from 0.333 to 0.417 s with the elbow straight at 0.367-0.375 s: **impact 0.367 s**
(clip 0.867 s). The installed 0.817 s lives in `assets_dev/worlds/mm6/models/actors.yml` (Druidess entries,
`events: attack_melee: {impact: 0.817}` and `attack_ranged: {impact: 0.817, launch_socket: Socket_Palm_Right}`);
not edited. `clip_timing_dru.py` printed 0.467 s for the reach frame, which disagrees with its own output master
(frame 11 = 0.367 s); use the measured value.

## Files

- `export/mm6_dru1_fel3r66_punch.glb`: the reduced 66 % pick with the new Attack. Build:
  `python3 scripts/splice_attack.py <runtime.glb> work/clips.glb <out.glb>` (only Attack replaced; meshes, skins,
  materials, variants and the other 7 clips verified byte-identical; static `Socket_Palm_*` keys kept over 0.867 s).
- Viewer (tiers a/b/c, new Attack; 24 loads, no errors):
  `http://127.0.0.1:8901/level_generation/creatures/mm6_dru1_anim_claude/review/viewer/index.html`
- Review: `review/attack_a_strip.png` (front / q34 / side every 2nd frame), `review/attack_closeups.png` (rows frames
  6, 11, 16 at 24 fps: right hand front/q34/side, face with the guard hand, shoulder).

Open: the fist stays a little loose (the index tip stands proud in the q34 view at the extension).

## Round 3 (user, 2026-10-14): a magic Attack instead of the punch

User: "her punch looks weak, like it is druidess, she is magic user". Her MM6 Attack 1 is an elemental missile from
the hand (Fire / Water / Earth by tier). Candidates (planted, `review/cand_magic_three_quarter_sheet.png`,
`cand_magic_left_sheet.png`): Mixamo Standing 1H Magic Attack 01-03, 2H Magic Attack 01/02/04/05, 2H Magic Area
Attack 01, Spell Cast. **Chosen: Standing 2H Magic Attack 01** (both arms swept up overhead, then a leaning two-palm
thrust: the hands travel 0.8 m in four frames). 1H 03 barely reaches forward, 2H 02 reads like Cast (palms forward
from the hip), 2H 04/05 and the area attack are 3 s or slam the floor, Spell Cast is a small gesture.

Chain: `rebuild_attack.sh` with `ATTACK_FBX="Standing 2H Magic Attack 01" ATTACK_SRC=8:60:1.3 ATTACK_RELEASE=R
FINGER_K_ATTACK_R=0.25 FINGER_K_ATTACK_L=0.25 TW_MAX=15 SW_MAX=38 WRIST_SIDES="L R"` (about 4 min), then
`export_clips.py` -> `work/clips_blast.glb` (the punch is kept as `work/clips_punch.glb`). New options:
`clip_timing_dru.py ATTACK_SRC=<first>:<last>:<speed>` (source frames 8-60 at 1.3x), `wrist_twist_limit.py SW_MAX`
(the push bent the palms back 56-65 deg and opened the wrist seam 6-8 mm; swing slerped back to 38 deg). Open hands
(finger K 0.25).

Gates: trace PASS (wrist gap L 2.4 / R 2.0 mm, twist 40.2 / 43.4, swing 31 / 26, hand turn <= 30 deg per half-frame);
G6 0 contacts; G5 R 2.08x, L 1.52x; G4 p99 <= 1.99 right, left clavicle 2.25 at the thrust (frame 24; old attack apex
2.0); cloak gate 37 vertex-frames through the cloth (Walking 24 as installed; the light notch at the cloak shoulder is
there in Standing too). Release = peak forward speed of the right hand after its highest point: **impact 0.65 s**
(11 m/s), clip 1.33 s. Strip: `review/blast_strip.png`.
