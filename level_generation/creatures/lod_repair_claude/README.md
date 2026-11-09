# Far-LOD repair of installed creatures (2026-10-22)

User: the lizardman peasant visibly changes when it switches LOD (Dagger Wound, Emerald Island); "can you detect
which other models have this issue?"; "do just proper 2)" in a batch, pilot first; then "check that in game and check
if we should apply this globally". Status: **installed 2026-10-22 on 156 of 185 creature bodies (29 kept as installed);
desktop and Android cooks verified (0 problems).** No Meshy credits. Region masks of 11 four-region models fixed and
reinstalled the same day (section at the end).

## Problem

An audit of all 185 installed creature bodies (renders of every LOD, each switch compared at the size where the game
makes it: 450 / 180 / 72 px of the bounds diagonal) found 40 with visibly broken far LODs, almost all at LOD3.

- `tools/build_actor_lods.py` defaults to ratios 0.5 / 0.18 / 0.06, so most LOD3s keep 4-8 % of LOD0
  (the [modelling guidelines](../../GAME_ASSET_MODELLING_GUIDELINES.md) ask for about 50 % per level).
- The installed atlases are split into tiny UV islands (median 2 triangles per island on the lizardman, cannibal and
  werewolf, 7-12 elsewhere). A strongly reduced LOD cannot use them: its triangles span many islands. Blender's
  collapse respects the seams and stalls (lizardman: 2,363 triangles at any ratio) or breaks into shards; a collapse
  that crosses them smears the atlas. **The far LODs need their own textures; ratios alone do not fix them.**

## Route (`scripts/`)

LOD0 and LOD1 stay byte-for-byte; LOD2 and LOD3 (and their shadow meshes) are rebuilt. Separate effect meshes and
death rubble keep their own LODs (the body is the skinned LOD node with the most triangles).

1. `build_lods.py` (Python with pymeshlab): one MeshLab quadric collapse of the welded LOD0 on positions only,
   borders free, no optimal placement, so every LOD vertex is an LOD0 vertex: skin weights, normals and burn order
   stay exact. Shadow LODs: merged colour LOD tucked inside LOD0. A MeshLab crash (MM6 Queen fighter) is retried
   with topology preserved. Rejected: texture-aware collapse (spikes, lost head), protected borders (closed body
   skin vanished at LOD3: cannibal, harpy), per-piece reduction (overshot the budget).
2. `unwrap_lods.py` (xatlas): new UVs per LOD primitive, in the primitive's own triangle order; texture size 512 px
   (LOD2) / 256 px (LOD3) scaled by each material's share of the surface (power of two, at least 64).
   Blender's Smart UV Project gave NaN UVs on multi-material bodies.
3. `transfer_textures.py`: per texel, the nearest LOD0 point on the same connected piece and facing the same way;
   base colour, metal/roughness (bilinear) and region mask (nearest, all four channels) from there, and LOD0's
   shaded normal re-encoded in the tangent frame that `fs_model.sc` rebuilds from derivatives (no stored tangents).
   A Cycles bake encodes against MikkTSpace tangents and shaded the coarse LOD3s dark and blotchy in game; its rays also picked up the
   cannibal's feather cape on the body.
4. `apply_bake.py`: new LOD vertices (LOD vertex + new UV), the images, and copies `<material>_LOD<N>` of the default
   and every variant material for the maps it has. Region ramps are unchanged, so A/B/C tiers keep working
   ([creature textures](../CLAUDE_CREATURE_TEXTURES.md) contract).
5. `audit.sh` (`lod_split.py`, `lod_render.py`, `lod_score.py`) scores each switch; `repair.py` runs 1-5 over the
   ladder (LOD2/LOD3 of LOD0: 25/12, 30/16, 35/20, 40/25 %) from `originals/<stem>.glb` (the installed GLB before
   its first repair, also the rollback source) and keeps the first step that passes the gate (LOD2 outline <= 6 %,
   colour <= 16 or LOD1's + 3; LOD3 <= 13 % and <= 19.5). `review_sheet.py` draws installed vs repaired.

```sh
python3 -m venv <venv> && <venv>/bin/pip install pymeshlab xatlas numpy scipy pillow
LOD_REPAIR_PYTHON=<venv>/bin/python python3 scripts/repair.py <stem>...   # export/<stem>.glb
LOD_REPAIR_RUN=<name> ...   # work/<name>/ and no export (experiments, the global run)
```

About 30 s per ladder step. If a model's LOD0 textures change later, rerun it: its far textures do not follow.

## In-game check of the pilots (2026-10-22)

`mm8_lizardman_peasant`, `mm7_m262` Harpy, `mm6_natm` PeasantM4, `mm6_wwf` Werewolf installed; A/B/C tiers spawned
as friendly actors (Dagger Wound, Deyja, New Sorpigal), forced LOD 0/2/3 close up and from 2,850 units (real LOD3
distance). Tiers keep their colours at every level; LOD2 -> LOD3 is seamless at distance. Harpies B/C do not render
when debug-spawned on Emerald Island (`actor model scale requires a valid standing sprite`): a debug spawn of a tier
the map does not preload; unrelated to LODs.

## Global run (`work/global/`, `decision.json`)

All 185 bodies, 0 pipeline errors. Compared with the installed LODs at the switch sizes:

| | models | LOD2 outline / colour (median) | LOD3 outline / colour (median) |
|---|---:|---|---|
| clearly better | 142 | 3.8 -> 3.2 % / 12.8 -> 9.9 | 10.4 -> 5.4 % / 16.9 -> 8.4 |
| mixed (LOD3 better, LOD2 slightly worse) | 15 | | |
| keep installed (already good, mostly recent MM8) | 28 | | |

39 of the 40 broken models are clearly better, the 40th (`mm6_cdr1`, Cover Dragon) mixed but visibly fixed.
Review sheets: `review/global_improved_sample.png`, `review/global_mixed_a.png`, `review/global_mixed_b.png`.
Of the mixed models only `mm8_m528` (Will o' Wisp ring) looks worse: its repaired far levels have a notch cut out of
the ring; keep it installed. Cost of the 142: LOD2 triangles 1.31x, LOD3 1.73x, GLBs 1,220 -> 1,363 MB, plus one small
far texture set per creature type.

Recommendation: install the 142 clearly better and the 14 good mixed models (156); keep 29 as installed.

## Install (done 2026-10-22)

`scripts/install_batch.sh global work/install_list.txt` installed 156 models (`work/global/install.log`); 6 first
failed `check_winding.py` on their new far meshes and were rebuilt after two fixes (a shadow piece thinner than the
tuck margin keeps its place; pieces collapsed to two triangles are dropped). Smoke runs on oute3, 7out01, 7out05,
out01 and out02: no model load errors. Ledger section "Far-LOD repair (2026-10-22)". A full desktop cook removed 72
stale textures of the replaced LODs; `tools/cook_android.sh` cooked and verified the Android textures.


`tools/install_model.py export/<stem>.glb --world <world>` (after `check_winding.py`), a line per model in
[REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md) (rollback source `originals/<stem>.glb`), then the Android cooked
assets.

## Region-mask alpha bug (found, fixed and reinstalled 2026-10-22)

`transfer_textures.py` loaded and wrote the region mask as RGB until 2026-10-22, so every far-LOD mask had alpha 255:
a model with a fourth colour region (ramp 4 on mask alpha) showed that region's colour over its whole LOD2/LOD3
(Hesper villagers: one hair-coloured figure; in game the MM6 Patrol Units turned flat pink/yellow, MM8 Gorgons red,
troll peasants white). The script now keeps RGBA. An audit of `assets_source` (every `*_LOD2`/`*_LOD3` mask against
its LOD0 mask, and every creature with four ramps) found exactly 11 affected models, all fixed and reinstalled:
`mm6_bld`, `mm6_fgt`, `mm6_hyd`, `mm6_mep`, `mm6_rob1`, `mm7_m182`, `mm7_m461`, `mm8_m408`, `mm8_m480`, `mm8_m492`,
`mm8_m564`. Other four-ramp models (`mm6_wel`, `mm8_m516`, attachments) kept their installed LODs and are unaffected. The other repaired models still carry RGB far masks, which is
harmless with three ramps (the shader ignores channels without a ramp); a fourth ramp added later needs a mask rerun.

Fix: the patched `transfer_textures.py` and `apply_bake.py` were rerun on each model's installed step
(`work/global/<stem>/<step>.built.glb` and its `bake_<step>/lod<N>.npz` unwrap), not on a new ladder run:
`build_lods.py` (MeshLab) is not deterministic, so a fresh `repair.py` run (`work/alphafix/`, kept for reference)
builds slightly different far meshes (all 11 chose the same step; `mm6_bld` then misses the LOD2 outline gate,
6.2 % against 6.0). Reapplying the old PNGs to the built GLB reproduces each installed GLB byte for byte; the new GLBs
differ from them only in the far-LOD mask images (RGB identical, alpha added): geometry, UVs, base colour,
metal/roughness, normals, materials and LOD0/LOD1 are byte-identical (to `originals/` for LOD0/LOD1), so the gate
numbers in `work/global/<stem>/result.json` still hold. Every far-LOD mask texel's RGBA now occurs in its LOD0 mask
(installed: 0-44 %, except the robot eye).

Tier check (`work/alphafix_tiers/`, Workbench renders of each tier with the shader's region recolour baked into the
base colour; colour difference to LOD0 at the switch size, old -> new, A/B/C similar): Patrol Unit 53 -> 5 (LOD2) /
52 -> 8 (LOD3), Follower of Baa 42 -> 10 / 43 -> 16, Couatl 34 -> 9 / 31 -> 13, Gorgon 41 -> 10 / 41 -> 13, troll
peasant B/C 40 -> 7 / 39 -> 10, MM7 troll B 18 -> 7 / 19 -> 11, MM7 dragon 23 -> 7 / 20 -> 10, MM8 dragon
14 -> 8 / 14 -> 8; bloodsucker, thug and hydra (small fourth region) 8-14 -> 5-12. Sheet: `review/alphafix_tier_renders.png`.

Installed with `tools/install_model.py` (winding 0, only the 36 mask textures re-cooked), full desktop cook (36 stale
textures removed), Android model cook (36 cooked, 36 removed) and `cook_models.py --verify`: 0 problems. In game
(engine-native minimized tours, A/B/C friendly debug spawns on a map that preloads them, forced LOD 0/2/3 close up
and natural LOD at mid and far distance, before and after): sci-fi.blv (robots), 6d06.blv (thugs), outd3 (bloodsuckers,
followers), outa2 (hydras), MM7 out12 (dragons), 7out13 (trolls), MM8 out01 (Couatl), out04 (troll peasants), out05
(wimpy dragons, `mm8_m492`), out08 (Gorgons); in the narrow 6d06 corridor only two of the three thugs show.
Every tier keeps its LOD0 colours at LOD2/LOD3 and at distance:
`review/alphafix_ingame_mm6.png`, `review/alphafix_ingame_mm7_mm8a.png`, `review/alphafix_ingame_mm8b.png`
(row pairs before / after).

## Head bob (2026-10-22)

Installed sources of 23 models repaired here (MM6 bar1, ert, fmp, gob2, jak1, kni, lzd, mep, natf, ogr, ske, wwf; MM7
m162, m178, m286, m418, m438, m461; MM8 m432, m456, m468, m476, m520) now carry walk/run clips reshaped by
[head_bob_claude](../head_bob_claude/README.md) (`bob_fix.py`: pelvis bob rescaled or evened, legs solved to the
original foot paths). Their `export/` files are the pre-bob GLBs and `originals/` predate both passes: **a rerun of
`repair.py` on one of them must be followed by `head_bob_claude/run_jobs.py --only <model>`** on the new export (copy it
to `head_bob_claude/work/<world>/` first), or the bob fix is lost.

## MM9 run (2026-11-07)

Handoff with open items: [HANDOFF_20261107.md](HANDOFF_20261107.md).

User: a Sturmford City townswoman (`mm9_peasantf8`) visibly swaps model at distance. It is the LOD2 -> LOD3 switch
(72 px): MM9 creatures got `build_actor_lods.py` defaults (LOD3 about 6 % of LOD0) after the repair above, which never
covered MM9. `audit.sh` over all 125 MM9 GLBs: 58 with a LOD3 outline above 13 %, 100 failing the gate somewhere.

- Pilot `work/mm9_pilot2/` (`mm9_peasantf4/5/7/8`), then `work/mm9_batch/` (the other 96 failing; six lanes,
  `LOD_RENDER_CULL=1`). Installed 94 bodies (`work/mm9_pilot2/install.log`, `work/mm9_batch/install.log`), almost all
  at the first ladder step; typical LOD3 outline 10-35 % -> 2-7 %, colour 18-45 -> 6-14. Kept: `mm9_skelwar` (repaired
  LOD2 15.8 % and bone-coloured trousers), `mm9_fish` (BLEND material: no merged shadow), attachments without a
  skinned LOD body (halberds, imp trident/tongue/wraps, elf ears, honk hat). `mm9_dagrell` and `mm9_skeleton` miss the
  gate but are far better than installed (dagrell LOD3 outline 76 -> 11 %). Sheets: `review/mm9_pilot2_sheet.png`,
  `review/mm9_batch_a.png`, `review/mm9_batch_b.png`.
- In game (engine-native tour at the user's poses, before/after): the Sturmford woman keeps her LOD0 silhouette,
  sleeves and colours at LOD3; Sturmford City and Sturmford load without model errors.
- Desktop cook verified (0 desktop problems). **Android not cooked**: `tools/cook_android.sh` had a 6,200-texture
  backlog (mostly older changes) and was stopped; run it before the next release.

`build_lods.py` fixes for MM9 bodies:
- Faces whose corners weld to one point (4 zero-area slivers per MM9 head) crashed MeshLab's collapse (segfault, also
  with pymeshlab 2023.12); `repair.py` then fell back to topology-preserving collapse, which shredded heads and hoods.
  They are dropped from the collapse input. (`work/mm9_pilot/` is that fallback, superseded.)
- `merge_body_shadow`: MM9 heads became double-sided after their shadows were merged; the merged shadow now takes the
  body material's culling, as the installed shadows did.
- `drop_inverted_parts`: the collapse turns a few small closed pieces inside out (earrings, a weapon tip; 7 models
  failed `check_winding.py`); such closed negative-volume parts are removed from far colour and shadow primitives of
  single-sided materials.

Variant far maps (bug since 2026-10-22, fixed 2026-11-07): `apply_bake.py` gave every variant's `<material>_LOD<N>`
copy the default material's far maps. Tiers with their own paint (MM9 guard/thrall/troglodyte B/C, second faces, the
MM7 robot and MM8 turtle region masks) showed the default tier at LOD2/LOD3, and a variant without a region mask got
the default's mask without ramps, which the loader rejects ("colour regions need a region mask and one to four ramps":
the troglodyte, bigfoot and PHOM1 failed to load). Now `transfer_textures.py` transfers such variants' own maps
(`lod<N>_p<i>_m<material>_<map>.png`) and `apply_bake.py` uses them, sharing the default's far map wherever the LOD0
maps are the same and omitting maps the variant lacks. Installed GLBs were patched in place by
`scripts/fix_variant_maps.py <in.glb> <out.glb>` (transfer onto the existing far UVs; geometry, clips and other
materials byte-identical): 43 models (`work/variant_fix/`), including `mm7_m386` and `mm8_m580` from the run above.

Grainy far textures (user, same day: "noticeable texture changes when walking" close to a Sturmford City half-orc
townswoman, `mm9_peasanthof1`, at the LOD1 -> LOD2 switch, 180 px). `transfer_textures.py` filled each far texel from
the nearest LOD0 point; a coarse surface cuts through LOD0's pleats, folds, mail and scales, so the nearest point
jumps between fold faces and the pattern turns into grain (also one point sample per texel). Forced-LOD captures
ruled out the normal map and vertex normals; LOD0 UVs on the far triangles (`<step>.built.glb`) kept the pleats but
tore wherever a triangle crosses UV charts. Now `transfer()` takes `param_uv` (the built GLB's LOD0 UVs per corner):
the LOD0 face under that UV (face-id raster of LOD0's layout, 2048 px) is used when its surface point lies within 2 %
of the bounding diagonal of the texel's point (`LOD_PARAM_TOLERANCE`), else the nearest point as before (median 85 % of
texels by UV), and every map is filled at 4x and box-filtered (`SUPERSAMPLE`; the mask keeps its centre sample).
`repair.py` uses it automatically (the transfer runs on the built GLB). All 94 installed MM9 bodies were re-transferred
in place (`fix_variant_maps.py <installed> <out> --all --param <built.glb>`, `work/param/`, geometry and clips
unchanged): culled audit equal or better at the switch sizes except Seamon/Sigmund (+2 colour, visibly better: their
mail and scales no longer scramble); in game the townswoman's LOD2/LOD3 keep LOD0's pleats, knit collar and sleeves.
The 2026-10-22 MM6-MM8 far maps still use the nearest-point transfer; their built GLBs were not kept, so improving
them needs a `repair.py` rerun (mind the head bob and appended-clip traps) and tiny Meshy charts limit the UV share.
Full desktop cook afterwards: 1,508 stale far textures removed, 0 desktop problems.

Far normals regression and fix (user, evening 2026-11-07: SF_2/SF_3 saves, Sturmford City dwarf townswoman Leppa the
Shy, `mm9_peasantdf1`, visibly worse at LOD2). The UV correspondence above had no facing check: thin cloth (skirts,
aprons, sleeves) has a lining with the outer layer's UVs, so the UV raster often returned the lining's face. Colours
were unaffected (same UV), but the normal faced away and the z clamp turned it into a near-horizontal far normal:
shiny white blotches on apron and sleeves. 42 % of df1's UV-matched texels faced away (0.9 % on the nearest-point
path); LOD2 normal texels tilted past 72 degrees rose from 2.4 % to 14.5 % on df1-4 and above 5 % on 28 models.
Flattening the far normal maps in game confirmed the cause. `transfer()` now takes the normal from the UV face only when
it faces the LOD's way (the nearest-point rule), else from the nearest outer face; colours keep the UV face.
All 94 re-transferred from the **installed** sources (`work/normalfix/`, `run_one.sh`, `check.py`, `check.txt`;
meshes, clips and near images unchanged, PeasantM2/M2d's seated clips kept, 11 orphan graft accessors dropped): median
tilt 3.6 % -> 2.4 %, models above 5 % 28 -> 4, none worse. Installed (`work/normalfix/install.log`), desktop cook and
verify clean; in game df1 at SF_3: LOD2 colour difference to LOD0 5.66 -> 3.72. Rollback: `work/normalfix/before/`.

Translucent tier on a shadow LOD (user, 2026-11-07: Lich Lab "Actor model load failed: dedicated shadow LODs require
opaque geometry"). `build_lods.py` copied the colour LOD's variant mappings onto the rebuilt shadow, so `mm9_dagrell`'s
LOD2/LOD3 shadows mapped the Spectre tier to the blended `Dagrell_C`; the original shadows map it to `Dagrell_A`. Now
a non-opaque mapping on a shadow takes the shadow's default material. Installed `mm9_dagrell` patched in place (JSON
only, `work/shadow_fix/patch.py`; before: `work/shadow_fix/mm9_dagrell.before.glb`). Every source model in
`assets_source` checked: no other shadow LOD maps a non-opaque material.

Audit trap: `lod_render.py` renders in Workbench without back-face culling, so single-sided inner layers (MM9 skirt
linings) show through coarse outer facets as dark patches that the game culls. `LOD_RENDER_CULL=1` culls all back
faces (double-sided ones too, alike at every LOD). Python 3.14 venv with pymeshlab 2025.7.post1.
