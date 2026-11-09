# Off-road cave and ogre camps

Driver image `test_img/1249.png` marks the east cache spur and the southern road network. Removed the three authored
routes `cave_trail`, `east_cache_trail` and `south_cache_trail`. Town streets, castle approach and regional roads remain.
Ground materials are regenerated from the remaining road mask, including the surviving junctions. The former roads
are not retained as continuous bare-dirt trails. Heights and native BModels are unchanged.

All chests, loose items, actors and arrival positions are preserved. Scenery is regenerated with the normal placement
rules after releasing the former road clearances: 38 decoration records change, with the same overall counts
(487 trees, 416 plants, 239 rocks, 18 props and six lights). Native buff/challenge markers retain their identities.
This is a road-layout change; the cave and guarded treasure still exist and are reached across open terrain.

The shared [outdoor calibration](../../OUTDOOR_CALIBRATION.md), README, checklist and brief now say that roads need a
credible settlement/travel purpose. Natural caves, monster camps and wilderness treasure normally stay off-road;
placing a point of interest does not automatically create a road to it.

Review the [updated minimap](runtime/worlds/mm8/icons/lg01.bmp),
[eastern camp](review/brackenford_native_offroad_east.png) and
[southern wilderness/cave](review/brackenford_native_offroad_south.png).
The native tile/frontage check includes both historical and current tile palettes, so removing the last instance of
an old road end-cap does not break its before/after comparison.

Rebuild with `author_brackenford_blender.py` through Blender MCP, normalize/reopen `source/lg01.blend`, then
`build_brackenford.py`. Run `check_frontage.py --review-directory road_purpose_revision` and
`check_facade_revision.py --review-directory road_purpose_revision`. Use `review_road_purpose_blender.py` for the
written-map automap and two focused views, then stage/package using [REBUILD.md](REBUILD.md).

Previous sources/native map/minimap are preserved under `review/road_purpose_revision/before/`.
Fresh God playtest: `/tmp/openyamm-brackenford-playtest-offroad/play.sh outdoor`, then **Load Game → Scenario**.
Use `indoor` for Greywatch. Earlier snapshots remain frozen.

[Written-map check](review/road_purpose_revision/road_check.json) passes: 82 road cells exclusive to the removed
routes now use natural terrain tiles; every retained road path is exact. All four chests, five loose items, actors,
arrivals, height samples and BModels match the previous native map. Native special decorations also remain exact.
[Tile/frontage](review/road_purpose_revision/frontage_check.json) and
[IDs/clearance](review/road_purpose_revision/quick_check.json) pass, with zero corner mismatches.
Outdoor SHA256: `1042e98eda5e9cce9feda806ef469ee0f7c9a9e9fed304b7ad30288768df51a5`.

The rebuilt minimap and both native wilderness views were opened and inspected: the marked road branches and their
linear dirt borders are gone, while the castle approach remains connected. These are visual/native-data checks,
not new combat or interaction tests. Blender MCP remains connected and the unrelated default scene is restored.
Package SHA256: `8504475bea327477cb74e1771706d938f264fc20b2ce70461ab13229f8b0787c`.

[Artifact verification](review/road_purpose_revision/artifacts.json): the archive installs and both copied God starts
reload with the expected map and party level.
