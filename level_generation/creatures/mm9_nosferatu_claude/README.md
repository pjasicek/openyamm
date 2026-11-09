# MM9 Nosferatu body (mm9_nosferatu) — 3D actor, 2026-10-31

MM9 `NOSFERATU.abc` (47 joints, 17 clips, visible mesh `Sphere05b` 570 triangles): rows 195 Bloodsucker L20 (`MM9 Nosferatu A`, NOSFERATU1), 196 Annelid L33 (`B`, NOSFERATU2), 197 Vampir L48 (`C`, NOSFERATU3). Inventory: 47 placed, on 17 maps.
Humanoid: built on the approved route (MM9 skeleton, MM9 clips, separate head set, five-finger hands from the mesh). Progress and receipts: `creature_3d_progress.json`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_nosferatu.glb` (`tools/install_model.py --world mm9`), variants `nos_a/b/c` |
| Binding | `assets_dev/worlds/mm9/models/actors.yml`, `MM9 Nosferatu A/B/C`, scale 100, `yaw_offset` -1.570796327, stride walk 1.8 / run 1.87 (planted foot), melee impact 0.333 s (`Hattack1` Rattack), ranged and cast impact 0.666 s released at `LHand1` (MM9's RangeAttack node, true left hand), look `Bip01 Neck, Head`, upper body `Bip01 Spine1` |
| Triangles LOD0/1/2/3 | 12,529 / 6,262 / 2,474 / 1,527; LOD0: robe 2,160 + lining 660, torso 1,098, sleeves 968 + lining 352, hands 1,498, head 4,300, teeth 96, eyes 158, plug 100, collar lining, trims, belt, clasp, pendant, wrist tubes about 1,140 |
| Skeleton | 110 joints: MM9's 47 renamed `vampiresB` -> `Bip01` (every shared gate expects it), + 10 third finger joints (`Finger02` .. `Finger42`), 5 half-rotation helpers (`Xhalf*`), 48 robe lattice bones (`XRobe<col>_<row>`) |
| Clips (30 fps) | Standing `stand`, Walking `walk`, Running `Run`, Fidget `fidget1`, AttackMelee `Hattack1`, AttackRanged `RAttack1`, Hit `wince1`, Death `die1`, Dead; script clips Fidget2, Taunt, ResurrectSpell, Resurrect, Hit2, Death2 `die2`, Backpedal, BackpedalRun |
| Textures | body 2K colour + 1K normal + 1K ORM + 1K region mask; head 1K colour + normal + ORM + mask. One set for all tiers, ramps only, no per-tier image |
| Meshy credits | **20 / 40**: body Smart Topology 5, head-only Smart Topology 5, body retexture 10 (backup account, no retries). Head paint by Codex projection, free |
| Viewer | http://127.0.0.1:8912/level_generation/creatures/mm9_nosferatu_claude/review/viewer/ revision r12, tiers `nos_a`, `nos_b`, `nos_c` |

## Route (`scripts/`)
0. **Sources**: `convert_sources.sh`: `convert_abc_model.py --scale 0.0256` per skin, `mirror_glb.py` (the exact conjugation, not `mirror_source.py`), `rename_bones.py`. `bone_length_audit.py` gives 0 stretching on the source and on every build. `Bip01 L Hand` at x +0.119 on a figure facing +Z in glTF: the anatomical left.
1. **What the model is**: only `Sphere05b` is the design. The other 45 pieces (`vampiresB *`, 8 to 84 faces) are the biped's boxes with every UV at (0, 0), so the pose catalogue's lumpy render is not the look. Masters are made from `Sphere05b` alone (`ref_piece.py`).
2. **Masters** (Codex): `references_hd/` five views of tier B (gold braid and red cloth segment by hue) in a symmetric A pose; `references_head/00_geometry.png` a clay head sculpt; `references_paint/` our exact clay painted; `references_head/b_*` the head clay painted.
3. **Meshy**: body Smart Topology gave clean separate parts, fingers apart with claws, a two-walled robe with slits, legs and feet inside. Head-only gave an excellent snarl, ears, and 26 bead teeth.
4. **`assemble.py`**: the robe and sleeves are rebuilt as regular grids r(azimuth, height) sampled from Meshy's outer wall (mirror symmetric, no slits, no doubled wall), hem narrowed to MM9's width with a train at the back; linings; torso, trims, hands mirrored from the left half; head mirrored, the far side decimated first; teeth rebuilt as sharp cones on Meshy's sites of the two real rows (the third row lay on the chin); dark mouth plug.
5. **Rig**: `fit_rig.py` (trunk and legs take MM9's bone lengths exactly, so MM9's root translations are used absolute; arm 0.538 m against MM9 0.537), `weights.py` (by part, no heat), `build_glb.py` (bind = the A pose; bind frames in the Mummy way, with the spine turned by the shoulder line because MM9's torso is yawed 30 deg in its bind, arms by axis and the sleeve's low side, fingers from MM9's Standing pose so no twist hides in their root).
6. **Robe**: `robe_keys.py`: 12 columns x 4 rows of lattice bones. Each point is carried by MM9's Pelvis, Thigh, Calf, Foot, Tail, Tail1 with weights by height and azimuth (any number of drivers; a vertex then needs only four influences), the displacement field smoothed along columns and rings, a hard floor, a minimum column spacing, the bell settling when the body lies down, hem frames kept level. Keys are rewritten after the floor pass.
7. **UVs**: `uv_nos.py` (body, frozen: the paint belongs to it), `uv_head2.py` (head only, free to redo since its paint is a projection).
8. **Paint**: Meshy retexture at 4K on `texturing/nos_body_upload_v1.glb`. Head: `head_clay.py`, `project_head.py` (face from the front view alone).
9. **Textures**: `compose_nos.py`, `finish_nos.py` (grade, AO, linings' texel, plain dark shoes were painted then dropped), `tier_ramps.py`.
10. **Runtime** `rebuild.sh [--install]`: clips, `half_keys.py`, `finger_keys.py` (MM9's two finger joints shared over our three), `robe_keys.py`, `arm_bump.py`, prepare, LODs, shadow fix, ramps, floor, robe keys again, sockets. `bind_actors.py` under the flock.

Rebuild: `python3 scripts/tweak_mesh.py; python3 scripts/finish_nos.py; python3 scripts/tier_ramps.py; scripts/rebuild.sh --install; scripts/viewer_update.sh <rev>; scripts/gates.sh; scripts/final_shots.sh`. Claim a lease first and put its token in `scripts/env.sh`. **Never re-run `uv_nos.py`.**

## Tiers
One paint, one mask each for body and head, ramps fitted to MM9's own texels of each tier: body R robe (and centre panel), G linen, B skin, A cord; head R skin, G eyes, B gums. Belt, clasp, gem and claws are as painted in every tier, as in MM9's skins.
The robe's texels in the base image are neutral grey at their own luminance, so a mask's soft edge at a chart border cannot leak red into A or C. The robe's ramp is one smooth curve: MM9's few dark levels posterised the damask.
Gains over MM9's texels, all because MM9's are very dark or its renders flatter than the viewer's light: skin 0.62, cord 0.62, linen 0.7, robe 1.25 / 1.35 / 1.5.

## Checks (final GLB, revision r12)
| Gate | Result |
|---|---|
| Thighs through cloth | None exist. MM9's robe has no legs, so ours has none: **Walking and Running 0 by construction** |
| `cloth_gate.py` (48 fps, every clip) | **hands through the robe 0, sleeves through the robe 0 in every clip**. Lining past the robe wall: 0 in all standing clips; Death 38/97 2.9 cm, Death2 62/73 8.0 cm, Dead 49/49 2.3 cm, Resurrect 23/77 15.6 cm: the inner wall where the robe lies flat on the floor, from inside the tube |
| Collapse `collapse_gate.py` (all LOD0 primitives) | table below; not zero |
| Arm and hand `arm_hand_gate.py --outer-only --exact` | 0 frames over 1 cm in Standing, Walking, Running, Backpedal, BackpedalRun, AttackMelee, Hit, Hit2, Death, Death2, Dead, Fidget2. **Over: Fidget L 1.2 cm 7 frames, Taunt L 1.4 cm 6, AttackRanged and ResurrectSpell L 2.1 cm 3, R forearm 4.9 cm (the hands meet: hand against the other sleeve, wider than MM9's)**. Resurrect (script) L 2.3 cm 50, R 2.9 cm 47, not corrected. First rig: AttackRanged L 5.8 cm, R 4.0 cm. Finger stretch p99 1.82, max 4.57 (first rig 12.6). 15 finger bones per side |
| `jitter_gate.py` against the untouched clips | **0 fails** |
| Head orientation against MM9 (`orient_gate.py`) | bound clips mean under 3.7 deg, max 20.4 (Hit, the ease from Standing), Standing 0.1 |
| Mouth | MM9 has no jaw bone: `cheek_gate.py`, face edge change over all clips **0.0 %** |
| Handedness | true: `RangeAttack` = MM9 node `L Hand`, our `LHand1` on the anatomical left; `Bip01 L Hand` at +x on a figure facing +Z |
| `bone_length_audit.py` | 0 stretching, source and final |
| `detached_parts_audit.py` (24 fps) | 44 components, **0 detached** |
| `flat_shading_check.py` | 0.02 body, 0.00 head |
| `check_winding.py` | 0 inverted closed parts |
| `texture_quality.py` | body atlas 62.1 %, fragments 0.0 %, stretch p90 1.06, spread n/a (linings have zero UV area by design); head atlas 55.1 %, spread 1.8 (face 1.45x by design), fragments 2.8 %, stretch 1.46 |
| `floor_audit.py --world mm9` | 3 ok: stand, walk, living +0.6, dead 0 |
| Regression `mm9_actor_models_build_every_binding` | PASS: 125 descriptors on 52 models, 0 failed; MM6-MM8 647 on 185, 0 failed |
| `run_creature_review.py check` | 51 switches, 0 failed, 0 console errors |
| In game (`bootcamp.odm`, review root, isolated) | `review/ingame_sheet.png`: three tiers friendly and hostile, attack, cast glow, hit, all with their own tier |

**Collapse, worst single frame per clip and region** (`review/gates/collapse.txt`, 30 fps; seen = faces any camera can see at the clip's worst frame):

| Clip | face-frames | shoulder L/R | elbow L/R | wrist L/R | finger | groin/torso | neck/head | robe | seen |
|---|---|---|---|---|---|---|---|---|---|
| Standing | 615 | 0/0 | 0/0 | 3/3 | 8 | 0/0 | 0/1 | 0 | 11 |
| Walking | 1189 | 4/0 | 0/0 | 3/3 | 13 | 0/1 | 1/3 | 27 | 34 |
| Running | 636 | 4/0 | 0/0 | 3/3 | 13 | 0/1 | 1/3 | 26 | 31 |
| Backpedal | 1279 | 5/0 | 0/0 | 3/3 | 13 | 0/1 | 1/3 | 36 | 40 |
| BackpedalRun | 694 | 5/0 | 0/0 | 3/3 | 13 | 0/1 | 1/3 | 36 | 39 |
| Fidget | 906 | 0/0 | 5/0 | 3/3 | 8 | 0/0 | 1/4 | 0 | 18 |
| Fidget2 | 1371 | 0/0 | 0/0 | 3/3 | 8 | 0/2 | 6/7 | 0 | 15 |
| Taunt | 608 | 0/0 | 5/0 | 3/3 | 8 | 0/0 | 1/4 | 0 | 19 |
| AttackMelee | 761 | 19/19 | 0/0 | 3/3 | 8 | 0/9 | 4/6 | 4 | 24 |
| AttackRanged | 2049 | 25/25 | 0/0 | 3/3 | 17 | 0/16 | 21/1 | 0 | 48 |
| ResurrectSpell | 2049 | 25/25 | 0/0 | 3/3 | 17 | 0/16 | 21/1 | 0 | 48 |
| Hit | 467 | 14/11 | 0/0 | 3/3 | 8 | 0/5 | 7/7 | 0 | 15 |
| Hit2 | 445 | 3/9 | 0/0 | 3/3 | 8 | 0/20 | 0/1 | 0 | 21 |
| Death | 5363 | 28/20 | 0/0 | 5/3 | 8 | 8/14 | 1/4 | 146 | 93 |
| Death2 | 5915 | 4/4 | 0/0 | 3/3 | 8 | 8/22 | 44/5 | 182 | 101 |
| Resurrect | 3960 | 0/0 | 2/0 | 4/3 | 10 | 0/10 | 0/1 | 283 | 246 |
| Dead | 5456 | 7/10 | 0/0 | 5/3 | 8 | 0/0 | 0/2 | 141 | 93 |

First rig for comparison: Walking 2047 face-frames, robe 48; AttackRanged 4094, shoulder 41/39, neck 59 (302 once the head primitive was counted); Hit neck 185.
Where they are: **robe outer wall 0 bad faces in Walking and Running**; those clips' `robe` count is all the flat cap inside the tube (27 of 51 at the worst frame, seen only up the hem). Dead and Death: 59 outer robe faces flattened against the floor, 82 lining. Shoulder up to 25 in AttackRanged, 22 exposed: the sleeve root and vest corner under arms raised overhead, where MM9's clavicle lifts 40 deg. Neck 44 in Death2 (script clip). Wrist 3-5 and finger 8-17: the thumb's web.

Sheets (viewer shots, `review/`): `mm9_vs_ours.png` (MM9 and ours, every tier, three views; MM9 is a Blender render of `Sphere05b`), `mm9_vs_ours_clips.png`, `sheet_heads.png`, `sheet_closeups_a.png`, `_b`, `_c` (knees, groin, armpits, elbows, neck, mouth, in crouch, run, fidget, death, dead), `strip_a.png`, `_b`, `_c` (all 17 clips, seven frames each), `ingame_sheet.png`. Knees and groin are robe on this body: the close-ups frame the cloth over them. Numbers: `review/gates/`. Playback: `review/playback/`, 34 clip runs at normal and half speed on r10 (textures only changed after it).

## Decisions and deviations
- **Humanoid**: Bip biped with five real two-bone fingers, so the humanoid route. No jaw bone, so no clip opens the mouth: the snarl is fixed, the face is rigid on `Bip01 Head`, teeth are rigid, a dark plug closes the skull behind them. Edge change on the face over all clips: 0 %.
- **Claws kept**: Meshy's long thin fingers from the mesh, 15 bones per side (MM9's 10 + third joints). The first knuckle takes MM9's curl but not its fan (30 deg of spread tore the webs of these long fingers); the thumb tip takes 45 % of MM9's 89 deg curl for the same reason (finger stretch max 12.6 -> 4.6). The tips and claws keep MM9's direction otherwise.
- **No legs, no feet**: MM9's `Sphere05b` has none, and ours went through the cloth in Walking (13.9 cm) whatever the hem did. The legs' bones stay to drive the robe. From below, the robe shows a dark lining and a dark cap at 0.6 m. This is the reason the cloth gate is clean by construction for legs; it measures hands, sleeves and lining instead.
- **Sleeve shoulder to elbow (r16)**: `scripts/tuck_sleeves.py` redraws it on the same grid as a straight tube from under the yoke corner, as in MM9, with its front behind the chest plate's slope; the old top stood 4.7 cm outside the yoke as an open ring with a puff below it (user feedback, 2026-10-31). Run it after `finish_nos.py`.
- **Sleeves**: wider and softer at the shoulder than MM9's boxy sleeve, from the masters. Cuffs narrowed twice to about MM9's 20 cm, and they do not hang: rigid on the forearm, as in MM9.
- **Skin alpha**: all opaque, `Transparent 0` on these rows, no fullbrite, no animated skin.
- **FX**: `DoFX` on RAttack1 and ResurrectSpell uses FX1 `greenyeldots`, FX0 `bluedots`: not wired, as on the other bodies; a generic glow at the palms. `ResurrectFX GreaterDemon` not wired.
- **Corpse**: the floor pass raises it 12.7 cm: the back of the vest and the head rest on the floor with the robe settled over nothing.

## Open points
- Gates still over: collapse is not zero (table above); AttackRanged and ResurrectSpell L hand 2.1 cm 3 frames, R forearm 4.9 cm where the hands meet; Fidget L 1.2 cm 7 frames, Taunt L 1.4 cm 6 frames. These are after a second and third pass; a larger bump would change the gesture more (AttackRanged is already moved up to 27 deg at the wrist, jitter 0 fails).
- Faint star of creases on top of the skull when seen from about 50 cm straight on (`sheet_closeups_a.png`, cr7): the decimated dome. Seam relief in the normal map is gone, this part remains.
- A small bump of the neck shows on the collar's front under the chin (st0, st1).
- A few orange flecks of Meshy's stray gold beside the centre panel, inside the zone kept for cords (cr0, ra0, ra2). The size of a fingertip.
- Close to, in the dark robe tiers the damask's darkest band posterises a little (fi3); from game distance it reads as cloth.
- Tier C: MM9's trims are almost black; ours keep a faint sheen. Tier A and C robes are lighter than MM9's, tier A's skin too, as accepted on the Imp and Lich.
- Memory: 8.2 MB cooked GLB, all tiers on one set. Each actor animates 110 joints.

## Not checked
- Motion by eye: `review/playback/*.webm` exist; I cannot watch video: I read frames, strips and the jitter gate. Strips for all 17 clips read on all three tiers (r12 for B and C, A on r12 too).
- LOD1-3 and shadow meshes by eye.
- Any MM9 map: the in-game check is `bootcamp.odm`, outdoors. No indoor light, and I did not trace which maps place these rows (47 placements on 17 maps).
- Which script clips any behaviour plays: `baserange.scr` not traced beyond its includes; Fidget2, Taunt, Hit2, Death2, Resurrect, ResurrectSpell, Backpedal are bound as script clips only.
- The projectile leaving `LHand1` by eye, melee contact moment, sounds, footstep events.
- `greenyeldots`, `bluedots` and `ResurrectFX` are not wired (engine anchors missing, as on the other bodies).
- Robe lattice cost: 48 extra keyed joints per actor; not measured with many Nosferatu on screen. Cooked size noted above, no FPS run.
- Loop seams measured by jitter only.
- Android cook (only on request).

User artistic acceptance: "nosferatu OK" (2026-10-31)


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_nosferatu_reduce_claude/`** (user-approved; ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `mm9_nosferatu_reduce_claude/before/`.
