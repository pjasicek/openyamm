# MM9 PeasantM5, the bearded townsman (mm9_peasantm5) — 3D actor variant, 2026-11-02

MM9 `PEASANTM5.abc`, two `MONSTERS.txt` rows: **46 Town** "Peasant Human1 MaleB B" (`PEASANTM5B.dtx`) and **48 Shopkeeper**
"Peasant Human1 MaleC B" (`PEASANTM5A.dtx`), both NPCbase.scr, PeasantMale library. No DAT placement of their classes
(`TownHumanMaleB`, `ShopkeeperHumanMaleB`) was found in the rebuilt maps. Batch: `devdocs/mm9_rework/overnight/VARIANTS_BRIEF.md`.
Owner m45-agent. Receipts: `creature_3d_progress.json`.

**Route: variant on Markel (approved, frozen), head and ornaments reshaped.** `mm9_meshcmp.py peasantm5:markel,...` (re-run): M5 has
Markel's and PeasantM1's exact binds (bind diff 0.00 cm; PeasantM3 3.1 cm, M2 5.7, Forad/M8 18 cm); vs Markel head p90 1.2, arms 1.6,
legs 1.1, torso 3.5 cm; vs M1 torso 4.7. Side by side (`references_hd/mm9_m5_vs_markel_pm1_body.png`, `_head.png`;
`review/sheet_mm9_m5_vs_ours_markel_pm1.png`; clay `review/clay_markel_pm1_pm8_body.png`, `_head.png`): our built Markel is a
stocky man in a plain long shirt with a belt, rounded shoulders, a belly, rolled boot cuffs and a full beard, which is M5's silhouette
(signed distance of our Markel to MM9 M5 ~ the same as to MM9 Markel: `scripts/signed.py`, `review/sil_ours_markel_red_mm9_m5_green.png`);
PeasantM1 (hood, open jacket) does not fit. What differs: M5 has a full head of hair (Markel a bald crown), no torc, medallion, lacing
or belt studs. So: Markel's master (`../mm9_markel_claude/work/hair_v1.blend`, only read; copied to `work/markel/`), rig, weights,
texture-pass UVs and library clip choice; geometry edits below; new body and head paint; tier B by ramps + its own head colour.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_peasantm5.glb` (`tools/install_model.py --world mm9 --name mm9_peasantm5.glb`), = `export/mm9_pm5.glb` = `work/r16_final.glb` (sha256 a7e5f69a2ed7..., body fit r16 below); variants `pm5_a`, `pm5_b` |
| Binding | `actors.yml` `MM9 46 Town` (pm5_b), `MM9 48 Shopkeeper` (pm5_a) (`scripts/binding_pm5.yml`, `scripts/bind_under_lock_pm5.sh` under the flock): Markel's values (scale 100, yaw -1.5708, stride 1.1 / 2.8, look Neck/Head, impact 0.5 s); script clips talk, cower, stand |
| Descriptors | rows 46 -> 362 and 48 -> 365 in `mm9_npc_actor_rows.tsv` (their `mm9_npc_legacy_replacements.tsv` stand-ins), tables regenerated |
| Triangles LOD0/1/2/3 | 8,698 / 4,347 / 1,563 / 521 (r16) |
| Clips (30 fps, `source/mm9_lib/pmale.glb`, soft offsets) | Markel's library roles: Standing stand1, Walking walk3, Running run, Fidget fidget4, Talk conv2 (Markel's hand rest + R abduction), AttackMelee hattack1, Hit wince1, Death die1, Dead, Cower cower (BaseRun.inc). Markel's own Argument/Sit clips are not M5's: left out |
| Textures | body 2K colour + 1K normal/ORM on Markel's texture-pass UVs (repainted), region mask (R shirt, G trousers) + ramps per tier; head + hands 2K colour (tier B its own) + 1K normal/ORM on Markel's head UVs (repainted) |
| Meshy credits | **20 / 25**: body 4K retexture 10 (backup 2705 before), head 4K retexture 10 (backup 2695 before); no retries |
| Viewer | http://127.0.0.1:8912/level_generation/creatures/mm9_peasantm5_claude/review/viewer/ (tiers pm5_a, pm5_b) |

## Body fit r16 (2026-11-02, user via coordinator: "isnt there a disparity between the body size and head size?") - current

Markel's body was wider than MM9 M5 along the torso sides, upper arms, shirt hem/hips and thighs and deeper in belly and back,
while the heads matched (`review/sil_before_fit_red_mm9_m5_green.png`). Fixed on the body only, in bind space, positions only
(topology, UVs, weights, clips unchanged; paid paints valid; 0 credits). Chain `scripts/fit_chain_m5.sh` from `work/lid_m5_v3.blend`:
1. `scripts/band_scale.py` (hip band z -0.20..0.30: shirt skirt, belt and the trouser tops inside them scaled together per height
   toward MM9 M5's extents, factors 0.77-1.0): an offset field pulled the skirt in onto the hidden trouser top, which then poked
   through (`review/clay_fit_final.png`, `review/clay_fit_kept.png`).
2. `scripts/fit_body_m5.py` x5 (band excluded): outer-layer vertices (free air along their normal) want the move onto MM9 M5's
   surface (nearest point along M5's normal; later passes also along their own normal and, for cloth off M5 with no surface on
   its normal, to the nearest point); a Gaussian average (2 cm, last pass 1 cm) of those moves is applied at every vertex so
   inner layers follow; region weight 1 on trunk, thighs, calves (boot shafts), clavicles, upper arms; 0 on head, neck, hands,
   feet and **forearms** and round both **armpit folds** (master x +-0.25, z 0.395): fitting those folded Meshy's armpit web and
   the upper-arm inner sleeve layer through the outer cloth (see-through tests r6-r15: sleeve R 21-32 px, torso up to 47 px).
3. `scripts/move_despike.py` (single vertices pulled away from their ring, e.g. a 47 mm dent in the upper back, replaced by
   the ring mean) -> `work/fit_m5_ds.blend`; then `scripts/linings_pm5.sh` (re-lined: neck cap, belt rim, cuffs) ->
   `work/linings_v1.blend` (the master), `scripts/head_b.sh`, `scripts/build.sh --install`.
Result vs MM9 M5 (`review/sil_fit_final_red_mm9_m5_green.png`, signed distance to M5's surface, cm, p50 / p90): trunk 2.5 / 4.6 ->
0.2 / 1.8, upper arms 3.1 / 5.4 -> 0.8 / 4.0, thighs 1.9 / 5.3 -> 0.4 / 1.5, calves/boots 1.6 / 4.9 -> 0.3 / 4.0 (boot toes),
head unchanged. **Not within 1 cm everywhere**: the armpit wedge (2-4 cm) and the forearm undersides (kept, see above), the
hands and the boot feet (pinned as asked; ours are larger than MM9's) and the shirt hem flare at the hip sides (~1-2 cm).
Clay before/after `review/clay_fit_final_r16.png`; viewer full body before/after next to MM9, both tiers:
`review/sheet_bodyfit_before_after.png`; faces unchanged (`review/sheet_face_viewer_a_r16.png`, `_b_r16.png`).
Gates on the installed `work/r16_final.glb` (sha256 a7e5f69a2ed7..., `review/gates_r16/`): arm/hand hands 0 except Fidget R
1.4 cm (4 f), forearms <= 0.9 cm (were 1.5-3.8 cm); jitter 0 fails; sleeve poke 0 mm; see-through (`review/see_through_r16/`)
torso 7 px (was 36), sleeves 1 / 0, head 2, trousers/boots/collar 0; detached 0; flat 0 %; winding 0; bones 0; floor ok;
LOD0 8,698; viewer `r16-20261102-bodyfit` 20 switches 0 failed; binding regression PASS (246 descriptors on 109 models).
The baked AO in the body colour is from the pre-fit shape (not re-baked). Rollback of r5: `work/before_fit/`. Markel unchanged
(534-line sha256 list identical again).

## Route (project folder; nothing written into mm9_markel_claude)
0. Sources `scripts/convert_sources.sh`; renders `scripts/render_mm9_set.sh`, `scripts/side_sheet.py`, clay `scripts/clay_blend.py`.
1. **Geometry** (positions and deleted ornament parts only; UVs of kept faces, weights unchanged):
   `scripts/hair_raise.py work/markel/hair_v1.blend work/hair_m5_v2.blend 1 2 0.0105 0.003` — Markel's hair shell was sunk 1.5-3 mm
   under the face shell over his bald crown; every hair vertex lower than 10.5 mm above the face shell is raised to it (front hairline
   3 mm, boundary otherwise fixed), Laplacian-diffused and faired (6 passes); face-shell pokes through the hair 64 -> 19 (the rest are
   Markel's temple pokes under the side hair, no crown poke; `review/clay/m5top2_sheet.png`, `review/clay_head_markel_vs_m5_v1.png`).
   `scripts/strip_parts_m5.py` deletes 26 small parts (408 vertices): torc/tie, pendant, chest medallion, lacing plates, belt studs;
   eyes and buckle kept (`work/strip_m5_v1.json`, clay `review/clay_torso_markel_vs_m5_v1.png`).
   `scripts/lid_fold.py work/strip_m5_v3.blend work/lid_m5_v3.blend` (3 vertices, 1.5 mm): Markel's lower-lid face 3801 folded
   46 deg (-> 30) and shaded as a dark triangle under the right eye in the viewer (Markel's README "speck"). Then `scripts/linings_pm5.sh` (PeasantDM2's tools; see-through gate): head neck bottom capped (`neck_cap.py`), the shirt's rim at the belt lined (`rim_lining.py`, band 12 cm), both cuffs lined (sleeve band 55 cm, inner layer skipped). The geometry chain was re-run with the hairline tucked 1.5 mm under the skin (`hair_raise.py ... 0.0105 -0.0015` -> `hair_m5_v3`, `strip_m5_v3`, `lid_m5_v3`): at 3 mm proud the see-through gate looked under the hair edge. **`work/linings_v1.blend` is the master.**
2. **Uploads** `scripts/export_uploads_m5.py` (no re-layout; checked byte-exact against Markel's own uploads on his master).
3. **HD masters** (Codex): `SHAPE=mm9_markel_claude scripts/codex_masters.sh <P> 1|2` (`references_hd/CODEX_BRIEF.md`; run 1 failed
   once on 5 reconnects, relaunched), head turnaround `scripts/codex_head.sh` (`references_head/CODEX_BRIEF.md`), `clean_alpha.py`.
   Read: `references_hd/selected_views_review.png`, `review/body_clean_check.png`, `references_head/selected_views_review.png`.
4. **Paint**: `requests/retexture_{body,head}_pm5.json` (4K). AO `scripts/bake_ao_texpass.py work/strip_m5_v1.blend`;
   `compose_texpass.py`; gentle grade; `scripts/sleeve_paint_fix_pm5.py`; **`scripts/chest_match.py`** (new: the chest skin in the shirt
   opening was paler/pinker than the head set's neck, a flat bib under the jaw: solid skin blobs toned to the neck median);
   **`scripts/trim_calm_pm5.py`** (the braided neckline came out as a wide yellow/black leopard print over the raised collar: calmed
   to a woven brown band). Head: `compose_head_texpass.py mk_tp pm5_tp ...` (path fix: Markel's head sets live in `textures/`), then
   `scripts/head_paint_pm5.sh` (lash-line sliver refill from the skin below the lid, no generic speck pass: brown irises read as beard
   specks; `hand_clean_pm5.py`; `pad_head_pm5.py`; `normal_sliver.py`: flat normal on that sliver).
5. **Tiers** `scripts/tiers_pm5.py` (from PeasantM1's): R shirt, G trousers; both tiers' shirt by MM9's own colours (luminance
   quantile x the gain mapping MM9 A onto our paint; the paint was more yellow-tan than MM9's warm brown), trousers MM9 knit x1.3; fit
   shirt A 1.9 / B 1.8, trousers A 4.9 / B 4.3 mean 8-bit. **Tier B head** `scripts/head_b.sh` (0 credits): A's head with hair and beard
   recoloured to MM9 B's golden-brown (`face_b.py hair`), a Codex repaint of the flat front render (`references_face/`, brief there:
   leaner fair man, blue eyes, short close beard inside A's beard outline, closed slight smile) projected in the face window
   (`face_b.py project`: chart-edge texels filled from the projection, the lip line de-reddened 40 %), the sliver refill. B shares A's
   head normal/ORM. Runtime: `scripts/tier_head.py` (PeasantM1's) + `claude_shared/region_variants.py` in `scripts/build_runtime_v2.sh`.
6. **Runtime** `BLEND=work/linings_v1.blend scripts/build.sh [--install]` (Markel's chain: export, clips_mm9 soft line,
   `hand_rest_pm5.txt` + `spread_pm5.txt` = Markel's Fidget/Talk lines, prepare, LODs, shadow fix, tiers, extras, floor `floor_ops_pm5.txt`,
   mirror to MM9 handedness, winding). Viewer `scripts/viewer_tiers_pm5.py` + `scripts/make_viewer_manifest.py`.

## Checks (installed GLB = `work/r5_final.glb`, `review/gates_r5/`)

| Gate | Result |
|---|---|
| Arm and hand (`arm_hand_gate.py`) | hands 0 except Fidget R 1.4 cm (4 f, Markel's); forearms up to 1.8 cm (Talk L; 3.8 before the cuff linings); finger stretch max 2.91; 19 chains per hand |
| Jitter (`jitter_gate.py` vs MM9's clips) | **0 fails** |
| Sleeve poke | **0 mm** in every clip, both sides |
| See-through (`scripts/see_through_gate.py`, every clip, 8 az x 0/20 deg, `review/see_through_r5/`) | before the linings (r4): sleeves 61/78 px, head 30 (under the raised hairline), torso 60 in every clip. After (r5): sleeves 0 / 1 px, head 1, collar 0, trousers 0; **torso not 0**: worst 36 px (Death 30, lying, seen from below the chin: a slot between the head's 19-edge neck loop and the shirt; capping that loop inverted 8 parts, so left), 16 px Dead/Running (a hairline slit at the belt side), 1-8 px elsewhere |
| Rigid head | Markel's weights (chin/jaw on the Head) unchanged |
| Detached / flat / winding / bones | 0 detached; flat 0.0 % both; 0 inverted; 0 stretching |
| Sleeve poke | 0 mm every clip (again after the linings) |
| `texture_quality.py` | body atlas 58.5 % (lining faces map to one texel each, so the density p10 reads 0: by design, as PeasantDM2), spread 1.06 before the linings, fragments 0.0 %, stretch p90 1.08; head set 39.1 %, fragments 1.8 %, stretch p90 1.73 (Markel 1.63: the raised crown charts; above the 1.5 target, not re-laid: the UVs the paid paint depends on) |
| Floor (`floor_audit.py --world mm9 --match 'MM9 4[68] *'`) | ok both: stand 0, walk -0.2..+1.8, dead 0 (Markel's) |
| Viewer check | 20 switches, 0 failed, 0 console errors |
| Regression `mm9_actor_models_build_every_binding` (`--world mm9`) | **PASS**, 234 descriptors on 103 models (`review/regression_binding.log`) |

Sheets read: `review/sheet_mm9_vs_ours_r1.png` (MM9 A vs ours), `review/sheet_face_viewer_a_r5.png` and `review/sheet_face_viewer_b_r4.png` (B's face is unchanged by r5)
(**viewer lighting**, per tier: front close-up, 3/4, both true profiles, low 3/4 from below, party view, 128 px party-distance head,
Standing and Talk, MM9's head of that skin), `review/zoom_b/sheet3.png` (viewer: mouth/nose and under-eye zooms, A and B), `review/r2_head.png`
(neck sides), `review/r3_eyes_mouth.png`, `review/eyeflat/f23.png`, `references_face/review.png`, `review/tier_preview_atlas.png`,
`review/sheet_ears_r5.png` (both ears, tight, 3/4 backs, from below, jaw-neck lines), `review/r5_neck.png` (neck sides, Death).

## Source model untouched
`mm9_markel_claude/` was only read (copies here). sha256 of its 532 files plus `assets_source` and `assets_dev` `mm9_markel.glb`:
`review/source_sha256_before.txt` = `review/source_sha256_after.txt` (identical, 534 lines). The `MM9 248 Markel the Great` block was not edited.

## Open points / not checked
- Tier B's medallion (MM9 PEASANTM5B) is not modelled or painted; B's shirt differs from A by colour only (ramps).
- Tier B's face is a projected Codex repaint on A's geometry: A's fuller beard volume stays (painted short and golden on B), and the
  beard sides in profile keep A's strand pattern recoloured.
- The braided neckline is a calmed woven band, not MM9's fine braid; the raised collar is Markel's fur-collar shape.
- Head-set stretch p90 1.7 over the 1.5 target (raised crown).
- Torso see-through slot under the chin in the lying corpse (36 px) and a belt-side slit (16 px) remain.
- The rebuild is not byte-reproducible (a second build gave another sha256); the installed file is the gated `work/r5_final.glb`.
- Skin variants beyond A/B: none exist. No in-game run (rows 46/48 have no placements; the transcoder switch is the orchestrator's);
  LOD1-3 and shadow meshes not looked at; clips watched only as stills/gates.

User artistic acceptance: not recorded.


**LOD0 reduced post-install on 2026-11-05 by `level_generation/creatures/mm9_peasantm5_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_peasantm5_reduce_claude/before/`.
