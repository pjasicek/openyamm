# Hesper Ashrunners: three tiers — Claude humanoid project

Hesper's surface scavengers ([concept](../../../design/kreegan_world/concepts/monsters/fam_ashrunners.png), approved;
brief `design/kreegan_world/concepts/monsters/CODEX_BRIEF_ZONE1_FAMILIES.md` §4), monsters 10070 Ashrunner Scav (A),
10071 Ashrunner Raider (B), 10072 Ashrunner Gunner (C) (`design/kreegan_world/data/make_monster_tables.py`).
Humanoid playbook default route; templates `hes_guard_claude/` (two-handed rifle chain), `mm7_m475_claude/` (blaster
pistol chain, cape on robe chains), `hes_villager_f_claude/` (thigh panels, leg-leak and hand-proximity gates).
**Exported, not installed** (the Hesper stage integrates it). Meshy: **30 of 80 credits** (Smart Topology 5, auto-rig 5
for joint estimates, body retexture 10, head retexture 10). User approved the model; **polish round 2026-10-22**
(review notes: run speed, tier colours, goggles and hood lip, wrists, running leg leak) done without Meshy spend, see
[Polish round](#polish-round-2026-10-22); **second review round 2026-10-22** (blurry texture, the Scav's pistol read as
two-handed) also without Meshy spend, see [Packed UVs and the one-handed Scav](#packed-uvs-and-the-one-handed-scav-2026-10-22).

[Review viewer](review/viewer/index.html) (`http://127.0.0.1:8912/level_generation/creatures/hes_ashrunner_claude/review/viewer/`) ·
[tiers](review/tiers_contact.jpg) · clip sheets [A](review/clips_har_a.jpg) / [B](review/clips_har_b.jpg) /
[C](review/clips_har_c.jpg) · [close-ups](review/closeups.jpg) (gun hands, feet, back, corpse) · [props](review/props/) ·
[viewer shots](review/shots/) · [gates](review/gates_v5.txt), [hands](review/g6_hands_v5.json),
[legs](review/g6_legs_v5.json), [rifle up](review/rifle_up.json) · [HD masters](references_hd/selected_views_review.png) ·
[head masters](references_head/selected_views_review.png)

## Deliverables

| File | What |
|---|---|
| `export/hes_ashrunner.glb` | body: one skinned mesh `HAR`, body + head sets merged (atlas 3104 x 1024: 2048 x 1024 packed body page, 1K head), LODs **8,926** / 4,456 / 2,219 / 1,107 triangles (body; LOD2/3 and their shadows by `lodrep/`, own 512 / 256 px textures) + shadow LODs, 3 variants `har_a/b/c`, 126 joints; two clip sets (below); bones `Rifle`/`RifleGlow`/`Socket_Muzzle`, `Carbine`/`CarbineGlow`/`Socket_Muzzle_C`, `Pistol`/`PistolGlow`/`Socket_Muzzle_P` (all in the right fist, one shared hand frame), `ChestPlate` (B_Spine2), `Buckler`/`BucklerGlow` (B_L_Forearm), `Socket_Palm_L/R` |
| `export/hes_ashrunner_pistol.glb`, `_pistol_glow.glb` | tier A: the Ancient blaster pistol (364 tris) and its blue cell window (emissive) |
| `export/hes_ashrunner_rifle.glb`, `_rifle_glow.glb` | tier B: the Landfall guard's Ancient rifle mesh (758 tris, reference reused), scavenged texture (`weather_rifle.py`); blue emitter and cell windows |
| `export/hes_ashrunner_chest_plate.glb` | tier B: the salvage chest plate (404 tris) fitted to the chest by ray-cast |
| `export/hes_ashrunner_carbine.glb`, `_carbine_glow.glb` | tier C: the stolen Kreegan pulse carbine (506 tris), orange glow slots and emitter |
| `export/hes_ashrunner_buckler.glb`, `_buckler_glow.glb` | tier C: the buckler emitter on the left forearm (142 tris), orange rings |
| `export/hes_ashrunner_lod0.glb`, `export/hes_ashrunner.blend` | portable LOD0 (every prop joined), editable textured master; clip chain `work/rig_v5.blend`, textured master `work/rig_v6.blend` |
| `textures/` | body set 2048 x 1024 on the packed layout (file names keep `_1k`), head 1K set, `har_region_mask.png` / `har_head_region_mask.png` + `har_ramps.json`, material class maps, prop maps `har_<prop>_*` |
| `integration/actors.yml` | staged binding for the three descriptors (skins, per-tier clips, attachments, muzzle sockets, events) |

Install later (parent), from the repository root, into the Hesper stage's model set (not `assets_dev`):
`tools/install_model.py` each `export/hes_ashrunner*.glb` listed above with the Hesper world target, then the
`integration/actors.yml` entries.

## Tiers (one mesh, region mask + ramps; per-tier gear and grip)

| Skin | Monster | Cloak + hood (R) | Scarf + wraps (G) | Scrap plate (B) | Under-clothes (A) | Gear | Clips |
|---|---|---|---|---|---|---|---|
| har_a | 10070 Scav | ash grey (authored: Meshy painted it warm brown-grey) | rust orange (texture) | white ceramic (texture) | brown (texture) | blaster pistol, one hand | `P_*` |
| har_b | 10071 Raider | charcoal | red-brown (104, 54, 40) | scorched | dark grey-brown | blaster rifle + chest plate | plain |
| har_c | 10072 Gunner | sand | muted ochre (138, 94, 46) | sand-stained ivory | dusty brown | Kreegan carbine + buckler emitter | plain |

`scripts/compose_har.py`: classes per texel (eye, goggle brass and lens, skin = one albedo × Meshy's fine shading,
rust wraps by saturation and red-green separation (the browns stay leather), plate = white texels of the plate pieces
and the boots' shin plates, cloak = P01 and the hood's grey, under-clothes = tunic, trousers and the torso's cloth,
leather, metal canisters; on the head set Meshy painted most of the scarf grey, so the hood piece's front below the
eyes is the scarf by position, repainted rust with a soft 5 cm edge into the hood; the face's forehead 2-10 cm above
the eyes is skin: Meshy painted the goggles' band there, the goggles are now a mesh on the hood); gold edging, brass, leather, skin and the pack stay out of every region. B/C (and A's cloak)
keep A's shading on the authored colour (`TIERS`, `TIER_A`); one set of ramps fitted over body and head texels together
(`merge_head_material.py`). Ramp fit to the texture: cloak 4.7, wraps 9.7, plate 2.0, under 5.7 mean 8-bit levels.
Material classes: skin, cloth, metal, eye, 11 = glazed Ancient ceramic (plates) and goggle lenses.

**Per-tier grip (supported today):** `game/fx/WorldFxSystem.cpp` reads `clips`, `animation.run`, `events`, `sockets`
and `attachments` per descriptor, so the one GLB carries two clip sets and each tier attaches only its own gear. All
three guns share the right fist's hand frame (`rifle_fit.py`): the rifle chain drives bone `Rifle` and the carbine's
foregrip sits where the left fist closes on the rifle's handguard (`make_slab_prop.py`), so the carbine rides the
same clips.

## Model, rig and weights

- HD masters (Codex, `references_hd/`, `references_head/`) from the approved concept (no native sprite): the primary
  after one correction (arms opened, the cloak behind the arms, the cloth solid with painted wear), four views
  (strict profiles not fully reached), head turnaround, prop references `pistol.png`, `carbine.png`, `buckler.png`,
  `chest_plate.png`; tier B's rifle reuses `hes_guard_claude/references_hd/rifle.png`.
- Smart Topology 15k → 13,843 triangles, 103 parts (`creature.json` note): torso + arms + fists with the chest
  scarf strips fused (P00), cloak (P01, open front), head (P02), hood + scarf (P03), tunic (P04, open front), boots,
  trousers, pack and its gear, belt gear, shoulder / elbow / knee plates, scarf tail, goggles, eyes.
- Joints: Meshy auto-rig + arm rings (wrist = narrowest ring) + `leg_rings.py` on the trousers / boots (knee x put on
  the straight hip-ankle line by `knees_straight.py`: the baggy trouser ring sat 5 cm inward). Rigid fists continuing
  the forearm; 52 bones + 4 twist + 14 × 4 robe chain bones.
- Weights (`weights_robe.py`, merged guard + villager rules): cloak above the waist = mantle (Meshy, legs → spine, arm
  share ≤ 0.25, smoothed), cloak and tunic below 0.95 m on 14 × 4 simulated chains (`robe_sim.py`, leg capsules ×1.6);
  the tunic's front panels on their own thigh (`panel_thigh`, full within 85° of straight ahead, from 1 cm under the
  belt); the trousers' waist on the pelvis; scarf tail one sector mix on the chains; hood head → neck → chest by height;
  pack, straps and buckles rigid on B_Spine2, belt gear rigid on the pelvis; plates as uniform pieces (no head share).
  Reduced after weighting to 9,999 (head protected), LOD0 to 8,926 (`halve_lod0.py RATIO=0.9`, face blocked).
- Face (`face_fix.py`, on the textured master after the clip sync, idempotent): the hood's front lip moved out of an
  eye window round both eyes (11 vertices moved radially, up to 3.2 cm, 32 more by diffusion; none deleted); welding
  goggles from the concept as new piece 103 (100 % B_Head, 226 vertices / 122 faces): two 12-gon brass lens cups
  tilted 27° up the forehead on the hood above the brow, dark glass insets, a nose bridge and a leather strap
  ray-cast 4 mm over the hood to the back of the head; one texel each of the body set's brass and leather and the
  head set's goggle lens, outside every region (no tier recolour). Smart Topology's goggle ring (P10, half under the
  brim) and buckle bits (P25/P81, poking out of the hood's back) are removed.
- `mark_strips.py`: the scarf strips fused onto the torso are an outer layer and left out of the inside tests.

## Props

`prop_profile.py` + `make_slab_prop.py`: each gun is its reference's alpha outline (holes kept, Douglas-Peucker on a
6 px grid) extruded to ±hw, glow windows 0.8 mm proud (own material, emissive), planar side UVs onto the reference.
The pistol is turned so its raked grip lies on the fist's tunnel axis; the carbine keeps its barrel on the rifle
frame and gets a straight octagon grip with UVs sheared onto the raked reference grip, plus a round foregrip.
`make_gear.py`: the chest plate is a 14 × 14 lattice ray-cast onto the chest (3 cm off, back face 6 mm); the buckler a
24-gon disc on the outer side of the left forearm with its orange rings as proud glow annuli. Textures are powers of
two (`split_attachment.py` crops on a grid).

## Clips

| Clip (B/C) | Source | Clip (A) | Source |
|---|---|---|---|
| Standing 0.8 s | set 2Hand Shooting Idle, feet levelled | P_Standing 2.0 s | set Relax Idle, arms out 8 + 6° |
| Walking 0.8 s | set 2Hand Shooting Walk (stride 1.545 m) | P_Walking 0.8 s | set Relax Walk Forward, arms out 8 + 10° |
| Running 0.8 s | set 2Hand Shooting Run Forward (3.335 m) | P_Running 0.8 s | `hybrid_run.py`: legs, trunk and head of the 2Hand run, arms of Mixamo Standard Run by phase (the Mixamo heel kick went 8 cm through the cloak) |
| Attack 1.1 s | raise into FireRifle1, feet pinned, **impact 0.367 s** | P_Attack 1.067 s | set Pistol Attack R1, planted, `aim_forward.py` (barrel heading ≤ 8.4°), **impact 0.65 s**; left arm as Standing (15 % of the source's) |
| Hit 0.5 s | 2Hand GetHit F1, feet pinned | P_Hit 0.5 s | set Unarmed Get Hit F1, planted; left arm as Standing (30 % of the source's) |
| Death 3.43 s / Dead | Mixamo Death From The Front, travel halved | P_Death / P_Dead | the same |
| Fidget 2.07 s | sights along the gun (IdleAlt) | P_Fidget 2.33 s | set Pistol Reload R1, right hand only (he checks the pistol); left arm as Standing (10 %) |

Rifle tiers: `rifle_drive.py` (barrel level in roll, the right hand from the gun), `support_hand.py` (left fist on the
handguard, sliding 0.28-0.37 m; a roll search about the handguard took the wrist from 64-75° to 58-67°),
`rifle_clear.py` (closed shells only), `wrist_elbow.py` (wrists ≤ 60°: per clip a Viterbi choice of the elbow plane
of both arms and, for the support fist while it holds the handguard, a roll about and a slide along it within
0.28-0.37 m; the right fist and the gun keep their world pose, so the rifle checks are unchanged). **Both Deaths drop the gun** (`drop_gun.py`): the gun bones fall with gravity
from 30 % of the clip onto the floor beside the right hand and lie on their side, so the corpse is not lifted by a
rifle through the floor (the first version raised the body 49 cm); every other clip keys the gun bones at rest.

## Gates (`review/gates_v5.txt`, `review/g6_*_v5.json`, `review/rifle_up.json`; final reduced mesh)

- Arm stretch p99 ≤ 1.77 in every living clip of both sets except P_Attack 2.07 (max 3.05, the raised right arm) and,
  after the wrist pass's elbow turn, the rifle Attack's right arm 1.90 (max 2.73) and Fidget's 1.83 (was 1.68 / 1.65);
  deaths 2.01 (max 2.88).
- Wrist swing: tier A ≤ 49° everywhere. Tiers B/C (two-handed, after `wrist_elbow.py`): left ≤ 58.5° (Standing 55.3,
  Walking 55.6, Running 54.4, Attack 57.1, Hit 58.5, Fidget 56.2; was 58-67°), right ≤ 55.5° (Attack 55.3, Fidget
  55.5; was 70 / 66°). Death: left 73.6° at frame 3 (as before: no elbow, roll or slide lowers it), right 52.6°.
- Hands in the closed body 0 cm in every living clip (P_Running 1.1 cm); deaths 4.3 cm (lying, Mixamo source).
- Hand proximity (`g6_hand_proximity.py`, open shells < 10 mm): rifle clips: the left fist now clears the cloak in
  Standing (18.6 mm, was 2.4), Attack (16.3, was 2.9) and Fidget (14.4); Hit 3.6 mm (2/16 frames) and the right fist
  0.1-0.4 mm from the cloak's edge in Attack (5/34) / Hit (6/16) as before; tier A: the hanging hands rest against the cloak's front edge in P_Standing /
  P_Walking (0-0.3 mm, in front of it in the renders: `review/shots/har_a_Standing_*`), no contact in P_Hit / P_Running (right).
  Larger abductions (15-20°) cleared them but read as a gunslinger's spread arms; kept 6-10°.
- Leg leak (`g6_leg_leak.py`, legs vs tunic + cloak, > 5 mm): **0 in Standing, Attack, Hit, Fidget and all tier A
  standing clips**; Walking 1 vertex 17 mm in 5/25 frames (both sets); Running 5 vertices up to 29 mm (both sets, the
  knee drive against the tunic side); Death 21 vertices up to 49 mm while lying (A: 15 / 31 mm). Unchanged in the
  polish round: the running leaks are scattered (front panel top under the belt, the side and the back hem at the
  heel kick), not one panel a thigh-follow rule fixes, and larger robe-sim leg capsules (LEG_R 2.0) left them at
  17/25 frames, 30 mm, so the weights were not reworked (a rig rebuild would redo the textured master).
- Rifle up axis: aim ≤ 9.3°, carry ≤ 30°, roll 0° (limits 20 / 35).
- Soles/floor: lowest point −0.2…−1.5 cm in living clips; Death −3.1 cm, P_Death −4.4 cm (cloth under the floor while
  lying: `robe_floor.py` limited).
- Key times (`check_key_times.py`, in `build_runtime.sh`): every sampler of every export finite and strictly
  increasing (6,048 samplers in the body GLB).
- `check_winding.py`: 0 inverted closed parts in all 11 exports. Viewer `tools/run_creature_review.py check` 48/48
  tier/clip switches, no console errors. Not checked in game (no engine work in this task).

## Engine needs and decisions for the parent

- **Run threshold (decided):** speed 230 for all three tiers in `make_monster_tables.py`, scale 98.84 kept: below the
  237 units/s run threshold the engine plays the walk, at 1.20× its natural 191 units/s (`integration/actors.yml`).
- **Emissive:** the glow attachments rely on the constant emissive factor; creatures do not bloom yet, so the cells,
  emitters and buckler rings read as bright paint (as the guard's rifle).
- **Tier C's personal shield** (500 Light) is an engine effect; not modelled.
- **Raider melee** (30 % Phys, "vibro knife" in the table's gear text): no knife is modelled; `attack_melee` plays the
  shot clip (as the guard).
- Nothing else needs engine work: per-tier clip sets and attachments are supported today.

## Known limits

- The pistol hangs a little outward in P_Standing (barrel 25° from straight down-forward; the fist continues the
  forearm).
- The pack is large (Smart Topology's), rigid on the upper spine; while doubled over in the Death it rises over the
  head.
- Running and lying leg leaks above; the Death's left wrist 73.6° in its first frames.
- The hood's opening keeps a small notch at the brim's top centre where the moved lip meets the forehead.
- The cloth's holes are painted wear (the masters asked for solid cloth); the ragged hem is geometry.

## Polish round (2026-10-22)

| Note | Done | Evidence |
|---|---|---|
| Run speed | speed 230 walks (below 237); actors.yml comment updated | `integration/actors.yml` |
| Tier colours | C wraps (200, 136, 44) → muted ochre (138, 94, 46); B (116, 48, 34) → (104, 54, 40) | [tiers before/after](review/tiers_contact.jpg) |
| Goggles, hood lip | `face_fix.py` (above); forehead texels repainted skin | [tiers](review/tiers_contact.jpg) rows 2-3, `review/shots/har_*_close_head*.png` |
| Wrists ≤ 60° | `wrist_elbow.py` in the rifle chain; left ≤ 58.5°, right ≤ 55.5° in held clips | `review/gates_v5.txt`, `work/wrist_elbow.json`, [close-ups before/after](review/closeups.jpg) |
| Running leg leak | not cheap (see Gates); unchanged | `review/g6_legs_v5.json` |
| Key-time gate | `check_key_times.py` in `build_runtime.sh` | all PASS |

## Replay

```sh
TOK=<lease> scripts/rebuild.sh rig            # joints, rig, weights, reduction, strips, grips, guns, gear
TOK=<lease> scripts/rebuild.sh rifle          # tiers B/C clips -> work/R_v4.blend
TOK=<lease> scripts/rebuild.sh pistol         # tier A clips -> work/P_v4.blend (needs R_s0 for the hybrid run)
TOK=<lease> scripts/rebuild.sh merge; TOK=<lease> scripts/rebuild.sh gates
# textures once: SRC=rig_v5.blend export_uploads.py (byte-identical to work/har_*_upload_sent.glb) -> Meshy
# requests/retexture_v1.json, head_retexture_v1.json -> transfer_uv.py (UVMap, then HeadUV) -> uv_raster.py x2 ->
# bake_ao_natm.py -> PREVIEW=1 python3 scripts/compose_har.py
# packed body UVs once (2026-10-22, on the textured master after face_fix.py; work/pre_pack/ = everything before it):
# step.sh uv_pack.py dump work/rig_v6.blend -> <venv>/bin/python -I uv_atlas.py work/uvpack_in.npz work/uv_pack.npz ->
# step.sh uv_pack.py apply work/rig_v6.blend work/uv_pack.npz -> <venv>/bin/python resample_meshy.py work/uvpack_in.npz
# work/uv_pack.npz -> step.sh uv_raster.py work/rig_v6.blend UVMap 2048x1024 -> LAYERS=UVMap BODY_SIZE=2048x1024
# step.sh bake_ao_natm.py work/rig_v6.blend -> PREVIEW=1 python3 scripts/compose_har.py (head raster/AO unchanged)
LOD_REPAIR_PYTHON=<venv>/bin/python TOK=<lease> scripts/build_runtime.sh   # face_fix.py applies once; far LODs by lodrep/
python3 scripts/viewer_tiers.py && python3 scripts/update_viewer_manifest.py
```

`scripts/step.sh <script> [args]` runs one Blender step under the lease (steps are serialized by the workspace lock:
never run two at once, a blocked step returns without a log).

## Packed UVs and the one-handed Scav (2026-10-22)

User (tier A Scav in the viewer, `75.png`): "good design, but blurry because texture doesnt cover everything imo + gun is
held as 2 handed but is too short its a pistol?". No Meshy credits (30 of 80 spent, unchanged).

**Texture density.** Measured on the body faces of the runtime GLBs (texels per metre, area-weighted median;
`scripts/uv_density.py`): Ashrunner before **224** (p10 128; cloak 174, wraps 302, plates 293,
under-clothes 248), Landfall guard 350, villagers 258-268. Meshy's own layout used 51 % of the 1K body page, part of
it the head faces' unused islands, and the Ashrunner has 6.69 m2 of body surface (the guard 3.93: the long cloak, the
large pack 1.63 m2, the belt gear), so even a perfect 1K page tops out near 265 texels/m at 4-texel padding
(xatlas, 524 charts). Route: re-unwrap the body faces of the textured master with xatlas (`uv_pack.py`,
`uv_atlas.py`; the pack and its gear 0.8x, face_fix's one-texel goggle faces 0.15x; Meshy's layout kept as layer
`MeshyUV`; the goggles' 98 quads triangulated) into a **2048 x 1024 body page** (two 1K pages side by side, 6-texel
padding), then move Meshy's 2K body maps onto it per triangle (`resample_meshy.py`: the same triangle's point in
Meshy's UVs; the normal map re-encoded from the old layout's fs_model.sc tangent frame into the new one), rebake the
body AO and rerun `compose_har.py` (non-square body page; head set, head raster and AO untouched). After: **385**
texels/m median, p10 366, every region 380-388 (cloak x2.2); the source is Meshy's 2K paint (cloak 348, the rest
450+), so the look is the approved one, only sharper. Tier ramps refitted over the new texels: region medians within
1-7 8-bit levels of before (`har_c` under-clothes +7). **Deviation:** the body page is 2048 x 1024 instead of the
playbook's 1K (merged atlas 3104 x 1024 instead of 2080 x 1024, about +50 % texture memory, one set for all three
tiers) because the 1K page could not reach the guard's density on this surface. Close-ups before/after:
[closeups_before_after.jpg](review/uv_pack/closeups_before_after.jpg) (front, back, cloak/pack, scarf, shoulder
plate, boots, pack, hem; `scripts/texture_closeups.py` on the viewer GLBs).

**One-handed pistol.** The screenshot shows the Scav on the rifle tiers' `Standing` (2Hand Shooting Idle, left fist
on a handguard): the viewer's default clip was the plain set for every tier, while `integration/actors.yml` already
binds tier A to `P_*`. Viewer fix: each tier GLB carries only its own clip set under the role names (tier A's `P_*`
renamed, `viewer_tiers.py`), the manifest gives each model its durations, sources and provenance
(`update_viewer_manifest.py`, `work/viewer_clips.json` `tier_clips`), `review.js` reads them; the badge shows
`Standing (P_Standing)`. Pose fix in the `P_*` set: `left_arm_rest.py` keeps the free left arm hanging as in
Standing (local rotations, so it follows the trunk) with a share of the source's motion in P_Attack (15 %), P_Hit
(30 %) and P_Fidget (10 %: the reload is now the right hand checking the pistol), then 4 degrees more abduction
(10 in all) off the cloak edge. P_Standing / P_Walking were already one-handed (Relax idle / walk, the pistol hanging).
The rigid Smart Topology fists cannot open; the left fist hangs relaxed at the side. The pistol is unchanged in size
(it reads as a pistol once held in one hand). Shots: [tier A poses](review/uv_pack/tierA_pose_sheet.jpg),
`review/shots/a2_*.png`.

**Gates (rerun, `review/gates_v5.txt`, `g6_*_v5.json`, `rifle_up.json`):** tier A wrists ≤ 17.1° in Standing, Walking,
Attack, Hit and Fidget (P_Running 45.5°), hands in the body 0 cm; B/C unchanged (left ≤ 58.5°, right ≤ 55.5°; Death
73.6° in its first frames as before); hand proximity: the hanging left hand rests on the cloak's front edge in
P_Attack (33/33 frames, 0.2 mm) and P_Fidget (34/71, 0.2 mm) as in P_Standing, P_Hit 3.6 mm; leg leak unchanged
(0 in every standing clip; walks 1 vertex 17 mm, runs 5 vertices 29 mm, deaths lying); rifle up/roll PASS; soles
unchanged (P_Death −4.4 cm lying); key times PASS (6,048 samplers); winding 0 in all 11 exports; viewer check 24/24
(3 tiers x 8 role clips), no console errors. **Far LODs:** `lodrep/repair_glb.py` (lod_repair_claude route, mask RGBA),
first ladder step r25_12 passes: LOD2 outline 2.6 % / colour 11.7, LOD3 4.6 % / 8.7 (the shared builder's LOD3 was
12.1 % / 17.1): [lods.jpg](review/uv_pack/lods.jpg). Tiers: [tiers_sheet.jpg](review/uv_pack/tiers_sheet.jpg).
