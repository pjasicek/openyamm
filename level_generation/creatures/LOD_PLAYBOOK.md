# LOD playbook: creatures and props (2026-11-12)

The procedure for building, checking and installing the LODs of any skinned creature or prop GLB. It distils what the
far-LOD repairs proved (MM6–MM8 2026-10-22, MM9 2026-11-07); history, numbers and failed alternatives are in
[lod_repair_claude/README.md](lod_repair_claude/README.md) and its [handoff](lod_repair_claude/HANDOFF_20261107.md).
Scripts: `lod_repair_claude/scripts/`. First audit against this playbook:
[audit_mm678_20261111/lod_audit/](audit_mm678_20261111/lod_audit/README.md).

## 1. What the engine does

| Item | Rule (source) |
|---|---|
| Colour chain | mesh extras `openyamm_lods` = LOD1..LOD3 (at most 3), drawn by the body node (`GltfModelLoader.cpp`) |
| Shadow chain | `openyamm_shadow_lods` = shadow meshes for levels 0..3 (at most 4), opaque in every tier, one merged primitive |
| Colour switch | projected bounds diameter below 500 / 200 / 80 px, 10 % hysteresis: down at **450 / 180 / 72**, up at 550 / 220 / 88 (`ModelLod.h`); frozen stand-ins 750 / 300 / 120 |
| Shadow switch | chosen **independently**, in shadow-map texels: 256 / 192 / 64 per cascade. In practice the shadow level is equal to or **coarser** than the colour level (estimate at medium quality: a person at 500-700 units draws colour LOD0 with shadow LOD2; far, colour LOD2 with shadow LOD3) |
| Shadow tolerance | normal offset 0.7 world units + depth bias + texel x grazing (`sun_shadows.sh`): a caster poking out of the drawn surface by more than about 1 world unit can shade it |
| Forced level | `debug.model_lod=N` / console `render lod N` force colour levels only; shadows keep their own level |
| Normal maps | `fs_model.sc` builds the tangent frame per pixel from position and UV derivatives (no stored tangents) |

## 2. The ladder

| Level | Triangles of LOD0 | Mesh | Textures |
|---|---|---|---|
| LOD0 | 100 % (a ceiling: [guidelines](../GAME_ASSET_MODELLING_GUIDELINES.md) §1) | authored | the model's sets |
| LOD1 | about 50 % | Blender collapse (`tools/build_actor_lods.py` level 1) | LOD0's atlas and materials |
| LOD2 / LOD3 | `repair.py` ladder: the **first step that passes the gates** (§6); default `--ladder fallback` = plain 25/12, 30/16, 35/20, 40/25 %, then the same four curvature-weighted (`c25_12`..`c40_25`), then 45/30 plain and curved | `build_lods.py` | own maps 512 / 256 px (`unwrap_lods.py`, `transfer_textures.py`) |

`build_actor_lods.py`'s defaults for LOD2/LOD3 (18 % / 6 %) are not a finished far chain: run `repair.py` after it.
Separate effect meshes and death rubble keep their own LODs; the body is the skinned LOD node with most triangles.
Skip LODs only on assets that are already simple (guidelines §7).

## 3. Mesh collapse (`build_lods.py`)

- One MeshLab quadric collapse of the welded LOD0 on **positions only**, borders free, no optimal placement:
  **every LOD vertex is an LOD0 vertex**, so skin weights, normals and burn order stay exact (LOD meshes carry no morph targets). No
  re-binding, no weight transfer, no texture-aware collapse (spikes, lost heads), no protected borders (closed body
  skin vanished), no per-piece budgets (overshoot).
- Drop welded zero-area faces before the collapse (they segfault MeshLab and force the topology-preserving fallback,
  which shreds heads). A `preserve_topology` in `result.json` means: look at that model by eye.
- **Curvature-weighted collapse** (ladder `c` steps; `LOD_CURVATURE_WEIGHT=8`, `LOD_CURVATURE_LEVELS=2` for LOD2 only):
  MeshLab's quadric error weighted per vertex by 1 + 8 x clip(curvature / median, 0, 8), so thin features (wing
  bones, twigs, ribs, crown spikes) survive and broad surfaces take the cut (Bat, Treant, Skeleton, Lich 2026-11-12).
  A border weight (protected open borders) made feather cards worse: not an option.
- **Lining fix** (default since 2026-11-12, `LOD_LINING_FIX=0` turns it off): a far corner whose LOD0 normal faces
  against its triangle (dot < -0.2) gets a copy with the normal flipped, and colours, like normals, come only from UV
  faces facing the far triangle's way. Fixes dark streaked hems on cloth whose lining joins the outer layer at the hem
  (`mm6_pfem`); neutral on four robed bodies (5-12 % of far triangles had an inward corner, scores equal).
- Pieces of two triangles or fewer are dropped; closed pieces the collapse turned inside out are removed
  (`drop_inverted_parts`, single-sided materials only).
- Each triangle takes LOD0 vertices of one UV island; a corner without one gets a copy with the UV extended from that
  island. These LOD0 UVs per corner are kept in `<step>.built.glb`: they are the UV correspondence for §4.

## 4. Far UVs and textures

- New UVs per far primitive (`unwrap_lods.py`, xatlas, padding 4): 512 px at LOD2, 256 px at LOD3, scaled by each
  material's share of the surface (power of two, at least 64). LOD0's atlas cannot serve a coarse LOD: its triangles
  span many islands and smear it. Smart UV Project gave NaN UVs on multi-material bodies.
- Fill with `transfer_textures.py` on the **built GLB** (`repair.py` does this), which uses the **UV correspondence**
  (the LOD0 face under each texel's LOD0 UV, accepted within 2 % of the bounding diagonal), the **facing check** (the
  normal comes from that face only when it faces the LOD's way, so cloth linings cannot give a backward normal) and
  **4x supersampling** (box-filtered; the mask keeps its centre sample).
- **Never the nearest-point mode** (`transfer()` without `param_uv`, `fix_variant_maps.py --all` without `--param`,
  the texpass `apply.py` refill): on pleats, mail, scales and fur the nearest LOD0 point jumps between folds and the far
  map turns to grain that the colour score cannot see.
- Region mask: all four channels (**RGBA**). A fourth region lives in alpha; an RGB far mask paints every far texel
  with ramp 4. Every far-mask texel's RGBA must occur in the LOD0 mask.
- Variants: a tier with its own LOD0 paint (maps that differ from the default's) gets its own far maps
  (`lod<N>_p<i>_m<material>_<map>.png`); tiers that share LOD0 maps share the far maps; a far copy never gets a map its
  LOD0 variant lacks (a mask without ramps fails to load). Far copies `<material>_LOD<N>` keep LOD0's ramps.
- Normals: LOD0's shaded normal (vertex normal + normal map at its scale) re-encoded in the far triangle's
  `fs_model.sc` frame against the far vertex normal. Never a Cycles/MikkTSpace bake (dark, blotchy LOD3s in game).

## 5. Shadow LODs and "leaking shadows"

The shadow mesh of a rebuilt level is its colour LOD merged into one primitive (body material's culling, opaque tier
for every mapping) and tucked inside LOD0 (`splice_lods.tuck_shadow`: 2 / 4 / 7 mm at levels 1 / 2 / 3, at most
15 mm; pieces thinner than the margin keep their place). **Leaking shadow** = a shadow caster that lies outside the
surface drawn with it: that surface sits inside the caster and shades itself in a triangle pattern (dark blotches on
the lit side). The tuck moves vertices only, so a coarse triangle that bridges a concavity (armpit, between legs, skirt
folds, jaw) still sticks out of the finer colour levels, and the shadow level is usually coarser than the colour level
(§1). Measure it: sample each shadow level's surface and take its signed distance to every colour level it is drawn
with (colour level <= shadow level), in world units (metres x the binding's `scale`)
(`audit_mm678_20261111/lod_audit/shadow_check.py`). Repaired MM9 bodies reach 1-8 % of the LOD3 shadow more than 1 unit
outside LOD0/LOD1; 26 of the 104 MM6–MM8 models in the first audit exceed 5 %. No in-game threshold is established yet
(the 2026-11-12 captures showed no blotches at that light): above 5 %, look in game at low shadow quality
(`video.model_shadow_quality=1` gives coarse shadow levels next to colour LOD0/LOD1) against high quality at the same
pose. The fix is a tuck against surface samples rather than vertices: push the shadow vertices of offending triangles
inward until the samples lie inside every colour level they meet (not written yet). Burning bodies cast from their
colour meshes.

## 6. Gates

| Check | Pass | Tool |
|---|---|---|
| LOD1 switch at 450 px | no calibrated gate; healthy models score about 1 % / 9 (look above 5 % / 15) | `audit.sh` |
| LOD2 switch at 180 px | outline <= 6 %, colour <= 16 or LOD1's + 3 | `audit.sh` with `LOD_RENDER_CULL=1` |
| LOD3 switch at 72 px | outline <= 13 %, colour <= 19.5 | same |
| Triangle counts | strictly decreasing, LOD3 >= 12 % unless the model is already simple | `build_lods.py` |
| Far maps | own maps at LOD2/3, RGBA mask, variants' own paint, ramps equal to LOD0's, UV correspondence share in the transfer log (median 85 %; below 50 % look) | `lod_static.py`, `fine_score.py` (audit folder) |
| Shadow | §5 (measure; look in game above 5 %) | `shadow_check.py` (audit folder) |
| Winding | 0 inverted closed parts in every mesh | `decorations/mm8_3d/animated/scripts/check_winding.py` |
| Load | no `Actor model load failed` in the log of a map that places it | game run |
| **In game** | forced LOD 0/1/2/3 captures close up and at the switch distance, every tier, compared by eye; textures keep LOD0's pattern, no grain, no shiny or dark blotches, no tier swap | `tools/RUN_GAME.md` |

The colour score is a downscaled Workbench render: it **cannot see grain**, normal or shadow faults (six MM9 bodies,
nearest-point against UV-correspondence maps: colour within 0.6; `fine_score.py`'s detail correlation at full render
size moves only +0.03 to +0.09). The in-game captures are mandatory: an isolated, minimized run
(`./tools/run_game.sh --isolated <name> --world <w> --map <map> --position X Y Z --yaw-radians A --pitch-degrees P
--set video.shadows=true --set debug.menu_input_tour_path=<abs tour.yml>`) whose menu-input tour spawns the models
(`console: model spawn worlds/<w>/models/<stem>.glb x y z <scale> <yaw>`: bind pose, default tier; `actor spawn <id> 1
x y z friendly` for tiers on a map that preloads them) and steps `console: render lod 0..3` between `capture:` steps.
Template: `audit_mm678_20261111/lod_audit/ingame/lods_high.yml`. Workbench renders draw back faces unless
`LOD_RENDER_CULL=1` (skirt linings look like holes).

## 7. When to rerun

Rerun the far chain whenever LOD0's **mesh, UVs or any LOD0 map** changes (texture pass, retexture, reduction, hand
graft, rebuild, mask or ramp edit): the far maps and shadow tucks do not follow LOD0. LOD1 shares LOD0's atlas, so
after a new layout its UVs must be projected per chart (texpass `apply.py`) or LOD1 rebuilt. Clip-only and
binding-only changes need nothing.

**Source = the current installed GLB** (`assets_source/worlds/<w>/models/<stem>.glb`), never `originals/` or an old
export: those predate head-bob reshaping, gait clips (Walk2/Jog/Run/Sprint), attack/hit fixes and texture passes.
`build_lods.py` keeps everything outside the far chain byte for byte, so clips appended since survive. Before a rerun:
1. Copy the installed GLB to `<project>/work/before/<stem>.glb` (rollback).
2. `repair.py` starts from the installed GLB by default (`--source installed`; `--source original` is the stale
   `originals/` route, `--source <glb>` an explicit file) and records its sha256 in `result.json`. `build_lods.py`
   drops the old `<material>_LOD<N>` materials and their images once the far meshes are replaced
   (`strip_lod_materials.py`; `apply_bake.py` refuses an input that still has them).
3. Run one `repair.py` process per stem (`LOD_REPAIR_PYTHON=<venv>/bin/python`, `LOD_REPAIR_RUN=<run>`,
   `LOD_RENDER_CULL=1`); keep the `<step>.built.glb` and `bake_<step>/`: later map-only fixes need them
   (`fix_variant_maps.py --param`).
4. `verify_far_only.py <run>/<stem>/installed.glb <run>/<stem>/<step>.glb` must print `OK: only the far levels differ`
   (nodes, skins, clips byte for byte; LOD0/LOD1, shadows and effect meshes with materials and images resolved;
   every `_LOD<N>` copy's ramps equal LOD0's).

MeshLab's collapse is **not deterministic**: a second run builds slightly different far meshes (one model missed a gate
by 0.2 %). To change only maps on an already-repaired model, reuse its `<step>.built.glb` and unwrap
(`fix_variant_maps.py <installed> <out> --all --param <built.glb>`), never a fresh collapse. Without a kept built GLB
the only correct route is a full rerun.

Venv (durable, git-ignored, set up 2026-11-12): `python3 -m venv lod_repair_claude/venv &&
lod_repair_claude/venv/bin/pip install pymeshlab xatlas numpy scipy pillow` (Python 3.14.4, pymeshlab 2025.7.post1,
xatlas 0.0.11, numpy 2.5.4, scipy 1.18.1, Pillow 13.0.0). About 30 s per ladder step plus the audit render; at most
four processes at once (two per agent when two agents share the machine). Example:
`LOD_REPAIR_PYTHON=$PWD/venv/bin/python LOD_REPAIR_RUN=<run> LOD_RENDER_CULL=1 venv/bin/python scripts/repair.py <stem>`
from `lod_repair_claude/`. Options: `--ladder plain|fallback|<spec>` (spec e.g. `0.25/0.125,c0.4/0.25`, `c` =
curvature-weighted; also `LOD_LADDER`), `--not-worse` for reruns of models that already pass (a passing step must also
score no worse than the installed far levels: outline + 0.5, colour + 1.0 at LOD2 and LOD3, else the ladder goes on;
no accepted step = keep the installed GLB). `result.json` records `accepted`, the chosen step and every step's scores;
without an accepted step `chosen` is the step closest to the gate. Exact one-model command:
[MERGED_20261112.md](lod_repair_claude/MERGED_20261112.md).

## 8. Install and rollback

1. `check_winding.py export/<stem>.glb` = 0, then `tools/install_model.py export/<stem>.glb --world <w>`
   (`install_batch.sh <run> <list>` does both per model; it overwrites `work/<run>/install.log`: copy it first).
2. A row per model in [REDUCTION_LEDGER.md](REDUCTION_LEDGER.md) with the rollback source (`work/before/<stem>.glb`).
3. Shared layouts: an MM7 copy built from an MM8 GLB (`mm7_m434` from `mm8_m560`, `mm7_m210` from `mm8_m500`) is
   rebuilt by its project's `build_glb.py` from the new MM8 source, with its own ramps.
4. Load the maps that place it (no load errors), `mm6_mm7_mm8_actor_models_build_every_binding` regression, desktop
   cook verify (`tools/cook_models.py --verify`); Android cook (`tools/cook_android.sh`) only when the user asks.
5. Rollback: `tools/install_model.py <rollback source> --world <w>` and the ledger row.

## 9. Traps

- `repair.py --source original` (stale `originals/`) silently drops texture passes, hand grafts, head bob and
  appended clips; the default since 2026-11-12 is the installed GLB.
- The texture pass's far refill (`apply.py` -> `transfer()` without `param_uv`) is the nearest-point mode, and it
  rewrites only the default material's far images: variants with their own far maps keep the old paint.
- Rebuilds that end in `build_actor_lods.py` get 6 % LOD3s sampling LOD0's atlas: run the ladder before install.
- `repair.py` stops at the first exception: one process per stem (attachments raise "no skinned node").
- A translucent tier on a shadow LOD fails to load; a variant far copy with a mask but no ramps fails to load.
- Tiny Meshy charts limit the UV-correspondence share (gutter hits fall back to the nearest point): check the share.
- Cloth with a separate dark lining joined to the outer layer at the hem (offset copy plus rim): the collapse mixes
  the layers, giving a dark streaked hem at LOD2/LOD3 that the scores barely see. The lining fix (§3) handles it and
  is on by default (installs before the merge of 2026-11-12, except `mm6_pfem`, lack it). It also applies to map-only
  refills through `fix_variant_maps.py --param` (colours from facing UV faces only).
- Identify the exact model before chasing an in-game report (`strace -e openat` lists the GLBs a map loads).
- Debug-spawned tiers a map does not preload may not render (`requires a valid standing sprite`): use a map that
  places them.
