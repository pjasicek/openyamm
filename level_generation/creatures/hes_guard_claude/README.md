# Hesper Landfall Guard: three ranks — Claude humanoid project

> **Reduced (2026-10-22):** [`../hes_guard_reduce_claude/`](../hes_guard_reduce_claude/README.md) has the triangle-reduced export (LOD0 8,559 -> 7,189, far LODs rebuilt, rifle attachments unchanged, no retexture); exported, not installed. This project's exports are unchanged.

Landfall's town guard ([concept](../../../design/kreegan_world/concepts/people/landfall_guard.png), approved
2026-10-22), monsters 10067 Landfall Guard / 10068 Guard Sergeant / 10069 Warden's Guard
(`design/kreegan_world/data/make_monster_tables.py`). Humanoid playbook default route; templates `mm7_m475_claude/`
(prop attachment, robe chains) and the humanoid set's **2Hand Shooting** clips for the two-handed rifle.
**Exported, not installed** (the Hesper stage integrates it). Meshy: **30 of 60 credits** (Smart Topology 5, auto-rig 5
for joint estimates, body retexture 10, head retexture 10). User artistic acceptance is not recorded.

[Review viewer](review/viewer/index.html) (serve the creatures folder over http) · [ranks](review/tiers_abc.jpg) ·
[viewer shots](review/shots/) · [clay clips](review/clay_v5.jpg) · [G1 candidates](review/g1_candidates.jpg),
[deaths](review/g1_deaths.jpg) · [rifle](review/rifle_tq.png) · [gates](review/gates_v5.json) ·
[HD masters](references_hd/selected_views_review.png) · [head masters](references_head/selected_views_review.png)

## Deliverables

| File | What |
|---|---|
| `export/hes_guard.glb` | body: one skinned mesh `HGD`, body + head sets merged (2080×1024 atlases), LODs **8,559** / 4,278 / 1,540 / 510 triangles + shadow LODs, 3 variants `guard_a/b/c`, clips Standing, Walking, Running, Attack, Hit, Death, Dead, Fidget; bones `Rifle`, `RifleGlow` (right hand), `Socket_Muzzle`, `Socket_Palm_L/R` |
| `export/hes_guard_rifle.glb` | rifle attachment on node `Rifle` (758 / 378 / 134 / 35 tris), white ceramic and gold |
| `export/hes_guard_rifle_glow.glb` | the rifle's emitter tip and power-cell windows on node `RifleGlow` (48 tris), emissive (0.55, 0.8, 1.0) |
| `export/hes_guard_lod0.glb`, `work/rig_v6.blend` | portable LOD0 (rifle joined), textured editable master; `work/rig_v5.blend` = the gated chain |
| `textures/` | body and head 1K sets, `hgd_region_mask.png` + `hgd_ramps.json`, material class maps, rifle maps (`hgd_rifle_*`, from `textures/props/rifle.png`) |
| `integration/actors.yml` | staged binding (skins, scale 105.86, strides, muzzle event, both rifle attachments) |

Install later (parent), from the repository root, into the Hesper stage's model set (not `assets_dev`):
`tools/install_model.py export/hes_guard.glb`, `export/hes_guard_rifle.glb`, `export/hes_guard_rifle_glow.glb`
with the Hesper world target, then the `integration/actors.yml` entries for the three descriptors.

## Ranks (one mesh, region mask + ramps)

| Skin | Monster | Coat and trousers (R) | Tabard (G) | Gold trim (B) |
|---|---|---|---|---|
| guard_a | 10067 Landfall Guard | slate blue (the texture) | town red (the texture) | as painted (no ramp) |
| guard_b | 10068 Guard Sergeant | dark slate grey-green | town red | as painted (no ramp) |
| guard_c | 10069 Warden's Guard | deep navy | white | bright gold |

`scripts/compose_hgd.py`: R = blue cloth texels, G = red cloth texels, B = gold texels further than 7 texels from the
tabard (its gold glyph and hem border keep their gold on every rank); the ceramic, gloves, belt, emitter and skin are
in no region; every channel feathered (1.5 texels) and padded into the gutters. Ramps fitted with
`region_variants.fit_ramps` (A to the texture itself: coat mean 2.5 / tabard 1.1 8-bit levels). Gold's hue varies with
its shading, which a luminance ramp misses (p95 18 levels), so ranks A and B carry no third ramp: the loader ignores a
trailing channel without one and their gold stays exactly as painted. The head set has no regions (shared by all).
Material classes: skin, hair, eye, cloth, metal (gold) and **11 = glazed Ancient ceramic** (plates, helmet, emitter
housing; specular 0.5, roughness 0.4). ORM R = specular mask.

## Model, rig and weights

- HD masters (Codex) from the approved concept sheet (no native sprite exists): primary after one correction; run 2
  stopped on a Codex capacity error after its first returns (front, back, rifle kept); the side views were redone as
  strict profiles (Claude selected `03_left_run3b`, a strict profile Codex had rejected); head turnaround.
- Smart Topology 27 parts, 15.5k tris (`creature.json` lists them): legs with fused shin plates, torso shell (coat,
  chest plate, tabard, belt), two arms with guards and fists, head, helmet, shoulder and knee plates, emitter, pouches.
- Joints: Meshy auto-rig + arm rings (wrist = narrowest ring in 70–90 % of the arm: arm, guards and fist are one piece)
  + **`leg_rings.py`** (Meshy's knees sat 11 cm in front of the leg, drawn by the knee plates).
- Rig: source-frame rig (52 bones + 4 twist + 48 skirt chain bones), the rigid fists continuing the forearm
  (`HAND_FROM_FOREARM`); grip tunnels of both fists measured on the mesh (`grip_from_fist.py`).
- Weights (`weights_robe.py`): skirt (tabard and coat below 0.93 m) on 12 × 4 chains, simulated per clip
  (`robe_sim.py`); belt fittings rigid on the pelvis, chest rivets on B_Spine2; **shoulder and knee plates as uniform
  pieces** (every vertex the piece's mean weights: they move without bending); hand fade 5 cm (2.5 cm sheared the
  wrist band). Reduced after weighting to 10,700, LOD0 to 8,559 (`halve_lod0.py RATIO=0.8`, face blocked).

## Rifle

`rifle_fit.py`: the rifle is held as a **pistol grip** in the right fist: origin = the right fist's grip tunnel, Z =
the tunnel axis toward the thumb (up the grip to the bore), Y = the hand's axis made perpendicular (the barrel along
the knuckles), X = the gun's right side; the handguard (left fist) at Y 0.35, Z 0.064. `make_rifle.py` builds the
reference silhouette (1.0 m, 806 tris: extruded stock and receiver, a 12-sided handguard where the left fist closes,
front body, gas tube, barrel, three cooling rings, collar, emitter tip, power-cell windows on both sides, non-raked
pistol grip with its UVs sheared onto the reference's raked grip, trigger guard, scope), planar side projection of
`references_hd/rifle.png`. The reference's vertical fore-grip and lower rail sit where the left hand holds the
handguard and are left out.

**Orientation (user review 2026-10-22, "wrong rotation of the gun, like 90 degrees off").** The first version fitted
the rifle to the set's right hand, whose finger curl runs sideways across the body (the set's right hand does not hold
a pistol grip), and turned our fist onto that axis: the rifle was rolled 90° about its barrel (the grip sideways into
the body, the cell window up, the stock flat). Now `rifle_drive.py` drives the rifle per frame from the source pose and
the right hand from the rifle: the barrel through both fists' places (the right -> left line turned down onto the
handguard), the up axis = world up made perpendicular to the barrel (roll 0), the barrel pitch within ±30°, the right
hand = that frame × the pistol hold, the arm by armik; in the Death the wrist stays rigid from the release on.
`rifle_up_check.py` (`review/rifle_up.json`): rifle up axis to world up ≤ 10° in the Attack's aim (limit 20), ≤ 30° in
every held frame of Standing, Walking, Running, Hit and Fidget (limit 35), roll 0°. Before/after:
[clay](review/rifle_roll/before_sheet.jpg) → [clay, six clips × front/left/right/above](review/rifle_roll/after_sheet.jpg),
[viewer](review/rifle_roll/before_after_viewer.jpg).

## Clips (G1 on this body: `review/g1_candidates.jpg`, `review/g1_deaths.jpg`)

| Clip | Source |
|---|---|
| Standing 0.8 s | set 2Hand Shooting Idle (low ready, the barrel 20° down), feet levelled |
| Walking 0.8 s | set 2Hand Shooting Walk (stride 1.438 m) |
| Running 0.8 s | set 2Hand Shooting Run Forward (stride 3.119 m; a sprint, flights up to 30 cm) |
| Attack 1.1 s | 0.30 s raise from Standing into the set's shouldered FireRifle1, feet pinned; **impact 0.367 s** = recoil onset (`clip_timing_hgd.py`), the shot from `Socket_Muzzle` |
| Hit 0.5 s | set 2Hand Shooting GetHit F1, eased, feet pinned (the source hopped 18 cm and slid 41 cm) |
| Death 3.43 s / Dead | Mixamo Death From The Front (doubles over, kneels, folds face down, the rifle under him), travel halved, `death_floor.py` (raised 5.2 cm while falling, lowered 19.9 cm once down: lowest point 0.0 cm) |
| Fidget 2.07 s | raises the rifle and sights along it (set IdleAlt, twice), lowers it |

Every held clip keeps the left fist on the handguard (`support_hand.py`: target on the handguard axis, sliding within
0.31–0.38 m, tunnel axis turned onto the barrel, armik minimal change; 0 mm residual in every held clip); the death
lets go where the source hand leaves the gun. `rifle_clear.py` moves the rifle (right hand) forward out of the
armoured chest, which is deeper than the source mannequin's (aim 5.0 → 0 cm, fidget 2.9 → 0). Rejected: the set's
rifle-butt Attack1 (wrists 99° / 138° on this hold: `attack_melee` plays Attack), its ReloadRifle (the free left hand
7 cm through the chest plate), Death1Rifle (a forward dive with the legs in the air).

## Gates (`review/gates_v5.json`, `review/rifle_up.json`, final reduced mesh, every half frame)

- Arm stretch p99 ≤ 1.90 in every clip (Standing 1.41, Walking 1.63, Running 1.60, Attack 1.90, Hit 1.58, Fidget
  1.80, Death 1.88); max ≤ 3.6 except **Death left arm 5.28** (one lying frame, 48).
- Hands rigid (1.00); wrist swing ≤ 53° in every clip (Standing 11, Walking 34, Running 44, Attack 47, Hit 46, Fidget
  52, Death 49); hand in body 0 except the Death's free left hand 4 cm (frame 48, lying).
- Rifle and right fist in the torso 0 cm (`rifle_clear.py`); the left fist on the handguard, 0 mm residual.
- Rifle up axis: aim ≤ 10°, carry ≤ 30°, roll 0° (limits 20 / 35).
- Skirt chains p99 ≤ 1.65 (Death 1.44); soles: planted clips −0.1 cm, walk −1.9…+0.6 cm; Death on the floor.
- `check_winding.py`: 0 inverted closed parts (body, rifle, rifle glow). Viewer check 24/24 rank/clip switches, no
  console errors. Not checked in game (no engine work in this task).

## For the user / the parent to review

- **Run threshold**: at scale 105.86 the engine plays `run` above 254 units/s; the table's speed 250 stays below it,
  so the guard walks (at about 1.3× the walk's natural 1.8 m/s). Raise the speed or accept the walk.
- **Melee**: no separate butt-stroke clip (see above).
- **Emissive**: the glow attachment relies on the model renderer's constant emissive factor; creatures do not bloom
  yet (`engine/render/MODEL_RENDERING.md`), so the tip and windows read as bright paint, not glow. Engine need only.
- **Shield**: the personal energy shell is an engine effect (not modelled); the belt emitter is in the mesh.
- One lying frame's left-arm stretch (5.3) and the free left hand under the body (4 cm) come from the Mixamo death.

## Replay

Claim the project, then `TOK=<lease> scripts/rebuild.sh rig` and `... anim`, texture chain once (`export_uploads.py`,
Meshy `requests/retexture_v1.json` and `head_retexture_v1.json`, `transfer_uv.py` (UVMap, then HeadUV),
`uv_raster.py` ×2, `bake_ao_natm.py`, `compose_hgd.py`), then `TOK=<lease> scripts/build_runtime.sh`,
`viewer_tiers.py`, `update_viewer_manifest.py`. `scripts/step.sh <script> [args]` runs one Blender step under the lease.

## Corpse floor fix (2026-10-22, clips only)

The Death end and Dead lay the corpse 35 cm above the floor (engine evaluation, `claude_shared/floor/glb_pose.py`):
`death_floor.py` counted the rifle (rigid in the right fist, pointing straight down) and the coat skirt chains (hanging
straight down under the lying body) as the floor contact. Fixed on `export/hes_guard.glb` with the scripts of
[`../hes_guard_reduce_claude/`](../hes_guard_reduce_claude/README.md) (the same operation as its export, so both
exports carry identical clips): `ground_body.py` (body without the skirt onto the floor, root keys on a 1/120 s grid),
`claude_shared/floor/floor_fix.py --lift-joints Death Dead --lift-only 'Robe_*' --ground-death Death Dead` (skirt
strips bent onto the floor), `death_rifle_floor.py` (the rifle eased from the fist onto the floor, lying on its side,
from 1.05 s over 0.4 s). Death and Dead now rest on the floor (lowest point -0.1 cm; the body lies 2.8 cm up on the
coat); every other clip is unchanged. Pre-fix export: `work/floor_fix_base/hes_guard.glb`. Only animation samplers
changed; `hes_guard_lod0.glb`, the viewer GLBs and the `.blend` masters predate the fix: rerun the three steps after
any re-export (`build_runtime.sh` does not include them). Before/after: `../hes_guard_reduce_claude/review/floor/before_after.png`.
