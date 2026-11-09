# Batch A install stage (installed 2026-10-20)

The five Batch A humanoids, accepted by the user on 2026-10-20 after the review fixes (archer aim, flat feet, walk/run
ankle twitch, walk head bob) and the triangle reduction. Laid out like the asset trees so the later install is one
command. Installed on 2026-10-20 with `install.sh` (11 GLBs, 15 bindings appended to the MM7 `actors.yml`).

```
BATCH_A_stage/
  assets_source/worlds/mm7/models/mm7_m222.glb (+ _sword)          Fighter Chain A/B/C    (mm7_m222_reduce_claude/export/)
                                  mm7_m226.glb (+ _sword)          Fighter Leather A/B/C  (mm7_m226_reduce_claude)
                                  mm7_m230.glb (+ _sword)          Fighter Plate A/B/C    (mm7_m230_reduce_claude)
                                  mm7_m406.glb (+ _sword)          Swordsman A/B/C        (mm7_m406_reduce_claude)
                                  mm7_m154.glb (+ _bow, _arrow)    Archer A/B/C           (mm7_m154_reduce_claude)
  assets_dev/worlds/mm7/models/actors.yml   15 bindings with their weapon/bow/arrow attachments
  manifest.json   sha256 of every staged file, source exports, variants and clips per model
  build_stage.py  rebuilds the stage from the reduce projects' exports and the projects' integration/actors.yml
  install.sh      the install, when wanted
```

## Install (done 2026-10-20)

```sh
level_generation/creatures/mm7_batches/BATCH_A_stage/install.sh
```

It checks the staged hashes and checks that none of the 15 descriptors is already bound. Then it runs
`check_winding.py` on each GLB (all 0 inverted closed parts at staging) and installs each one with
`tools/install_model.py <glb> --world mm7`. Last, it writes `assets_dev/worlds/mm7/models/actors.yml`. If that file
already exists (for example after the Batch E stage was installed), the Batch A entries are appended to it. Do not
copy the staged GLBs into `assets_dev` by hand: `install_model.py` writes the runtime copy with hidden back faces culled.

## Checked at staging (`build_stage.py`)

- every descriptor exists in `assets_dev/engine/data_tables/monster_descriptors.txt`;
- every skin is a `KHR_materials_variants` variant of its GLB;
- every clip, `run` clip, `upper_body_root`, look node and socket (`Socket_Arrow_Release`) exists in its GLB;
- every attachment GLB is staged, and its node (`Sword`, `Bow`, `Arrow`) exists both in the body and in the attachment;
- every descriptor with a spell in `monster_data.txt` names an `animation.cast` clip (the game refuses the whole
  `actors.yml` otherwise; added after the install, when Archer and Fighter Plate lacked it).

The bindings are the projects' staged `integration/actors.yml` unchanged (tiers B/C use `scale_reference` to A).

## Still open

- In game so far: Archer and Fighter Plate spawned on 7out01 (load, draw, Shield cast). Still to do: load MM7 maps that spawn these monsters (Archer: a ranged
  attack, which checks that the arrow leaves `Socket_Arrow_Release` at 1.167 s) and run the actor regressions.
- Rebuild the stage (`python3 build_stage.py`) after any later change to a reduce project's export. A source
  re-export reaches the reduction through `scripts/transplant_clips.py` (clips) or a new reduction (geometry).
