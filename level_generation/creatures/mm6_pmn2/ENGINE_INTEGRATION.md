# Restored mages in Brackenford

Seven groups of three restored MM6 mages occupy the eastern wilderness near the two centaur patrol areas.
Each group contains all three variants. The original 102 actors, including 11 centaurs and 29 town residents,
retain their source records and positions. Brackenford now has 123 fixed actors, 94 hostile, in 18 wilderness areas.
No extra random spawns are added. The town placement buffer remains at least 8,192 units.

## Play

From the repository root:

```sh
./level_generation/creatures/mm6_pmn2/play.sh
```

Choose **Load Game → Scenario**. Two God-character starts are provided:

- Default (or `play.sh mages`): beside the eastern ridge group, facing the enemies. They will attack.
- `play.sh town`: the ordinary western arrival, for exploring the complete map.

Each start has its own save folder and a single initial **Scenario** entry.
The launcher uses the frozen executable, assets and separate saves in `/tmp/openyamm-pmn2-playtest`.
Previous crusader and map snapshots retain their old contents. Set `OPENYAMM_PMN2_DEMO` to select another prepared
directory. To recreate a removed `/tmp` snapshot:

```sh
python3 level_generation/creatures/mm6_pmn2/install_runtime.py
python3 level_generation/creatures/mm6_pmn2/prepare_playtest.py
```

Preparation requires a current compiled game. It rejects existing directories to preserve personal saves;
use `--directory /tmp/openyamm-pmn2-playtest-new` for another snapshot. The checked-in God seed is an ordinary
save from Dagger Wound Island, before entering Brackenford; this avoids reusing old cached map actors.
The authored map plan, scene companions and content archive also contain the groups, so future map builds retain them.
The map archive requires this checkout's installed custom monster tables, sprite groups and pmn2 atlas assets.

## Native variant behavior

| New ID | Original ID / name | Color / palette | Staff damage | Spell (native chance and skill) |
| --- | --- | --- | --- | --- |
| 904 | 610 / Apprentice Mage | Red / 801 | 2D4 | Fire Bolt, 20%, Normal 1 |
| 905 | 611 / Journeyman Mage | Green / 802 | 2D4+2 | Ice Bolt, 30%, Normal 1 |
| 906 | 612 / Mage | Blue / 803 | 2D4+6 | Lightning Bolt, 50%, Normal 2 |

All combat fields are copied exactly, including levels 2/6/10, HP 6/21/40, recovery, AI, resistances and loot.
These are the original weak town-mage statistics, without a balance increase for this test region.
Map actors explicitly start hostile and use local ally type 34, matching their centaur neighbors. Global relations
and the original MM6 monster entries remain unchanged. Group centers are authored in Brackenford's `outdoor_plan.json`;
deterministic local placement avoids steep ground and roads.

## Runtime art and animation

`assets_dev/engine/sprites_new/pmn2` contains three RGBA base pages and three R8 masks, shared across all actors and
variants. The decoded page total is **46.14 MiB**. Review PNGs and baked palette previews are not installed.
Namespaced identities are `custom:pmn2_red`, `custom:pmn2_green`, `custom:pmn2_blue`.
Sprite families `m903`–`m905` reserve frame records **30102–30194** and refer to `atlas:pmn2/<native-frame>`.
The installer checks table/family/frame collisions before writes.

All 93 native animation records retain their durations, flags, texture view suffixes, scale 0.699997 and action
assignments, including the separately named corpse group and native fidget aliases. The existing shared actor
animator selects melee/spell attacks, hit, death, walking and directions; there is no separate animation controller.
The 331×272 logical bottom-centered canvas and 2× crop offsets preserve sprite placement at the native size.

The shared atlas parser/shader now accepts `masked_luminance_rgb_v1`, matching the offline pmn2 previews:
encoded RGB luminance times the variant vector, blended by coverage, with alpha unchanged. Uniform mode 0 is exact
base bypass, 1 remains the crusader's green-chroma operation, and 2 selects luminance. This adds no new texture page
per color and applies through the shared indoor/outdoor atlas path. Native indexed sprites keep their existing path.

## Focused validation

- Game and shaders built; 18 focused sprite/billboard tests passed with 184 assertions.
- All 93 animation records and all three copied combat/descriptor records match their originals apart from declared
  identity/group changes. Source BMP hashes are unchanged.
- Quick placement checks preserve the previous 102 actors and put new actors on dry terrain within travel bounds.
- Both God saves reload with all 21 mages hostile; the nearby trio detects and targets the party after one runtime second.
- [Actual gameplay capture](review/runtime/pmn2_groups.png) shows red, green and blue mages, native centaurs, attacks,
  correct grounding and selective colors under scene lighting. Each of the three page pairs was allocated once.

[Content checks](review/runtime/content_validation.json) and [playtest details](review/runtime/playtest.json)
record the concrete actors and positions. The capture is a software-display rendering check, not a target-GPU
performance measurement or exhaustive spell balance test. No terrain, building geometry or dungeon mechanisms changed.
