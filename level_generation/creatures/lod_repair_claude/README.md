# Far-LOD repair of installed creatures (2026-10-22)

> The procedure distilled from this project is the [LOD playbook](../LOD_PLAYBOOK.md) (2026-11-12); this README is
> its history.

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

## Tooling for reruns on installed GLBs (2026-11-12)

For step 1 of the LOD plan ([playbook](../LOD_PLAYBOOK.md) section 7; marker `SETUP_DONE_20261112.md`):
- Durable venv `venv/` (git-ignored; setup command in the playbook). The /tmp venv of October/November is gone.
- `repair.py --source installed|original|<glb>`, default `installed` (the current `assets_source` GLB, copied to
  `work/<run>/<stem>/installed.glb`, sha256 in `result.json`). The old default, `originals/`, predates the texture
  passes, head bob, gait clips and rebuilds. `repair.py` now guards its CLI (`main()`), so its helpers can be imported.
- `strip_lod_materials.py`: `build_lods.py` drops the old `<material>_LOD<N>` copies and the images only they used after
  replacing the far meshes, so `apply_bake.py` accepts an already-repaired input.
- `verify_far_only.py <before> <after>`: content diff (texture indices resolved to image bytes) that allows changes
  only in the body's rebuilt far colour and shadow meshes, and checks each `_LOD<N>` copy against its LOD0 material.
  Scratch check on the installed Bat (`work/scratch_m158/`, all four ladder steps): OK; against `originals/` it flags
  LOD0, LOD1, their shadows and the materials, as it should.

## MM6 rebuilds' far LODs (2026-11-12, lod-step1)

The four 2026-11-11 rebuilds had `build_actor_lods.py` far chains (LOD3 6 %, LOD0 atlas). Ladder from the installed
GLBs (`work/mm678_20261112/`, leases through each `mm6_<id>_rebuild_claude` project, backups in their
`work/before_lodrepair/` and in `work/mm678_20261112/before/`). All four passed at the first step (25/12 %);
`verify_far_only.py` OK, winding 0, every_binding PASS (647 descriptors, 0 failed), desktop cook verify 0 desktop
problems (Android not cooked). Outline % / colour at the switch sizes, installed -> repaired:

| Model | LOD2 | LOD3 | Triangles LOD0/1/2/3 | UV share | Shadow worst > 1 u |
|---|---|---|---|---|---|
| `mm6_gua` | 1.9/8.4 -> 1.7/9.1 | 6.9/12.3 -> 2.1/6.9 | 9,781/4,889/1,759/584 -> .../2,439/1,220 | 74-94 % | 1.7 -> 0.3 % |
| `mm6_pfem` (lining fix) | 2.5/15.1 -> 3.1/14.1 | 4.8/24.2 -> 5.4/9.7 | 9,456/4,720/1,699/565 -> .../2,363/1,181 | 63-86 % | 23.0 -> 2.2 % |
| `mm6_thf` | 2.2/11.6 -> 1.9/9.4 | 4.9/13.4 -> 2.8/7.2 | 9,638/4,817/1,730/572 -> .../2,401/1,200 | 88-96 % | 7.3 -> 2.1 % |
| `mm6_mer1` | 2.0/7.8 -> 1.5/6.6 | 4.4/10.0 -> 2.8/7.0 | 10,584/5,290/1,902/634 -> .../2,645/1,315 | 87-94 % | 0.7 -> 0.4 % |

Sheets: `review/mm678_20261112_gua_pfem.png`, `review/mm678_20261112_thf_mer1.png`. In game (New Sorpigal start pose,
spawned bind pose, forced `render lod 0..3`; `work/mm678_20261112/ingame/`, `run_tours.sh before|after2`):
`crop_close_gua_pfem_final.png`, `crop_far_gua_pfem_final.png` (3x), `crop_close_thf_mer1.png` (first install). Gua
keeps its mail at LOD2/LOD3 (before: flat dark LOD3); pfem's LOD3 skirt no longer tears; thief's LOD3 no longer murky.

**Lining fix (`LOD_LINING_FIX=1`, opt-in).** The first pfem install showed a dark, streaked hem at LOD2/LOD3 (in game
worse than the old atlas LOD2). Cause: the skirt's lining is a 4 mm offset copy joined to the outer layer by a rim at
the hem, one welded piece, so the collapse builds outward far triangles with lining corners: inward LOD0 normals
(dark shading even untextured) and lining UVs, whose dark paint the UV correspondence copied (MM9 linings share the
outer's UVs, which hid it). Not the cause: border collapse (MeshLab `boundaryweight` 4 and 16 unchanged), coincident
fold vertices (none), normal maps (Workbench ignores them). Fix: `build_lods.py` gives a far corner whose LOD0 normal
faces against its triangle (dot < -0.2) a copy of its vertex with the normal flipped, and `transfer_textures.py`
takes colours, like normals, from a UV face only when it faces the far triangle's way. Pfem: LOD3 colour 12.4 -> 9.7,
stripes intact in renders (`review/mm678_20261112_pfem_liningfix.png`) and in game. Installed from
`work/scratch_pfem_lining/` (its source was the first repaired install: also the first real strip-step rerun).
Opt-in so concurrent runs kept their behaviour; worth making the default after a check on a few skirted bodies
(it also changes the UV share: colours from away-facing UV faces now take the nearest outer point).
Diagnostic renders: `work/scratch_pfem_diag/`.

## Gate misses and atlas far LODs (2026-11-12, lod-step1b)

Twelve models from the [LOD audit](../audit_mm678_20261111/lod_audit/README.md) (ten pre-existing gate misses, two
atlas far LODs), each from its installed GLB, leases and rollback copies in `<stem>_lodrepair_claude/`
(`work/before_lodrepair/<stem>.glb`). Runs: `work/step1b/` (plain ladder, `run_one.sh`), `work/step1b_curv8/` and
`work/step1b_c2/` (fork, `run_fork.sh`), `work/step1b_l45/`, `work/step1b_bnd2/` (rejected experiments); installs
`work/step1b/install_one.sh` (claim-time source guard, winding, `shadow_check.py` before/after, `install_model.py`),
log `work/step1b/install.log`.

**Curvature-weighted collapse (fork, `../mm7_m158_lodrepair_claude/scripts/`).** Thin features (bat finger bones,
treant twigs, skeleton ribs, lich crown spikes) erode in the plain collapse. The fork's `build_lods.py` weights
MeshLab's quadric error per vertex (`qualityweight`) by 1 + w x clip(curvature / median, 0, 8), curvature = umbrella
Laplacian over the squared mean edge length (MeshLab's own curvature filter refuses non-manifold meshes); opt-in
`LOD_CURVATURE_WEIGHT=8`, `LOD_CURVATURE_LEVELS=2` for LOD2 only; `LOD_LADDER` adds the 45 %/30 % step (still below
LOD1's 50 %). A border weight (`LOD_BOUNDARY_WEIGHT=2`) made the Phoenix's feather cards much worse (LOD3 39 %).

| Model | Step | LOD2 out/col before -> after | LOD3 before -> after | Tris LOD2/LOD3 before -> after |
|---|---|---|---|---|
| `mm6_lzd` | plain 30/16 | 6.1/14.4 -> 5.4/14.1 | 6.8/9.5 -> 6.1/8.0 | 1,722/860 -> 2,064/1,099 |
| `mm7_m242` | plain 35/20 | 7.7/6.8 -> 6.0/5.8 | 9.6/8.2 -> 5.6/5.5 | 1,674/837 -> 2,326/1,335 |
| `mm8_m516` | plain 25/12 | 3.2/9.5 -> 4.0/11.2 | 3.7/8.3 -> 6.5/7.6 | 1,895/948 -> 1,895/943 (own far maps instead of the LOD0 atlas) |
| `mm8_m608` | plain 25/12 | 2.7/8.8 -> 3.8/12.4 | 5.3/9.8 -> 5.0/9.1 | 1,279/627 -> 1,281/639 (own far maps instead of the LOD0 atlas) |
| `mm7_m479` | curvature 45/30 | 6.5/14.1 -> 5.6/13.5 | 7.0/7.6 -> 4.9/6.3 | 4,130/2,580 -> 4,630/3,052 |
| `mm6_ske` | curvature 45/30 | 7.6/17.1 -> 5.9/17.0 | 12.2/6.4 -> 10.2/6.1 | 2,516/1,572 -> 2,811/1,855 |
| `mm6_lch` | curvature 40/25 | 7.4/8.8 -> 5.8/8.9 | 5.4/5.6 -> 7.0/5.8 | 2,515/1,572 -> 2,445/1,526 |
| `mm8_m552` | curvature LOD2 45 + plain LOD3 25 | 6.5/14.0 -> 5.4/13.5 | 6.5/5.9 -> 9.5/7.2 (LOD3 vs LOD0 unchanged 13.1/9.3) | 2,747/1,717 -> 3,087/1,715 |
| `mm7_m158` | curvature 40/25 | 29.7/21.7 -> 17.7/18.0 (unculled 3.4/9.5 -> 1.7/8.7) | 30.0/15.5 -> 14.8/8.8 (unculled 3.0/7.1 -> 1.6/4.4) | 1,520/759 -> 2,429/1,508 |

Bat: the culled gate cannot be met (its own LOD1 scores 8.6 % culled, 1.4 % unculled): its double-sided membrane is
culled away in the audit and only sub-pixel finger bones remain; scored unculled as the game draws it
(`work/step1b/bat_nocull/`), every candidate and even the installed LODs pass. Installed the curvature 40/25 step:
better on both measures, and in game its LOD2/LOD3 keep the finger bones and membrane veins that the installed LOD3
lost. Kept as installed: `mm8_m572` Phoenix (no step passes LOD2: best plain 45/30 9.3 %/17.6 against an LOD1 that is
itself 6.5 % off LOD0; LOD3 9.1 %/10.6 would pass; candidate `work/step1b_l45/mm8_m572/r45_30.glb`), `mm7_m386` Robot
(LOD1 10.4 % off LOD0; best 7.3 %/13.3, mixed against installed), `mm7_m390` Roc (own reduced LOD0, so the Thunderbird's
chain cannot be reused: its LOD2 would be 1 % under the Roc's LOD1; own best LOD2 6.5 %, LOD3 11.0 % against installed
7.4/8.4).

Checks: `verify_far_only.py` OK and winding 0 on all nine; `mm6_mm7_mm8_actor_models_build_every_binding` PASS after
each install; `cook_models.py --verify --only` clean on desktop (only Android textures missing: not cooked). In game
(New Sorpigal start, spawned bind pose, forced `render lod 0..3`, `work/step1b/ingame/`, before/after rows):
`compare_bat.png`, `compare_treant.png`, `compare_juggernaut.png`, `compare_phoenix.png` (Phoenix unchanged: a control).
Juggernaut's LOD2/LOD3 are softer close up than the old atlas levels (own 512/256 px maps) but lose the stray dark
triangles. Rollback: `tools/install_model.py ../<stem>_lodrepair_claude/work/before_lodrepair/<stem>.glb --world <w>`.

## Tooling merge and the mm6/mm7 batch (2026-11-12, lod-batch-a)

Marker for the next agents: [MERGED_20261112.md](MERGED_20261112.md) (options and the exact one-model command).

- **Merged** the fork's curvature-weighted collapse into `scripts/build_lods.py` (`LOD_CURVATURE_WEIGHT`,
  `LOD_CURVATURE_LEVELS`, `LOD_CURVATURE_CAP`; the border weight stays out: it made the Phoenix worse) and its ladder
  variable into `scripts/repair.py`, which now has `--ladder plain|fallback|<spec>` (default `fallback`: plain 25/12 ..
  40/25, then the same curvature-weighted `c` steps, then r45_30 and c45_30) and `--not-worse` (a passing step must
  also be within outline + 0.5 / colour + 1.0 of the installed far levels; `result.json` `accepted`). The fork
  (`../mm7_m158_lodrepair_claude/scripts/`) is superseded.
- **Lining fix default.** Runs `work/lining_off/` and `work/lining_on/` (25/12, mm7_m430 Wight, mm6_sor1 Sorcerer,
  mm8_m472, mm7_m290; nothing installed): far triangles with a corner whose normal faces against the triangle
  (`work/batch_a/lining_stats.py`) LOD2 5.3-8.3 %, LOD3 7.4-11.8 % without the fix, 0 with it (LOD1, Blender's
  collapse: 1.2-3.7 %); culled audit equal within MeshLab noise (colour -0.3 .. +0.7); renders the same, m290's LOD3
  hem wedge slightly lighter (`work/batch_a/sheets/lining_q34.png`, `lining_crops.png`); UV share about 1 point lower.
  With pfem's clear fix and no regression here, `LOD_LINING_FIX` now defaults to on (`=0` turns it off).
- **Phoenix** `mm8_m572` installed from `work/step1b_l45/mm8_m572/r45_30.glb` (better than installed on every score,
  LOD2 still misses the gate against an LOD1 that is itself 6.5 % off LOD0); verify OK, winding 0, every_binding PASS.

## Batch of the MM8 texture-pass models (2026-11-12, lod-batch-b)

The "ladder, batch" MM8 models of the [LOD audit](../audit_mm678_20261111/lod_audit/README.md) (16; `mm8_m472` run
after the robe-fix stream's install (16:02), `mm8_m620` left to the texture stream, `mm8_m572`/`m552`/`m516`/`m608` done earlier;
`mm7_m434` is rebuilt from the new `mm8_m560` by lod-batch-a). Route: `work/batchb/lane.sh` (lease through
`<stem>_lodrepair_claude`, backup `work/before_lodrepair/<stem>.glb`, `repair.py --not-worse` fallback ladder from
that backup, lining fix on by default), two lanes; `autoinstall.sh` -> `install_one.sh` (claim-time source guard,
`verify_far_only.py` OK, winding 0, `shadow_check.py` before/after, `install_model.py`), log `work/batchb/install.log`.
All 16 accepted and installed (`mm8_m472` after the robe fix, `regr_4.log`); `mm6_mm7_mm8_actor_models_build_every_binding` PASS after each group (647
descriptors, `work/batchb/regr_1..4.log`); `cook_models.py --verify --only` clean on desktop for all 16 (only
Android textures missing: not cooked). Outline % / colour at the switch sizes, installed -> repaired:

| Model | Step | LOD2 | LOD3 | Triangles LOD0/1/2/3 | UV share LOD2/LOD3 |
|---|---|---|---|---|---|
| `mm8_m560` | r25_12 | 5.5/6.8 -> 5.6/7.0 | 6.0/3.8 -> 6.0/3.9 | 9,071/4,535/2,268/1,133 -> .../2,242/1,133 | 93/89 % |
| `mm8_m436` | r25_12 | 3.3/7.1 -> 3.7/7.4 | 7.5/9.0 -> 7.5/8.7 | 10,527/5,152/2,631/1,315 -> .../2,486/1,253 | 91/82 % |
| `mm8_centaur` | r25_12 | 4.4/9.6 -> 4.4/9.6 | 5.2/8.7 -> 5.2/9.0 | 9,149/4,547/2,287/1,144 -> .../2,280/1,139 | 91/84 % |
| `mm8_m524` | r25_12 | 1.7/7.0 -> 1.7/7.0 | 3.0/3.9 -> 3.0/4.0 | 6,156/3,078/1,539/770 -> .../1,537/770 | 95/90 % |
| `mm8_m408` | r30_16 | 4.5/11.6 -> 4.5/11.4 | 11.3/10.3 -> 11.3/10.2 | 7,122/3,560/2,136/1,140 -> .../2,136/1,140 | 92/85 % |
| `mm8_m604` | r25_12 | 3.5/11.3 -> 3.5/10.4 | 6.4/9.7 -> 6.8/8.6 | 8,332/4,151/2,082/1,041 -> .../2,075/1,039 | 89/82 % |
| `mm8_m628` | r35_20 | 5.0/11.4 -> 5.0/11.4 | 7.9/8.0 -> 7.9/7.7 | 10,243/5,066/3,584/2,048 -> .../3,556/2,041 | 86/52 % |
| `mm8_m564` | r25_12 | 3.0/14.3 -> 3.0/14.3 | 4.7/9.4 -> 4.7/9.4 | 7,042/3,520/1,759/879 -> .../1,758/879 | 82/66 % |
| `mm8_m576` | r25_12 | 4.1/9.7 -> 4.1/9.7 | 4.7/6.9 -> 4.7/6.7 | 6,818/3,407/1,703/852 -> .../1,701/850 | 89/81 % |
| `mm8_m476` | r25_12 | 2.1/7.9 -> 2.1/7.9 | 4.1/6.9 -> 4.1/7.1 | 8,802/4,395/2,195/1,086 -> .../2,195/1,086 | 92/84 % |
| `mm8_lizardman_peasant` | r30_16 | 5.1/17.0 -> 5.1/16.7 | 9.9/14.1 -> 9.9/13.2 | 8,245/4,120/2,473/1,318 -> .../2,471/1,316 | 73/59 % |
| `mm8_m588` | r40_25 | 4.9/18.1 -> 4.9/18.1 | 3.8/11.7 -> 4.1/11.6 | 4,928/2,600/1,970/1,231 -> .../1,970/1,226 | 87/74 % |
| `mm8_m556` | r40_25 | 2.5/11.8 -> 1.0/12.0 | 4.2/5.2 -> 3.4/5.5 | 8,187/4,093/2,045/1,022 -> .../3,274/2,045 | 97/92 % |
| `mm8_m484` | r25_12 | 3.1/9.7 -> 3.1/9.8 | 5.6/10.0 -> 5.5/10.2 | 6,751/3,357/1,687/843 -> .../1,678/837 | 91/82 % |
| `mm8_ratman` | r25_12 | 5.1/9.6 -> 5.1/9.5 | 11.3/12.3 -> 11.3/12.2 | 7,831/3,871/1,958/979 -> .../1,884/940 | 91/82 % |
| `mm8_m472` | r25_12 | 1.9/11.1 -> 1.9/11.3 | 3.1/7.8 -> 3.1/8.7 | 11,013/5,505/2,752/1,377 -> .../2,752/1,377 | 90/82 % |

Most far meshes come out of the collapse almost as installed (same step as in October), so the scores barely move: the
gain is the UV-correspondence far maps (sharper skirt stripes on the lizardman peasant's LOD3, for example). Five
went up the ladder because `--not-worse` rejected lower steps: `mm8_m408` 30/16, `mm8_m628` 35/20,
`mm8_lizardman_peasant` 30/16, `mm8_m588` 40/25 (the boulder: 25/12 fails both gates), and `mm8_m556` Wasp 40/25
(25/12 to 35/20 pass the gate but are worse in colour: its wings get light streaks at 25/12; at 40/25 they are closest
to LOD0, `review/batchb_m556_steps.png`; cost LOD2 2,045 -> 3,274, LOD3 1,022 -> 2,045). Worst shadow outside > 1 u
unchanged within 0.6 points except `mm8_m604` 6.9 -> 4.5 %; still high on `mm8_m588` (21.4 %) and `mm8_m560`
(12.2 %), which the ladder does not address (playbook section 5). Sheets: `review/batchb_m560_m436.png`,
`review/batchb_m628_lizpeas.png`, `review/batchb_m556_m588.png`, full-size front renders
`review/batchb_closeup_a.png` (lizardman peasant, m628), `review/batchb_closeup_b.png` (ratman, m408), `review/batchb_closeup_m472.png` (Necromancer: its LOD3 shows a bare
chest instead of the breastplate, as the installed LOD3 did; the ratman's LOD3 arms are slabs, also as installed). No in-game
captures in this batch. Rollback: `tools/install_model.py ../<stem>_lodrepair_claude/work/before_lodrepair/<stem>.glb
--world mm8`.
- **mm6/mm7 batch** (the audit's "ladder, batch" models with mm6_/mm7_ stems; mm8_ by lod-batch-b): 35 models in
  `work/batch_a/` (`group.sh` -> `lane.sh` per lane: lease through each `<stem>_lodrepair_claude` project, backup
  `work/before_lodrepair/<stem>.glb`, `repair.py --not-worse` with the fallback ladder and the lining fix,
  `install_one.sh`: claim-time guard, verify_far_only, winding, shadow_check, install; every_binding after each group of
  six, 20 s after the last install; `ledger_add.py` rows; release). **All 35 installed, none kept**: 22 at r25_12,
  8 at r30_16, mm6_ckt r35_20, mm6_drg1 and mm6_cdr1 r40_25, mm6_gar c40_25 (plain 40/25 was 1.6/2.2 colour worse),
  mm7_m182 r45_30 (every 40/25 step was 0.8 outline worse than installed). Per-model scores and triangles:
  `work/batch_a/summary.md` and the ledger. The gain is UV-correspondence far maps instead of the texture pass's
  nearest-point refill (grain the colour score cannot see); scores stay equal within noise, and several improve
  (mm6_natm LOD3 9.1/10.6 -> 6.7/9.2, mm6_nobl 6.2/10.6 -> 4.7/9.4, mm7_m278 8.1/11.1 -> 5.8/9.5, mm6_drg1
  7.9/4.2 -> 5.3/3.5). All six regressions PASS (647 descriptors, 0 failed); desktop cook verify clean (Android not
  cooked). `mm7_m434` rebuilt by `mm7_m434_claude/scripts/build_glb.py` from lod-batch-b's `mm8_m560` (binary
  chunk identical, MM7 ramps on the far copies; verify_far_only OK).
- **Looked at**: `work/batch_a/sheets/review_g1.png`, `review_sample_a.png`, `review_sample_b.png` (installed against
  repaired, LOD2 at 180 px and LOD3 at 72 px; 12 models): no lost parts, colours or tiers. In game
  (`work/batch_a/ingame/`, New Sorpigal, `model spawn` of mm6_nobl, mm6_natf, mm6_drg1, forced `render lod 0..3`,
  close and about 1,500 units): `compare_close.png`, `compare_far.png`: LOD2/LOD3 keep LOD0's patterns (tunic,
  feather skirt hem, dragon belly plates), no grain, dark hems or blotches.
- Rollback per model: `tools/install_model.py level_generation/creatures/<stem>_lodrepair_claude/work/before_lodrepair/<stem>.glb --world <w>`
  (`mm7_m434`: `mm7_m434_claude/work/before_lodrepair/mm7_m434.glb`).
- Full actors suite after the batch (`work/batch_a/actors_suite.log`): passed 191, failed 2, the same two as on
  2026-11-11 before any LOD work (`every_map_loads_and_builds_its_actor_models`: 42 MM9 maps only;
  `out05_event_clearance_completes_from_monster_killed_hook`): not caused by these installs.
