# Accepted new dirt shoreline pack

This pack combines the 36 accepted land tiles, 15 accepted native_water_v3 tiles, and twelve newly composed RGBA shores at 256×256 (2x runtime). The 51 accepted files remain byte-identical to HANDOFF_ASSETS.json.

Version 2 fixes the nearly invisible shading in 1280.png. The original tiles have a broader, finer-grained, less saturated bank. A built-in imagegen call produced a matching damp-earth detail material using the accepted master and original north shoreline as references; [prompt](bank_detail/prompt.txt), [raw output](bank_detail/generated.png). prepare.py quilts it using the accepted material convention, fits the finer grain and reduces saturation. build.py blends it into an 80-authoring-pixel band (40 runtime pixels maximum), strongest at the water, with additional contact shading. Existing alpha and inland dirt phase remain unchanged. Land beyond the band retains the master exactly. Wrapped material gutters and premultiplied-alpha reduction avoid averaged border strips. The prior pack and its evidence are preserved in versions/v1.

[Visual review](review.html) includes complete shoreline contexts, centered local join windows, coastline, island, inward corners, low-angle water, the supplied dirt view, and native animation samples. Join statistics cover all 332 distinct corrected-map adjacencies and fourteen water frames. Animated joins are gated over the complete cycle; individual phase screening values remain in validation.json. This is not a hardware performance certification.

Rebuild from the repository root:

```sh
python3 level_generation/terrain/mm6_new_sorpigal_dirt_fidelity/transitions/shorelines/bank_detail/prepare.py
python3 level_generation/terrain/mm6_new_sorpigal_dirt_fidelity/transitions/shorelines/build.py
python3 level_generation/terrain/mm6_new_sorpigal_dirt_fidelity/transitions/shorelines/check.py
```

Native review uses prepare_review.py to clone the current enhanced stage into isolated map/flat stages. Only the flat fixture excludes actor overlays. Capture poses are in captures/*.oysav; elevated poses need the Fly buff as well as flying movement state to survive faithful save round-tripping. Capture metadata records executable/map hashes. After collecting the five views and 28 empty-pool animation samples (coastline samples include monster spell flashes), run review.py to validate and package them. Regenerated assets need fresh native review if their hashes change.

Install with integrate.py for a before/after preservation audit, or the normal terrain-only installer:

```sh
python3 level_generation/creatures/mm6_peasants/prepare_playtest.py --terrain-only
./level_generation/creatures/mm6_peasants/play.sh enhanced
```

The current reviewed executable is retained; this pack requires its water-repeat sampler fix. The installer checks the reviewed binary hash and refuses unreviewed builds. Settings already using terrain x2 remain byte-identical. Previous terrain is retained under seed/terrain_before_dirt_fidelity_shores_v2. integration.json records protected file hashes and symlink targets, including original mode, saves, other enhanced art, map and additional scene overlays.
