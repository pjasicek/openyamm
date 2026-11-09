# MM9 Half Orc family (mm9_dookmilitia) — 3D actor, 2026-10-31

Queue item 15: Half Orc Recruit L14 (`MM9 Half Orc A`), Soldier L24 (`B`), Captain L35 (`C`); body `DOOKMILITIA.abc`, 32 nodes. Humanoid on the approved Yrsa route (MM9 skeleton, MM9 clips, grafted five-finger hands, separate head set), close to `mm9_highwayman_claude/`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_dookmilitia.glb` (`tools/install_model.py --world mm9`), variants `dook_a/b/c` |
| Binding | `assets_dev/worlds/mm9/models/actors.yml`, block `mm9_dookmilitia_claude`: scale 100, stride walk 1.65 / run 3.3 (Highwayman's values scaled by foot travel, 1.04), melee impact 0.3 s (Hattack1 `rattack`), ranged impact 0.5 s from the dagger socket |
| Triangles | LOD0/1/2/3 12,906 / 6,442 / 2,314 / 769 |
| Skeleton | DOOKMILITIA.abc, joints on our mesh, rest frames turned onto our limbs (`rerest.py`), 15 finger bones per side, `Skirt_*` hinges, half-joint helpers |
| Clips | 21 + Dead: every clip of DOOKMILITIA.abc and its child FIGHTERBASE.abc (`merge_child.py`) except the bind poses `militiasetup01` and `static_model`; `cowerstart` + `cower` + `cowerend` are one Cower, `tauntSAVE` is Taunt2 (run 2) |
| Meshy credits | **40 / 40**: Smart Topology body 5, head 5, three 4K paints 10 each. None spent on the resume or on run 2 |

## Route

`mirror_glb.py` for true handedness (the bind is a stride, never `mirror_source.py`), then Codex masters, Meshy, clean, head graft, fit, weights, hands, helpers, UVs (frozen: `work/uv_v1.blend`, never re-run `uv_dook.py` or `rebuild_mesh.sh`), paints, `project_head.py`, `scripts/rebuild.sh [--install]`, `scripts/retier.sh` from the tier step. `textures.sh` ends with `tier_paint.py`.

## Changes on the resume (2026-10-31)

- **Left hand:** the thumb was bent back along the wrist and read as a pointing finger. The left fist now uses the grip solver round a thin virtual grip.
- **Head layers (the Guard lesson):** the right side view had drifted: its strap lay on the cheek behind the bar and skin lay on the bar, in tiers A and C. `project_head.py` now mirrors the left bar onto the right bar and the left cheek, jaw and ear onto the right (|x| > 5.5 cm, fading over 3 cm). The middle of the face comes from the front view alone. A z-buffer per view was already there; it could not catch a drifted paint.
- **Collar:** the viewer's background showed through beside the neck in every tier. A dark well of 64 faces now runs from the yoke's rim toward the neck.
- **Tier C gloves:** MM9's Captain has dark gloves; the hands were bare skin. `tier_paint.py`, Captain's limb image only.
- **Tier A lacing:** Codex's cream X lacing, which MM9 does not have, is cloned out (colour and normal).
- **Cheek bars:** skinned from the skin beneath them and raised off the collar. This cut the detached audit from 3 parts to 1, not to 0.
- **Clips:** `arm_out.py` gained a hold mode and a world axis (Death, Dead, Sleep, AttackRanged, Cower), `arm_bump.py` on Fidget2 and Cower, a smoothed `R UpperArm_h` track in Hit2, wider skirt margins in Cower and AttackMelee2/3.

## Run 2 (2026-10-31): the open gates closed

The user accepted r9 ("half-orc - fine"). Run 2 kept its mesh and every image byte for byte (checked against `work/accepted_r9.glb`: all 22 images identical, LOD0 vertices identical except the two cheek bars' 38 lower vertices, at most 0.9 cm) and changed clips only where a gate failed. Viewer r12, installed.

- **Right cheek bar detached 5.0 cm (Sleep):** the bars' lower ends stood 3 mm over the collar, within the audit's 4 mm touch distance, so the audit took the collar for the bar's holder and saw it lift off with the head bowed. `finish_dook.py` now leaves them 1.2 cm over it (`BAR_GAP`): the bars hang from the helmet alone. Detached 0.
- **Cower hilt through the head 5.6 cm, right hand 2.5 cm:** new `scripts/sword_clear.py` (after `arm_bump.py`, jobs in `sword_jobs.txt`): one raised-cosine window over the contact (0.65-2.17 s, 0.35 s ramps), the upper arm and wrist turned about constant axes that carry the deepest point straight away from the head's centre, least amplitude solved on blade_gate's points and arm_hand_gate's measure: 16 deg (upper arm 9.6). Blade 0.6 cm (the grip fingers), hand 0.4 cm, jitter 0 fails.
- **Hands 1.5-2.5 cm in Sleep, Death, Dead:** the `arm_out.py` holds went from 12 to 18 deg (Sleep R) and 17.5 to 23.5 deg (Death and Dead L, same axis so the fall ends on the corpse). All under 1 cm.
- **Running floor -4.5:** `--smooth-loop Running 0.05` low-passed the per-key raise and let contact dip. 0.015 now: floor audit -1.1 at keys, -1.85 cm at 48 fps; pelvis acceleration 3.5 cm/f^2 against 3.1 for the raw clip and 2.5 before.
- **Soft `clips_mm9.py` line** (`np.sign(off) * np.maximum(np.abs(off) - 0.004, 0) * k`) in place of the hard 4 mm cut; every clip rebuilt with it.
- **Taunt2** (`tauntSAVE`, 1.5 s, a different taunt from `taunt`) added and bound as `taunt2` in `script_clips`; nothing drives it.
- Tried and dropped: evening the albedo of the cheek strip under the lifted bars (`cheek_tone.py`, deleted). The step reads as shading (the fill's flat relief and the built bar's edge), not tone, and tier C got a yellow patch. The accepted images are kept.
- `tier_paint.py`'s lace step on `dook_torso_a_normal.png` is **not idempotent** (a rerun moved 962 texels by up to 7): do not rerun `textures.sh`/`tier_paint.py` without restoring that image first. Run 2 restored it from the accepted GLB.

## Run 2, follow-up (coordinator, 2026-10-31): collapse and the cheek strip, viewer r17, installed

**Collapse, what the counts were:** `scripts/collapse_diag.py` split the worst regions by material, rest height and bone. The neck and head counts are all painted skin of the head set: faces under the chin and at the hood seam (`Bip01 Head_h`, `Neck`) flipping as the head bows, not the helmet, bars or collar. AttackMelee3's torso count was the mantle at the clavicles (`Spine3`). The shoulder counts are the shoulder puff and its lining (`Clavicle`, `UpperArm_h`, |x| over 16.5 cm).
**What was done:** `scripts/weight_smooth.py` (zones in `weight_zones.txt`, run in `rebuild.sh` on the body before the clips): a weight Laplacian per zone that keeps the zone's share on its own joints, welded across materials, islands under 60 vertices (bars, studs) untouched. Zones: neck (Spine3 to Head, 1.55-1.76 m, 40 passes), hood seam (1.70-1.86 m), belly (Spine-Spine3, 1.20-1.50 m), clavicles (Spine3 and Clavicle only). The half-joint helpers at neck and shoulders were already in the rig (`helpers_dook.py`); moving their pivots was not tried.
- Tried and dropped: a full shoulder zone (with `UpperArm` and `UpperArm_h`). It cut AttackMelee3 shoulders to 4/6, Sleep 8/6, Death 10, Hit 7, but moved the puff's weights off the arm and opened a dark gap along the puff's hem in AttackMelee3 (`work/run2/sh_cmp14.png`). A zone kept off the puff (|x| <= 16.5 cm) changes nothing: the counts are on the puff itself.
- Side effects fixed: the belly smoothing put the Sleep right hand 1.2 cm into the belly (hold 18 -> 21 deg) and the sword 1.3 cm into the left upper arm in Sleep (`sword_clear.py` Sleep:R, 4 deg, constant over the loop). Sleep L hold 4 -> 8 deg.

Collapse, worst single frame, r12 -> r17 (regions asked for, and every region at 20 or more):

| Clip | Neck | Head | Torso | Shoulder L / R |
|---|---|---|---|---|
| Sleep | 58 -> 1 | 66 -> 7 | 4 -> 6 | 30 / 24 -> 35 / 28 |
| Death | 63 -> 7 | 49 -> 24 | 4 -> 0 | 47 / 10 -> 48 / 10 |
| Dead | 54 -> 5 | 22 -> 24 | 3 -> 0 | 47 / 3 -> 48 / 4 |
| Hit2 | 45 -> 2 | 51 -> 10 | 2 -> 2 | 15 / 4 -> 14 / 6 |
| AttackMelee3 | 46 -> 5 | 14 -> 11 | 54 -> 12 | 51 / 33 -> 25 / 16 |
| AttackMelee / 2 | 21 / 22 -> 4 / 5 | 12 / 15 -> 12 / 13 | - | - |
| Cower | 25 -> 3 | 24 -> 6 | 27 -> 6 | 8 / 19 -> 8 / 12 |
| Hit | - | - | - | 7 / 43 -> 8 / 44 |
| Fidget3 | - | - | - | 30 / 4 -> 31 / 5 |
| Death2 | 36 -> 4 | 48 -> 10 | - | 33 / 32 -> 34 / 33 |

**Still at 20 or more (gate failed):** the shoulder puff in Sleep 35/28, Death and Dead L 48, Death2 34/33, Fidget3 L 31, AttackMelee3 L 25, Hit R 44; head 24 in Death and Dead (the back of the hood against the ground-side shoulder in the corpse pose). Close-ups of those frames (`review/sheet_shoulders_final.png`, `sheet_neck_final_{a,b,c}.png`) show no visible fold, which does not excuse the count.

**Cheek strip under the bars:** one paint source per tier, the left side Codex view with the lower bar painted out by Codex (`references_head/strip/<t>_03_left_nobar.png`, brief `CODEX_BRIEF_STRIP.md`, masks from the strip's projection). `scripts/project_strip.py` registers the edit to the original, seamless-clones it (a Laplace membrane at quarter resolution, so the edit meets the original paint at the red area's edge), projects it onto the strip with project_head.py's camera and silhouette fit, mirrors it onto the right strip (as project_head.py mirrors the cheek), and writes the head colour, final and normal images; the strip's normal is project_head.py's luminance normal of the new colour, faded in over 1.2 cm. Only the head images changed; `tier_paint.py` was not run. Head-space box checked by a debug paint in the viewer. 0 Meshy credits; 3 Codex image edits.

## Run 2, verification (coordinator, 2026-10-31): hood hem, viewer r19, installed

**Hood hem from behind (r17):** the neck zone had moved the hood's back and side hem from `Neck` onto `Head`/`Head_h`. Seen from behind and both rear quarters (`review/sheet_hood_back_{a,b,c}.png`), with the head bowed the hem lifted with the head and opened a gap showing the inside of the hood and the bare nape, in Sleep and Hit2, every tier (r12 against r17: `work/run2/hood_cmp.png`). **Fixed in r19:** `weight_smooth.py --keep` boxes (`scripts/weight_keep.txt`: the hood's back and sides, rest y 1.655-1.80 m) give those vertices their own weights back, faded over 2 cm so no step is left. The hem hangs from the neck again as on r12 (r18 kept a wider box and showed the same; r19 is the narrow one).
**What it costs:** the collapse counts at the hood hem come back: Death neck 7 -> 67, Dead neck 5 -> 54, AttackMelee3 neck 5 -> 49 and torso 12 -> 45, AttackMelee / 2 neck 23 / 24. These are the hem itself folding as the head turns (they were r12's counts). Sleep and Hit2 stay low (neck 5 / 6, head 8 / 11). Arm and hand rerun on r19: every clip under 1 cm. The Cower sword clear re-solved to 16 deg as on r12 (blade 0.6 cm).

## Checks

Final build r17 (run 2 follow-up), installed; all gates rerun on it (r12 numbers in `review/gates_r12/`) (`scripts/gates_run2.sh`, `review/gates/`). Before -> after where run 2 changed something.

| Gate | Result |
|---|---|
| `bone_length_audit.py` | 0 stretching of 12 |
| Handedness | `R Hand` and sword anatomical right |
| `skirt_gate.py` 48 fps (thighs through the skirt) | Walking 0/53, Running 0/20, Backpedal 0/53, BackpedalRun 0/25, all one-shots 0 except AttackMelee2 2/29 at 0.2 cm, AttackMelee3 1/33 at 0.2 cm, Cower 75/145 at 1.1 -> **58/145 at 0.9 cm** |
| `cloth_torso_gate.py` (new: skirt through the torso) | 0.0 cm in every clip, bind 0.0 |
| `arm_hand_gate.py` (r17) | Cower R 2.5 -> 0.0, Sleep R 1.6 (forearm 1.7) -> 0.0, Death L 1.6 -> 0.0, Dead L 1.5 -> 0.0 cm. **Every clip under 1 cm**; worst Fidget3 L 0.6, Fidget2 L 0.5. Wrist swing over 60 deg in AttackMelee R 97, Death L 103, Dead L 95, Death2 L 81, AttackMelee2 R 82, Taunt R 78, AttackRanged L 72, Taunt2 R 65: MM9's own wrists (jitter gate: 0 excess over MM9) |
| `jitter_gate.py` against MM9 | 0 fails (Cower R upper arm excess 0.37 deg/f) |
| `grip_gate.py` | inside the grip at most 0.5 cm; wrap 165-225 deg per finger, thumb 90-120, Sleep thumb 75 |
| `blade_gate.py` sword against skin (r17) | Cower 5.6 -> **0.6 cm** (the grip fingers), Sleep 0.6 cm. 0 frames over 1 cm in every clip; Death 0.1, Dead 0.0 |
| `detached_parts_audit.py` | 1 (right cheek bar, 5.0 cm) -> **0** |
| `flat_shading_check.py` | body 0.00-0.01, weapon 0.07 |
| `check_winding.py` | 0 inverted |
| `texture_quality.py` | unchanged: limbs atlas 57.9 %, torso 63.5 %, head 62.6 %, head spread 1.27; limbs spread 1.49 (target 1.3); weapon atlas 53.8 % |
| `floor_audit.py` | living -4.5 -> **-1.1** (tolerance 2.5) on Half Orc A/B/C and Town Guard 108; stand 0, walk -1.1..+0.8, dead 0 |
| `orient_gate.py` | head against MM9 at most 12.5 deg (Death), feet 9.9 deg (Death2 L) |
| Regression `mm9_actor_models_build_every_binding` (r17) | PASS, 149 descriptors on 59 models, 0 failed; MM6-8 case PASS (647 on 185). Suite cut at 600 s after these |
| `run_creature_review.py check` | 66 switches, 0 failed |
| In game | Dook's Castle (`dookscastle.blv`, review root): three tiers and Town Guard 108 spawned, hostile Captain fights, Recruit dies and falls on the floor, then the engine's corpse dissolve. `review/ingame_sheet.png`, `review/ingame_sheet2.png` |

Collapse gate on r12 (before the follow-up; r17 numbers above), worst single frame per region (`review/gates/collapse.txt`), unchanged by run 2 within a few faces. Knees and hips are under 20 in every clip. Regions at 20 or more:

| Clip | Shoulder L/R | Torso | Neck | Head |
|---|---|---|---|---|
| AttackMelee | - | - | 21 | - |
| AttackMelee2 | - | - | 22 | - |
| AttackMelee3 | 51 / 33 | 54 | 46 | - |
| Hit | - / 43 | - | - | - |
| Hit2 | - | - | 45 | 51 |
| Cower | - | 27 | 25 | 24 |
| Fidget3 | 30 / - | - | - | - |
| Sleep | 30 / 24 | - | 58 | 66 |
| Death | 47 / - | - | 63 | 49 |
| Death2 | 33 / 32 | - | 36 | 48 |
| Dead | 47 / - | - | 54 | 22 |

These are real fold counts and higher than the Highwayman's. The head and neck ones are small faces under the chin with the head tucked; the shoulder ones in AttackMelee3 are flips on the inner side of the mantle, and close-ups of that frame look clean. Neither is excused.

Sheets read at full size in run 2 (r12 unless noted; r17: `strips_a.png`, `sheet_heads.png`, `sheet_neck_final_{a,b,c}.png`, `sheet_shoulders_final.png`): `review/strips_{a,b,c}.png` (all 22 clips with Dead, six times, quarter and side), `review/sheet_heads.png` (every tier front, quarter, right, left; full-size shots in `review/run2/heads/`), `review/sheet_closeups_{a,b,c}.png` (knees, groin, armpits, elbows, neck, head in Cower, Death, Dead, Running), `review/sheet_neck_mouth.png` (neck and mouth where the collapse gate counts folds: Sleep, Hit2, AttackMelee3, Cower, Death, Dead, every tier), `review/sheet_cower_taunt2.png` (the Cower fist and hilt in front of the face; Taunt2's raised arm), `review/sheet_hands.png`, `review/sheet_tiers.png`, `review/sheet_mm9_vs_ours.png`, `review/ingame_sheet.png`, `review/ingame_sheet2.png`.

What the reads found (not fixed, none a gate):
- **Cheek strip under the bars:** fixed in the follow-up (above); read on r17 at full size from both sides, every tier (`review/run2/heads_final/`).
- **Shoulder puff from above in Death and Dead (left arm raised over the head):** the puff's scalloped hem stands open round the upper arm and shows its dark inside; reads as a ragged shell at close range.
- **Taunt2 (script clip, nothing drives it):** with the right arm high a pale crescent shows at the sleeve top under the mantle edge, all tiers.
- Cower: the fist and cross-guard sit in front of the face and touch the helmet rim from the camera's view; the blade gate measures no pass (0.6 cm at the grip fingers).

## Deviations and open points

- **Per-tier images:** the tiers differ in design, as on the Highwayman: torso and head per tier, limbs shared by A and B, C own. 57.8 MB GLB; cooked size not measured.
- **Right cheek and bar are a mirror of the left** in all tiers, against MM9's slight asymmetry.
- **Cheek bars end about 5 cm higher than built**, to clear the collar.
- **Tone:** in unlit renders the albedo is close to MM9 tier by tier. The viewer runs brighter, so tier A reads more orange than MM9's studio renders. Left as painted. Mail rings are finer and flatter than MM9's.
- **Neck under the jaw** is filled from seen skin plus noise, softer than the cheek. The underside of the nose is dark and faceted from below.
- **Dead L hand** and **Sleep arms** carry constant shoulder offsets of 23.5 (Death/Dead L), 18 (Sleep R) and 4 deg (Sleep L); Cower R a 16 deg window (`sword_clear.py`).
- **Clips kept from the ABC:** all but the bind poses (`militiasetup01`, `static_model`). The cower set is one clip (`cowerstart` + `cower` + `cowerend`), not three. `taunt2` is not on Town Guard 108's binding (it lives in the `mm9_guard_claude` block, not ours).
- **Left hand holds no knife:** MM9's dagger piece is one empty face.

## Not checked

- Playback at normal speed by eye (frame strips and timed shots only).
- LOD1-3 and the shadow meshes by eye (LOD2/3 were re-decimated by the rebuild; triangle counts unchanged).
- In game: only Dook's Castle start room with spawned rows; the 42 placed Half Orcs upstairs, the thrown knife, its socket, sounds and the Town Guard rows on a town map were not seen. The engine's corpse dissolve hides the corpse about a second after it lands.
- The cheek-bar change against the accepted r9 side by side in the viewer (the old GLB lacks Taunt2, so the viewer would not load it in place); compared by mesh diff only (38 vertices, at most 0.9 cm).
- On r19: strips of tiers B and C, `sheet_closeups_{a,b,c}`, `sheet_hands`, `sheet_tiers`, the hood from behind and the in-game run (Dook's Castle) are r19 and were read; tier A's strips and `sheet_heads` are r17 (r19 changed only the hood hem's weights). `sheet_mm9_vs_ours` is r12.
- Android, cooked size, GPU memory.

User artistic acceptance: "half-orc - fine" (2026-10-31)


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_dookmilitia_reduce_claude/`** (user-approved; ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `mm9_dookmilitia_reduce_claude/before/`.


**2026-11-04 later: the reduction was rolled back** (installed source = `mm9_dookmilitia_reduce_claude/before/`): the UV audit (`claude_shared/reduction_uv_audit.py`) found reduced faces whose UVs left the painted charts, visible in close-up. A fixed reduction may be reinstalled later; see the ledger.


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_dookmilitia_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_dookmilitia_reduce_claude/before/`.
