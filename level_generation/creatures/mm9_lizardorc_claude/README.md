# MM9 Lizard-Orc family (mm9_lizardorc) — 3D actor, 2026-10-31

MM9 `LIZARDORC.abc` (42 nodes, 15 clips, no child model): rows 189 Lizard-Orc L40 (`MM9 Lizard-Orc A`), 190 Warrior L60 (`B`), 191 Mage L80 (`C`). One skin `LIZARDORC.dtx` for all three, cutlass `LIZORCCUTLASS.dtx`.
Humanoid route: a Bip01 biped with two arms and two legs, tail, jaw and tongue. Meshy body and open-mouth head on MM9's skeleton, MM9's own clips. Progress and Meshy receipts: `creature_3d_progress.json`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_lizardorc.glb` (`tools/install_model.py --world mm9`), variants `liz_a/b/c` |
| Binding | `assets_dev/worlds/mm9/models/actors.yml`, block "MM9 Lizard-Orc family". Scale 100 (MONSTERS Scale 1), `yaw_offset` -1.570796327, stride walk 1.7 / run 2.5 (mean planted foot), melee impact 0.304 s (`Rattack`), ranged and cast 0.5 s released at `cast_hand` = `Bip01 L Finger11` (MM9's RangeAttack socket is on the LEFT hand), look on neck and head (HeadTurn 1) |
| Triangles LOD0/1/2/3 | 13,881 / 6,922 / 2,480 / 816 (r16, r17). Body 8,166, head 4,920, cutlass 795 |
| Skeleton | MM9's 40 joints, bind = MM9's rest (exactly symmetric), + Finger2/3 chains, third phalanges, 11 half-rotation helpers, `XFlap` hinge at the belt. 68 joints |
| Clips (30 fps) | Standing, Walking, Running, Fidget, AttackMelee `Hattack1`, AttackRanged `Rattack1`, Hit, Death, Dead; script clips AttackMelee2, Fidget2, Taunt, Hit2, Death2, Backpedal, BackpedalRun |
| Textures | one shared set for all tiers: two body pages 2K, head 2K, normal, ORM and mask 1K per set, cutlass 1024x512 + 512x256 maps. No per-tier image. Deviation: the second body page, about 7 MB more colour |
| Meshy credits | **30 / 40**: body Smart Topology 5, head Smart Topology 5, body retexture 10, head retexture 10 (backup account, no retries) |

## What MM9's model taught
- **Jaw and tongue:** `Box01` is the jaw, opening 35 degrees further from an already open rest; `Bone02-05` is a tongue that flicks in `fidget1`; `Box02` never moves. MM9's upper head is a steel skull helm.
- **Hand:** three fingers on one chain (`Finger1`) and a thumb, the cutlass rigid on `Bone07`. MM9 never closes the hand round the grip.
- **RangeAttack is on the left hand** (socket node 14 = `L Finger11`): the stone and the fire bolt leave the empty hand.
- **The bind is symmetric** (residual 0.0), so no stride problem and no `mirror_source.py`. `mirror_glb.py` on the source only.

## Route (`scripts/`)
0. **Source:** `convert_abc_model.py --scale 0.0256`, `mirror_glb.py`: `source/true/lizardorc_true.glb`. `bone_length_audit.py` 0 of 12.
1. **Masters** (`codex_masters.sh`, `references_hd/CODEX_BRIEF.md`): five body views, five head views with the mouth open.
2. **Body** (`parts0.py`, `clean_body.py`): rivets and the head removed, half kept, reduced (chest and hands protected), `fit_liz.py` onto MM9's exact joints with armour shells rigid on their limb, tail 1.46 -> 0.62 m by arc length.
3. **Head** (`headfr.py`, `head_prep.py`, `head_build.py`): half mirrored, teeth rebuilt as cones on Meshy's sites, forked tongue built, jaw closed 8 degrees by an arc.
4. **Join** (`join_liz.py`): one plane under the chin and the hood, rings met half way, throat capped.
5. **Rig** (`rig.sh`, `fingers.py`, `weights_liz.py`, `build_glb.py`): heat on the hide, shell rules (pauldrons on the half-shoulder, bracers, greaves rigid, hip plates Spine -> half thigh -> Thigh), helm rigid, neck band analytic, jaw by weight.
6. **UVs** (`uv_liz.py`): atlas 58.7 / 61.8 %. Frozen: `work/uv.npz`, `work/joined_frozen.npz`. **Never change the topology of `joined`.**
7. **Paint** (`uploads.py`, `textures.sh`, `tex_final.py`): 4K downsampled, gentle grade, head levelled per class, seam by luminance only, masks and ramps. Head and body each have one Meshy paint; nothing is projected over it, so no feature has two paint sources.
8. **Cutlass and fist** (`fist.py`, `make_cutlass.py`, `finger_keys.py`): MM9's blade stations, no Codex master. Constant wrist turn 36.7 degrees, grip centre moved 4.7 cm from `Bone07`.
9. **Clips** (`clips_mm9.py` with ORBIT and the soft offset line, `half_keys.py`, `arm_bump.py`, `tip_lift.py`, `flap_solve.py`, floor pass in two steps). Rebuild: `scripts/rebuild.sh [--install]`, gates `scripts/gates.sh`, all `scripts/deliver.sh`. Binding `scripts/bind_actors.py 1.7 2.5` under the flock.

## Tiers
MM9 shows all three rows alike. **Deviation:** to tell them apart in play, A is the paint (MM9's look, ramps dropped), B has a teal hide and blackened steel, C a rust hide and bronze armour, by ramps on the same images. Regions: R hide, G steel, B leather. Not from MM9: the colours of B and C are my choice.

## Run 2, third request (jaw underside and throat, install r18, 2026-10-31). Overrides the sections below where they differ

- **One paint source** (`scripts/throat_paint.py`, called from `tex_pages.py`): an orthographic render of the current paint from below and in front (`references_head/throat/throat_below.png`), the jaw underside and throat repainted by Codex inside the region (`throat_below_edit.png`, brief `CODEX_BRIEF_THROAT.md`, `scripts/codex_throat.sh`): pale belly scales down the middle, green scaled hide at the sides. It is projected back onto every texel that sees that camera (z-buffer over all skin, facing weight, 3D feather), with a membrane offset so its edge meets the paint round it. A second view from the front (`throat_front*.png`, `CODEX_BRIEF_THROAT_FRONT.md`) paints the band just over the neck ring that is edge-on from below, only where the first view did not reach. Codex said its second edit "does not fully meet the brief" (steel left at the far left of the band); in the shots that band reads as scales. Relief there comes from the new paint (`lum_normal`). 0 credits.
- **Octagon and pale slivers, at the source:** the chin fans and the neck-ring strip were one texel each. They now have real UV cells in free head atlas space (`throat_paint.cells`), painted by 3D position. The slivers were the strip's own geometry: `join_liz.py`'s triangles crossed the flat annulus between the head's cut rim and the body ring copy (edges up to 17 cm, folded 180 deg, 285 cm2). `throat_paint.zipper` rebuilds those 148 triangles in angle order round the neck: 9.6 cm2 in all, lying flat in the cut plane (final mesh only; `joined.npz` and the UVs are unchanged). Welding the ring weights was tried and dropped (`RINGWELD`, `INNERWELD`; collapse worse).
- **Read at full size** (`review/run2/sheet_throat_a.png`, `_b`, `_c`: below, front, left and right of the throat, cameras on an open line of sight by `scripts/throat_shots2.py`, in Standing, Hit2, Death2 and Dead): continuous scale pattern from the jaw tip to the breastplate, no octagon, no dark diamond, no yellow slivers. **Open:** in Hit2 from below a pale streaky band at the bottom of the throat. It is the body's throat faces just over the plate, stretched up to 3x when the head throws back (skin stretch, not paint); faint in Standing. Dead front has no open view (the corpse lies on its face); Death2 left and Standing left are partly blocked by the pauldron.
- **Gates on r18:** flat 0.00 on every primitive; texture quality head atlas 62.1 % (was 61.8), fragments 3.7 % (was 5.1), stretch p90 1.49, spread 1.13; jitter 0 fails; bones 0 of 20; detached 2; winding 0; floor 0 flagged; validator 150 descriptors on 60 models, 0 refused; `mm9_actor_models_build_every_binding` PASS, 0 failed (suite stopped after it). Arm, plates and blade as r17.
- **Collapse:** the zipped strip's near-zero triangles (under 0.1 cm2 each) flip in poses and are counted: head Hit2 88, Death 118, Death2 85 with them. Leaving faces under 0.1 cm2 out (`MIN_AREA=1e-5 scripts/collapse_gate.py`, `review/gates/collapse_min.txt`): Hit2 64, Death 81, Death2 60, Dead 17, Standing 0 (r17: 71, 96, 68, 20, 1; r17 counted the old folded strip).

## Run 2, second request (collapse and close-ups, install r17, 2026-10-31). Overrides "Run 2" below where they differ

**What the collapse counts were** (`scripts/collapse_parts.py`: the same test split by mesh part at each clip's worst frame). In r16 the "head" and "torso" counts were the **neck**, all of them: the head mesh's band under the jaw and the body's band under the ring. **Mouth (teeth, tongue, palate) 0 and skull 0 in every clip.** Torso was not armour folding: 42 of Death's 56 were head-material neck faces dominated by Spine3, 14 body hide just under the ring. MM9 bends the neck only at `Bip01 Head` (32 deg in Standing, 80 in Hit2, 85 in Death against the bind) while our neck weights went from Spine3 to Head over 7 cm, with `Bip01 Neck` at about 0.
- **Neck:** the Head ramp along the head axis runs from 30 cm instead of 13, and the body's band blends into it from 12 cm under the ring instead of 7.5, over |x| < 22 cm only (`NECKBAND` in `weights_liz.py`; r16 values in the comment). A half-joint helper at the head (`Bip01 XhalfHead`, `NECKHALF=1`) was tried first: Death 164 -> 192 neck faces, worse, so it is off. Wider ramps: Death 164 -> 103.
- **Hips:** the thigh zone smoothing is 40 passes over 22 cm (was 10 over 17): hip and groin faces Running 12 -> 9, AttackMelee2 14 -> 12, Death2 15 -> 10.
- **Shoulders, tried and dropped:** fading clavicle and upper-arm weight off the lower chest (`CHEST_ARM`) gave Hit 9 -> 6 but AttackMelee 9 -> 15 and Taunt 5 -> 10. Hinge pivots moved to the outside of the bend were not tried.
- The wider neck band moved the Hit L shoulder skin over the jitter limit (2.12 mm/f2). The Hit L bump is now 6 deg (was 9): jitter 1.57, hand still 0.0 cm in the arm gate.

Collapse gate, worst frame per region, r16 -> r17 (`collapse_gate.py`, all LOD0 primitives):

| Clip | face-frames | head | neck | torso | shoulder_L | shoulder_R | groin | hip_L | hip_R | knee_L | knee_R | elbow_L | elbow_R | body |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Standing | 1249 -> 276 | 10 -> 1 |  | 12 -> 0 |  |  |  | 2 -> 2 |  |  |  |  | 1 -> 1 | 5 -> 2 |
| Walking | 1451 -> 453 | 29 -> 13 |  | 17 -> 1 | 1 -> 2 |  | 3 -> 3 | 3 -> 4 | 3 -> 3 |  |  |  |  | 8 -> 6 |
| Running | 754 -> 306 | 18 -> 5 |  | 12 -> 2 | 0 -> 2 |  | 3 -> 3 | 7 -> 4 | 4 -> 3 | 1 -> 1 | 1 -> 1 | 1 -> 1 |  | 9 -> 6 |
| Fidget | 2096 -> 908 | 18 -> 5 |  | 16 -> 1 | 1 -> 1 | 1 -> 1 | 2 -> 2 | 3 -> 3 | 1 -> 1 |  |  |  | 1 -> 1 | 5 -> 3 |
| Fidget2 | 1961 -> 1007 | 34 -> 27 |  | 16 -> 2 | 1 -> 2 | 4 -> 4 | 4 -> 4 | 3 -> 3 | 1 -> 2 |  |  |  | 1 -> 1 | 7 -> 3 |
| Taunt | 846 -> 397 | 7 -> 1 |  | 12 -> 0 |  | 4 -> 5 | 1 -> 2 | 3 -> 3 | 0 -> 3 |  |  |  | 2 -> 2 | 5 -> 3 |
| AttackMelee | 1085 -> 532 | 46 -> 22 |  | 36 -> 4 | 1 -> 2 | 5 -> 12 | 7 -> 7 | 8 -> 6 | 0 -> 3 |  |  |  | 1 -> 1 | 9 -> 7 |
| AttackMelee2 | 1546 -> 670 | 60 -> 49 |  | 34 -> 1 | 1 -> 3 | 2 -> 7 | 8 -> 7 | 7 -> 4 | 1 -> 4 |  |  |  | 1 -> 1 | 8 -> 7 |
| AttackRanged | 1299 -> 514 | 46 -> 28 |  | 28 -> 1 | 7 -> 8 |  | 4 -> 4 | 3 -> 3 | 1 -> 0 |  |  | 3 -> 3 | 1 -> 1 | 6 -> 6 |
| Hit | 1257 -> 728 | 21 -> 10 |  | 14 -> 5 | 9 -> 10 | 3 -> 2 | 4 -> 4 | 3 -> 4 | 2 -> 2 |  |  |  | 1 -> 1 | 10 -> 10 |
| Hit2 | 2370 -> 1235 | 94 -> 71 |  | 44 -> 5 | 5 -> 3 | 1 -> 4 | 1 -> 1 | 3 -> 3 | 1 -> 0 |  |  |  | 1 -> 1 | 13 -> 12 |
| Death | 3899 -> 1782 | 104 -> 96 |  | 56 -> 5 | 2 -> 4 | 2 -> 4 | 3 -> 3 | 4 -> 4 | 2 -> 1 |  |  |  | 1 -> 1 | 11 -> 8 |
| Death2 | 2605 -> 1689 | 73 -> 68 |  | 38 -> 6 | 2 -> 1 | 0 -> 1 | 14 -> 12 | 4 -> 7 | 9 -> 5 |  |  |  | 1 -> 1 | 10 -> 12 |
| Backpedal | 1428 -> 438 | 29 -> 13 |  | 16 -> 1 | 1 -> 2 |  | 3 -> 3 | 3 -> 4 | 3 -> 3 |  |  |  |  | 8 -> 6 |
| BackpedalRun | 890 -> 276 | 29 -> 13 |  | 16 -> 1 | 1 -> 2 |  | 3 -> 3 | 3 -> 4 | 3 -> 3 |  |  |  |  | 9 -> 6 |
| Dead | 2883 -> 930 | 49 -> 20 |  | 31 -> 0 | 2 -> 1 | 1 -> 1 |  | 1 -> 0 | 2 -> 0 |  |  |  |  | 7 -> 8 |

Left in r17 at the worst frame of Death (96 "head"): 38 head-mesh neck faces and 58 body hide faces under the ring, dominated by Head. That is the ring band itself with the head bent 85 deg; in the shots the throat now reads smooth where r16 crumpled into shards (`review/run2/sheet_neck_r17.png`, `g17_d27`; r16 `review/run2/cn_death_q.png`, `cn_hit2_f.png`). Shoulder_R in AttackMelee rose 5 -> 12 with the neck band (faces relabelled from torso and head by their dominant bone); groin 12 in Death2 is the hip plates (part 15) and flap (part 9) at their top band plus 5 hide faces.

**Throat paint and mouth Hit2 from below:** the pale square patch was the r16 median colour on 14 throat slivers, whose streaky relief stayed in the normal map. Now 110 fan and sliver faces behind the jaw (the folded fan at the jaw's back included) take the body throat's scale paint above the plate, front-projected, mirror-tiled and low-passed, blended over 4 texels, and their relief is flattened (`head_normal_1k.png` from `head_normal_1k_src.png`). The neck band's body-paint fade averages 12 neighbours instead of one. Strip faces whose ring UVs share a chart span them (31 of 148). The chin fan disks take one bright texel each (a radial star from below in r16).

**Close-ups** (`scripts/closeups2.py`): per clip and joint the camera sits 0.6 m out along the most open direction near the joint's preferred side. Nothing may stand between camera and joint (first hit within 12 cm of it, 20 for the groin), the camera may not be inside the mesh (odd hits on most of 6 axes) or within 4 cm of a surface, and it stays above the floor. `review/sheet_closeups.png` is rebuilt from these. The black and smeared knee and groin frames in Death, Dead and Death2 were cameras inside the corpse.

Sheets on r17 (read): `review/sheet_closeups.png` (outside cameras), `review/sheet_strips_a.png`, `_b`, `_c`, `review/sheet_tiers.png`, `review/mm9_vs_ours.png`, neck and throat `review/run2/sheet_neck_r17.png`; in game (bootcamp.odm, review root) `review/ingame_sheet_r17.png`. Regression `mm9_actor_models_build_every_binding` PASS, 149 descriptors on 59 models, 0 failed (suite stopped after that case).

Other gates on r17: jitter 0 fails; arm and hand as r16 (Death2 L 3.6 cm 1 frame, AttackRanged L forearm 2.0); plates Walking 1.5 / 0 / 1.9, Running 2.5 / 2.0 / 1.9, AttackMelee 3.9 / 3.9 / 2.5, AttackMelee2 5.6 / 4.1 / 4.7 (**failed, as reported**); blade AttackMelee2 1.3 cm 1 frame; detached 2 (thigh strap 1.9 cm, chest shell 0.95 cm); bones 0 of 20; flat 0.00; winding 0; floor 0 flagged; validator 149 descriptors on 59 models, 0 refused.

## Run 2 (finishing pass, viewer and install r16, 2026-10-31). This section overrides everything below where they differ

Every MM9 clip of `LIZARDORC.abc` is carried (14 of 15; `static_model` is the bind pose): the 8 driven roles plus `script_clips` attack2, fidget2, hit2, taunt, backpedal, backpedal_run, death2, as in `mm9_clansoldier_claude`. Nothing left out. The binding was already complete; unchanged. 0 credits (30/40 in all).

What changed, all from the existing paint and mesh:
- **Breastplate top** (`plate_fix.py`, `assemble.py`): the chest shell (part 11) is clipped to its own paint: vertices outside the outer edge of the side plates' rim slide in along the shell's surface and take that point's UV, so the texture stays put and the outline follows the rim (18 of 72 vertices, topology unchanged). The shell's top edge takes a leather trim copied from the trim Meshy painted down the throat's sides, so the throat reads as a trimmed V on the plate, as in the masters. The flat cut and its stripes are gone.
- **Orange flecks in the chest mail** at the armpit: made grey at their own luminance (5,632 texels, both pages).
- **Pale streak on the neck, figure's right:** a neck-ring strip face took one pale texel (L .93). Each strip face now takes the centroid texel of a head face round its ring vertex, the one nearest the ring's median colour (148 faces). Throat fan slivers (14 faces) take the median hide colour within 1.5 cm.
- **Crease under the chin** (`build_glb.py`): long fan triangles at the back of the jaw fold onto each other (140-175 deg), and their flipped normals made a bright V line. In that zone (|x| < 5.5 cm) the vertex normals sum only faces that face down or forward. The fold itself is still in the mesh; it no longer shows in the viewer.
- **Fist in its tasset** (`arm_bump.py`): the cutlass counted as body, so every R job measured the fist "inside" its own grip and stopped at 3-6 deg. Excluded; Fidget R and AttackMelee R clear at 15 deg.
- **Cutlass tip under the floor and blade in the thigh** (`tip_lift.py`, new): AttackMelee's wrist turns the blade up by one raised-cosine window over 0.385-0.448 s, 27 deg at the peak, the arm's swing stays MM9's.
- **Front flap** (`flap_solve.py`, replaces `flap_keys.py`): per key the flap swings further forward or sideways only when a hinged flap point is inside a leg, held and low-passed.
- **Jitter:** AttackMelee L and Hit L bumps ramp from before the clip start (`free`); Death2 L bump 6 deg (a 24 deg bump cleared the hand but failed jitter by 2.56 deg/f). Death's corpse grounding is its own `floor_fix.py` pass with a held, low-passed raise (the corpse lies on its left pauldron, 16 cm up; the old pass stopped the fall in one frame, 79 mm/f2).
- `clips_mm9.py` uses the soft offset line. `scripts/mid.sh` builds to `work/final_clips.glb` for gate iteration; `scripts/deliver_r16.sh` makes the sheets.

| Gate (final r16 GLB, installed) | r15 | r16 |
|---|---|---|
| Floor audit | living -9.0 (cutlass tip), 3 bindings flagged | stand -1.9, walk -1.8..+1.1, living -1.9, dead 0, dying ok: **0 flagged** |
| Arm and hand, hands over 1 cm | Fidget R 5.5 (12 f), AttackMelee R 2.5 (1 f), Death2 L 0.4 | Fidget R 0, AttackMelee R 0; **Death2 L 3.6 cm 1 f, forearm 3.5 cm 1 f** (falling, frames 25-26) |
| Forearms | AttackMelee2 R 2.0, AttackRanged L 2.0 | AttackMelee2 R 0.7, **AttackRanged L 2.0** |
| Jitter against untouched clips | 5 fails (Death 63.8 mm/f2 skin) | **0 fails** |
| Blade against body | not rerun (Fidget 4.9, AttackMelee 5.3 before bumps) | 0 in every clip except **AttackMelee2 1.3 cm into the head, 1 frame** |
| Plates in legs (`plate_gate.py`, flap / inner / tasset cm) | Walking 1.5/0/1.7, Running 3.3/1.6/1.6, AttackMelee 6.1/3.9/2.5 | Walking 1.5/0/1.7, Running 3.3/1.6/1.6, **AttackMelee 3.4/3.9/2.5**, AttackMelee2 5.2/4.0/3.5, AttackRanged 3.9/0/5.2, Hit 0.7/0.7/4.2, Death2 4.2/3.1/3.9 |
| Detached | 3 flagged, unread | 3 flagged, read: R thigh strap 1.9 cm (AttackMelee), chest shell 0.95 cm, L pauldron 0.78 cm off the body's cluster. All armour shells standing off by design; attached in the shots (`review/run2/d25a.png`, `d25b`, `d31a`, `d31b`, `d91`) |
| Collapse, worst frame | knees 1, hips 9, shoulders 9, groin 12, torso 56, head 104 | knees 1, hips 9, elbows 3, shoulders 9, groin 14, torso 56, head 104 (Death; head includes the mouth) |
| Bone lengths, flat, winding | 0 of 20, 0.00, 0 | 0 of 20, 0.00, 0 inverted |
| Grip | fingers inside 0.0 cm | fingers inside 0.0 cm every clip |
| Regression | PASS | `mm9_actor_models_build_every_binding` PASS, 147 descriptors on 58 models, 0 failed; validator 0 refused; rest of the suite stopped after that case |

**Plates: not fixed (failed gate).** Walking and Backpedal 1.5/1.7 cm and Running 3.3 cm are the plates' top band (y .075-.09) tucked behind the buckle and under the belt skirt (part 13), where the thigh's heat weights bulge the hide: hidden in the shots (`review/run2/h_*.png` on r15, same plates). A second try gave the hide under the hip plates the plates' weights and then the plates' top band the hide's: tassets got worse (Standing 6.2, Walking 2.8 cm) and both were reverted (`PLATE_R1=0`, `PLATE_TOP=0` in `weights_liz.py`). `skirt_gate.py` (the older measure, 9 cm cap) is unchanged at 5.9-9.0 cm in the living clips.
**Death2 L** trades the arm gate for jitter: a 24 deg bump clears the hand (0.4 cm) but fails jitter (2.56 deg/f excess over MM9 in a fast fall); 6 deg passes jitter and leaves the hand 3.6 cm in for one frame at 48 fps.
**Head orientation, AttackMelee:** max 21.4 deg (mean 4.7) against MM9's head, already in the untouched clips with the old hard 4 mm line too; not caused by this pass and not looked into.
**Neck, still open:** the jaw corner tips under the jaw are small pale-yellow slivers on both sides (`review/run2/f_side.png`, `f_neckR.png`); the throat between jaw and plate keeps some soft vertical streaks; the fan fold is still in the mesh (hidden by its normals).

Sheets (r16, viewer shots): strips of every clip per tier `review/sheet_strips_a.png`, `_b`, `_c`; close-ups at knees, groin, armpits, elbows, neck and mouth in Death, Dead, Hit2, AttackMelee, Death2 `review/sheet_closeups.png`; tiers `review/sheet_tiers.png`; MM9 vs ours `review/mm9_vs_ours.png`; neck and chest `review/run2/f_chin.png`, `f_side.png`, `f_neckR.png`, `f_chestq.png`, `n_torso.png`; fist and cutlass `review/run2/n_fid.png`, `n_atk40.png`. In game (bootcamp.odm, review root, three tiers spawned close, then a hostile A attacking): `review/ingame_sheet_r16b.png` (`review/ingame_r16/g0*.png`), and the old tour's framing `review/ingame_sheet_r16.png`.

## Third pass (user feedback 32, viewer r15, 2026-10-31)

- **Skin on the breastplate, fixed.** Meshy painted the throat, its red-brown corners and the neckline trim onto the top of the chest plate shell (part 11). `plate_fix.py`, inside `tex_pages.py`: above y = .455 + .55 |x| the shell takes its own paint reflected across that line, the relief there fades to flat, and the region mask is computed afterwards, so the zone is steel on every tier. The neckline trim on the shell went with it. Throat skin ends at the plate's top edge. 0 credits.
- **Dark patch beside the neck.** Meshy's filler, pulled in by the join: a separate cause. The torso's top beside the neck (y over .578, |x| .082-.22, front) takes a plain 4 cm patch of plate, mirror-tiled. A first try from lower chest brought stripes across; replaced.
- Open, seen at full size: bright wavy stripes remain on the plate just under that patch; pale streaks on the neck hide on the figure's right; orange flecks in the mail at the left chest (blue on tier C); tiny green flecks on tier C's lower lip.

## Second pass (user feedback 19-24, 2026-10-31). This section overrides the Checks below where they differ

- **Neck.** The flat green sheet was my bug: `join_liz.py` left body rim vertices with a limb label unmoved, so the head-material strip spanned to them. Now the ring is the head's, the torso comes in to it (no mask), the sheet and the hard cut are gone. Chin holes (the plane cut the open jaw before it closed) are filled with fans. The head's neck band fades into the body's paint mirrored across the ring over 11.5 cm (`tex_pages.py`), so colour and scale carry across.
- **Body blur, measured.** Texels per metre, median: body 693, head 1440 (`repage.py`). The 4K paint was downsampled to one 2K page, so the body had half the head's density; 58 % atlas did not show it. Fix from the existing paint, 0 credits: the right half takes the left half's UVs (mesh exactly mirrored), the charts move 1:1 from the 4K paint, graded at 4K, onto two 2K pages with no resample. Body now 1386 texels per metre. Deviation: right side mirrors the left's paint, and +1 page. Normal and ORM 1K per page.
- **Chest patches: not removed.** The rectangular chest plate shell (part 11) remains over the hide, with the V painted on it; it reads sharper now. Not clipped.
- **Grip.** Grip radius 2.4 cm (was 1.8), `fist.py` closes the grip against the palm: fingers inside 0.0 cm, wrap 150 deg on the fingers quoted, thumb tip on the grip (radial 3.7 cm, wanted 3.7), wrap 60. Bow widened to clear the fingers. Grip centre 2.8 cm from `Bone07`.
- **Plates.** Hip plates are rigid on their thigh under a short belt band and stand 3.2 cm off the thigh axis; flap narrower and further forward on its hinge. `plate_gate.py`, Walking: flap 1.5, inner 0, tasset 1.7 cm. Running: 3.3 / 1.6 / 1.6. AttackMelee: 6.1 / 3.9 / 2.5. Hit: tasset 4.2. Death2: 4.2 / 3.1 / 3.9. **Not near 0 in Walking and Running for flap and tasset**; down from 2.2 / 5.9 / 5.0 and 3.4 / 7.0 / 6.1.
- **Arms after the plates moved out:** `arm_bump.py` 11 jobs (`bumps.txt`). Hands over 1 cm: **Fidget R 5.5 cm 12 f (fist in its tasset), AttackMelee R 2.5 cm 1 f.** Blade against the thigh before the bumps: Fidget 4.9, AttackMelee 5.3 cm; not rerun after them.
- **Jitter:** 5 lines flagged (AttackMelee, Hit, Death, Death2 and one more), Death's shoulder skin the known one; the others from the bumps, not looked at frame by frame.
- **Floor -9.0 AttackMelee, traced:** the lowest point is `Bone07`, the cutlass tip at 0.4 s, 9 cm under the floor. The body does not sink. Left as MM9's swing; the audit still flags all three bindings.
- **Collapse, worst of any clip:** knees 1, hips 9, elbows 3, shoulders 9, groin 12, torso 56, head 104.
- **Detached:** 3 flagged (was 7), not looked at. **Density tool:** body 2342 / 2280, head 883 per creature size (was 1172 body). **Regression on the final build:** `mm9_actor_models_build_every_binding` PASS, 147 descriptors on 58 models, 0 failed; validator 0 refused; rest of the suite stopped. Viewer r13: 48 switches, 0 failed. In game (r12): three tiers, 0 load failures.
- Frame strips `sheet_strips_*` and the acceptance sheet are from r12, before the arm bumps and the chin UV fix (chin fans first spanned the atlas; each now takes one texel). Not re-shot. Acceptance sheet `review/sheet_fix_tiers.png`: neck front, side, below, chest, palm side, thighs at AttackMelee frame 8, all tiers.

## Checks (viewer r7: final GLB. Collapse rerun on r7; the other clip gates, strips and close-ups on r5-r6, same weights and clips, neck ring moved only)
| Gate | Result |
|---|---|
| Regression | `mm9_actor_models_build_every_binding` PASS, 140 descriptors on 57 models, 0 failed (r5); `--headless-validate-actor-models` on r7: 143 descriptors, 0 refused. An early install failed it (`XFlap` duplicate channels), fixed in `flap_keys.py` at 09:26. The rest of the `actors` suite was stopped (machine load): not run |
| Bone lengths | 0 stretching of 20 |
| Handedness | Cutlass and `R Hand` at -x on a figure facing +z: anatomical right |
| Arm and hand (48 fps) | Hand clips all under 1 cm except **Fidget2 L 3.5 cm 3 f**, Death2 L 1.4 cm 1 f. Forearm: **Death2 L 3.7, AttackMelee2 R 2.4, AttackRanged L 1.9 cm**. Finger stretch max 1.71 |
| Jitter against untouched clips | 1 clip flagged by `grep`: Death (skin of the shoulder in the corpse raise); hands equal MM9 |
| Grip | Fingers inside the grip 0.0 cm in every clip; wrap Finger1 195, Finger2 165 deg. **Thumb 15 deg: it rests short of the grip** |
| Blade against body | 0 over 1 cm in the clips read (Hit2, Death, Death2, Backpedal, BackpedalRun, Dead); see `review/gates/blade.txt` |
| Orientation | Head and feet mean under 2 deg in the main clips, max 7.5 |
| Flat, winding | 0.00; 0 inverted |
| Texture quality | body atlas 58.7 %, head 61.8 %, spread 1.10 / 1.18 on the layout; 40 + 24 near-zero-area UV triangles |

**Failed, cloth (armour plates).** `plate_gate.py`, plate points inside a leg, cap 7 cm: Walking flap 2.2 / inner 5.9 / tasset 5.0 cm, Running 3.4 / 7.0 / 6.1 cm, every frame; AttackMelee and Death2 reach the cap. Shots of Walking and Running read as plates over the thigh, but the numbers say the thighs pass through the upper plates, and I did not get them clear. The flap hinge swings up to 75 degrees and 25 degrees at Standing. `skirt_gate.py` Walking 3.6, Running 8.9 cm (its 9 cm cap).
**Failed, floor.** `floor_audit.py`: stand -1.9, walk -1.8..+1.1, dead 0, **living -9.5 units (AttackMelee)**, tolerance 2.5: all three bindings flagged. Cause not traced.
**Detached audit:** 7 parts flagged, pauldron spikes, worst 4.6 cm, 2 of 528 poses, not looked at.

**Collapse, worst frame:** knees 0-1; hips up to 17 (AttackMelee L; hip plates count here); elbows 3-5; shoulders up to 15; groin up to 8; torso up to 55 (Death); head up to 93 (Death, includes the mouth). Per clip with exposed counts: `review/gates/collapse.txt`.

Sheets: `review/mm9_vs_ours.png`, `review/sheet_tiers.png`, `review/sheet_closeups.png`, `review/sheet_head_front.png`, `review/sheet_strips_a.png`, `_b`, `_c`, `review/ingame_sheet.png`.
Heads, front on, each tier (`review/sheet_head_front.png`): one set of teeth, one eye per side, nothing doubled: one paint source. **Open: a thin flat sliver of head skin still stands off at the neck ring, on the figure's right under the jaw** (narrowed, not gone). Death2 close-up can see the throat cap inside the neck.
Tone: steel reads whiter than MM9 in the viewer's light and darker in game; hide is yellower. Not retuned.

## Deviations and open points
- Tiers B and C (above). Teeth procedural. Tail fitted to MM9's short length, not the masters'. Wrist turn 36.7 degrees and grip moved 4.7 cm. Pauldrons follow half the shoulder, MM9's the whole. `doubleSided` on all materials for the open shells; the install's split handles it.
- Row height stays 200 / radius 60 from the sprite tables.

## Not checked
Motion by eye at normal speed (no playback recorded; the new wrist turn in AttackMelee and the free-start bumps in Hit and AttackMelee L were seen in stills only); LOD1-3; placing maps and indoor light (in game only `bootcamp.odm`: three tiers close and a hostile A attacking, r16); corpse in game, attack contact, missile from the left hand, sounds in game; rest of the actors suite; Android; tiers B and C close up at full size on r16 (sheets only).

User artistic acceptance: "lizard orc - ok" (2026-10-31, r15). r16, r17 and r18 (run 2): not recorded


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_lizardorc_reduce_claude/`** (user-approved; ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `mm9_lizardorc_reduce_claude/before/`.


**2026-11-04 later: the reduction was rolled back** (installed source = `mm9_lizardorc_reduce_claude/before/`): the UV audit (`claude_shared/reduction_uv_audit.py`) found reduced faces whose UVs left the painted charts, visible in close-up. A fixed reduction may be reinstalled later; see the ledger.


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_lizardorc_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_lizardorc_reduce_claude/before/`.
