# Batch C install stage (installed 2026-10-20)

The five Batch C humanoids, accepted by the user on 2026-10-20 after three review rounds (bow/spear carry, spear
thrust, skirt, Titan grip, flat feet, ankle twitch, walk bob, Thief spike and texture repairs) and the triangle
reduction. Installed with `install.sh` (11 GLBs, 15 bindings appended to the MM7 `actors.yml`), built like
`../BATCH_A_stage/` (`build_stage.py` with this batch's models).

```
BATCH_C_stage/
  assets_source/worlds/mm7/models/mm7_m214.glb (+ _bow, _arrow)   Elf Archer A/B/C     (mm7_m214_reduce_claude/export/)
                                  mm7_m218.glb (+ _spear)         Elf Spearman A/B/C   (mm7_m218_reduce_claude)
                                  mm7_m190.glb (+ _axe)           Dwarf A/B/C          (mm7_m190_reduce_claude)
                                  mm7_m410.glb (+ _dagger)        Thief A/B/C          (mm7_m410_reduce_claude)
                                  mm7_m414.glb (+ _sword)         Titan A/B/C          (mm7_m414_reduce_claude)
  assets_dev/worlds/mm7/models/actors.yml   15 bindings (each project's integration/actors.yml)
  manifest.json, build_stage.py, install.sh
```

Bindings: the README bindings of each source project, three tiers each. Dwarf B/C use `scale_reference: Dwarf A`
(the sprite frames draw the tiers at 1.0 / 1.05 / 1.10); the other four share one sprite scale across tiers. The
Titans cast (Psychic Shock, Sparks) and have no cast sprite, so `animation.cast: Attack`.

Checked at install: staged hashes, 0 inverted closed parts per GLB, the stage checks of `build_stage.py` (descriptors,
variants, clips, nodes, sockets, attachments, cast clip for casters), and an isolated desktop run on 7out01 (loads,
no actor-model errors; that map does not spawn these monsters, so they were not seen in game).
