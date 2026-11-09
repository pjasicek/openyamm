# Batch E install stage

**Installed 2026-10-20** by `install.sh` at the user's request: the five smooth GLBs in
`assets_source/worlds/mm7/models/` (runtime copies cooked into `assets_dev/worlds/mm7/models/`) and
`assets_dev/worlds/mm7/models/actors.yml`. Boot check: `7d06.blv` (rats, spiders) and `7out03.odm` (griffins) load
with no actor-model errors and no missing actors; no close-up of the models in game yet.

The five accepted, reduced Batch E models and their `actors.yml` bindings, laid out like the asset trees so the later
install is one command. Nothing here is in `assets_source/` or `assets_dev/` yet. MM7 has no 3D actor models so far,
so the stage creates `worlds/mm7/models/` and its first `actors.yml`.

```
BATCH_E_stage/
  assets_source/worlds/mm7/models/mm7_m162.glb  Behemoth A/B/C   (from mm7_m162_reduce_claude/export/, smooth)
                                  mm7_m258.glb  Griffin A/B/C    (mm7_m258_reduce_claude)
                                  mm7_m278.glb  Manticore A/B/C  (mm7_m278_reduce_claude)
                                  mm7_m382.glb  Rat A/B/C        (mm7_m382_reduce_claude)
                                  mm7_m402.glb  Spider A/B/C     (mm7_m402_reduce_claude)
  assets_dev/worlds/mm7/models/actors.yml        15 bindings (descriptors 208-210, 280-282, 295-297, 385-387, 400-402)
  manifest.json   sha256 of every staged file, source exports, variants and clips per model
  build_stage.py  rebuilds the stage from the reduce projects' exports and the project READMEs' bindings
  install.sh      the install, when wanted
```

## Install (when the user asks)

```sh
level_generation/creatures/mm7_batches/BATCH_E_stage/install.sh
```

It checks the staged hashes, runs `check_winding.py` on each GLB (all 0 inverted closed parts at staging), installs
each with `tools/install_model.py <glb> --world mm7` and then copies `actors.yml` (it refuses if one already exists).
Do not copy the staged GLBs into `assets_dev` by hand: `install_model.py` writes the runtime copy with hidden back
faces culled.

## How the bindings were built and checked

`build_stage.py` takes the tier A binding from each project README (`mm7_mXXX_claude/README.md`) and repeats it for
B and C with skin `mXXX_b` / `mXXX_c`; Behemoth and Manticore B/C add `scale_reference` to their A (bigger native
frames make them larger in game). Checked at staging:
- every descriptor exists in `assets_dev/engine/data_tables/monster_descriptors.txt`;
- every skin is a `KHR_materials_variants` variant of its GLB;
- every clip, `cast` and `run` clip, `upper_body_root`, look node and socket (`Socket_Stinger`, `Socket_Mouth`) exists
  in its GLB.

Correction made while staging: the Behemoth's `run_stride_length` was 1.35 m from a foot-slide measurement on an
in-place clip whose feet never plant. The Creature Pack copy of Mixamo Mutant Run keeps its root motion (2.081 m per
0.867 s cycle against 1.894 m for Mutant Walking), scaled by our measured walk (2.573 / 1.894): **2.83 m**.

## Choices still open

- **Smooth or flat shading:** the staged GLBs are the smooth exports. To stage the flat builds instead, use each
  reduce project's flat export (`mm7_m162_reduce_claude/export/mm7_m162_flat.glb`,
  `mm7_m258_reduce_claude/export/mm7_m258_flat.glb`, `mm7_m278_reduce_claude/work/mm7_m278_flat.glb`,
  `mm7_m402_reduce_claude/work/mm7_m402_flat.glb`, Rat: `REA_FLAT=1` build in `mm7_m382_reduce_claude/`) renamed to
  `mm7_mXXX.glb`, then rerun `build_stage.py`.
- No close-up in-game check yet: look at the monsters on MM7 maps that spawn them and run the actor
  regressions.
- [REDUCTION_LEDGER.md](../../REDUCTION_LEDGER.md): five rows added at install.
