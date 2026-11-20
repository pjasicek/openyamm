# MM7 Ghoul (m470) — Claude rig-first project

Batch D, model 4 ([batch file](../mm7_batches/BATCH_D.md)). Descriptors 454 Ghast (palette 511, ash-blond hair), 455
Ghoul (517, black hair) and 456 Revenant (525, orange-brown hair). **Installed 2026-10-20** in `assets_source/worlds/mm7/models/` and `assets_dev/worlds/mm7/models/` (bindings in its `actors.yml`). Status:
technically complete, pending user review.

[Review viewer](review/viewer/index.html) (served at
`http://127.0.0.1:8912/level_generation/creatures/mm7_m470_claude/review/viewer/`) ·
[clip sheets](review/clips_three_quarter.png) · [attack candidates](review/cand_attack.png) ·
[HD masters](references_hd/selected_views_review.png) · [head masters](references_head/selected_views_review.png)

| Item | Value |
|---|---|
| Exports | `export/mm7_m470.glb` (body, LODs, 3 tier variants, head merged; unarmed); editable master `work/rig_v6.blend` |
| Triangles | LOD0/1/2/3 6,290 / 3,145 / 1,130 / 371 (was 8,718 / 4,356 / 1,567 / 516). Second cut on the textured master (user review 2026-10-20, `reduce_textured.py`, targets per garment in `scripts/reduce2.json`; protected: Hand, Finger, Thumb bones, the head/body texture boundary, head region weight 0.4); both texture sets get new UVs and are baked garment by garment from the unreduced copy `work/rig_v6_full.blend` (`rebake_uv.py` -> `texturing/rebake_v2/`, read by the compose script) |
| Mesh | Smart Topology of the HD three-quarter master (orchestrator override: Codex picked v2, v1 keeps the native's toothy grin): one closed skin body with the overalls, bracers and lacing painted on it, plus hair, teeth, eyes, chest lacing bars and 41 eyelet studs |
| Rig | 52 `B_*` bones + twist bones; Meshy auto-rig joints (the ring line fits for the elbows degenerated on the thin arms), wrists from the skin ring fit; hand frames follow the forearm (a PCA of the curled claws was 44 degrees off) |
| Weights | `weights_fix.py`: skin from Meshy with the shoulder fade and the jaw free of the shoulders; the mane by height from the head to the upper back; teeth and eyes rigid on the head; lacing bars and eyelets rigid on the skin under them. The curled claws hook into each other (connectivity separated 3 of 4 fingers), so the hands stay rigid on the hand bones: no finger weights, the claws keep their shape |
| Clips (30 fps) | Standing Mixamo Standard Idle, arms out 16 degrees (3.0 s); Walking Mixamo Walk, arms out 12 degrees (1.0 s, 1.741 m stride); Running Mixamo Standard Run fit; **Attack** Mixamo "Zombie Attack (1)" planted with 20 % of its leg motion and IK steps, 1.4x: wind back, lunge and reach with the claws (blow 0.817 s), cut 0.1 s after the reach and eased to Standing (1.37 s); Hit set Unarmed get-hit F1, arms out 8 degrees; Death Mixamo Standing React Death Backward, travel halved; Dead; Fidget Mixamo Annoyed Head Shake planted, arms out 16 degrees |
| Textures | body 1K + head 1K (Meshy retextures from the HD masters / head turnaround), AO graded, ORM red = per-class specular mask; one region, the hair, which lies in the head set (the body carries an empty mask with the same ramps); ramps: a square-root luminance curve through each tier's native median, chroma by luminance rank, tier A keeping the texture's chroma |
| Meshy credits | **30 of 100**: Smart Topology 5, auto-rig 5, body retexture 10, head retexture 10 |

## Installed 2026-10-20 (user request; commands as run)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m470_claude/export/mm7_m470.glb --world mm7
```

[actors_m470_binding.yml](actors_m470_binding.yml) is added to `assets_dev/worlds/mm7/models/actors.yml` (scale 114.5 =
native stand 198 px x 1.0 over the 1.730 m Standing pose; stride 1.741 m; blow 0.817 s; head look). Tier speeds
160/180/200 stay under the run threshold (275).

## Replay

`scripts/rebuild.sh` (`STAGE=rig`, then `STAGE=anim`), texture chain once (`export_uploads.py`, Meshy `retexture_v1`
and `head_retexture_v1`, `transfer_uv.py -- work/rig_v5h.blend meshy/retexture_v1 work/rig_v6.blend`), then
`scripts/build_runtime.sh`, `viewer_tiers.py`, `update_viewer_manifest.py`.

## Gates and choices (final export)

- G1: three claw attacks retargeted onto the rig and compared (`review/cand_attack.png`): Zombie Attack (1) reaches
  forward like the native lunge; Mutant Swiping keeps a hunched stance; Mutant Jump Attack travels out of place.
- G4: arm stretch p99 <= 1.38, max 2.28 (upper arm in the attack).
- G6 (closed skin, inside test): the curled claws sank 7-8 cm into the thighs in the idle, walk, hit and fidget (the
  Mixamo arms hang close) - fixed by turning the upper arms out (`arm_abduct.py`; the native holds them out too): 0.
  The source attack ends by pulling a grabbed victim to the belly (claw 8-9 cm inside): the clip is cut 0.1 s after
  the reach; remaining 3.7 cm on its first frame. The death puts the hands on the body while falling (<= 6.4 cm).
- Feet: grounded soles -2.4..+2.2 cm in the walk. Viewer: 3 tiers x 8 clips, no console errors; textured EEVEE frames
  in `work/r_glb/`, head close-up `work/head470_*.png`. Not checked in game.
- Feet (user review 2026-10-20: feet on their outer edges, ankle twist, head bob): `foot_level.py` from batch C (mm7_m218_claude: sole pitch + roll weighted by sole flatness, capped at 20 deg, smoothed; the run levelled too) and `walk_bob.py` from batch A (mm7_m154_claude: walk pelvis height averaged over both steps and smoothed, legs re-solved onto the same ankle paths) after clip timing. Idle/attack/fidget soles 0.9-1.8 deg from flat (were 9-10 deg on the outer edge); walk mid-stance 1.2-6.4 deg (were 8-30); foot turn per frame unchanged from the source clips (walk/run <= 25.9 deg, hit <= 13.2); walk pelvis second difference 3.52 -> 0.56 cm. Batch A's per-frame roll on the hit made its landing snap (21 deg per frame); batch C's flatness weighting does not.

## Known limits

- The claws do not articulate (rigid hands); the source fist/grab finger motion is not shown.
- The overalls, bracers and lacing are painted on the skin (Smart Topology made them one surface); the eyelets are
  separate studs.
- Tier B's "black" hair renders dark grey (the native palette's hair entries are dark grey, not black).

## Floor fix (2026-10-21, MM7 creature post-process)

[Creature post-process](../CREATURE_POSTPROCESS.md) step 2. Audit before: dying sinks to -3.2.
`claude_shared/floor/floor_fix.py work/floor_fix_base/mm7_m470.glb export/mm7_m470.glb --lift-joints Dead Death --lift-only 'B_Skirt*,Robe_*,…' --ground-death Death Dead`, then
`check_winding.py` (0 inverted) and `tools/install_model.py --world mm7`. Only animation samplers changed; the
pre-fix export is `work/floor_fix_base/mm7_m470.glb`, and the `.blend` master predates the fix (rerun the same operation
after any re-export).

## Gait rollout (2026-10-31, package h09)

New clip appended to the installed source: `Sprint` (humanoid set Unarmed-Sprint, 0.60 s, stride 3.9194) for MAW's chase, bound as `sprint`. Walking and Running stay bound.

Rebuild: `level_generation/creatures/gait_rollout_20261031/h09/scripts/rebuild.sh m470` (composes from the pre-gait copy
`h09/work/mm7_m470_pre_gait.glb` and `h09/jobs/`, runs `gait_gate.py` and `check_winding.py`), then
`python3 tools/install_model.py level_generation/creatures/gait_rollout_20261031/h09/export/mm7_m470.glb --world mm7 --name
mm7_m470.glb`. Bindings: `h09/bindings.yml` (applied by the rollout coordinator). A far-LOD repair, head-bob, floor or
reduction rerun on this model must re-graft these clips: copy the new installed source over the pre-gait copy and
rebuild. Details, gates and doubts: [h09 README](../gait_rollout_20261031/h09/README.md).
