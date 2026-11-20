# Honk male (`mm9_honkm`): handoff, 2026-10-30

**Superseded on 2026-10-31: the steps and defects below were worked through by the night pass. The current state, gates and open points are in `README.md`; rebuild with `v2/scripts/master_v3.sh`, then `build_runtime_v2.sh` with `BLEND=v2/work/medal_v3.blend`. This file stays as the day session's record, including its route notes and Keep list. Its hashes and numbers are the 18:13 build's.**

Stopped on the coordinator's order. Nothing is mid-edit and no job is running. The project lease is released. Sister body: `../mm9_honkfemale_claude/HANDOFF.md`.

## Installed and bound
| Item | State |
|---|---|
| Body | `assets_source/worlds/mm9/models/mm9_honkm.glb`, sha256 `d74df9b7de06...`, identical to `v2/export/mm9_honkm.glb`. Installed 18:13. LOD 7,717 / 3,850 / 1,379 / 454 |
| Hats | `mm9_honkhat.glb` `b2dabfa07df1...` (1,860 tris), `mm9_elderhonkhat.glb` `f4090f604b76...` (1,800 tris), identical to `export/`. Installed 17:36, unchanged since |
| Viewer | revision `v7-20261030`, tiers `honk_a`, `honk_b`, `honk_c`; http://127.0.0.1:8912/level_generation/creatures/mm9_honkmale_claude/review/viewer/ |
| Binding | `assets_dev/worlds/mm9/models/actors.yml`, block in `scripts/honk_binding.yml` (scale 100, stride 1.2 / 3.0, impacts 0.35 / 0.341 / 0.366, release socket `Bip01 L Finger11`) |

| Descriptor | Row | Skin | Variant | Hat |
|---|---|---|---|---|
| `MM9 Honk A` | 216 Honk | HONKM2 | `honk_a` | none |
| `MM9 Honk B` | 187 Elder Honk | HONKM3 | `honk_b` | goose (`mm9_honkhat`) |
| `MM9 Honk C` | 188 Honk Seer | HONKLEADER | `honk_c` | elder (`mm9_elderhonkhat`) |

Hats come from MM9's `object.lto` (`HonkHat.abc`, `ElderHonkHat.abc`) and the male `hat` socket, attached on `Bip01 Head`. Which row wears which is my reading of `SkinName2`; I did not disassemble the class.

**Stale copy:** the review root `output/mm9_rework/assets_dev` still holds the 17:51 `mm9_honkm.glb`, not the 18:13 install (step 1).

## Gates on the installed body
Run on the final GLB:
| Gate | Result |
|---|---|
| Winding | 0 inverted closed parts (body and both hats) |
| Detached parts, 48 fps | 0 detached |
| Flat shading | 0.00 on both materials |
| Jitter, against MM9's untouched clips | 0 fails |
| Sleeve gate, 48 fps | forearm poke 0 frames in every clip; see-through worst 74 px of 120 x 120 (Fidget R). Run with views front and q34 only |
| Arm and hand, `--outer-only --exact` | Hit L 0.8 cm; Fidget L 5.8 cm (8 frames over 1 cm); Death L 3.5 cm (9) and R 4.5 cm (18); all other clips 0. Finger stretch max 3.67 |
| Viewer tiers/clips | 30 switches, 0 failed: run on v5, **not rerun on v7** |

`texture_quality.py`:
| Set | Atlas | Spread | Fragments | Stretch p90 |
|---|---|---|---|---|
| Body | 60.0 % | 1.04 | 1.7 % | 1.06 |
| Head + hands | 42.3 % (60.3 % on the head upload) | 2.04 | **4.8 %, over the 3 % target** | 1.33 |

**Last run on the previous build, not this one (before the buckle seat and the cuff lining):**
- `mm9_actor_models_build_every_binding`: 78 descriptors on 37 models, 0 failed.
- `floor_audit.py`: all three OK, stand 0, walk -0.4..+0.2, living -0.9, dead 0.
- In-game Temple tour: `review/ingame_sheet.png`. Showed rows 216 and 187 only. Row 188 has not been seen in game.

Symmetry was measured on the pre-graft mesh and not made exact: median 3.2 mm, p95 12.7 mm, max 17.8 mm.

## Left, in order
Run from the repo root unless a step says otherwise.
1. Refresh the review root: `python3 level_generation/projects/mm9r_common/review_root.py`
2. Regression and floor audit on this build:
   `OPENYAMM_REGRESSION_FILTER=mm9_actor_models ./build/game/openyamm --world mm9 --headless-run-regression-suite actors`
   `python3 level_generation/creatures/claude_shared/floor/floor_audit.py --world mm9 --match 'MM9 Honk*'`
3. Claim the lease: `python3 tools/creature_workspace.py claim --project level_generation/creatures/mm9_honkmale_claude --identity mm9:honkmale --owner <session> --state creature_3d_progress.json --budget 40` (the 60-credit pair budget is spent, see below).
4. Viewer: `python3 tools/run_creature_review.py --project level_generation/creatures/mm9_honkmale_claude check`, then retake the tier shots (spec list `S` is in step 5).
5. Shots and sheets. The existing shots are v6, and `review/sheet_compare.png` is cut off: `scripts/make_sheets.py` got a tight crop afterwards and was not rerun.
   ```sh
   S="r0:Standing:0.5:front:body r1:Standing:0.5:quarter:body w:Walking:0.25:left:body u:Running:0.075:front:body a:AttackMelee:0.35:left:body g:AttackRanged:0.33:left:body c:Cast:0.3:quarter:body h:Hit:0.2:front:body d:Death:0.9:left:body e:Dead:0.5:quarter:body cl:Standing:0.5:front:head ar:Fidget:1.0:quarter:arms"
   for t in honk_a honk_b honk_c; do python3 tools/run_creature_review.py --project level_generation/creatures/mm9_honkmale_claude --token <T> --tier $t shots $(for s in $S; do echo ${t}_$s; done); done
   cd level_generation/creatures/mm9_honkmale_claude && python3 scripts/make_sheets.py honk_a,honk_b,honk_c work/mm9f
   ```
   Look at every sheet. `sheet_close` (texture close-ups) is listed in the script's header but never written; make it.
6. Watch every clip at normal speed: `python3 tools/run_creature_review.py --project ... --token <T> playback`. **Not done yet.** Motion so far is judged from stills and the jitter gate.
7. In game, see row 188 too (`--isolated`, tour `review/ingame_tour.yml`, `actor spawn 9188 ...`). Attack with a hostile Honk to check the egg release from the hand: never tested.
8. Write `README.md` in the reference format, ending "User artistic acceptance: not recorded". Not written; this file is the only record.
9. Work through the defects below, and rebuild if any change the body:
   ```sh
   cd level_generation/creatures/mm9_honkmale_claude
   V=$PWD/../claude_shared/gltf_venv/bin/python
   TOKEN=<T> PATH=$(dirname $V):$PATH PYGLTF_PYTHON=$V BLEND=v2/work/sleeves_v2.blend v2/scripts/build_runtime_v2.sh honkm HonkM v2/scripts/roles_honkm.json
   ```
   Then from the repo root: `python3 tools/install_model.py level_generation/creatures/mm9_honkmale_claude/v2/export/mm9_honkm.glb --world mm9`. Viewer: `v2/scripts/viewer_tiers.py honkm HonkM honk_b=export/mm9_honkhat.glb honk_c=export/mm9_elderhonkhat.glb`, then `v2/scripts/make_viewer_tiers.py <rev> "honk_a=...=review/viewer/honk_a.glb" ...`.

## Known defects and plan
- **Medallion and knot bands** are blotchy Meshy paint (black and white flecks). The ramp tamed the trim's colour only. Plan: project the medallion from `v2/references_head/01_front.png` onto its disc in the body set. 0 credits.
- **Head set fragments 4.8 %**, over target. Cause not measured. Plan: run `texture_quality.py --by-bone`; expect the forearm and lining faces.
- **Hands in Fidget and Death.** Fidget L 5.8 cm is the hand against the other sleeve in MM9's own gesture, as seen in the shots; left as is. Death 3.5 / 4.5 cm is the fall against the robe; I did not push it, to keep the fall. Review at speed.
- **Hats are one fit, not per-animation checked.** Head and hat clearance is only seen at Standing. A tiny pink speck sits on the elder hat's front dome (paint or poke, not resolved). Check Running, Hit, Death. The re-seat is `HAT_XFORM` in `hats/export_hat.py` (goose `1.07 0.03`, elder `1.1 0.035`).
- **Elder hat inner surfaces**: 61 % of texels are covered by the Codex views, the rest are nearest-filled. Check from below.
- **Skirt hem from below**: no lining, not checked.
- **Stride** 1.2 / 3.0 is measured (`stride.py`), but foot sliding in game is unchecked. Rows differ in speed: 75/200 for 187/188, 50/150 for 216.
- **Fingers read claw-like** in some raised-hand poses (MM9's mitten curl on five fingers). Finger stretch max 3.67.
- **Cast uses `Hattack2`** because MM9 has no cast clip for this body; my choice. It suits row 216's Dispel Magic, unconfirmed.

## Half-applied
No file is mid-edit and no rebuild is unfinished. Only the items above: review root stale, `make_sheets.py` not rerun, no README, gates in "last run on the previous build" not repeated.

## Credits
60 of 60 for the pair, all on the backup account, none left. This body 35: Smart Topology 5, body retexture 10, head retexture 10, goose hat 5, elder hat 5. No retries. Elder and Seer heads and the elder hat paint are Codex (0 Meshy).

## Handedness
Confirmed on this body from the raw ABC. The nose is at +Z and `Bip01 L Hand` at x -27.6, `R Hand` at +27.6. A Biped `L` is the anatomical left only if those numbers are left-handed, so LithTech's data is left-handed, and `convert_abc_model.py` copies them into right-handed glTF unchanged: every converted GLB is the mirror of the game's actor. This is inferred from coordinates and bone names, not compared with MM9 footage.
- Fix: `v2/scripts/mirror_glb.py` (the Imp's) is the last geometry step of `build_runtime_v2.sh`. Bone names keep MM9's meaning.
- The hats go through it too (`hats/post_hat.py`).
- `build_runtime_v2.sh` applies it after the floor pass, so `v2/work/mm9_honkm_floor1.glb` is the **unmirrored** build. Anything aligned to master coordinates (head views, hat placement) must use that one, not the export.
- MM9 renders in the sheets are unmirrored, so they read as the mirror of ours.
- Other installed MM9 models were not touched.

## Keep
- `scripts/`, `v2/scripts/`, `hats/*.py`, `requests/`, `v2/requests/`, `meshy/` (paid), `references_hd/`, `v2/references_head/`, `hats/references/`, `source/`.
- `work/uv_tp.blend` and `v2/work/head_uv.blend`: **the UV layouts the paid paints belong to. Never rerun `texpass_uv.py` or `texpass_head_uv.py`.**
- `v2/work/fix_v1.blend`, `v2/work/sleeves_v2.blend` (current master), `v2/work/mouth_uv.json`, `v2/work/uv_*.npz`, `v2/work/mm9_honkm_floor1.glb`.
- `textures/`, `v2/textures/` (`honkm_head_basecolor_nocrown.png` is the raw source, `_nomouth` the input of the tier projection), `v2/tier_heads/`, `hats/work/`, `work/refs/`, `work/mm9f_*.png`.
- `v2/work/sleeves_nolining.blend` can go.

Master chain: `work/fit_v1.blend` -> `uv_v1` -> `label_v1` -> `uv_tp` -> `v2/work/hands_v1` -> `head_v1` -> `head_uv` -> `honk_fix.py` (`lip_z=0.6815 lip_rim=0.004 small=110 sink=0.004`) -> `fix_v1` -> `sleeve_lining.py` (`lining=1 near=0.14 end=0.255 radius_end=0.012 cap=0 dark_pct=10`) -> `sleeves_v2`.

Re-converting an ABC needs `pygltflib` and `yaml` together: my scratch link to the system `yaml` is not durable (`mkdir d; ln -s /usr/lib/python3/dist-packages/yaml d/yaml; PYTHONPATH=d claude_shared/gltf_venv/bin/python ...`).
