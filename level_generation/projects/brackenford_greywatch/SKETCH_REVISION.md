# Brackenford sketch revision

The driver accepted the closer spacing but rejected the parallel rectangular road grid in `test_img/1220.png`.
The new composition follows [the driver's sketch](../../../test_img/1221.png): unequal main-loop sides, a diagonal
western street, a smaller southern loop, an inn lane, an uphill residence and a rotated raised temple.

## Play

```sh
/tmp/openyamm-brackenford-playtest-sketch/play.sh outdoor
```

Choose **Load Game → Scenario** for the God character. `play.sh indoor` opens unchanged Greywatch. The earlier
`playtest-density` and `playtest-calibrated` snapshots remain available. A new snapshot is necessary because existing
saves retain old map positions/state. The package in `dist/` is the durable deliverable; `/tmp` can disappear on reboot.

## Interpretation and implementation

The sketch defines relationships rather than exact pixel-scale footprints or a requirement to duplicate every pink
mark. The same 24 logical houses/services remain in 23 physical structures. Sizes and setbacks vary; weapon/armor shops
still form one joined building with independent doors. Rotated houses and the diagonal west edge break the former grid.
The ordinary facade kit retains its calibrated textures and dimensions.

The large northern building now houses **Myles Greydawn**, reusing the existing MM8 resident/topics in the civic slot.
Its new exterior has a projecting three-level central hall, lower recessed wings, two octagonal towers and separate
hipped roofs. The entrance stays normal size. The broad native plateau is at 1536; the town floor is about 576–704.
Erathia's native town hall (model 46, 2432×1152×880) and Castle Gryphonheart's multipart composition were inspected as
scale/massing references. This is original geometry in the MM8 town palette, not an imported Erathia castle or invented NPC.
The map's separate wilderness castle dungeon entrance remains distinct.

The temple stands on a smaller raised site at 1088 and turns 135 degrees toward its branch approach. Native terrain
is graded along both ascents, with local building pads, rather than merely painting roads over plateau shoulders.
Barrels sit beside the manor and temple, following the four green dots. The two wells and larger fountain are set
back from traffic; the fountain has an open garden court instead of occupying an intersection.

The western diagonal uses the actual native `drsrne1`/`drsrne2` half-tile pair (raw 217/218 in road bank 414), arranged
like native Ravenshore examples. These tiles form one continuous slanted strip. Other junctions use native bend/T/fork
variants. The texture grid remains 512 units; no road BModel or substituted terrain format is introduced.

The fountain reuses Ravenshore's **assembled models 83+84**, retaining both halves in their common coordinate frame.
Its authored event restores **15 HP and 15 mana to the selected character per use**, with **40 uses shared by the party
per game day**. This is the stated interpretation of the brief's “restore 15 and mana ... max 40 per day.” HP/mana use
normal runtime clamps. Even a drink at full resources counts as a use. Named map state persists the day/count, and
supply resets on the next use after midnight, including after leaving/reloading or a long absence. It does not import
Ravenshore's gold-grant or town-portal quest state.

Four native `dec03` interactive barrels replace the three previous scattered stable barrels. The existing MM8 barrel
system assigns their stat colors and grants **+2 to one permanent base stat**, then remembers the empty barrel through
normal map save state. These are ordinary native barrel rewards, not infinite repeatable boosts; the normal map-refill
policy still applies. The well near the temple keeps the temporary Might effect; the southern well is refreshing only.

## Evidence and checks

- Written native ODM overview and street views are stored under `review/`; see the final links below.
- [Native spacing/assembly measurements](review/sketch_revision/measurements.json) and
  [quick native check](review/sketch_revision/quick_check.json).
- `check_fountain.lua` exercises the new handler directly: 40 grants, 41st denied, Lua-module reload retaining depletion,
  next midnight and a long absence resetting supply. This fast handler check does not simulate gameplay or prove engine
  save serialization; the existing named-map-state API owns persistence.
- Native writer readback verifies terrain arrays, actors/decor and face bindings. The quick checker retains old event/house
  identities, checks the new prop bindings, rotated house clearances, and four stat-barrel anchors. Both God starts are
  created and reloaded by the snapshot installer. No exhaustive shop/travel/combat scenario suite is used.

![Native overview](review/brackenford_native_sketch_overview.png)

![Raised residence](review/brackenford_native_sketch_manor.png)

Geometry counts, final hashes and final captures are recorded in `review/sketch_revision/verification.json`.
The previous native map, Blender scene, geometry/placement scripts and semantic manifest are preserved in
`review/sketch_revision/before/`.

Rebuild through [REBUILD.md](REBUILD.md), then use `--review-directory sketch_revision` with the native quick checker
and density measurement script. Run `lua level_generation/projects/brackenford_greywatch/check_fountain.lua` for the
new fountain handler. Stage after rebuilding the native automap, export the archive, and prepare a fresh snapshot with
an unused directory and the original God seed saved before visiting either generated map.

![Final native game fountain court](review/gameplay/sketch_final_court.png)

Subsequent screenshots 1222–1230 are addressed in [FRONTAGE_REVISION.md](FRONTAGE_REVISION.md), including closer
street frontages, aligned approaches, corrected transition artwork, court houses and additional town planting.
