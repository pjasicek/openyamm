# MM9 Bembridge Scholars (mm9_scholar) — 3D actor, 2026-11-02

MM9 `MONSTERS.txt` rows 274 Scholar (`scholar.abc`, skin `scholar1.dtx`, "Bembridge ScholarA") and 275 Master Scholar (`scholar.abc`, skin
`scholar3.dtx`, "Bembridge Scholar B"), basecrawl.scr, BaseName Scholar (the model's own clips). Two tiers on one body. Own GLB `mm9_scholar.glb`.
(`scholar2.dtx`, a red robe with a brown beard, exists in SKINS but no MONSTERS row names it: not carried.)

## Route decision: a new body
`mm9_meshcmp.py scholar:foraddarre,peasantm8,markel`: 6-12 cm from every built man, and SCHOLAR.abc has its own 94-node Bip01 skeleton (eight
robe chains XF/XFR/XR/XBR/XB with the side ones paired, Yhair/Ybeard chains, three-joint thumbs): a new Meshy body on the approved MM9 humanoid
route. The skeleton is the Monk's family (`mm9_monk_claude`: the same chain names, no thighs, calves off `Bip01 Spine`), so the Monk's role
table conventions and the Wyrde / Igrid scripts (analytic chain weights, npz pipeline) were combined.

## Clips (what the scripts play)
No DAT object places a Scholar in the extracted maps (the only "scholar" in the map data is `Scholarpromo.scr`, the promotion script in
Thjorgard), and basecrawl.scr plays no clip by name: MM9's roles only, from SCHOLAR.abc's own clips: Standing `stand`, Walking `walk`, Running
`run`, Fidget `fidget1`, AttackMelee `Hattack1` (MM9's `Rattack` at 0.35 s = `attack_melee` impact; the rows have no ranged attack: ranged
plays the melee clip), Hit `wince1`, Death `die1`, Dead, script clip Cower `cower`. Not carried: aware, fidget2, cower start/end, the
open/close book-less gestures, Hattack2, wince2, die2, Backpedal(Run).

## Route (`scripts/`)
0. `convert_abc_model.py --scale 0.0256` for scholar1 and scholar3 (`source/mm9/`), `mm9_dump.py`, reference renders (`ref_renders.py`).
1. HD masters (Codex via `codex_slot.sh`, `references_hd/CODEX_BRIEF.md`, runs 1 and 2): tier A's man; `review/masters_vs_mm9.png`. Head
   turnarounds for both men (`references_head/`, `codex_heads.sh`): `review/head_masters.png`.
2. Smart Topology 15k from `00_three_quarter_clean.png` -> `step1_clean.py` (height 1.89).
3. `assemble_sc.py`: robe (with the stole) mirrored from +x, face shell mirrored with fitted eye spheres (lids open ~6.8 mm: no change), hair +
   beard shell mirrored, cap as made (tilted like MM9's), jewellery (chain beads, medallion, buckle) as made, the +x shoe on MM9's foot with a
   shin tube, sleeves turned 15.9 deg and scaled x0.91 onto MM9's arm, MPFB male hands (195 mm) with forearm stubs. Mouth closed by Meshy: no
   mouth rebuild needed.
4. `uv_sc.py` (never re-run: the paid paints belong to `work/uv.npz`): body 2K 64.0 %, head set (face 1.7x, eyes, hair + beard, cap) 60.5 %.
5. Paint: body retexture 4K (tier A's clothes), head retextures 4K for both men (`make_upload.py ... head` + the two head turnarounds), AO
   bakes, `compose_sc.py`, `finish_sc.py`. `body_fix_sc.py`: the beard Meshy painted on the robe and stole behind the beard (it would move
   over ginger patches on the white-bearded tier) -> the cloth around it; the hands one clean skin colour. `head_fix_sc.py <tier>`: the ear
   Meshy painted on the hair beside the temple -> hair. `tiers_sc.py`: region R = the robe's blue cloth, ramps per tier by luminance quantiles
   onto MM9's own blue texels of each skin (scholar1 navy, scholar3 mid blue). `textures/tier_images.json`: one head colour per tier.
6. After the paint (positions only, no face feature moved): `tweak_sc.py` folds the ear tips (they poked out through openings in the hair
   shell) flat against the skull under the hair.
7. `rig_sc.sh` (fit_rig_sc: MM9's joints, arms on the sleeve axis, MM9's head pivot; `weights_sc.py`: robe on the eight chains below the
   waist, spine and clavicles above, sleeves along the arm, head rigid above the jaw plane, cap rigid, beard on Ybeardpiv -> Ybeard, side
   locks on the Yhair chains, the back hair blending to Neck / Spine3; `clips_pf.py` with `roles_sc.json`) -> `build_runtime_sc.sh [--install]`
   -> `viewer_update.sh <rev>`; `quick_face.sh <tag>` writes the viewer face sheets for both tiers.
8. After the paint, `geo_post_sc.sh`: `tweak_sc.py` (the ear tips folded flat under the hair; the 27 cm Meshy boots compressed to low shoes
   with a short shin stub: the boot shafts pushed through the lagging robe when walking), then linings (`linings_wy.py`: faces seen from behind
   at rest, 96, and in posed frames, 790 polygons, plus the robe's hem band: 693 twin faces + 56 rim edges). Tried and dropped: inner sleeve
   caps (`cuff_caps_sc.py`: the closed sleeve trapped MM9's folded-back Fidget hand), a 2x forearm stub (it poked through the sleeve in Death),
   wrist linings (their twins poked 2 mm through every cuff). Fidget: arm offsets eased in and out (`arm_clip_sc.txt`: now left abd 18,
   right abd 6) and the left wrist bend clamped 114 -> 60 deg (`wrist_clamp_sc.txt`, `wrist_clamp.py`: the wrist skin tore into a dark wedge).
9. Review round 2 (coordinator, 2026-11-02 night): `head_fix_sc.py` 1b JAW: the face shell's lower jaw and chin texels Meshy painted the
   robe's blue (tier B's two dark triangles beside the chin) -> the tier's beard colour (whole chin now, not only |x| > 2 cm); 1d MOUTH
   (tier B): the white moustache's hanging tips beside the mouth -> the skin around them (the horseshoe moustache read as a frown); 1c SMILE
   (tier B, after 1d): the paint within 12 mm of each mouth corner lifted 3.5 mm (corners placed from a render of a grid painted on the face,
   `review/face_dbg_b/`); `tweak_sc.py` also lifts the mouth-corner vertices 2.2 mm (before any repaint; both tiers). Legs: the shoe+shin
   stub compressed further (BOOTTOP 0.09, BOOTK 0.05: the stub's top ring was what came out through the robe front in Running and Cower);
   `legs_hide.py` in Death from 0.05 s (was 0.2). Fidget left arm: abd 18 (was 8 / flex -15).

10. Finishing round (2026-11-04, no credits):
   - `head_fix_sc.py` **1e LOWERA** (tier b; replaces 1d, `MOUTHFIX` defaults to 0): the Master Scholar still read as a pout (B's paint: a
     horseshoe moustache over a full pink lower lip, a bare chin). Tier A's head paint has MM9's layout on the same face shell (moustache
     over the lips, beard from the lower lip down, jaw beard). In the lower face (below the nose base, up the jaw sides, feathered 4 mm)
     tier A's colour is carried onto B: its facial-hair texels (hue 21.5-42, saturation > 0.45, plus all below z 0.712, minus the lips)
     in B's white beard colour at the same luminance quantile as on B's beard sheet (A's strand detail kept), its skin and lips times the
     cheek-skin ratio B / A. The shared head normal map is A's, so the relief now matches B too. The skin texels Meshy painted on the top
     edge of the beard sheet under the chin take the beard colour. 1c SMILE (3.5 mm corner lift) applies on top.
   - `head_fix_sc.py` **1f EARHAIR** (both tiers): the head shell's ears under the hair (still painted as ears, their tips show through the
     hair at grazing angles) take the hair colour; and step 1's ear removal on the hair sheet now fills with strand detail from hair texels
     24-72 texels along v (`EARDET` 0; the old 0.6 x the ear's own detail kept its outline strokes: "the faint ear outline on tier A").
   - `legs_hide.py` ported from Igrid with its pull toward the parent joint and a separate pull window (sixth/seventh fields):
     `Death:0.05:0.35:0.05:0.3:0.3:0.42 Dead:0:0:0.05:0.3` (the shrunken knee blob left the robe front at 0.42-0.5 s). A pull during the
     shrink pushed the shins out at 0.17-0.25 s (up to 7.9 cm); shrinking earlier or to 2 % did not help (`work/legtry/`).
   - Fidget left hand, proof (`work/fidproof/run.sh`): the same rig and clips built on the mesh without linings (`work/uv_cap.npz`) and with
     them (`work/uv_ln.npz`): `arm_hand_gate.py --outer-only --exact` Fidget L **0 frames > 1 cm (max 0.9 cm) without linings, 24 frames
     5.5 cm with them**: the gate reads the inward-facing lining twins behind the stole as body. The arm is unchanged.
   - The rig re-run on `uv_tex.npz` gives a byte-identical `work/half.glb` (sha bc8d73f43a40), so the r21 LODs (`work/mm9_scholar_rv.glb`)
     were reused: `scripts/tail_sc.sh` (tier images -> winding -> legs -> floor -> mirror, no Blender).

## Result (r22, installed 2026-11-04; r21 = the 2026-11-02 23:49 build, README r13 before it)

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_scholar.glb` (`tools/install_model.py --world mm9`), = `export/mm9_scholar.glb` (sha256 176c7de25696...; r21 716421a7bd93 kept as `work/lf/mm9_scholar_r21_installed.glb`, r13 was d07c5ec8bfcd) |
| Binding | `assets_dev/worlds/mm9/models/actors.yml` block `mm9_scholar_claude` (`scripts/bind_actors_sc.py` via `scripts/bind_under_lock.sh` under the flock): `MM9 274 Scholar` (skin sc_a), `MM9 275 Master Scholar` (sc_b); scale 100, yaw_offset -1.570796327, stride walk 1.2 (`stride.py`) / run 1.92 (MM9's RunVelocity x the run clip: the planted run foot is only 10 % of the cycle), attack_melee impact 0.35 (MM9's Rattack), look Neck + Head, script clip cower |
| Descriptors | rows 274, 275 in `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv` (fallbacks 292, 294 = the stand-ins of `mm9_npc_legacy_replacements.tsv`); `mm9_monster_bodies.py --write-overrides` + tables: ids 9274, 9275, **height 184, radius 31** (MM9's rule on scholsetup's upright (12, 36, 12) box; our model stands 1.89 m to the cap top, so no exception) |
| Triangles LOD0/1/2/3 | 13,782 / 6,882 / 2,462 / 806 |
| Skeleton | SCHOLAR.abc's 94 nodes (93 joints) + 30 finger bones + 5 half-joint helpers |
| Textures | body colour 2K, normal + ORM 1K, region mask 1K (R robe); head set colour 1K per tier (2), head normal + ORM 1K shared |
| Meshy credits | **35 / 50**: Smart Topology 5 (backup 2475 before), body retexture 4K 10 (2450), head A 10 (2440), head B 10 (2430); no retries. Backup 2370 at the end (other agents spend too). Finishing round 2026-11-04: 0 credits |
| Viewer | http://127.0.0.1:8912/level_generation/creatures/mm9_scholar_claude/review/viewer/ revision `r22-20261104`, tiers `sc_a`, `sc_b` |

## Gates (`review/gates/`)

| Gate | Result |
|---|---|
| `arm_hand_gate.py --outer-only --exact` | 0 frames > 1 cm in every clip except **Fidget L: 24 frames, up to 5.5 cm** (r21/r22; r13: 35 f 5.3 cm). The hand rests on the stole and medallion (`review/fid_r10_sheet.png`). **Proof** (`work/fidproof/`): the same rig and clips without the linings measure 0 frames > 1 cm (max 0.9 cm): the gate reads the lining twins as body |
| `jitter_gate.py` | 0 fails |
| `see_through_gate.py` (pdm2's) | r1 (no linings) torso 1,274 px Death / 635 Dead / 601 Cower / 382 Hit, head 1,269 Death; r4: torso <= 32 except Death 132, head <= 23 except Death 115; **r6 (r22, `see_through_r6.json`): torso <= 32 except Death 132; head <= 22 except Death 115; sleeves <= 14. Torso and head in Death are real spots (77 / 117 px, 40 / 77 px after a 1-px erosion, 3 mm pixels) under the beard at the collar as the head tips back at 0.5-0.6 s (`see_through_r6_head_Death_18_az000_el20.png`, `..._torso_Death_15_az315_el00.png`): NOT fixed (posed back faces of those frames would need new linings and a new LOD build)** |
| `robe_gate.py` | r22: 0 in every clip except **Death 2/32 frames, 2.4 cm** (0.17-0.21 s: the shins as he tips back, before they have shrunk); r21: Running 0, Cower 0, Death 5/32 2.5 cm; r13: Running 5/25 7.3 cm, Death 4/32 6.9 cm, Cower 22/22 5.5 cm |
| `sleeve_poke_gate.py` | 0 except **Death L 22 mm, 1 vertex, 2 frames** (r13: 1 frame) |
| `detached_parts_audit.py` | the shoes (with their shin stubs) part from the robe in Running by up to 8 cm (legs hang free inside the robe: no thighs in MM9); chain beads on the stole lift up to 1.6 cm in Hit |
| `bone_length_audit.py` | Calves 0.36 -> 0.48 m (Death), 0.40 -> 0.47 m (Walking): MM9's keyed calf translations |
| `flat_shading_check.py` / `check_winding.py` | 0.00 body, 0.07 head / 0 inverted |
| `texture_quality.py` | body atlas 64.0 %, spread 1.08; head 60.5 %, spread 1.11 |
| `floor_audit.py --world mm9` | r22, rows 274, 275: stand +1.2, walk -0.7..+0.5, living -0.7, dead 0.0: ok |
| `mm9_actor_models_build_every_binding` | r22 (with Igrid r15): PASS, 248 descriptors on 110 models, 0 failed (`review/gates/regression_actors.log`) |
| Viewer `run_creature_review.py check` | r22: 18 switches (2 tiers x 9 clips), 0 failed, 0 console errors |

## Sheets (read)
**Finishing round (r22): `review/face_f24_a_sheet.png`, `review/face_f24_b_sheet.png`** (f22 before the ear fix; f16 before the lower-face
transplant), **`review/mm9_vs_ours_r22.png`** (MM9 scholar1 / scholar3 vs sc_a / sc_b, five views), `review/ear_a_before_after_f24.png`,
`work/lf/front_head.png` (tier B lower face in front projection: before / after / tier A). Earlier: `review/mm9_scholar_skins.png` (MM9's three skins), `review/masters_vs_mm9.png`, `review/head_masters.png`, **`review/mm9_vs_ours_r8.png`** (MM9
scholar1 / scholar3 vs our sc_a / sc_b, five views, viewer), **`review/face_f9_a_sheet.png` and `review/face_f9_b_sheet.png`** (viewer
lighting: MM9 front + profile, front close-up, both 3/4, true profile, low 3/4, under the jaw, party, 128 px), `review/ears_f6.png` and
`review/ears_sheet.png` (ears, jaw-neck line, party), `review/fid_r10_sheet.png` / `fid_r11_sheet.png` (Fidget left hand), `work/st/clay1_sheet.png`.

## Open points / what to look at
- **Master Scholar (r22)**: tier A's facial-hair layout in white: a short moustache over a slight smile, the chin and jaw bearded as in MM9;
  no dark jaw gaps. The Scholar (A) is unchanged apart from the ears.
- **Ears**: the outline on tier A's hair is nearly gone (`review/ear_a_before_after_f24.png`); a faint smoother patch remains on one side.
- **Fidget**: a small dark notch at the left wrist from a high front view at 1.15 s (the wrist bend, clamped to 60 deg); the hand rests on
  the stole.
- **Death**: the shins show under the front hem for two frames as he tips back (0.17-0.21 s, 2.4 cm); Cower and Running are clean.
- **Death see-through**: a small gap under the beard at the collar for about two frames as the head tips back (0.5-0.6 s).
- Tier B's cap is a little more saturated than MM9's scholar3 cap.
- No map places the Scholars (no DAT object in the extracted maps): descriptors 9274 / 9275 are ready for whichever encounter table uses them.

## Not checked
In game; motion at normal speed by eye beyond clay strips and the gates; LOD1-3 by eye; the unused scholar2 skin.


**LOD0 reduced post-install on 2026-11-05 by `level_generation/creatures/mm9_scholar_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_scholar_reduce_claude/before/`.
