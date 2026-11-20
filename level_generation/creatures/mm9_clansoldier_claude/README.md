# MM9 Horde Soldier family (mm9_clansoldier) — 3D actor, 2026-10-31

MM9's Beldonian Horde, queue item 16: Horde Grunt L34 (`MONSTERS.txt` 129, `MM9 Horde A`, BELDONIAN1), Horde Warrior L44 (130, `B`, BELDONIAN2), Horde Leader L54 (131, `C`, BELDONIAN3); body `CLANSOLDIER.abc`, 30 nodes. Humanoid: built on the approved Yrsa route (MM9 skeleton, MM9 clips, grafted five-finger hands, a separate head set). Sword in the true right fist, shield on a centre grip in the true left. Progress, hashes and Meshy receipts: `creature_3d_progress.json`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_clansoldier.glb` (`tools/install_model.py --world mm9`), variants `clan_a/b/c` |
| Binding | `assets_dev/worlds/mm9/models/actors.yml`, block `mm9_clansoldier_claude`: `scale: 100` (MONSTERS Scale 1), `yaw_offset: -1.570796327`, stride walk 1.8 / run 2.9, look `Bip01 Neck, Bip01 Head`, melee impact 0.32 s (Hattack1 `Rattack`), ranged impact 0.35 s (Hattack2 `Rattack`), release socket `sword` = `Ybasesword` |
| Triangles LOD0/1/2/3 | 12,869 / 6,432 / 2,312 / 771. LOD0: limbs set 3,009 (hands 640 each), torso set 4,438 (skirt lining 870), head set 4,728 (helmet 1,116), weapons 694 |
| Skeleton | CLANSOLDIER.abc, 30 nodes, joints moved onto our mesh, rest frames = source frame turned by the least rotation onto our limb (`fit_clan.py`), + 15 finger bones per side + 8 hinges `Skirt_*` + 12 half-joint helpers `*_h` |
| Clips (30 fps) | Standing `stand`, Walking `walk`, Running `run`, Fidget `fidget1`, AttackMelee `Hattack1`, AttackRanged = AttackMelee2 `Hattack2`, Hit `wince1`, Death `die1`, Dead; script clips Fidget2, Aware, Aware2, Sleep, Block, Hit2 `wince2`, Cower, Backpedal, BackpedalRun, Death2 `die2` |
| Textures | limbs 1536 + 1K normal + 1K ORM (A, B shared; C own), torso 2048 + 1K normal + 1K ORM per tier, head 1536 + 1K normal per tier, weapons 1536x1024 + 768x512 normal and ORM per tier. 34.9 MB cooked (torso 18.9, head 7.4, limbs 5.4, weapons 3.2), 31 images |
| Meshy credits | **40 / 40**: Smart Topology body 5, head 5, three 4K body paints 10 each (backup account) |

## Findings in the source

- **No child model.** `CLANSOLDIER.abc`'s ChildModels section counts 1 (itself; `HIGHWAYMAN.abc` counts 2). All 23 clips are in the file. Same biped family as the Highwayman but without Finger02, Hattack3 or any Rattack.
- **The bind is symmetric** (arms 27 degrees down, feet apart), so no stride problem here. `mirror_glb.py` gives the true-handed source; `bone_length_audit.py` was 0 stretching on the source and on every build. `mirror_source.py` is not used.
- **The rows carry a thrown axe, the body has no throw.** `monster_data.txt` gives the rows `MM9Axe` at 100 %, MM9 runs them on `basemelee.scr`. Bound as on the Guard: `attack_ranged` is Hattack2, with the missile released at the sword. No axe model exists on the body. Worth a data decision (see Open points).
- **Other rows on this body** (Clan Soldier, Corporal, Sergeant, Town Guard, Tamur Leng with skins CLANSOLDIER*, BELDONIANDRAGON) are replaced by legacy actors in `mm9_npc_legacy_replacements.tsv`; they have no descriptors here and were not built.

## User fix, 2026-10-31 (viewer r22, 0 credits)

Feedback images `review/user_feedback_*.png`. Acceptance sheets, viewer shots: `review/sheet_fix_{a,b,c}.png` (Standing, Walking, Running, AttackMelee; front, side, back, below), `review/sheet_fix_waist.png`.

- **Shield:** the inner plate and outer plate were wound the same way (`recalc_face_normals` guesses on open islands), so from behind only the rim drew. Winding is now built in `make_weapons.py`; the back shows the planks and the handle.
- **Waist:** the garments were reduced apart, leaving a jagged gap along the sash's lower edge, in the rest pose too. The sash's lower rim now laps down and out over the skirt's top rim, both on the Spine block (`finish_clan.py`).
- **Skirt:** now hangs. Toward the hem up to 72 % of each vertex follows the thighs, blended across the front and back (`reweight.py`). `skirt_keys.py` measures against that moved skirt, lifts each panel only for its own thigh, neighbours take 55 %, capped at 45 deg. Lining is dark cloth per tier, not black.
- **Trade, as measured by `skirt_gate.py`:** thighs through the skirt were 0 in Walking and Running while it fanned out. Now **Walking 1.4 cm (18/44 frames), Running 4.0 cm (18/25), Backpedal and BackpedalRun 1.4 cm**. Other living clips 0.3-2.0 cm, Cower 5.0, Death 7.5, Death2 6.3, Dead 2.1. Running's front hinges sit at the 45 deg cap: more lift clears it but brings the fan back.
- **Regression on r22:** `mm9_actor_models_build_every_binding` PASS, 140 descriptors on 57 models, 0 failed; validator 0 refused. The run was stopped after that case.
- **Not rerun after this fix:** collapse, arm and hand, jitter, grip, blade, detached, and the sheets and strips listed below (they show the fanned skirt). The Checks table below is the build before it, except this list. The shoulder holds in Walking, Backpedal and BackpedalRun were set for the old lifted skirt and are probably larger than needed now.

## Deviation: per-tier images

The rule is one shared set, region mask and colour ramps. The MM9 skins differ in **design**: Grunt studded quilted coat and scale panels, Warrior strip lamellar with a knotwork disc, plate skirt and a laminated neck guard, Leader breastplate, red-and-white lamellar, a painted lion helmet, knee plates and greaves. No ramp makes those. Per tier: torso set (coat, sleeves, skirt, sash), head set, weapons set. Limbs (legs, boots, gloves) shared by A and B; C has its own for knee plates and greaves, and takes the Grunt's thigh texels above the knee. Full design differences, like the Highwayman. All variant images upload for one tier (the Guard's finding); here the cost is up to 34.9 MB on any map with this body.

## Route (scripts/)

0. **Sources:** `convert_sources.sh` (`convert_abc_model.py --scale 0.0256` per tier, `mirror_glb.py` to `source/true/`), `make_refs.sh` for the masters' inputs.
1. **Masters** (Codex through `codex_slot.sh`): `references_hd/` five tier A views, `references_tiers/` four views each of B and C, `references_head/` clay sculpt and seven painted views per tier on clay renders of our own head, `references_shield/` flat outer and inner faces per tier.
2. **Meshy:** Smart Topology 15k on the body and on the sculpt (`requests/`). Three 4K paints on one layout.
3. **Clean** (`clean_clan.py`): height scale, each central piece on its mid-plane, figure's right half kept and mirrored, reduced per garment. The nine Meshy skirt panels are dropped (paint only): no shards off the cloth. The glove piece is split at the wrist, the bracer stays with the sleeve.
4. **Head** (`head_prep_clan.py`, `graft_head_clan.py`): Meshy's head shell had 582 boundary edges and crossed layers at the brim, and every decimation tore there (five attempts). Right half mirrored, all holes filled, voxel level set, staged reduction: one clean shell. Dome and brim rebuilt as rings of the raw shell's radius. Meshy's body neck is a mess behind the collar, so the new neck runs down in rings, its front on the old surface (the bare V). Head scale 0.345 against the sculpt's 0.31: MM9's head is large on this body (top to chin 38 cm; ours 29 cm).
5. **Rest and weights:** `fit_clan.py`, `rig_clan.py` (structural bands, eight skirt hinges at the sash, nape curtain rigid on the head), `graft_hands.py` (MPFB), `glove_clan.py` (4 mm thicker: a leather glove), `helpers_clan.py`, `uv_clan.py` (never re-run), `reweight.py`.
6. **Paint:** `compose_clan.py`, gentle grade, `tone_clan.py` (soft knee on luminance, an extra grey term), `project_head.py`, `finish_tex.py` (Leader's thighs, the sash tails' colour, cuirass brightness, dark blocks).
7. **Finish** (`finish_clan.py`): fists, sword, shield, handle, sleeve rims, linings. `make_weapons.py` first.
8. **Clips** (`scripts/rebuild.sh`, `corrections.sh`): `clips_mm9.py`, `finger_keys.py`, `arm_hold.py`, `half_keys.py`, `skirt_keys.py`, `arm_bump.py`.
9. **Runtime:** prepare, LODs, shadow fix, `tier_materials.py`, floor, winding, install, viewer. `scripts/retier.sh` from the tier step. Binding: `flock level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock python3 <project>/scripts/bind_actors.py` from the repo root.

Rebuild after the paid steps: `scripts/textures.sh`, then `scripts/rebuild.sh --install` (project folder), then `review_root.py`. `scripts/rebuild_mesh.sh` replays the mesh chain; never after the upload went to Meshy.

## Weapons

No Codex master for the sword, as the brief's lesson says: outline and stations are MM9's vertices, blade 79 cm, guard 21 cm, grip 14 cm, disc pommel; rigid on `Ybasesword`. Procedural paint, pale steel, verdigris on the Leader as BELDSWORDOLD. Shield: MM9's coffin outline made symmetric, 1.32 x 0.61 m, a 3 cm dome (MM9's is flat), own rim faces; Codex painted the flat faces on the outline template, no refusal. Rigid on `Ybaseshield`, MM9 keeps both rigid to the hand (0.0-0.1 deg in `grip_gate.py`).

**Fists:** per finger on a grid round the grip, thumb over the fingers (`finish_clan.py`, from the Guard). Right: a constant wrist turn of 17 deg lines the knuckles up with MM9's axis, the sword is built turned back by it, so it points where MM9's points. Left: MM9's arm meets the shield square on, so the shield is a **centre grip**: a handle along the knuckles with two iron struts to the plate, no wrist turn, the shield in MM9's pose against the hand.

## Checks

Final build (viewer r18). Gate outputs: `review/gates/`. Clip gates ran on r14; the changes after it are a uniform raise of Running and BackpedalRun (root height only) and image changes (no geometry). Detached, flat shading, texture quality, winding and floor audit are from r16. `sheet_heads`, `sheet_neck_mouth` are r18; strips, `sheet_tiers`, `sheet_closeups_*`, `sheet_hands`, `sheet_mm9_vs_ours` and `ingame_sheet` are r16, which differs from r18 only by the nasal bar's paint.

| Gate | Result |
|---|---|
| `bone_length_audit.py` | 0 stretching of 12 |
| Handedness | sword and `R Hand` anatomical right |
| `skirt_gate.py`, 48 fps, thigh vertices through the outer skirt, per clip | r22: see User fix above (Walking 1.4 cm, Running 4.0 cm). The fanned r18 skirt read 0 in all living clips |
| `arm_hand_gate.py --outer-only --exact`, 48 fps | every hand under 1 cm in every clip except Death L 1.1 cm, 1 frame, and **Sleep R 5.0 cm, 10 frames** (script clip). Finger stretch max 1.94 |
| `jitter_gate.py` against the untouched MM9 clips | **0 fails** |
| `grip_gate.py`, every clip, both hands | fingers inside the grip 0.0 cm; wrap per finger minimum 105, median 165 deg |
| `blade_gate.py`, sword against skin and cloth | 0 over 1 cm in every driven clip. Block 0.6 cm. Script clips: Sleep 4.2 cm in the skirt, 10 frames; **Cower 6.0 cm in the head, 26 frames** |
| `blade_gate.py`, shield against skin and cloth | Running 0.7 cm, AttackMelee 0.9, Dead 0.1. **Death 4.0 cm into the thigh, 4 frames** mid-fall. Sleep 3.4 cm (script clip) |
| `detached_parts_audit.py` | **0 detached**, 24 components |
| `flat_shading_check.py` | 0.00-0.01 on all sets |
| `check_winding.py` | 0 inverted |
| `texture_quality.py` | limbs atlas 57.3 %, spread 1.52 (dense gloves), stretch 1.2; torso 69.1 %, stretch 1.0; head 61.1 %, fragments 0.3 %, stretch 1.13, spread 2.06 (face at twice the helmet's density by design). Torso spread is meaningless (lining on one texel). Weapons stretch 4.58 on the rim faces |
| `orient_gate.py`, head and feet against MM9 per frame | head at the mean under 1 deg in Standing, Walking, Running and both attacks, worst Hit 2.6 and Death 2.1; head maximum Death 9.8, Hit2 8.7 (thinned keys and the floor pass). Feet 2.8 constant (our stance), up to 9.7 in Running and the deaths |
| `floor_audit.py --world mm9 --match 'MM9 Horde*'` | stand 0, walk -1.6..+1.2, living -1.6, dead 0: **0 of 3 with floor problems** |
| `run_creature_review.py check` | 57 switches, 0 failed |
| Regression `mm9_actor_models_build_every_binding` | PASS, 125 descriptors on 52 models, 0 failed. The validator on r16: no Horde refusal; 131 descriptors, 3 refused, all `MM9 Nobleman A/B/C` (another agent's new binding: invalid key `attack_ranged`) |
| In game (`bootcamp.odm`, review root) | `review/ingame_sheet.png`: three tiers with their own costumes, hostile, attack, death, corpse |

Collapse gate, faces collapsed below 20 % of rest area or flipped, worst single frame per region, weapons excluded. `body` holds the fists' finger faces, which fold inside the curl by design. Exposed = faces any camera can see at the clip's worst frame.

| Clip | Knee | Groin | Elbow | Armpit | Ankle | Wrist | Neck/head | Body | Face-frames | Exposed |
|---|---|---|---|---|---|---|---|---|---|---|
| Standing | 0 | 0 | 2 | 0 | 0 | 0 | 5 | 20 | 1311 | 20 |
| Walking | 0 | 0 | 5 | 0 | 0 | 0 | 7 | 24 | 777 | 24 |
| Running | 0 | 0 | 4 | 0 | 0 | 0 | 11 | 22 | 475 | 29 |
| Fidget | 0 | 0 | 2 | 0 | 0 | 0 | 15 | 20 | 1891 | 25 |
| Fidget2 | 0 | 0 | 11 | 0 | 0 | 0 | 32 | 25 | 3866 | 43 |
| Aware | 0 | 0 | 17 | 0 | 0 | 1 | 14 | 21 | 1225 | 25 |
| Aware2 | 0 | 0 | 22 | 0 | 0 | 0 | 10 | 22 | 1631 | 22 |
| Sleep | 0 | 0 | 2 | 0 | 0 | 0 | 5 | 23 | 1595 | 20 |
| AttackMelee | 0 | 0 | 6 | 0 | 0 | 4 | 33 | 26 | 938 | 30 |
| AttackMelee2 | 0 | 0 | 17 | 0 | 0 | 0 | 16 | 22 | 769 | 30 |
| Block | 0 | 0 | 25 | 0 | 0 | 3 | 18 | 24 | 976 | 30 |
| Hit | 0 | 0 | 2 | 0 | 0 | 0 | 32 | 21 | 745 | 24 |
| Hit2 | 0 | 0 | 4 | 0 | 0 | 0 | 6 | 21 | 639 | 21 |
| Cower | 0 | 1 | 27 | 7 | 1 | 0 | 27 | 49 | 4301 | 43 |
| Backpedal | 0 | 0 | 5 | 0 | 0 | 0 | 7 | 24 | 777 | 24 |
| BackpedalRun | 0 | 0 | 5 | 0 | 0 | 0 | 7 | 23 | 551 | 23 |
| Death | 0 | 16 | 35 | 12 | 0 | 1 | 73 | 30 | 2492 | 37 |
| Death2 | 0 | 14 | 2 | 0 | 0 | 2 | 29 | 22 | 1133 | 23 |
| Dead | 0 | 0 | 28 | 5 | 0 | 1 | 16 | 25 | 2325 | 40 |

These are real fold counts, not excused. Where the big ones are (`collapse_where.py`): neck/head faces are 0.02-2.6 cm² flips at rest height 1.76-1.82 m on the back of the neck behind the nape curtain (the head turns against the neck there); elbow is the shield arm's inner bend, at the bend limit MM9 uses in Block, Aware and Dead. First rig for comparison: elbows 34, knees 0, ankles 0-1, armpits 22.

Sheets (viewer shots unless noted): `review/sheet_mm9_vs_ours.png` (MM9 is a Blender render, seven clip extremes, three tiers), `review/sheet_tiers.png`, `review/sheet_heads.png` (each tier's head from six sides, framed by head-local cameras), `review/sheet_closeups_{a,b,c}.png` (knees, groin, armpits, elbows in Cower, Death, Dead, Running), `review/sheet_neck_mouth.png` (neck and mouth in Cower and Dead, every tier), `review/sheet_hands.png` (both fists, Standing, AttackMelee, Dead), `review/strips_{a,b,c}.png` (every clip, six times, two views), `review/ingame_sheet.png`.

## Deviations and open points

- **Per-tier images**: above.
- **Corrections on MM9's clips**, all single smooth curves (`corrections.sh`): right shoulder held out 13 deg over Walking, Backpedal, BackpedalRun, 6 over Running, so the sword clears the lifted skirt (the sword hand sits at the hip in MM9's walk); 9 deg windowed in Fidget, 10 in Sleep, 5 in Block; left shoulder -9 deg in Death and Dead and 5 in Fidget2's end, so the shield clears the skirt. `arm_bump.py` Fidget2 R.
- **Skirt**: eight hinges at the sash plus thigh weights toward the hem, lift solved on keys (User fix above).
- **Sash tails**: mirroring Meshy's single tail gave two, unseen by the paint and ending in a fin. They are pulled up into stubs and recoloured per tier.
- **Skirt panels**, MM9's scale and plate rows, are paint and normal map, not geometry.
- **Head**: painted by projection on our own clay, no Meshy paint. Larger than the sculpt (scale above), still 9 cm shorter top to chin than MM9's. The voxel shell closed the lids round small eye parts, so the irises are paint over both. The nasal bar is projected straight through from the front, with dark edges; the voxel shell fused it to the nose bridge, so from the side it reads as a thick plate over the nose, not a clean bar standing clear (the sculpt's bar stood 5 mm off). Looked at on the Grunt close up; two paint passes, the geometry was not rebuilt.
- **Tone**: `tone_clan.py` darkens pale fine patterns (mail rings, scales, fur) against Meshy's paint; viewer lights run brighter than the game. Mail still shows brighter rings than MM9's blurred skin close up.
- **Row height**: the body is 2.08 m at `scale: 100` against the row's height 155; collision keeps the row's value. The health bar drew above the helmet in the in-game shots.
- **`MM9Axe` on the rows**: thrown from the sword's grip with no throw clip. Either the table should drop the missile (MM9 plays them melee) or the body wants a throw.
- **Not used**: `clansetup02`, `static_die1/2`. Clip events `lunge`, `playanimsound`, `playsoundFX`, `speakanimsound` were not bound.
- **Not checked**: LOD1-3 and shadow meshes by eye; normal-speed playback by eye (only frame strips); missile flight and launch point in game; sounds; a map with these rows placed (the check ran in `bootcamp.odm` with spawned rows); the full `actors` regression suite (the two binding cases passed; the run hit my 15-minute limit in its later map cases, and it ran before the last floor and image changes, after which I reran only the validator); Android; the Leader's thigh patch against the knee plate close up from behind; Sleep and Cower contacts were not worked further (script clips nothing drives).

## Dropped-clip pass, 2026-10-31 (run 2, 0 credits)

`scripts/roles_clan_extra.json`: DeadStatic (`static_die1`) and Dead2 (`static_die2`), MM9's static corpse poses as 1 s holds, through finger_keys, half_keys, skirt_keys (two-key clips not eased) and a floor ground-loop, grafted onto the installed export with `claude_shared/graft_clips.py`. Bound `dead_static`, `dead2` (also on MM9 110 Town Guard). Hands 0.4 cm, sword 0, shield 0.5 cm, floor 0. Numbers, strips: `review/clips_restore/`; summary `devdocs/mm9_rework/overnight/status/clips_groupA.md`.

User artistic acceptance: "clan soldier - good" (2026-10-31)


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_clansoldier_reduce_claude/`** (user-approved; ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `mm9_clansoldier_reduce_claude/before/`.


**2026-11-04 later: the reduction was rolled back** (installed source = `mm9_clansoldier_reduce_claude/before/`): the UV audit (`claude_shared/reduction_uv_audit.py`) found reduced faces whose UVs left the painted charts, visible in close-up. A fixed reduction may be reinstalled later; see the ledger.


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_clansoldier_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_clansoldier_reduce_claude/before/`.
