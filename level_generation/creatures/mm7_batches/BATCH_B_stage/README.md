# Batch B install stage (installed 2026-10-20)

The five Batch B robed casters, accepted by the user on 2026-10-20 after two review rounds and the triangle
reduction. Laid out like the asset trees. Installed with `install.sh` on 2026-10-20 at the user's request.

```
BATCH_B_stage/
  assets_source/worlds/mm7/models/mm7_m170.glb                    Cleric Moon A/B/C  (mm7_m170_reduce_claude/export/)
                                  mm7_m174.glb                    Cleric Sun A/B/C   (mm7_m174_reduce_claude)
                                  mm7_m274.glb (+ _staff)         Mage A/B/C         (mm7_m274_reduce_claude)
                                  mm7_m426.glb (+ _wand)          Warlock A/B/C      (mm7_m426_reduce_claude)
                                  mm7_m290.glb                    Monk A/B/C         (mm7_m290_reduce_claude)
  assets_dev/worlds/mm7/models/actors.yml   15 bindings (staff and wand attachments on node Staff)
  manifest.json   sha256 of every staged file, source exports, variants and clips per model
  build_stage.py  rebuilds the stage from the reduce projects' exports and the projects' integration/actors.yml
  install.sh      the install, when wanted
```

| Model | LOD0 triangles (production -> staged) | Release times |
|---|---|---|
| Cleric Moon | 9,883 -> 7,179 | attack 0.483 s (left palm), cast 0.8 s |
| Cleric Sun | 8,761 -> 6,305 | attack 0.483 s (right palm), cast 0.8 s |
| Mage | 10,188 -> 8,228, staff 664 | attack 0.483 s (right palm), cast 0.667 s (staff gem) |
| Warlock | 10,732 -> 8,846, wand 581 | one Cast clip for attack and spell, 0.8 s (wand crystal) |
| Monk | 9,331 -> 7,081 | attack 0.483 s, cast 0.683 s (right palm) |

## Install (when the user asks)

```sh
level_generation/creatures/mm7_batches/BATCH_B_stage/install.sh
```

The script:
- checks the staged hashes, and that none of the 15 descriptors is already bound;
- runs `check_winding.py` on each GLB (all 0 inverted closed parts at staging);
- installs each GLB with `tools/install_model.py <glb> --world mm7`;
- writes `assets_dev/worlds/mm7/models/actors.yml`, or appends the Batch B entries if another batch's stage was
  installed first.

## Checked at staging (`build_stage.py`)

- every descriptor exists in `assets_dev/engine/data_tables/monster_descriptors.txt`;
- every skin is a `KHR_materials_variants` variant of its GLB;
- every clip, `cast`/`run` clip, `upper_body_root`, look node and socket (palms, `Socket_Staff_Head`) exists in its
  GLB;
- the staff and wand attachments are staged, and their node (`Staff`) exists in the body and in the attachment.

Every reduction's rollback copy is byte-identical to its production export (`work/*_source_pre_reduce.glb`). The
bindings are the projects' `integration/actors.yml`: tiers B and C write out the full A entry with their own skin and
`scale_reference` to A. At staging, the Moon and Sun Cleric cast release was corrected to 0.8 s: full reach since the
face-forward revision; it was 1.10 s.

## Still open

- No in-game check has been run. After the install, load MM7 maps that spawn these monsters and run the actor
  regressions. Check especially:
  - the Mage's and Warlock's staff/wand attachments and bolts leaving `Socket_Staff_Head`;
  - the Monk's hands hidden in the sleeves (bone-scale channels).
- The Warlock's skin stays smooth (Meshy's paint); a new body and head retexture (about 20 credits) is the option if
  more skin detail is wanted.
- Rebuild the stage (`python3 build_stage.py`) after any later change to a reduce project's export.
