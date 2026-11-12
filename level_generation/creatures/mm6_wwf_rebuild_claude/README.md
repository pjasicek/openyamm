# MM6 Wolfman / Werewolf / Greater Werewolf: full rebuild (rebuild stream, 2026-11-11)

Audit fix ([audit](../audit_mm678_20261111/README.md), brief [REBUILD.md](../audit_mm678_20261111/fixes/REBUILD.md)
row 7), agent `rebuild-2`. The installed model (`mm6_wfigt1_claude`, reduced in `mm6_wwf_reduce_claude`, gait clips from
`gait_rollout_20261031/h02`) was a Meshy auto-rig with rigid open claws, "placeholder quality", and bodybuilder
proportions bulkier than the sprite. Replaced as a whole. Meshy credits **20** (Smart Topology 5, auto-rig for joint
estimates 5, 4K body retexture 10).

## Route: MM9 BIGFOOT skeleton and clips (Yrsa route)

- **New HD masters** (`references_hd/`, Codex, `CODEX_BRIEF.md` = the 2026-10-09 brief with the build changed to the
  sprites' LEAN, wiry, long-limbed wolf-man and knee-length shorts; inputs: the native five-view sheet and native frames).
  Gate: identity, palette, pose, true alpha; the front paws show three toes (accepted). Hashes in `creature_3d_progress.json`.
- **Body**: Meshy Smart Topology (14k) from `00_three_quarter.png`. Meshy invented a **tail** behind the shorts (as for
  the 2026-10 model): `scripts/cut_tail.py` removes it (284 faces) and fills the seat before anything else.
- **Fit / weights / fingers / UVs**: the lizardman rebuild's scripts generalised (`fit_wwf.py`, `rig_wwf.py`: no neck
  joint, toe joints; `fingers_wwf.py`: thumb + four fingers by connectivity, chains `Finger0..4` x3 driven by MM9's
  bigfoot `Finger0`/`Finger1` curl through `finger_alias`), joint estimates from a Meshy auto-rig of our body, reduction
  after weighting (head 0.7, hands 0.7, body 0.6) -> 8,956 triangles, `uv_atlas.py` (fast packer) atlas 58.7 %.
- **Paint** (`compose_wwf.py`): 4K retexture with the four masters, 2K once, gentle grade with AO; classes shorts, gem,
  gold, ivory, fur; MR red specular mask. **Tiers** (`ramps_wwf.py`): shorts by luminance rank from the native palettes
  831/832/833 for all three tiers (rust / navy / red; a paint-fitted A came out light tan and B lavender), gem A as painted,
  B/C from the native palettes. Skins `wwf_a/b/c`.
- **Clips** (`clips_mm9.py`, `roles_wwf.json`, MM9 `BIGFOOT.abc`): Standing `stand` 2.2 s, Walking `walk` (legs x1.65, x1.3
  speed), Running `run` (legs x1.5, x1.35), Sprint `run` (legs x1.8, x1.6), Fidget `fidget1` 4.87 s, Attack `Hattack1`
  0.97 s (two-armed overhead claw rake, contact 0.456 s), Hit `wince1` 0-0.9 s at x1.2 (0.73 s, the native 0.75), Death
  `die1` 1.8 s, Dead. `hand_rest.py` pushes the hands out of the body in Fidget and Attack. The werewolf moves fast
  (wander 2.2, chase 4.4 model units/s), hence the leg gains.
- **Runtime**: `TOKEN=<lease> BLEND=work/uv_v1.blend scripts/build_runtime.sh [--install]` (export, clips, material,
  prepare, LODs, shadow tuck, variants, far LODs r25_12, hand rest, floor fix `floor_ops.txt`, winding).

## Binding

`assets_dev/worlds/mm6/models/actors.yml` Werewolf A/B/C: scale 139.462 (native 221 units / 1.5847 m Standing),
strides walk 1.666, run 1.905, sprint 2.551 (`gait_gate.py` PASSED: Standard wander x0.90-1.05, chase x1.20-1.41, MAW
chase x1.10-1.16), Attack for melee/ranged/cast with impact 0.456 s, look `Bip01 Spine3`/`Bip01 Head`, upper body
`Bip01 Spine2`. The regression `mm6_werewolf_actor_model_tiers_share_the_native_height` needs no change and passes.

## Checks (installed 2026-11-11)

| Check | Before | After |
|---|---|---|
| LOD triangles | 6,489 / 3,108 / 1,622 / 811 | 8,956 / 4,414 / 2,221 / 1,104 |
| Rig | Meshy auto-rig + jaw, rigid open claws | MM9 BIGFOOT 27 joints + 26 finger joints, 4 influences |
| `texture_quality.py` | atlas 34.0 %, fragments 17.2 %, density p50 524, stretch p90 2.27 | atlas 58.6 %, fragments 9.6 % (mane strands), p50 1,083, stretch 1.11 |
| Attack motion ratio (`rebuild_measure.py`) | 0.91 | **0.99** |
| Worst region beyond Standing | Hit spine 18.5 % | Attack arm 9.2 % (all clips under 12 %) |
| Hand inside the body, worst | 0 | Attack 6.9 % (3.5 cm into the shorts at 0.57 s, after hand_rest) |
| Floor audit, gait gate, winding | ok / - / 0 | ok / PASSED / 0 |
| `mm6_werewolf_...`, `mm6_mm7_mm8_actor_models_build_every_binding` | pass | pass |
| Viewer check | | 54 switches, 0 console errors |

Sheets (viewer shots, identical cameras): `review/sheet_tiers.png` (A/B/C front, three-quarter, head, attack contact),
`review/sheet_a_all.png` (tier A: body views, head, hands, attack wind-up and contact, walk, hit, corpse). Flat strips
`review/v2_sheet.png`, `review/gait_walk.png`. In game (New Sorpigal, Agar's Laboratory; the three tiers fighting):
`review/ingame/ingame_sheet.png`.

Open: the claws rake through the front of the shorts for a few frames of the Attack (3.5 cm); fragments 9.6 % from the
mane and fur strands (cards are small pieces); the chest fur paints lighter (ash grey) than the sprites' charcoal; front
paws have three toes; no head-only paint (budget).

Revert: `python3 tools/install_model.py level_generation/creatures/mm6_wwf_rebuild_claude/work/before_rebuild/mm6_wwf.glb --world mm6`
and restore the three Werewolf bindings from `work/before_rebuild/actors_mm6.yml`.

## Follow-up 2026-11-11: fur tone and claws past the shorts (agent `followup-wwf-ttn`)

The rebuild's sheet showed the body fur light grey with a fine crosshatch that read as chainmail (native sprites and the
pre-rebuild model: dark grey-black fur), and the Attack's claws raked 3.5 cm into the shorts. No geometry change, no
Meshy credits (0).

- **Cause of the pale chainmail**: the 4K paint's chest/shoulder/back ruff is a net of bright strands over dark gaps;
  `compose_wwf.py` classed the bright strands as `ivory` (low saturation, bright), so they also carried the claws'
  specular 0.9 in game.
- **`followup/fur_tone.py`** (run once on compose_wwf.py's outputs; originals kept as
  `work/before_followup/wwf_{basecolor,metal_rough,classes}_rebuild.png`): fur texels only (class fur plus the
  torso's ivory strands, |x| < 0.4 m, z < 0.17 m, so the teeth and claws stay ivory; no region weight, so the tier
  ramps are untouched), per UV chart: (1) the crosshatch is damped where the local detail RMS is high (torso to 0.2,
  limbs 0.45, head kept); (2) the large-scale tone per height band goes to the native sprite fur median (palette 831,
  walk and fight frames, `followup/tone_stats.py`) x 1.1, the pale charts compressed toward it ((L/median)^0.35-0.5);
  the head band only darkens and keeps its spread; (3) fine detail rides on top as a ratio, highlights eased off the
  head. The ruff strands' specular mask 0.9 -> 0.35 (fur) and the class map follow.
- **Claws**: `hand_rest.py` on the Attack with max push 0.07 -> 0.14 m, hold 0.04 -> 0.08 s, sigma 0.06 -> 0.05 s
  (`scripts/build_runtime.sh`): the arms swing ~12 cm wider for 0.1 s round 0.56 s, so the claws pass beside the hips.
- Rebuilt with `scripts/build_runtime.sh` (LOD2/3 re-baked from the new LOD0 colour), installed 2026-11-11 22:09.

| Check | Before follow-up | After |
|---|---|---|
| Fur luminance p50/p90 (sRGB) legs / chest / shoulders / head | 44/84, 43/92, 45/146 (p99 241), 28/74 | 27/37, 39/52, 50/77 (p99 93), 28/73 |
| Native sprite fur x1.1 (target), same bands | 26/37, 37/73, 54/109, 37/54 | |
| Rendered viewer front, shoulders band p50/p90 | 132/196 | 69/130 (native front frames 74-82/107-115) |
| Fine-detail RMS / mean: head, torso, limbs | 0.49, 0.55, 0.43-0.45 | 0.49, 0.24, 0.21-0.23 (head kept, crosshatch damped) |
| `glb_diff.py` vs installed | | only the 6 Attack arm channels and the base colour / metal-rough images (LOD0, LOD2, LOD3); every LOD's geometry, skin, normals, mask, normal map, ramps identical |
| Attack hand inside (motion_audit) | 6.9 % (3.5 cm at 0.57 s) | **0** |
| arm_hand_gate Attack, worst hand depth | L 5.9 / R 5.8 cm at frame 27 | L 1.3 / R 0.9 cm (one frame over 1 cm) |
| Attack motion ratio (`rebuild_measure.py`), worst region | 0.99, arm 11.3 % | 0.99, arm 10.8 % |
| texture_quality, winding, floor (Werewolf*) | 58.6 % atlas, 0, ok | unchanged, 0, ok |
| `mm6_mm7_mm8_actor_models_build_every_binding`, `mm6_werewolf_...` | pass | pass (647 descriptors, 0 failed) |
| viewer check (`followup/viewer_manifest.py export/mm6_wwf.glb fu cur`) | | 54 switches, 0 console errors |

Sheets (viewer shots, identical cameras): `review/followup/sheet_followup_tiers.png` (A/B/C before|after: front,
three-quarter, back, head front and three-quarter, Attack at 0.5625 s), `review/followup/sheet_followup_a.png`
(pre-rebuild | rebuild | follow-up), `review/followup/attack_claws_before_after.png` (flat, 0.50-0.60 s),
`review/followup/native_frames_831.png` (the native reference). Note: the rebuild's own `review/sheet_tiers.png` was
shot from a stale viewer GLB (tan shorts); the installed shorts were already rust (A).

Still open: a faint net remains on the chest ruff at close range; the head mane keeps its light grey streaks (head left
as painted); Fidget's right hand still reads up to 5 cm into the thigh in `arm_hand_gate` (installed, not in scope).

Revert: `python3 tools/install_model.py level_generation/creatures/mm6_wwf_rebuild_claude/work/before_followup/mm6_wwf.glb --world mm6`
(actors.yml unchanged; to rebuild the old textures, copy `work/before_followup/wwf_*_rebuild.png` back to
`textures/wwf_*.png` and restore the old Attack hand_rest line in `scripts/build_runtime.sh`).
