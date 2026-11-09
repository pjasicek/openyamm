# MM9 Rooster (mm9_rooster) — 3D model, 2026-10-30

The MM9 rooster (`mm9/extracted/MODELS/MODELS/ROOSTER.abc`, 35 nodes, 193 tris, 11 clips, skin ROOSTER.dtx) for MM9 NPC
row 270 (`rooster.scr`, Hostility 2, `Transparent 1`). Built on the MM9 rig-reuse route (`../mm9_dfly_claude/`,
`../mm9_wolf_claude/`, `../mm9_crow_claude/`) with the scripts of `../mm9_hen_claude/`: a new HD Meshy rooster weighted
to the original MM9 skeleton, the MM9 clips played with only the listed fixes. Progress and receipts:
`creature_3d_progress.json`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_rooster.glb` (cooked copy in `assets_dev`) |
| Binding | `assets_dev/worlds/mm9/models/actors.yml` block `mm9_rooster_claude`: descriptor MM9 270 Rooster, scale 100 (100 x MONSTERS.txt `Scale` 1), one skin |
| Data | `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv` row 270 -> legacy Chicken B (467), runtime id 9270 |
| Triangles LOD0/1/2/3 | 6,930 / 3,465 / 1,245 / 408 |
| Skeleton | the MM9 one, names unchanged (`XCENTER`, `Xbody`, `Xneck/B/C`, `Xhead`, `Xbeak`, `Xtail/B/C/E`, legs `Xlegpiv-Xuprleg-Xleg-Xlowrleg-Xfoot`, toes `Xtoepiv*`, `Xtoe*`) + `Socket_Mouth` at the beak tip |
| Clips (30 fps) | Standing 1.4 (Stand), Walking 1.1 (Walk), Running 0.37 (Run), Fidget 2.0 (Fidget1), AttackMelee 0.8 (HAttack1), Hit 1.4 (Wince1), Death 1.8 (Die1), Dead 1.0 |
| Events | peck 0.355 s (MM9 `bite` of HAttack1) |
| Gait | stride 0.46 (walk), 1.18 (run) model units per cycle (`scripts/gait_measure.py`) |
| Floor | ground rule; Running one uniform lift (+2.2 cm, no bob); `floor_audit.py --world mm9` ok |
| Meshy credits | **20** (backup account): body Smart Topology 5, head Smart Topology 5, 4K retexture 10 |

## Decisions

- **MM9 skin alpha (`Transparent 1`).** ROOSTER.dtx has binary and soft alpha on two parts only: the serrated comb
  (a flat card, `d_crest`) and the tail plume's outline with its fringed sickle tips (5.8 % texels fully, 7.4 % partly
  transparent). MM9 cuts the silhouettes out of two flat cards; here both are real geometry: a fleshy serrated comb from
  the head-only model and Meshy's separate sickle feathers (open sheets). That matches or gains on the cut-outs, so the
  material stays opaque, `doubleSided` because the sheets are open.
- **Head graft from the start.** The body Smart Topology read the wattles as an open crowing beak. A head-only HD
  turnaround (`references_head/`) and head-only Smart Topology gave a closed short deep beak, serrated comb, earlobes and
  long wattles as separate pieces; `scripts/graft_chicken.py` places them on MM9's head. Beak elevation: MM9 -8 deg,
  ours -10 deg. Eyes, wattles, earlobes and comb are rigid on Xhead (`scripts/reanchor_pieces.py`).
- **Symmetry.** `scripts/sym_meshy.py`: mirrored right half (mirror error before 0.4 % of size).
- **Legs on MM9's chains.** Height by a no-rotation ICP (free rotation pitched the bird 20 deg forward). The rooster's
  hock points back (Xlowrleg 6 cm behind the ankle-knee line); leg_fit.py alone laid the shank across a Z-fold, so
  `scripts/fix_uv_mesh.py` (after the paid retexture, UVs untouched) maps each leg vertex back to the straight Meshy
  shank by barycentric lookup on fit_v2/fit_v1 and lays it on MM9's real leg path; the shank weights become Xlowrleg with
  soft blends at hock and ankle. Feet yawed 7 deg onto MM9's toes.
- **Throat step.** The neck stood proud of the head's stub and left a slit; `fix_uv_mesh.py` welds it, patches the rest
  and relaxes the throat into a slope (viewer shots, `rear` view).
- **Stray shards.** Tail pieces of six faces or fewer and loose vertices are deleted (63 vertices, `fix_uv_mesh.py`).
- **Comb.** Seated 5 mm into the filled skull; the skull under it is rigid with it.
- **Tail.** The sickle feather sheets keep per-vertex MM9 tail labels so they bend with Xtail, XtailB, XtailC, XtailE.
- **Compose** (`scripts/compose_chicken.py`): the hidden throat pocket and maroon wattle blotches take the feather and
  wattle colours. One skin, no mask or ramps; head charts 2x density.

## Rebuild

As `../mm9_hen_claude/README.md` with `hen` -> `rooster`, these differences:

```sh
$B $P/scripts/mm9_rig_source.py $P/source/rooster/rooster.glb $P/work/mm9_rooster_rig.blend 0 0.3805
$B $P/scripts/reduce_body.py $P/work/rig_v1.blend $P/work/reduced_v1.blend $P/work/reduced_v1.json 0.3 0.35 0.5
# after the retexture download:
$B $P/scripts/reanchor_pieces.py $P/work/uv_v1.blend $P/work/uv_v1b.blend 0.05      # tail pieces keep their labels
$B $P/scripts/dump_body.py $P/work/fit_v1.blend $P/work/fit_v1.npz                  # and fit_v2
$B $P/scripts/fix_uv_mesh.py $P/work/uv_v1b.blend $P/work/uv_v1c.blend $P/work/fit_v2.json $P/work/fit_v1.npz $P/work/fit_v2.npz
# dump_uv3d, bake_ao, compose, grade, compose, build_export on uv_v1c.blend, then build_runtime.sh --install
```

## Checks (2026-10-30)

- Viewer `review/viewer/`: `tools/run_creature_review.py check` 1 skin x 8 clips, 0 console errors; playback
  `review/playback/`.
- Sheets from viewer shots: `review/sheet_rest_mm9_vs_ours.png`, `review/sheet_clips_mm9_vs_ours.png` (same camera, time
  and light; MM9 reference tier), `review/sheet_texture_closeup.png`. All shots read by the author; the viewer found the
  throat slit and step, the leg Z-fold, wattle blotches and back-face-culled tail, none of which showed in Blender.
- `texture_quality.py`: atlas 57.4 %, equivalent 1552 px, density p50 1040, spread 1.99 (the 2x head charts, comb and
  wattles, are a large share here), 213 islands, fragments 0.5 %, stretch p90 1.3, 4K source. Flat shading 0.00.
- Head (`scripts/head_angles.py`, 48 fps, against MM9's mesh; `review/head_angles.json`): bind direction 1.4 deg off
  MM9; orientation max per clip: Standing 2.2, Walking 3.0, Running 2.3, Fidget 5.7, AttackMelee 3.8, Hit 11.2, Death
  10.0; roll max 8.5; fold 0.0 (rigid).
- Neck/feet gate: neck edge ratio p1 0.79-0.97, folded neck triangles 1-5 (wattle-side slivers); feet p1 0.27-0.84,
  up to 11 folded at the toe roots in Death and 8 in Running.
- Gates `review/gates.json`: loop seams 0; edge ratio p1/p99 per clip 0.58-0.95 / 1.05-2.08. The extreme 17x is a 0.2 mm
  edge at a tail feather root; 1-4 edges stretch more than 2 cm in the fast tail swings.
- Jitter (`scripts/jitter.py`, XCENTER height acceleration, MM9 / ours, mm per frame^2): Walking 6.1 / 4.0, Running 33.3
  / 29.7, AttackMelee 23.7 / 27.3, Hit 2.7 / 1.9, Death 21.7 / 15.5.
- `detached_parts_audit.py` (strict rules, 30 fps, 304 poses, 69 parts): the stray slivers are gone; the one flag is the
  comb (4.9 cm `lifted`, Running 0.27 s), a false flag: every comb vertex within 1 cm of another part has an Xhead-rigid
  skull neighbour, both at weight 1.0, and that contact distance changes 0.00000 m over every clip (`review/detached.json`).
  The viewer shows it seated. The sickle feathers lift at the root as they fan (up to 5.6 cm on one feather), as feathers do.
- Winding 0 inverted. Floor audit `floor_audit.py --world mm9`: ok. Regression `mm9_actor_models_build_every_binding`
  (`--world mm9`): 61 descriptors on 28 models, 0 failed.

## Deviations and open points

- MM9's Fidget2, Wince2 and Die2 are not exported; MM9 `Velocity`/`lunge` events are not reproduced (clips stay in place).
- MM9 draws fringed feather tips with soft alpha; ours are clean sickle shapes. The undersides of the tail sheets are
  darker (Meshy painted them from the side views), seen only when the corpse's tail turns over.
- The comb is larger than MM9's card relative to the skull, close to the HD master; the shank is stretched about 1.4x
  to reach MM9's long leg, which widens its scales.
- A small patch closes the former throat slit, behind the wattles; it carries one feather texel area.
- `doubleSided` on the whole material: `check_winding.py` then has no closed parts to judge on it (it passed 0 inverted
  before the flag on the same mesh).
- User artistic acceptance: not recorded.
