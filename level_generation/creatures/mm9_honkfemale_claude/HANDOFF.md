# Honk female (`mm9_honkf`): handoff, 2026-10-30

**Superseded on 2026-10-31: the steps and defects below were worked through by the night pass. The current state, gates and open points are in `README.md`; rebuild with `v2/scripts/master_v3.sh`, then `build_runtime_v2.sh` with `BLEND=v2/work/medal_v3.blend`. This file stays as the day session's record, including its route notes and Keep list. Its hashes and numbers are the 18:13 build's.**

Stopped on the coordinator's order. Nothing is mid-edit and no job is running. The project lease is released. Sister body, with the hats and the shared route notes: `../mm9_honkmale_claude/HANDOFF.md`.

## Installed and bound
| Item | State |
|---|---|
| Body | `assets_source/worlds/mm9/models/mm9_honkf.glb`, sha256 `bf705f07a6ff...`, identical to `v2/export/mm9_honkf.glb`. Installed 18:13. LOD 9,201 / 4,600 / 1,654 / 550 |
| Viewer | revision `v7-20261030`, tiers `honkf_a`, `honkf_b`; http://127.0.0.1:8912/level_generation/creatures/mm9_honkfemale_claude/review/viewer/ |
| Binding | `assets_dev/worlds/mm9/models/actors.yml`, block in `../mm9_honkmale_claude/scripts/honk_binding.yml` (scale 100, stride 1.0 / 3.2, impacts 0.35 / 0.3 / 0.4, release socket `Socket_Beak`, the MM9 `RangeAttack` socket sits in front of the hat) |

| Descriptor | Row | Skin | Variant |
|---|---|---|---|
| `MM9 Honk Female A` | 186 Honk | HONKF1 | `honkf_a` |
| `MM9 Honk Female B` | 217 Elder Honk | HONKF3 | `honkf_b` |

HONKF2 is on no monster row, so it has no tier.

**Stale copy:** the review root `output/mm9_rework/assets_dev` still holds the 17:51 `mm9_honkf.glb`, not the 18:13 install (step 1).

## Gates on the installed body
Run on the final GLB:
| Gate | Result |
|---|---|
| Winding | 0 inverted closed parts |
| Detached parts, 48 fps | 0 detached |
| Flat shading | 0.00 on the body; the head value was cut off in my output, 0.00 on the previous build |
| Jitter | 0 fails, **against `v2/work/mm9_honkf_armout.glb`** (MM9's clips plus the constant 8.5 deg arm offset), not the raw clips |
| Sleeve gate, 48 fps | forearm poke 0 frames; see-through worst 316 px of 120 x 120 in Death R, 136 Death L, 72 Dead R, under 7 elsewhere. Views front and q34 only |
| Arm and hand, `--outer-only --exact` | Death R 5.3 cm (18 frames over 1 cm); Dead R 3.1 cm (49); Hit L 2.2 cm (6); AttackRanged and Cast L 1.9 cm (5); Fidget L 1.5 cm (5); Death L 1.9 cm (2); Standing, AttackMelee 0.4 cm; Walking, Running 0. Finger stretch max 4.97 (Death) |
| Viewer tiers/clips | 20 switches, 0 failed: on v2, **not rerun on v7** |

`texture_quality.py`:
| Set | Atlas | Spread | Fragments | Stretch p90 |
|---|---|---|---|---|
| Body | 61.1 % | 1.06 | 0.0 % | 1.07 |
| Head + hands | 41.1 % (59.5 % on the head upload) | 1.09 | 0.6 % | 1.28 |

**Last run on the previous build, not this one (before the cuff lining):**
- `mm9_actor_models_build_every_binding`: 78 descriptors on 37 models, 0 failed.
- `floor_audit.py`: **fails**, see defects. Stand 0, walk -0.3..+0.2, living -1.5, dead 0, dying -3.8 at the current `--smooth Death 0.09`.
- In-game Temple tour: `../mm9_honkmale_claude/review/ingame_sheet.png`. Row 186 only. Row 217 has not been seen in game.

Symmetry was not measured on this body (`scripts/symmetry.py -- work/label_v1.blend`).

## Left, in order
Run from the repo root unless a step says otherwise.
1. Refresh the review root: `python3 level_generation/projects/mm9r_common/review_root.py`
2. Regression and floor audit: same commands as the male handoff; `--match 'MM9 Honk*'` covers both.
3. Claim the lease: `python3 tools/creature_workspace.py claim --project level_generation/creatures/mm9_honkfemale_claude --identity mm9:honkfemale --owner <session> --state creature_3d_progress.json --budget 40` (the 60-credit pair budget is spent).
4. `python3 tools/run_creature_review.py --project level_generation/creatures/mm9_honkfemale_claude check`
5. Retake the shots with the `S` list in the male handoff, tiers `honkf_a honkf_b`, then in this folder: `python3 scripts/make_sheets.py honkf_a,honkf_b work/mm9f`. Existing shots are older builds, and `review/sheet_tiers.png` predates the tight crop. `sheet_close` is not written by the script; make it.
6. Watch every clip at normal speed (`playback`). **Not done yet.**
7. In game, see row 217 too; attack with a hostile Honk to check the egg from `Socket_Beak`: never tested. `Socket_Beak` is an estimate of the beak tip.
8. Write `README.md` in the reference format, ending "User artistic acceptance: not recorded". Not written.
9. Work through the defects, then rebuild:
   ```sh
   cd level_generation/creatures/mm9_honkfemale_claude
   V=$PWD/../claude_shared/gltf_venv/bin/python
   TOKEN=<T> PATH=$(dirname $V):$PATH PYGLTF_PYTHON=$V BLEND=v2/work/sleeves_v2.blend v2/scripts/build_runtime_v2.sh honkf HonkF v2/scripts/roles_honkf.json
   ```
   Then from the repo root `python3 tools/install_model.py level_generation/creatures/mm9_honkfemale_claude/v2/export/mm9_honkf.glb --world mm9`. Viewer: `v2/scripts/viewer_tiers.py honkf HonkF`, then `v2/scripts/make_viewer_tiers.py <rev> "honkf_a=...=review/viewer/honkf_a.glb" "honkf_b=...=review/viewer/honkf_b.glb"`.

## Known defects and plan
- **Floor audit fails on Death: dying sinks about 3.8 world units (tolerance 2.5).** `--smooth Death 0.075` still gave -3.6 and failed the jitter gate (shoulder skin 2.63 mm/f2), so I kept 0.09: the failure is a short sink, the alternative is a shake. Plan: find which part sinks; a stronger skirt bend in `--lift-joints` is the next try.
- **The Elder head (row 217) is a recolour of tier A, not MM9's HONKF3 face.** The Codex repaint in `v2/tier_heads/` is good art but would not project: double lips at every view seam, even with block-matching flow (NCC 0.59 / 0.79 / 0.73). `v2/scripts/head_tier_f3.py` changes the colours only: skin, brows, eyes, lips, dark hair in place of the veil, blue-grey neck. She has HONKF1's face, and her neck reads flat. Plan with credits: a Meshy head retexture on `v2/texturing/honkf_head_upload.glb` with the repaints as views (10 credits, needs approval). Without credits: warp the front repaint onto the face with hand landmarks.
- **Goose hat brim is low**, at the brows; I kept the old hat's seat. 240 head shell faces above z 0.728 were deleted because the skull poked through the hat. Check for holes from below.
- **Brim front centre has no knotwork**: a plain gold patch where Meshy painted the skull that poked through. The male goose hat shares this paint. Plan: copy a neighbouring stretch of the band in the head set, then rebuild the male hat (`hats/goose_tex.py`, `export_hat.py`, `post_hat.py`).
- **Meshy eyes read wide and staring** in the viewer on both tiers. The face is long; the chin was only judged by eye in close-ups.
- **Death R hand 5.3 cm and corpse hand 3.1 cm** in the dress. The Dead hand is held: review from the party's view.
- **See-through in Death** (316 px): into the sleeve while falling. Not inspected.
- **Medallion** is blotchy Meshy paint. Same plan as the male, from `v2/references_head/01_front.png`.
- **Walk stride 1.0 is an estimate.** `stride.py` read 0.5 m, which looks wrong under the dress (the male measures 1.2). Check foot sliding in game.
- **`AttackRanged` and `Cast` have identical gate numbers**, so `Rattack1` and `Hattack1` look like the same motion with different events. Cast 0.4 is the `bite` event.
- **Her hands and the head skin** differ slightly in tone in the viewer; hands use `--hand-gain 1.25`.

## Half-applied
No file is mid-edit and no rebuild is unfinished. Only the items above: review root stale, shots and sheets old, no README, some gates not repeated.
`v2/work/uv_body.npz` and `uv_head.npz` predate the cuff lining. Harmless: lining only adds faces, but `regions_honkf.py` and `head_tier_f3.py` read them, so re-dump them with `v2/scripts/uv_xyz.py` if the mesh changes further.

## Credits
25 here, of the pair's 60 (all spent, backup account, none left): Smart Topology 5, body retexture 10, head retexture 10. No retries.

## Handedness
Confirmed on this body from the raw ABC: `Bip01 L Hand` at x -21.3, `R Hand` at +21.3, same convention as the male, whose nose is at +Z. Full reasoning in the male handoff; inferred, not compared with MM9 footage. `v2/scripts/mirror_glb.py` is the last geometry step of `build_runtime_v2.sh`, so `v2/work/mm9_honkf_floor1.glb` is the **unmirrored** build: use it for head views and anything in master coordinates. The arm offset's sign in `arm_offset.py` is for the unmirrored GLB.

## Keep
- `scripts/`, `v2/scripts/`, `requests/`, `v2/requests/`, `meshy/` (paid), `references_hd/`, `v2/references_head/`, `source/`.
- `work/uv_tp.blend` and `v2/work/head_uv.blend`: **the UV layouts the paid paints belong to. Never rerun `texpass_uv.py` or `texpass_head_uv.py`.**
- `v2/work/fix_v1.blend`, `v2/work/sleeves_v2.blend` (current master), `v2/work/uv_*.npz`, `v2/work/mm9_honkf_armout.glb` (jitter reference), `v2/work/mm9_honkf_floor1.glb`, `work/clean_v1.glb`, `work/fit_v1.blend`, `work/hat_v1.blend`.
- `textures/`, `v2/textures/` (`honkf_head_basecolor_raw.png` is the source before the neck clean), `v2/tier_heads/`, `work/refs/`, `work/mm9f_*.png`.
- The goose hat mesh comes from `../mm9_honkmale_claude/meshy/hat_goose/`, and the male goose attachment reads this project's `v2/work/head_uv.blend` and head textures.

Master chain: `scripts/clean_meshy.py` (Meshy joined a braid to the sleeve by a thread) -> `work/clean_v1.glb` -> `fit_rig.py` (`strands` place the braid chains) -> `fit_v1` -> `graft_hat.py` -> `hat_v1` -> `uv_v1` -> `label_v1` -> `uv_tp` -> `v2/work/hands_v1` -> `head_v1` -> `head_uv` -> `honk_fix.py` (`small=110 shell_cut_z=0.728 drop_parts=6,11`) -> `fix_v1` -> `sleeve_lining.py` (`lining=1 near=0.14 end=0.17 radius_end=0.012 cap=0 dark_pct=10`) -> `sleeves_v2`.
Clips: `v2/scripts/arm_offset_honkf.txt` (8.5 deg, constant, replaced per-clip pushes that failed jitter), `hand_rest_honkf.txt` (Fidget only).
