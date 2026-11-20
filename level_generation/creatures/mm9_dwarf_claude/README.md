# MM9 Dwarf (mm9_dwarf) — 3D actor, 2026-10-31

MM9's dwarves, queue item 17: Dwarven Guard L10 (`MONSTERS.txt` 120, `MM9 Dwarf A`), Dwarven Soldier L20 (121, `B`), Dwarven Commander L30 (122, `C`); body `DWARF.abc`, 21 nodes, skin `DWARF.dtx` for all three rows. Humanoid: built on the approved Yrsa route (MM9 skeleton, MM9 clips, grafted five-finger hands, a separate head set). Throwing axe in the true right fist. Progress, hashes and Meshy receipts: `creature_3d_progress.json`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_dwarf.glb` (`tools/install_model.py --world mm9`), variants `dwarf_a/b/c` |
| Binding | `assets_dev/worlds/mm9/models/actors.yml`, block `mm9_dwarf_claude`: `scale: 100` (MONSTERS Scale 1), `yaw_offset: -1.570796327`, stride 0.6 / 1.0 (twice the foot's sweep), look `Bip01 Head` only (MM9's `Neck` node carries the shoulders), melee impact 0.5 s (WAttack1 `Rattack`), ranged impact 0.5 s, release socket `axe` = `RHand1` |
| Triangles LOD0/1/2/3 | 13,643 / 6,817 / 2,452 / 812. LOD0: limbs set 3,498 (hands 680 each), torso set 5,888 (skirt lining about 220), head set 3,893, axe 364 |
| Skeleton | DWARF.abc, 21 nodes, no pelvis (thighs on `Spine`) and no clavicle (arms on `Neck`), joints moved onto our mesh, rest frames = source frame turned by the least rotation onto our limb (`fit_dwarf.py`), + 15 finger bones per side + 8 hinges `Skirt_*` + 4 skirt leg bones `SkirtLeg*` (run 2) + 11 half-joint helpers `*_h` + 2 ankle helpers `Foot_h` |
| Clips (30 fps) | Standing `Stand`, Walking `Walk`, Running `Run`, Fidget `Fidget1`, AttackMelee `WAttack1`, AttackRanged `Rattack1`, Hit `Wince1`, Death `Die1`, Dead; script clips AttackMelee2 `WAttack2`, AttackMelee3 `HAttack1`, Fidget2, Search, Aware, Taunt, Hit2 `Wince2`, Death2 `Die2`. All 16 MM9 clips are in. `Rattack1` and `WAttack1` are the same motion in MM9 |
| Textures | one shared set: torso 2K + 1K normal + 1K ORM, limbs 1536 + 1K normal + 1K ORM, head 1536 + 1K normal, region masks 1K, weapon 1024x512. Tiers are ramps, no per-tier image |
| Meshy credits | **20 / 40**: Smart Topology body 5, head 5, one 4K body paint 10 (backup account, no retries) |

## User fix, r14 (2026-10-31)

- **Beard:** the tip was held by the chest bones and stretched in the attacks. The face and whole beard are now rigid on `Bip01 Head`; only the collar tube under the helmet blends to `Neck`. `beard_gate.py`: edge stretch 1.00 in all 17 clips (target 1.2). It stays clear of the mail in AttackMelee and Hit in the shots read (`review/sheet_fix_b.png`). No per-clip number for beard against mail: the head gate also counts the helmet's rim.
- **Standing shoulders (r15):** `clips_mm9.py` cut joint offsets under 4 mm hard, so the shoulders popped 0.4 cm at frames 19-21; MM9's clip is smooth. Now a soft threshold.
- **Skirt:** it no longer fans. Toward the hem up to 72 % of each vertex follows the thighs, blended across front and back (`reweight.py`), and `skirt_keys.py` from the Clan Soldier lifts each panel only for its own thigh, neighbours 55 %, capped at 45 deg. Lining is lighter dark cloth. It hangs in Standing, Walking, Running and AttackMelee (`review/sheet_fix_skirt.png`, `review/sheet_fix_b.png`). In Running and AttackMelee the upper skirt bunches in a shiny roll under the belt, where the hinge lifts and the thigh holds the hem.
- **Trade, `skirt_gate.py`, thighs through the skirt:** Standing, Walking, Fidget, Aware, Taunt, AttackMelee3, Hit, Hit2 0. Running 0.3 cm 15/31, Fidget2 0.2, Search 0.6, AttackMelee and AttackRanged 0.8 cm 12/73, AttackMelee2 2.5, Death 1.4, Death2 2.4, Dead 1.3.
- **Not rerun after this fix (done in run 2, below):** collapse, arm and hand, jitter, grip, blade, detached, in game, and the older sheets and strips (they show the fanned skirt). `sheet_tiers`, `sheet_closeups_*` and `strips_*` are r13. The Walking and Running arm corrections were set for the fanned skirt and may now be larger than needed.

## Run 2, r17 (2026-10-31): the open gates of r14 closed

Look kept: r14 fan and beard, our tiers, textures and UVs untouched (vertex moves and weights only). No Meshy credits.

- **Skirt roll gone.** r14 gave the skirt's hem a 72 % share of the thighs; turned about the hip, that share pushed the cloth at hip height up under the belt (the shiny roll in Running and AttackMelee). The same share now rides on four new bones `SkirtLeg{F,B}_{L,R}`, children of Bip01 Spine with pivots on the cloth at the belt, front and back (`reweight.py`, `skirt_leg_keys.py`): the front bones follow the thigh's forward swing only, the back bones its backward swing only, both 0.8 of its outward swing, no twist, on the clip's own keys; per key the least factor 1.0-1.5 that keeps the thigh under the cloth the leg bones carry. The share starts higher (`KK` 0.72 from 3 cm under the belt). The hinges then lift only the upper cloth: cap 20 deg (was 45), no per-clip margins, and a second pass (`skirt_keys.py` `fix_pass`) lifts, key by key, the hinge that still clears a thigh, by skirt_gate's own test. The hip's outer side under the upper skirt is slimmed to 55 % (hidden at rest). `skirt_bunch.py` (new): Running faces under 50 % of rest area 34 -> 1, upper vertical edges p2 0.51 -> 0.75; AttackMelee 5 -> 1; Death2 94 -> 2; crease p99.5 Running 72.6 -> 40.9 deg, AttackMelee 48.2 -> 28.7 deg (the rest are hem lip folds).
- **Thighs through the skirt** (`skirt_gate.py`, now pants vertices only: r14's thigh-carried cloth no longer counts as leg; r14 re-measured the same way gives the same numbers): Running 0.3 -> 0, Search 0.6 -> 0, AttackMelee/AttackRanged 0.8 -> 0, AttackMelee2 2.5 -> 0, Death 1.4 -> 0.6, Dead 1.3 -> 0.5, **Death2 2.4 -> 2.1 cm** (4 of 73 frames, the fall at 0.17 s, thigh's outer side at the front-left corner under the belt). All other clips 0.
- **Arm corrections smaller.** `arm_bump.py` read r14's thigh-carried hem as body (the hem's dominant bone was a thigh), so its bumps grew (Fidget L 39 -> 42, Search L 36, Hit2 L 27 deg) and the jitter gate failed 3 clips. Cloth is now every `Skirt*` bone; the bumps are Fidget L 30 deg (capped, `arm_jobs.txt` field 8), Fidget R 42, Fidget2 L 24 (ramp runs 0.3 s into the contact), Search L 21, Hit2 L 3. `arm_out.py` is gone (`corrections.sh` empty): with the skirt hanging the hands clear it on MM9's own swing (Walking R 0.4 cm, Running 0).
- **Axe off the shoulder** (`axe_lift.py`, new): one raised-cosine wrist turn over the contact, the fist turns with the haft so the grip is unchanged. Fidget 4 deg (axe in the upper arm 6.0 -> 0 cm), AttackMelee3 18 deg (axe in the neck 3.1 -> 0.8 cm).
- **Helmet rim.** The old head gate (blade_gate with HEADMAT) counted the neck tube that sits in the collar by design (its "2.9 cm at rest") and the collar's own wall facing the neck tube under the helmet (its "6 cm when the head tips"). `rim_gate.py` (new) splits the head set by layer (head_faces.npz by UV) and measures helmet and horns against the torso's outer surface without those hidden faces. r15: Hit2 5.1, Death 4.3, AttackMelee 1.0, Taunt 1.0 cm. Fix: the skin under the rim takes up to 40 % of the head's turn, plates half (`reweight.py` `HEAD_SHARE`), and `head_clear.py` (new) takes back the least fraction of the head's turn from the neck that keeps the rim within 0.8 cm, held and smoothed on keys: Search and Death2 10 %, AttackMelee3 and Hit2 20 %. Now every clip under 1 cm (max 0.7).

- **Wrist seam (r18, coordinator):** the glove (limbs set, a closed shell whose top sits inside the bracer) took its hand share from 0 to 0.8 within 1 cm at the cuff, and the bracer (voxel skin, closed at the wrist by a cap on the dark texel) was rigid on the forearm; no open edge. A hard wrist bend pulled the glove off the cuff's mouth and showed the dark cap as a jagged wedge. Now (`reweight.py`, vertex weights only) the glove's hand share rises smoothly from 3.5 cm inside the cuff to 3 cm past it, and the bracer's last 3.5 cm take up to 45 % of the hand, so the cuff's mouth leans with the wrist. `wrist_gap_gate.py` (new; how far the widest point of the cuff's rim moves off the glove against rest): worst AttackMelee/AttackRanged R 1.75 -> 0.74 cm (bend 126 deg), Fidget R 1.62 -> 0.91, AttackMelee3 R 1.57 -> 0.97, Aware L 1.43 -> 0.87, Death R 1.40 -> 0.71; every clip now under 1 cm. Seen at full size (`review/run2/sheet_wrists.png`, `review/sheet_hands.png`): the black wedge is gone in AttackMelee and AttackRanged; at the hardest bends (Fidget R, Aware L, AttackMelee3 R) a thin dark-brown rim of the cuff's mouth and the gold trim's sawtooth edge still show.

## Findings in the source

- **No child model.** ChildModels is empty; DWARF.abc holds all 16 clips, each of only 8-12 keys.
- **The weapon is not `DWARFAXE.abc`.** That pick belongs to the scripted miner (`AttachProp` in DWARVENMINER.scr) and floats 60 cm off the socket. The rows run `baserange.scr` with projectile `Axe`, and the clips' `ShowWeapon` / `HideWeapon` events hide the axe at the throw and show it at 1.5 s. `PROJECTILES/AXE.abc` on socket `RHand1` lands in the fist in every clip (`review/mm9_strips2/sheet.png`).
- **MM9's bind is asymmetric:** legs 12 cm apart in depth, arms differ. Raw ABC with `mirror_glb.py` last, no `mirror_source.py`. Our symmetric mesh stays as built and the rest frames turn to it.
- **One skin:** MM9 tells the three rows apart only by name.

## Route (scripts/)

0. `convert_sources.sh`, `axe_in_hand.py`, `ref_renders.py`.
1. **Masters** (Codex): `references_hd/` five views, `references_head/00_geometry` clay sculpt, seven painted views on our own clay.
2. **Meshy:** Smart Topology 15k on the body and the sculpt, one 4K paint.
3. **Clean** `clean_dwarf.py`: head, bandolier and buckle dropped (the bandolier is paint), figure's right half kept and mirrored. Meshy's garments are open sheets, so tunic, sleeves, forearms and bracers are closed and fused into one voxel skin; skirt, pants, boots, cuffs, belt and plates stay separate.
4. **Head** `head_prep_dwarf.py` (S 0.41 fits MM9's head box), `graft_head_dwarf.py` (a plain neck tube, shoulders pressed under the rim).
5. **Rest and weights:** `fit_dwarf.py`, `rig_dwarf.py`, `graft_hands.py` (finger direction and hand length from config: Meshy's mitt is as wide as long), `glove_dwarf.py`, `helpers_dwarf.py`, `uv_dwarf.py` (**never re-run**: the paint belongs to it), `reweight.py`, which also moves vertices only: thighs slimmed 45 % where the skirt hides them, belly 28 %, waist 20 %, hem 7 %, more room under the rim; run 2: hip side 55 %, skirt leg bones `SkirtLeg*`, the skin under the rim shares the head. UVs and paint stay.
6. **Paint:** `textures.sh` (saturation 0.84, contrast 1.0, `tone_dwarf.py` for the pale mail), `fix_back.py`, `project_head.py`, `tier_dwarf.py`.
7. **Finish** `finish_dwarf.py`: fists solved on the haft, left fist round nothing as MM9's mitt, axe from `make_weapons.py`, lining of skirt and cuffs (skirt lining reduced), bracer ends and the skin's cap under the belt on a dark texel.
8. **Clips** `scripts/rebuild.sh`: `clips_mm9.py` with `ORBIT` and the soft joint-offset line, `finger_keys.py`, `corrections.sh` (empty since run 2), `half_keys.py`, `skirt_leg_keys.py`, `skirt_keys.py`, `axe_hide.py`, `arm_bump.py`, `head_clear.py`, `axe_lift.py`. Gates: `scripts/gates.sh` (adds `skirt_bunch.py`, `rim_gate.py`, `beard_gate.py`).
9. **Runtime:** prepare, LODs, shadow fix, `region_variants.py`, floor, winding, install, viewer. `retier.sh` from the ramps; `swap_head.py` puts a repainted head in without re-running the clips. Binding: `flock level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock python3 <project>/scripts/bind_actors.py 0.6 1.0` from the repo root.

## Head projection

The head is layered: helmet shell, face and beard, eyes, horns, neck. After the Guard's defect `project_head.py` takes a view only where that view's first surface is the texel's own layer, 5 pixels clear of the layer's edge (1 for the eyes); unseen texels fill from seen texels of their own layer. `head_audit.py` lists the accepted faces per view. All three tiers were read at full size from front, quarter, side and below (`review/sheet_heads.png`, viewer shots): one pair of eyes each, no helmet paint on the face, no face paint on the helmet. Front-on at full size per tier: `review/sheet_faces_front.png`: one set of eyes, nose and moustache; eyes and nose come from the front view alone. Open: a pale strip of the helmet's inner wall shows above the brow and beside the temples, and the upper lip under the nose is bare skin.

## Checks

All on r17 and r18 (r18 = r17 plus the wrist weights; jitter, arm and hand, grip, axe, skirt, rim, collapse and the rest rerun on r18 with the same results), the installed build (`review/gates/`); run-2 working files in `work/run2/` (`gates_before/` holds r15's gates).

| Gate | r15 (installed before run 2) | r17 |
|---|---|---|
| `bone_length_audit.py` | 0 stretching of 12 | 0 stretching of 12 |
| Handedness | axe on `Bip01 R Hand`, anatomical right | same |
| `skirt_gate.py`, thighs through the outer skirt | AttackMelee2 2.5, Death2 2.4, Death 1.4, Dead 1.3, AttackMelee 0.8, Search 0.6, Running 0.3 cm | Death2 **2.1** (4 frames), Death 0.6, Dead 0.5, every other clip 0 |
| `skirt_bunch.py`, faces under 50 % of rest | Running 34, Death2 94 | 1 and 2 |
| `arm_hand_gate.py --outer-only --exact` | Fidget R hand 4.5 cm (71 frames); script Fidget2 4.9 both hands | every bound clip 0; script Fidget2 3.1 cm both hands (folded arms, each hand on the other upper arm) |
| `jitter_gate.py` against the untouched MM9 clips | 3 fails (Fidget L, Search L, Hit2 L) | **0 fails** |
| `grip_gate.py`, right hand, every clip | inside the haft 0.3 cm | 0.3 cm; wrap thumb 105-120, index 135-180, middle 180-195, ring 120-135, pinky 120-135 deg |
| `blade_gate.py`, axe against skin | Fidget 2.9 (r13 6.0+), AttackMelee3 3.1, script Fidget2 2.7 cm; Death, Dead 0 | Fidget 0, AttackMelee3 0.8, script Fidget2 2.1 cm (against the folded left forearm); Death, Dead 0 |
| `rim_gate.py`, helmet and horns against the torso | Hit2 5.1, Death 4.3, AttackMelee 1.0, Taunt 1.0 cm | all under 1 cm (max 0.7, Search and Taunt) |
| `beard_gate.py`, edge stretch | 1.00 | 1.00 in all 17 clips |
| `wrist_gap_gate.py`, cuff rim off the glove against rest | worst 1.75 cm (AttackMelee R) | worst 0.97 cm (AttackMelee3 R), r18 |
| `detached_parts_audit.py` | only the axe head (RHand1, a held part) | same; nothing else |
| `flat_shading_check.py` | 0.00 limbs, 0.02 torso, 0.00 head | same |
| `check_winding.py` | 0 inverted | 0 inverted |
| `texture_quality.py` | limbs 57.1 %, torso 55.1 %, head 63.8 % | same images |
| `orient_gate.py`, head and feet against MM9 | head mean <= 2.6 deg | head mean <= 4.6 deg (AttackMelee3, Hit2: `head_clear.py`); feet unchanged |
| `floor_audit.py --world mm9 --match 'MM9 Dwarf*'` | 3 bindings, 0 problems | 3 bindings, 0 problems (stand 0, walk -0.8..+1.1, dead 0) |
| `mm9_actor_models_build_every_binding` | PASS | **PASS** on r18, 150 descriptors on 60 models, 0 failed |
| In game (`bootcamp.odm`, review root) | r8 | r17: `review/ingame_sheet.png`, standing tiers front, near, quarter, side |

Collapse gate, faces below 20 % of rest area or flipped, worst frame per region, axe excluded, r10 (r17's `review/gates/collapse.txt` is within a few faces of it per region; knees and ankles 0):

| Clip | Knee | Groin | Elbow | Shoulder | Ankle | Wrist | Neck | Body | Face-frames | Exposed |
|---|---|---|---|---|---|---|---|---|---|---|
| Standing | 0 | 0 | 5 | 17 | 0 | 2 | 3 | 3 | 1557 | 17 |
| Walking | 0 | 2 | 1 | 0 | 0 | 2 | 1 | 1 | 579 | 5 |
| Running | 0 | 3 | 3 | 2 | 0 | 5 | 8 | 14 | 661 | 22 |
| Fidget | 0 | 2 | 41 | 46 | 0 | 5 | 6 | 49 | 12544 | 43 |
| Fidget2 | 0 | 2 | 10 | 23 | 0 | 2 | 33 | 73 | 7379 | 78 |
| Search | 0 | 4 | 30 | 40 | 0 | 2 | 8 | 20 | 6080 | 24 |
| Aware | 0 | 3 | 27 | 40 | 0 | 5 | 37 | 52 | 4949 | 86 |
| Taunt | 0 | 4 | 20 | 34 | 0 | 5 | 14 | 19 | 2576 | 34 |
| AttackMelee | 0 | 3 | 10 | 24 | 0 | 6 | 38 | 54 | 2547 | 67 |
| AttackMelee2 | 0 | 2 | 24 | 40 | 0 | 4 | 31 | 59 | 3567 | 70 |
| AttackMelee3 | 0 | 4 | 32 | 42 | 0 | 5 | 41 | 76 | 3562 | 71 |
| AttackRanged | 0 | 3 | 10 | 24 | 0 | 6 | 38 | 54 | 12527 | 67 |
| Hit | 0 | 2 | 12 | 30 | 0 | 2 | 14 | 17 | 2237 | 20 |
| Hit2 | 0 | 2 | 20 | 33 | 0 | 2 | 22 | 50 | 2230 | 37 |
| Death | 0 | 4 | 16 | 37 | 0 | 5 | 43 | 76 | 5498 | 94 |
| Death2 | 0 | 2 | 7 | 17 | 0 | 5 | 40 | 79 | 4925 | 116 |
| Dead | 0 | 2 | 5 | 17 | 0 | 2 | 19 | 36 | 3007 | 69 |

Knees and ankles 0. The large elbow and shoulder counts are the arm fully folded (Fidget, hand to the shoulder): at most 6 elbow faces exposed. Neck is the tube under the helmet; the shots read show the collar clean. MM9's left arm rest differs from ours by 33 deg, hence Standing's shoulder count.

Sheets (viewer shots unless noted), r17: `review/sheet_mm9_vs_ours.png` (MM9 is a Blender render), `review/sheet_tiers.png`, `review/sheet_closeups_a.png`, `_b.png`, `_c.png`, `review/sheet_hands.png`, `review/strips_a.png`, `_b.png`, `_c.png`, `review/run2/sheet_skirt_b.png` (skirt at the belt, Standing to Death2), `review/ingame_sheet.png` (game, `review/ingame_r17/`). Heads unchanged since r13: `review/sheet_heads.png`, `review/sheet_faces_front.png`. Viewer check: 51 tier/clip switches, 0 console errors.

## Deviations and open points

- **Tiers:** MM9 has one skin. Ours: A tuned toward MM9's darker red-brown, B darker leather, blued steel, dark red beard, C darkest leather, grey beard, paler steel. To match MM9 exactly, give all three A's ramps in `tier_dwarf.py`. Eyebrows stay red on C.
- **Corrections on MM9's clips:** `arm_bump.py` Fidget L 30 deg, Fidget R 42 deg, Fidget2 L 24 deg, Search L 21 deg, Hit2 L 3 deg; `axe_lift.py` right wrist Fidget 4 deg, AttackMelee3 18 deg; `head_clear.py` head turn taken back by at most 20 % (AttackMelee3, Hit2). The hand on the hip stands further from the body than MM9's. Search L stays 4.2 cm into the body by `arm_bump.py`'s own measure (script clip; the arm gate reads 0).
- **Skirt highlight:** in Running and AttackMelee2 the bent upper skirt at the hip still catches a white crescent of light in the viewer (the leather's roughness about 0.6); the roll under it is gone. The engine draws the torso with `openyamm_specular 0`.
- **Death2:** the left thigh's outer side shows 2.1 cm through the skirt's front-left corner for 4 frames of the fall (0.15-0.2 s).
- **Silhouette:** torso, waist and thighs are vertices moved after the paint, so the bandolier and the tunic's seams sit a little closer together than painted.
- **Bandolier and buckle** are paint with no relief. The mirrored skin carries them on the true left only by the paint.
- **Shoulder plates:** the paint is smeared where the two plate pieces meet.
- **Boot cuff:** its dark lining shows with a jagged rim behind the knee in Dead at close range.
- **Under the helmet:** the inner wall reads as flat dark shapes beside the beard from directly below.
- **Rattack1:** the axe hides at 0.5 s and returns at 1.43 s as the hand closes (MM9 1.5 s). The right hand opens in between.
- **Clip events** `lunge`, `playanimsound`, `playsoundFX`: not bound.
- **Not checked:** LOD1-3 and shadow meshes by eye; thrown axe's flight and launch point; sounds; a map with these rows placed; the rest of the `actors` regression suite (only the binding cases); normal-speed playback by eye; Android. In game (r17) shows standing only: the screenshot tour pauses the world, so attack, hit and death were not seen in game. Tried for r18: `debug.actor_spawn_*` (hostile, live AI) in bootcamp brings the map's own monsters round the party and hides the dwarf; `debug.model_spawn_*` (a looping clip) placed the model floating or behind rock in that canyon, and a flat spot nearby put the camera under the terrain. Not achieved.

User artistic acceptance: "dwarf - ok" (2026-10-31)


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_dwarf_reduce_claude/`** (user-approved; ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `mm9_dwarf_reduce_claude/before/`.


**2026-11-04 later: the reduction was rolled back** (installed source = `mm9_dwarf_reduce_claude/before/`): the UV audit (`claude_shared/reduction_uv_audit.py`) found reduced faces whose UVs left the painted charts, visible in close-up. A fixed reduction may be reinstalled later; see the ledger.


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_dwarf_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_dwarf_reduce_claude/before/`.

## MM9 sockets (2026-11-10)

The installed model carries MM9's attach points as `Socket_<name>` nodes for held items (scene `held_items`, MM9's AttachProp), added after this project's install by [`mm9_held_items_claude/scripts/add_sockets.py`](../../props/mm9_held_items_claude/scripts/add_sockets.py) (`Socket_RHand1`). A rebuild installed from here drops them: run that script again and install its export (`tools/install_model.py --world mm9`).
