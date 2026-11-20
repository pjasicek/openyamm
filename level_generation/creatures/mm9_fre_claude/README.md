# MM9 Fre, the goddess in the Hall of the Gods (mm9_fre) — 3D actor on the PeasantF4 body, 2026-11-04

MM9 `FRE.abc` with skin `Fre.dtx`, `MONSTERS.txt` row **256 Fre** (BaseName PeasantFemale, NPCbase.scr, IsMonster 0, Move 0). One DAT
object in the rebuilt maps: `Fre` in `hallofthegods` (NPC337.scr: her voice and the Golden Honk quest reward; DAT Scale 1.6). The same
map has a statue prop on `Fre.ABC` with the `Fresculpt` skin (a decoration, not this job; converted for reference into
`source/mm9_sculpt/`). Built under `devdocs/mm9_rework/overnight/FINISH_BRIEF_20261104.md` (Job 4) as a **variant of a built body**.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_fre.glb` (`tools/install_model.py --world mm9`) = `export/mm9_fre.glb`; one skin, no tiers |
| Binding | `assets_dev/worlds/mm9/models/actors.yml` block `mm9_fre_claude`: `MM9 256 Fre` (`scripts/bind_actors_fre.py` under the flock by `scripts/bind_under_lock_fre.sh`) |
| Descriptor | row 256 in `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv` (fallback visual 352 = the stand-in of `mm9_npc_legacy_replacements.tsv`), tables regenerated. Map placement is the orchestrator's switch |
| Skeleton, clips | PeasantF4's = PeasantF1's: MM9's 73 PeasantFemale joints + 30 MPFB finger bones + 5 half-joint helpers; F1's 11 clips (stand1, Walk, run, Fidget4, Conv1-3/Talk, Wince1, Die1, Dead, cower) unchanged. NPC337.scr plays no clip of its own |
| Textures | body colour 2K (F4's paid UV layout), normal and ORM 1K; head set (pass 7: the new Meshy head, face + hair) colour/normal/ORM 1K; braid on PeasantF2's 1K hair set (toned) |
| Meshy credits | **35**: body retexture 4K `fre_body_tex_4k` (10), head retexture 4K `fre_head_tex_4k` (10); backup account 2305 -> 2295 -> 2285. Pass 7 (new head, budget 40): Smart Topology `fre_newhead_smart` (5) + 4K retexture `fre_newhead_tex_4k` (10); 2190 -> 2175 |
| Codex | one run: four body HD masters on PeasantF4's masters, four head paint-overs of renders of our own head (`references_hd/`, `references_head/`) |
| Viewer | http://127.0.0.1:8912/level_generation/creatures/mm9_fre_claude/review/viewer/ |

## Why a variant of PeasantF4
`claude_shared/mm9_meshcmp.py` against every built MM9 female body (`review/mm9/fre_vs_f4_f3_f1.png`, `heads_clay_fre_f4_f1_f3.png`):
`peasantf4:fre` head p90 1.8 / max 3.3 cm, torso 1.5 / 3.6, arms 0.7 / 2.3, legs 0.1 / 1.3 (shifted), same skeleton and binds
(73 nodes, bind diff 0.00 cm); `fre:peasantf4` adds the head piece (max 12.6 cm: the braid). F3 and F1 differ more (F3's veil, F1's
short sleeves). Fre = PeasantF4's body with the long bell sleeves, **no hood**: a rounded hair cap that covers the ears and frames the
face to the jaw, and **one braid** from the nape down the back (MM9 bones Ponytail11 / Ponytail12). PeasantF4 is not one of the frozen
approved models; its sources were copied into `work/f4/` (read only) and nothing in `../mm9_peasantf4_claude/` was written.

## Route
1. `scripts/convert_sources.sh`: FRE.abc + Fre.dtx (`source/mm9/`), the statue skin, and F1b / F3a / F4a for comparison.
2. `scripts/add_parts_fre.py` (from `add_parts_pf4.py`): F4's asm without its hood; F1 rows back on F1's own positions; the **hair cap**
   (component name `hood4` kept so F4's tools treat it as the head-set shell): F4's disk parametrisation round a pole behind the head,
   the face opening on F1's head/old-hood seam + 5.5 deg hugging the face 1.5 mm out, the hem on our neck at 0.575 m (back) / 0.59 m
   (sides); radius = MM9 Fre's head surface, never inside our head + 3 mm; F1's old hood (hidden skull) pushed under it everywhere;
   lining over the outer two rings and a rim. The **braid**: F3's plaited tube (6 sides, a ring every 7.5 mm, tie and tuft), 27 cm,
   from inside the cap at the nape down the back 1.5 cm off it. LOD0 14,958 -> after the fixes below 14,782.
3. PeasantF4 job 8 fixes (snapshots of that agent's scripts, `work/j8_scripts_sha.txt`): `sleeve_rings_pf4.py` (the sleeve tubes'
   upper rings wound inward: the "transparent" forearm patches) on the asm; `bodice_fix_pf4.py` (F1's eyelet holes filled, lacing
   chevrons and peplum spikes dropped) in the positions chain.
4. UVs `scripts/uv_fre.py`: the body set is F4's paid layout row for row; the head set re-laid with `uv_atlas.py` (face 1.7x, hidden
   old hood 0.3x). **Never re-run** (the head paint belongs to `work/uv.npz`). `scripts/drop_open_lining_fre.py` then removed the cap's
   rim and lining along the face opening (a dark line on the forehead and cheeks), faces only.
5. Geometry finalised before the paint: `scripts/geo_chain_fre.sh` (F4's tweak, chin, under-hood, puff, bust, eyelid steps, then the
   bodice fix, the braid pose and the hem drop) produced the uploads `texturing/fre_body_upload.glb` / `fre_head_upload.glb`
   (`work/uv_geo_upload.npz`). Face geometry was not moved after the paint.
6. Codex (`scripts/codex_masters_fre.sh`, brief `references_hd/CODEX_BRIEF.md`): body views on F4's HD masters (pose and sleeves) with
   MM9 Fre's costume; head views painted over clay renders of our head (`references_head/cur_*.png`), calm warm closed-lip smile,
   green-grey eyes, chestnut-auburn hair, gold circlet with a violet jewel, gold-bound braid. Clean alpha from our renders
   (`scripts/mask_from_alpha.py`).
7. Meshy 4K retextures on the two uploads; `compose_pf.py`; AO baked on the uploads (`texpass_bake_ao.py` + `pad_ao.py`).
8. Paint fixes (in `scripts/rebuild_fre.sh` / `head_fix_fre.sh`): `sleeve_red_fre.py` (Meshy put the feather shawl on F1's whole puffed
   upper sleeve: red cloth from the skirt's own paint, mirrored tiles mapped round the arm), `collar_feather_fre.py` (flat yellow
   back collar -> feathers), `cap_hair_fre.py` (skin-coloured teeth on the cap's edge -> hair), `hair_tone_fre.py` (copper red ->
   MM9's chestnut: hue +4 deg, saturation x0.88, value x1.12), `underchin_pf4.py`, gutter fills (colour and normal).
9. Weights `scripts/weights_fre.py` (F1's weights on every F1 vertex via `merge_weights_pf4.py`): cap = MM9 Fre's head weights, its
   outer rings easing onto what lies under the hem (neck skin, bodice); the old hood takes the nearest cap vertex's; braid = Head at
   the root easing onto the back under it (MM9's own Ponytail chain swung it 3 cm into the back in every clip, `gate_fre.py`).
10. Runtime `scripts/build_runtime_fre.sh` (prepare, LODs, shadow fix, material extras specular 0 / metallic 0, winding, floor, mirror
    to MM9's handedness), viewer `scripts/viewer_update.sh`. One command: `scripts/rebuild_fre.sh <rev> [--install]`.

## Face and paint work in the review viewer (r1 -> r20)
Each step judged in viewer shots (`scripts/face_shots_fre.sh <rev>`: front close-up, 3/4, both true profiles, low 3/4 from below the chin,
under the jaw, Talk mid-sentence, both hair edges by the ears, back of the head, party view, full body):
- r1: good face (warm, green-grey eyes, one brow, closed relaxed lips); faults: feather paint on F1's puffed upper sleeves, copper-red
  hair, skin teeth on the cap edge, a dark line along the hair edge (cap rim crossing the skin), flat yellow back collar, ragged collar
  points and background slivers between the hem and the collar.
- r2-r5: those fixed (route step 8, `drop_open_lining_fre.py`, `cap_hem_fre.py`: hem rings behind the ears lowered 22 mm, eased 6 mm out).
- r6-r20: a thin dark line across her left cheek and down the neck. Traced: present faintly in Meshy's own returned model
  (`review/geo/texonly/meshy_front.png`); made solid by two of my own steps, both fixed: `sym_paint.py` (dropped) and a gutter pass
  that painted one chart's colour into a neighbour's polygon (`compose_islands_fre.py`, island-aware 4K padding + box downsample).
  It is now back to Meshy's faint level but NOT gone (see Open points); `skin_line_fre.py` / `normal_line_fre.py` did not reach it.
- Under the jaw the view from straight below is dark: the paint there is skin (204-216/135-144/99-107); the dark is the viewer's light on
  F4's carved under-chin (downward faces), as in PeasantF4.

## Open points (honest list)
- **Cheek line**: a faint thin dark line from beside her left nostril down the cheek to the jaw and on down the neck, visible in the
  front close-up and clearly in Talk close-ups; faint at party distance. Not fixed.
- **Cap hem metric** (`gate_fre.py` "hood", F4's hood-vs-body reading on the cap's lower rings): 2.1-2.9 cm in most clips. The
  ray-based poke gate (`cap_poke_fre.py`: neck or collar visible OUTSIDE the hair) reads 0 mm in 8 of 11 clips, but Talk 11.9 mm
  (85/197 frames), Cower 7.2 mm (all frames), Conv1 2.3 mm (6 frames) on r6: neck skin pokes through the hair's lower edge when the head
  turns. Not fixed.
- **Hair shape**: a fuller bob than MM9's sleek cap (it must cover F1's hidden old hood); reaches the collar at the back.
- **Inherited from PeasantF1/F4**: dark holes in the bodice's back in Walking/Conv1 (the approved F1 has them too,
  `review/geo/f1_walk_back.png`), the hollow dress seen from the feet (see-through torso / sleeve L / collar in Death and Dead), the bell
  sleeve on the bust in Cower (forearm 2.4 cm).
- The circlet's openwork lost a few cream texels to hair colour (`cap_hair_fre.py`), reads as hair between the gold.
- PeasantF4's job-8 scripts were taken as snapshots while that work was in progress (`work/j8_scripts_sha.txt`); later changes there
  are not in Fre.
- MM9 Fre's red is more orange in MM9's baked-light skin; ours matches the skin's median hue/saturation numerically (8 deg / 0.96).

User artistic acceptance: not recorded.

## Gates (final geometry and weights = r19/r20, `review/gates_r19/`, `scripts/gates_fre.sh` + `scripts/cap_poke_fre.py`; see-through on r6, same geometry)

| Gate | Fre |
|---|---|
| `arm_hand_gate.py --outer-only --exact` | 0 frames > 1 cm (hand) in all 11 clips; forearm 2.4 cm in Cower (F4's bell sleeve on the bust) |
| `jitter_gate.py` | 0 fails |
| `robe_gate.py` / `sleeve_poke_pf1.py` | 0 frames / 0 mm in every clip |
| `gate_fre.py` braid into the body | 0 cm in 9 clips; Hit 1.9 cm (2/119 frames > 1 cm), Death 0.7 cm |
| `gate_fre.py` old hood (hidden skull) out of the cap | 0 in every clip |
| `gate_fre.py` cap hem (F4's hood metric) | 1.0-2.9 cm, > 1 cm in most frames: **fails F4's 0-frames bar** (see the poke gate for what shows) |
| `cap_poke_fre.py` neck/collar outside the hair | 0 mm in 8 clips; **Talk 11.9 mm (85/197 frames), Cower 7.2 mm (52/52), Conv1 2.3 mm (6/197)** |
| sleeve tube (arm under the tube) | <= 1.0 cm, 0 frames > 1 cm |
| `collapse_gate.py` | as F4 (Hit armpit R 77, waist 64; Death neck 83) |
| `detached_parts_audit.py` | 2: the legs, by design (as F1/F4) |
| `bone_length_audit.py` / `flat_shading_check.py` / `check_winding.py` | 0 stretching / 0.00 body, 0.01 head / 0 inverted |
| `texture_quality.py` | body atlas 69.6 % (F4's layout), fragments 0.0 %, stretch p90 1.08; head set atlas 60.9 %, fragments 1.8 %, stretch p90 1.47, spread 4.48 (face 1.7x, hidden old hood 0.3x by design) |
| `see_through_gate.py`, hole max px (elevation 0 / 20 deg) | head 65 / 27, torso 1596 / 50, sleeve L 2004 / 40, collar 974 / 63, sleeve R 7 / 44, boots 0 (worst: Death from the feet up F1's hollow dress, as F1/F4: F4 r31 head 146/156, torso 1559/118, sleeve L 2000/24, collar 907/22) |
| LOD0 / LODs | 14,782 / 7,257 / 2,611 / 868 triangles |
| `floor_audit.py --world mm9 --match 'MM9 256*'` | stand -0.2, walk -0.1..+1.6, living -1.2, dead 0.0: ok |
| `mm9_actor_models_build_every_binding` | PASS, 250 descriptors on 112 models, 0 failed (after the final install) |
| Viewer `run_creature_review.py check` | 11 switches, 0 failed, 0 console errors |

Installed `assets_source/worlds/mm9/models/mm9_fre.glb` sha256 02437871566e...5989 (= `export/mm9_fre.glb`, r20).

## Sheets (read)
`review/faces/r20_face.png` (front close-up, 3/4, both true profiles, low 3/4 from below, Talk, under the jaw, party view),
`review/faces/r20_head_back.png` (back, rear 3/4, both hair edges by the ears), `review/mm9_vs_ours_r20.png` (MM9 vs ours, full body:
front, 3/4, left, back), `review/faces/r1_face.png` .. `r19_face.png` (history), `review/geo/texonly/meshy_front.png` and
`r9..r18_front.png` (base colour only: the cheek line), `review/geo/v12_sheet.png` (cap and braid in clay), `review/geo/clips_hem_sheet3.png`,
`review/geo/braid_ease.png`, `review/mm9/fre_vs_f4_f3_f1.png`, `review/mm9/heads_clay_fre_f4_f1_f3.png`, `review/mm9/fre_head_sheet.png`,
`references_hd/selected_views_review.png`, `references_head/selected_views_review.png`.

## What was not checked
In game (the maps place the stand-in 352 until the orchestrator's switch; DAT Scale 1.6 in the Hall of the Gods not tried); motion at
normal speed by eye (viewer stills, clay frames and numeric gates only); LOD1-3 and shadow meshes by eye; the statue prop (FRESCULPT).

## Pass 2 (orchestrator pre-screen of r20, 2026-11-04) -> r36, 0 Meshy credits
1. **Cheek and neck lines**: found in screen space and traced to texels. `scripts/uv_probe_render.py` renders the rest-pose model twice per
   view (front, both 3/4, both profiles, low 3/4, from below): the base colour unlit with nearest-texel sampling, and an exact UV render
   (EXR, no film filter). `scripts/heal_lines_fre.py detect` maps thin dark lines and specks (darker than 0.88-0.90 of the local median or
   off-colour by > 0.065) to texels (`work/line_texels.npy`, union of passes on r20/r21/r22/r29); `apply` heals them in the base colour and
   the normal map from the clean skin round them. Features (eyes, brows, upper lip and lip line, nostrils) excluded by 3D zones.
2. **Under the jaw**: the paint there is skin; the dark wedge was the viewer's light on F4's carved, downward-facing under-chin. In
   `build_glb_pf.py` the head-shell normals 1.465-1.545 m over the soles, |x| < 10 cm, facing down, are turned forward and a little up
   (UCHIN 1.5); positions untouched.
3. **Chin V / specks**: `speck_heal_fre.py` (small off-colour blobs in the skin), `sliver_texel_fre.py` (texels sampled by the collapsed
   lip/chin slivers of `uv_sliver_fix_pf3.py` take the median of chart-interior texels), gutter fill back on for the head colour. A
   1-2 px dot remains at the chin point in the front close-up.
4. **Sleeves from behind**: part-coloured renders with back faces magenta (`scripts/posed_npz_fre.py` + `view_parts_magenta.py`, Standing,
   Walking, Fidget, Hit, Cower; back, both back 3/4, low back: `review/arms/back_parts_r34.png`): no back faces on the forearm tubes or
   at the elbows (F4's ring fix was already in). PeasantF4's final `bodice_fix_pf4.py` (r41, user-approved; side hem tips) taken again.
   Remaining magenta, inherited from F1/F4: the inside of the bodice hem seen from below, a skirt fold at the hips in Walking, a patch of
   the bodice's inside behind the arm in Hit/Cower back 3/4. Textured viewer back views: `review/arms/r34_back_sheet.png`.
Also: `compose_islands_fre.py` + `normal_line_fre.py` stay; `sym_paint` and `underchin_pf4.py` are no longer used.
Sheets (read): `review/faces/r36_face.png` (front close-up, 3/4, both true profiles, low 3/4, Talk, under the jaw, party view),
`review/arms/back_parts_r34.png`, `review/arms/r34_back_sheet.png`. Installed r36 sha256 990ccb7efda8288e... (= export); binding
regression PASS (252 descriptors on 114 models, 0 failed); floor ok; viewer 11 switches, 0 errors.

## Pass 3 (user review of r36, 2026-11-04) -> r43, 0 Meshy credits
User: "the parts of the face like different contour or differently shaded" and "the hair is like cut into the face there - I would make it
a normal hair" (`review/user_20261104/`).
- **Shading**: the pass-2 hard-region under-chin normal turn is replaced by a smooth falloff in `build_glb_pf.py` (Gaussian in height round
  the under-chin, sigma 3.5 cm, across 7 cm, back toward the neck 5 cm, times a smooth ramp of how much the normal faces down, strength
  0.9; no boundary anywhere). Positions untouched.
- **Hair drawn back** (`add_parts_fre.py HAIR_BACK=0.630,0.595`, same topology and paid UVs: `RB_TOPO`, `BRAID_NRING=37`): the cap's edge
  may not reach below ear-lobe height at the sides nor below 0.595 m at the nape, so the hair covers the ears and ends at the nape like
  MM9's Fre / PeasantF2's cap; face sides, jaw and neck free. The braid root re-pathed into the cap (`BCTRL`). PeasantF2's own hair was
  looked at (`review/hair/f2_sheet.png`) but not transplanted: its head is another Meshy head, and the parametric cap on our head reached
  the same drawn-back shape without a new UV layout or paint. F1's old hood (hidden skull): faces outside the new cap dropped
  (`DROP_ALL_OUT`, `DROP_SIDE_SEAM`), edge vertices pulled 8 mm in (`OLD_EDGE_IN`), the rest pushed under the cap as before.
- **Newly bare skin**: the jaw sides, below the ears and the nape were painted hair under the bob; `scripts/expose_skin_fre.py` repaints
  the band the old cap covered and the new one does not with smooth skin from the nearest clean skin (and flattens its normal map);
  `island_pad_fre.py` (head charts only) now extends each chart 3 px into its own gutter after the gutter fill (dark hair-coloured lines
  along the neck's UV seams in the viewer, r40-r41).
- Sheets (read): `review/faces/face_r36_vs_r42.png` (front, 3/4, profile, low 3/4, under the jaw: before/after), `review/faces/r43_face.png`
  (front close-up, 3/4, both profiles, low 3/4, Talk, under the jaw, party), `review/mm9_vs_ours_r36_r42.png` (full body vs MM9 before/after),
  `review/hair/v18_sheet.png` (parts: the new cap, old hood and braid).
- Gates r42/r43: arm/hand 0 frames > 1 cm in 11 clips, jitter 0, robe 0, sleeve poke 0, braid 0 in every clip, flat 0.00/0.01, bones 0,
  detached 2 legs. Cap poke (neck/old hood outside the hair): 0 mm in 8 clips, Talk 10.3 mm (85 frames), Cower 8.7 mm (all frames),
  Fidget 7.5 mm (58 frames), Conv1 2.1 mm - still open. gate_fre "old hood out" 0.6-1.1 cm in every frame: three old-hood seam vertices
  below the ears now border only face skin (their old-hood faces were dropped), so it reads them as outside. Head-set density spread 19
  (the exposed band's tiny old-hood remnants; atlas 58.4 %).
- Installed r43 sha256 ad6b61746ca2... (= export); binding PASS (252 descriptors on 114 models, 0 failed); floor ok; viewer 11/0.
- Remaining marks: a slightly flatter, smoother tone on the newly bare jaw sides and neck than on the cheeks; small hair-edge bits at the
  lower edge beside the neck in the front close-up; the cap's lower back is a rounded bowl in profile.

## Pass 4 (orchestrator review of r43: "do real hair") -> r62, 0 Meshy credits
PeasantF2's approved hair (sleek drawn-back cap + braid: its geometry from `../mm9_peasantf2_claude/work/geom_final_v3.npz`, its weights,
head-set UVs and paint, copied read-only to `work/f2/`) replaces Fre's parametric cap ('hood4') and braid ('braids') as part `hair2` on
a third material `FreHair` (doubleSided like F2's head set, `double_hair_fre.py`). Rollback: `work/pre_pass4/` (asm, uv, head paint).
- **Geometry** (`scripts/build_hair_fre.py`, then `work/asm_frozen.npz` / `work/uv.npz`): F2's braid decimated to 45 %
  (`decimate_braid_fre.py`, cap untouched); same skeleton and bind frame, so no transform. The cap's open rim gets two extra rows per
  edge (`RIM_SPLIT`), every rim row within reach (2 cm at the sides, 5 cm at the forehead/temples) is pulled onto F1's face-shell outline
  and 10 mm past it onto the skin (`OVER`), the pulled rim is smoothed along itself and laid on the skin 1.5 mm out; the move fades 3 cm
  into the cap. **Max fit distance: rim pull 25.8 mm (median 11.2 mm); Fre's skull/face rows moved under the cap at most 24.5 mm**
  (3 mm clearance; `under_hair2_fre.py` re-applies 4 mm after the chain's face tweaks). Old-hood faces the hair does not cover are dropped
  except the teeth on the face outline (kept, painted skin; their free corners tucked under the rim). Two 4-vertex holes in F1's face
  shell in front of the ears (hidden by the old bob) fanned shut. LOD0 14,887 triangles (hair 1,527).
- **Weights**: cap rigid on Head (F2's), the lowest 2.5 cm of the rim below the ears/nape eased onto the skin under it, the braid tube
  Head at the tie then the back's weights (as Fre's own braid: MM9's Ponytail clips swing a Ponytail braid into the back); face-shell and
  old-hood rows the cap covers take the cap's weights (`merge_weights_pf4.py`), so nothing under the hair moves through it.
- **Hair paint** (`hair_tex_fre.py` -> `textures/fre_hair_{base,normal,orm}.png`): F2's copper paint recoloured to Fre's chestnut-auburn
  (per-channel mean/spread of the old cap's hair texels); Fre's circlet repainted on the cap from the old cap's paint along rays from the
  head centre (gold/violet only, flat normal, roughness 0.45; not on the braid); the lowest 5 cm brightened and its AO floored (F2's paint
  darkened toward its own nape: a black helmet rim on Fre); a soft hairline: the outer 8 mm mixes toward skin, more in the strand gaps.
  `build_glb_pf.py`: cap normals near the lower rim turned outward (no dark underside), the teeth's normals relaxed.
- **Bare skin** (where the bob was): `seam_skin_fre.py` (old-hood teeth and hair/ear paint under the old cap -> skin, blurred band,
  their chart gutters grown), `temple_skin_fre.py` (orchestrator on r55: one smooth 3D-weighted heal of the temples/face sides from the
  clean cheek skin, feathered, normal toward flat, AO to 1), `ao_lift_fre.py` (the bob's baked AO 0.1-0.5 off the jaw sides, nape and
  under the chin).
- Sheets (read zoomed): `review/faces/r62_face.png` (front close-up, 3/4, both true profiles, low 3/4, Talk, under the jaw, party),
  `review/faces/r62_back.png` (back, 3/4 back, both ears), `review/faces/face_r43_vs_r62.png` (before/after),
  `review/mm9_vs_ours_r43_r62.png` (full body: MM9, r43, r62).
- Gates r62 (`review/gates_r62/`): arm/hand 0 frames > 1 cm in 11 clips, jitter 0, robe 0, sleeve poke 0, braid 0 frames > 1 cm (max
  0.5 cm), flat 0.00/0.01/0.00, bones 0, detached 2 legs (as before), winding 0. **Cap poke 0.0 mm in every clip** (body and old hood,
  vertices the hair covers > 8 mm from its rim; also 0.0 mm at > 4 mm, `cap_poke_4mm.txt`). `cap_poke_fre.py` now tests only what the
  hair covers (the rim lies on the skin, so hairline skin is beside it); `gate_fre.py`'s old-hood-out reads the kept skin teeth beside the
  rim (1.1-2.0 cm, by design). Texture: FreHead atlas 58.4 % -> 34.2 % (the old cap's texels are unused now), FreHair 21.5 % (F2's layout).
- Installed r62 sha256 6cf1b2664aff7997... (= export); binding PASS (252 descriptors on 114 models, 0 failed); floor ok; viewer 11/0.
- Remaining marks: a faint tone step at the temple beside the brow tail in Talk; small polygon facets of the skin teeth at the temples
  in profile; under the chin reads darker from below (the accepted smooth under-chin shading, kept as asked); the braid is F2's tube
  without the MM9 gold binding; a few light specks beside the braid's tie in the 3/4 back view.

## Pass 5 (orchestrator on r62: temple/face-side panels) -> r72, 0 credits
- Unlit base-colour renders (`scripts/uv_probe_render.py`, `review/hair/r63_unlit.png` .. `r65_unlit.png`) showed the paint itself had
  hard-edged patches at the temples (the earlier heals cut hard edges in 3D). `temple_skin_fre.py` now treats every side-of-head texel
  that differs from Meshy's raw paint as repainted, blurs that mask in 3D into a soft weight and paints the whole area from one smooth
  cheek-skin field (circlet front and brow tails kept); expose_skin's / seam_skin's hard normal flattening is replaced by the same soft
  weight. Unlit, the temples and face sides are now one continuous tone (`review/hair/r65_unlit.png`).
- Geometry: the hair now goes out to Fre's head instead of her face shell going in under it (`build_hair_fre.py OUT_FIT`: cap rows in
  front of the ears less than 4 mm outside her head move out, at most 12.4 mm, median 3.5 mm; the back keeps F2's shape). Face-shell
  rows moved by the fit dropped from 24.5 mm max at the temples to small moves under the hair (largest at the nape midline and forehead
  top, hidden). The old-hood teeth in front of the ears are no longer tucked (they stay on F1's own shell, one surface with the face).
- `build_glb_pf.py`: the hair's front/side rim takes the normals of the skin under it; flipped face-shell normals (folded teeth) are
  replaced by their neighbours'. `ao_lift_fre.py`: the face-shell AO is divided by its own broad mean, so the bob's broad occlusion goes
  and crevices stay. `smooth_side_fre.py` (position relaxing) was tried and is off (SIDE_PASSES=0): it did not change the temple and
  pushed shards out at the ear.
- **Residue that further rounds did not fix (r65-r72)**: in Talk (head turned to the light) a pale angular area remains at the temple
  between the brow tail and the hairline, and small dark-brown shards at the hair edge below the ear; front, 3/4, both profiles and
  low 3/4 read clean. Unlit the paint there is smooth, so it is lighting on that geometry (the face shell's outline / ear-plate folds
  under the hair edge); a fix would mean rebuilding that strip of the face shell or a fresh head paint, not more tweaks.
- Gates r72 (`review/gates_r72/`): cap poke 0.0 mm in all 11 clips (8 mm and 4 mm rim skip), arm/hand 0 frames > 1 cm, jitter 0, robe
  0, sleeve poke 0, braid max 0.5 cm (0 frames > 1 cm), flat 0.00/0.01/0.00, bones 0, winding 0, detached 2 legs (as before; plus a
  hidden old-hood part's "root lift" 14 cm in Hit, not visible: `review/faces/r72_hit_sheet.png`).
- Installed r72 sha256 aabcf1a42423d991... (= export); floor ok; viewer 11 switches, 0 errors. Binding regression could not run: the
  game fails to load `worlds/mm9/modifiers.yml:33` (`evade_min_seconds`, another agent's change ahead of the built binary).
- Sheets: `review/faces/r72_face.png`, `review/faces/r72_back.png`, `review/hair/talk_67_72.png` (Talk temple, r67 vs r72).

## Pass 6 (stopped, user decision 2026-11-04: Fre gets a new head from a fresh agent)
In progress when stopped: rebuilding the side-of-head strip (temple to behind the ear, down to the jaw angle) of F1's face shell:
`scripts/rebuild_strip_fre.py` (delete the folded old-bob faces, ear plates and old-hood flaps in the side box; fill with a symmetric
RBF-fitted Delaunay patch welded to the kept face; new UV charts in the old cap's free texels). Not converged (holes in front of the
ear, flaps outside the box); outputs only in `work/asm_s6.npz`, `work/uv_s6.npz`, `work/strip_report.json`, previews
`review/hair/s6_parts.png`. Nothing from pass 6 was installed: the installed model stays r72 (sha256 aabcf1a42423d991...;
`work/asm_frozen.npz` / `work/uv.npz` are r72's). The head is being replaced (Codex references + Meshy head).

## Pass 7: new head (user decision 2026-11-04) -> r76, 15 Meshy credits
Face and hair are now ONE new Meshy head from fresh Codex references, joined to Fre's own neck; F1's face shell ('head'), the hidden old
hood ('scarf') and PeasantF2's hair cap ('hair2' outside the braid tube) are gone. Body, dress, skeleton, weights, clips and the braid tube
are r72's. Rollback: `work/r72_rollback/mm9_fre.glb` (r72, sha256 aabcf1a42423d991...) and `work/r72_rollback/build_glb_pf.py`.

**Route** (scripts `scripts/nh_*.py`, one rebuild command `scripts/rebuild_nh_fre.sh <rev> [--install]`):
1. Codex HD masters `references_newhead/` (`scripts/codex_newhead.sh 1|2`, brief `CODEX_BRIEF.md`): from MM9's head renders
   (`references_hd/mm9_head_views.png`) and the approved head paint-overs (`references_head/0*.png`, face and colours only); a bust with
   a bare neck and shoulders, no braid (kept as its own piece), a sleek centre-parted bob over the ears, the gold circlet with the violet
   jewel and the crown band. 00 (run 1, attempt 2 of 2) then 01-04 (run 2, 00 as input); every view read; clean alpha by
   `nh_key_bg.py`. Hashes in `creature_3d_progress.json` -> `references_newhead`.
2. Meshy (backup account): Smart Topology 15k from `00_three_quarter_clean.png` (`requests/newhead_smart_v1.json`, job `fre_newhead_smart`,
   5 credits) and a 4K retexture on our upload with 01/03/02/04 (`requests/retexture_fre_newhead.json`, job `fre_newhead_tex_4k`,
   10 credits). Balance 2190 -> 2185 -> 2175.
3. `nh_prep.py` (Blender): pieces kept = face/neck/skull, hair shell, eyeballs; the circlet wires, beads and mouth inserts dropped (the circlet
   is paint, as MM9's); frame from the eyeball centroids (yaw 0.65 deg, roll 0.11 deg), scale 0.411 (eye distance and eye-to-chin agree),
   eye midpoint on r72's (0, -0.0983, 0.6839); the figure's right half mirrored (symmetric by construction: midline overlay in the sheet).
4. `nh_build.py` (Blender): the parting slit Meshy cut through the hair shell is closed (wall faces deleted, the two outer edges bridged by
   mirror pairs, leftover inward faces and pockets in the band removed; voxel remesh and collapse attempts left holes and were dropped);
   a slimmer bob behind the face (x 0.90, back 0.92 above the jaw; hair width 20.7 -> 18.7 cm; MM9 20.8, r72 16.2); the Meshy neck cut 4 mm
   above the slanted plane z = 0.556 + 0.16 (y + 0.05), r72's neck band below that plane kept (its bottom stays welded to the dress
   neckline, its weights kept), the new neck's lowest 3.5 cm fitted radially onto r72's neck section (ring difference -1.0..+0.9 cm,
   faded upward), one bridge strip between the rings; symmetric decimation (face 2.9k, hair 1.4k, eyes 200), Meshy fins removed.
5. UVs `nh_uv.py` with `claude_shared/uv_atlas.py` (1024, 2 px margin, face front x2.0, hidden skull/inner hair x0.3, chart cost 4):
   **never re-run** (the paint belongs to `work/nh/head_uv.npz` / `texturing/fre_newhead_upload.glb`). A one-island face was tried
   (`FACE_ONE=1`) and dropped: minimum-stretch p90 4.2, conformal collapsed 31 triangles.
6. Head set 1K (`nh_textures.py`): Meshy's 4K maps with gutters filled from the nearest chart texel and ONE Lanczos downsample
   (`nh_compose.py`; `compose_islands_fre.py`'s border-band repaint cut the brows into blocks); no grade (the gentle grade's AO multiply drew
   polygon-shaped dark patches on the jaw: `review/newhead/grade_cmp.png`); `nh_mirror_paint.py` at 4K: her right brow tail and upper lid
   (painted on another chart in another tone) take her left side's paint at the mirrored 3D point, and both brow tails fade into the skin
   where they crossed a chart seam in a square step; `nh_eyes.py` a soft lid shade on the eyeballs. ORM: AO baked on the upload
   (`texpass_bake_ao.py`, `pad_ao.py`), mild (skin >= 0.92, hair 1 - 0.4 (1 - ao)), roughness >= 0.6, metallic 0. The braid keeps
   PeasantF2's paint toned to the new hair (`nh_braid_tone.py` -> `textures/nh_braid_base.png`).
7. Assembly and weights (`nh_assemble.py`): head, hair and eyes rigid on Head; the new neck's lowest 2 cm eased from r72's ring weights to
   Head; r72's neck band keeps its weights (Neck / XhalfHead / Head); the braid's top moved 5.5 cm into the hair at the nape (fading to 0
   at z 0.45). Two 18-triangle zero-volume hair flaps dropped (check_winding's inverted part). Mesh build `rig_nh_fre.sh` with
   `build_glb_pf.py` (new block for 'nhead': the under-chin and nose-underside normals turned forward with a smooth Gaussian falloff,
   positions untouched; the old F1-face steps find no 'head' vertices). Runtime `build_runtime_fre.sh` unchanged.
- LOD0 14,596 triangles (head 4,733: face/neck/skull 2,914 + r72 neck band 232 + bridge 82, hair 1,341, eyes 200 minus the dropped flaps;
  r72 14,887); LOD1-3 7,263 / 2,612 / 867.

**Gates r74/r76** (`review/gates_nh/`; `scripts/gates_nh_fre.sh` = gates_fre.sh without gate_fre.py, which reads F4/F2 hair indices):
| Gate | r72 | r76 |
|---|---|---|
| hair poke (`nh_poke.py`: neck, dress, braid through the new hair) / old `cap_poke_fre.py` | 0.0 mm all clips | 0.2 mm max (Hit), 0 frames > 2 mm in all 11 clips |
| `arm_hand_gate.py --outer-only --exact` | 0 frames > 1 cm; forearm 2.4 Cower | same |
| `jitter_gate.py` / `robe_gate.py` / `sleeve_poke_pf1.py` | 0 / 0 / 0 | 0 / 0 / 0 |
| `flat_shading_check.py` | 0.00 / 0.01 / 0.00 | 0.00 / 0.00 / 0.00 |
| `check_winding.py` | 0 | 0 |
| `detached_parts_audit.py` | 2 legs (+ hidden old-hood root lift) | 2 legs (by design) |
| `bone_length_audit.py` | 0 | 0 |
| `collapse_gate.py` | Hit armpit R 77, waist 64; Death neck 83 | Hit armpit R 77, waist 64; Death neck 9 |
| `texture_quality.py` FreHead | atlas 34.2 % | atlas 64.9 %, spread 3.63 (face x2 / hidden x0.3 by design), fragments 1.0 %, stretch p90 1.15, 8 zero-area UV triangles (<= 1.3 mm2 slivers) |
| `texture_quality.py` FreHair | 21.5 % | 6.0 % (the braid only now uses this 1K set) |
| `see_through_gate.py` hole max px (el 0 / 20 deg) | head 65 / 27, torso 1596 / 50, sleeve L 2004 / 40, collar 974 / 63, sleeve R 7 / 44 | head 211 / 23, torso 1597 / 26, sleeve L 2004 / 8, collar 996 / 20, sleeve R 3 / 4, boots 0 (`review/gates_nh/seethrough/`). Head worst = Death frame 36 seen from the feet up the hollow dress into the open neck tube (`review/newhead/seethrough_head.png`); at 20 deg only the collar/neck-base corners (23 px) |
| `floor_audit.py --world mm9 --match 'MM9 256*'` | ok | stand -0.2, walk -0.1..+1.6, living -1.2, dead 0.0: ok |
| viewer `run_creature_review.py check` | 11 / 0 | 11 switches, 0 failed, 0 console errors |
Binding regression not run (another session's modifiers.yml change ahead of the game build; the orchestrator runs it).
Installed r76 sha256 0acc1da4638af366... (= export).

**Sheets (read at full size)**: `review/faces/r76_face_sheet.png` (front close-up, midline overlay, 3/4 both sides, both true profiles,
low 3/4 both sides, Talk, under the jaw, back, back 3/4, party, neck front, neck 3/4, hair by the ear), `review/faces/r76_face.png`,
`review/faces/r76_back.png`, `review/mm9_vs_ours_r72_r76.png` (full body: MM9, r72, r76), `review/newhead/` (Codex/Meshy/clay stages:
`smart_sheet.png`, `geo21_sheet.png`, `tex0_sheet.png` raw paint on our UVs, `eyes_flat*.png`, `browcmp.png`).

**Remaining marks**: the eyes read a little wide-open in the front close-up (Meshy's eye openings; geometry not moved after the paint, a lid
shade painted on the eyeballs); the right brow tail still has a small step at its lower edge in flat close-ups; a faint seam line across
the hair below the ear in the ear close-up; the braid comes out from under the hair at the nape as a thick stub with PeasantF2's plait paint
(no gold bindings); the parting is a crease over the top. Inherited and unchanged: the feather collar's ragged top edge with skin-coloured
teeth, the bell sleeve on the bust in Cower.

**Not checked**: in game (the map places the stand-in); motion at normal speed by eye; LOD1-3 and shadow meshes by eye; the binding
regression.

## Pass 7 round 2 (orchestrator pre-screen of r76) -> r78, 0 credits
1. **Eyes** (startled, white above the iris): calmer, slightly heavy upper lids in geometry (`nh_assemble.py` `lids()`): the upper lid moves
   down by up to 3.2 mm at the middle of the opening (cos^2 across the eye's width, smoothstep fades to the brow and the lower lid,
   mirrored), 100 vertices; 6 that would enter the eyeball pushed onto it + 0.6 mm. The lids now cover the top ~20 % of the iris. The
   paint follows (UVs travel with the vertices: lash line and crease stay on the rim; lid texels stretch by <= 3.2 mm), no repaint needed.
   Lids and eyeballs are both rigid on Head and there is no blink clip, so nothing moves between them in any clip.
2. **Crown** (gold stripe over the top): `nh_paint_fix.py` on the 4K paint: gold hair texels more than 12 mm above the circlet's own height
   at their azimuth (forehead ornament kept) take hair from the same surface turned 14-42 deg round the head (or shifted 3-5 cm at the very
   top), then the broad tone is matched to the hair round them. Two rounds; a faint lighter streak remains across the crown in the top-down
   'crown' shot.
3. **Jewel**: royal blue -> MM9's violet (hue +24 deg, saturation x0.85; the jewel's lower half lies on the forehead piece and is included).
4. **Braid**: three gold bindings painted on the braid (MM9-like: the tie just under the bob, mid, near the tip; `nh_braid_tone.py`), its top
   tucked 6.8 cm into the nape (was 5.5). It still leaves the bob as a thick plait under the hair edge (MM9's does too); a longer braid
   root would need the hair's nape remodelled.
- Gates r78 (`review/gates_nh_r78/`): hair poke 0.0 mm in all 11 clips; arm/hand 0 frames > 1 cm (forearm 2.4 Cower as before); jitter 0;
  robe 0; sleeve poke 0; flat 0.00/0.00/0.00; winding 0; bones 0; detached 2 legs; collapse as r76; FreHead atlas 64.9 %, stretch 1.16;
  floor ok; viewer 11 switches / 0 failed / 0 errors. See-through not rerun (lid and braid moves only; r76: head 211 / 23 px, the hollow
  dress from the feet).
- Installed r78 sha256 4b30f56d7f7ee01f... (= export). Sheet (read): `review/faces/r78_face_sheet.png` (front, midline, 3/4 both, both
  profiles, low 3/4 both, Talk, under the jaw, back, back 3/4, party, eyes close-up, crown top-down, ear).


**LOD0 reduced post-install on 2026-11-05 by `level_generation/creatures/mm9_fre_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_fre_reduce_claude/before/`.
