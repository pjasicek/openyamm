# Night glow with surface materials off (D-55)

**DECISION:** (b), limited to worlds that opt in. A world can declare in `world.yml` that its surface glow is content and not a quality option. A1 names the field, for example `surface_glow_default: true`. For such a world, the glow channel is drawn even when Settings' "Surface materials" is off. Only Xeen declares it. Relief, roughness, metal, parallax and reflections stay behind the setting. For MM6–MM8 the default stays exactly as it is now: no glow with the setting off. Option (a) holds only until A1's change lands. Option (c) is rejected.

**WHY:** The setting is off by default because it is experimental, not because it is slow. `GameSettings.h` says "Experimental, off by default and outside the graphics presets", and SURFACE_MATERIALS_PLAN §7 measured "the materials cost almost nothing". The real costs are memory (the maps are loaded only when the setting is on; New Sorpigal uses 649 MB of textures with it off and 699 MB with it on) and unfinished MM6–MM8 production (§8.1: "check of every texture with glass or the glowing class" is still open). So turning glow on by default for every world would change shipped MM6–MM8 visuals across only some of their maps, and indoors glass "glows at any hour" (§4.3). That breaks AGENTS.md's no-regression rule. Option (c) would give "night-glowing windows" a second owner next to surface materials. AGENTS.md names surface materials as their owner and forbids duplicated ownership. A whole-face emissive flag also cannot light the slits inside `xaenergy` without a mask, and that mask is exactly the `_n.b` channel. Option (a) fails D-49 change 10 and D-36 for most players. With the setting off, shot 04 of `d6/pics/sheet_final.jpg` shows Alamar as an unlit silhouette, while `sheet_s14night.jpg` shows the lit slits and fields.

**WHO ACTS:**
- **A1** makes the smallest general change:
  1. `tools/surface_materials.py` records which cooked textures have any glowing texels (`_n.b` > 0), as a list next to each world's `surface_materials<tier>`.
  2. With the setting off, and only on a map of a declaring world, `loadFaceTextures` loads `_n` (never `_d`) for textures on that list. It reads them from the folder next to each texture's own source, as it does now, so a borrowed MM7 `hkm3elw` is covered.
  3. Those draw groups use a glow variant of the ordinary programs: outdoor baked BModels (`fs_outdoor_bmodel_baked{,_array}{,_shadow}`) and indoor `fs_indoor_textured_lit`/`_baked`. The variant keeps today's shading and only adds `surfaceGlowColor(albedo) × glow × SURFACE_GLOW_SCALE`, with the existing night factor outdoors. A texel with glow 0 must draw identically to today.
  4. A unit test: a declaring world with the setting off loads only the glow textures' `_n`; a world without the field loads nothing.
  5. A capture check: New Sorpigal with the setting off is pixel-identical before and after the change.
  6. Document the field in §3.1 and §4.6 of the plan.

  It must not change:
  - MM6–MM8: no field means no loads, the same programs, the same memory and the same pixels with the setting off.
  - The setting-on path in any world.
  - MM9's BModel-world path, which already draws without maps.
  - The setting's default, the graphics presets and Android packaging. Android ships no surface maps, so Xeen on Android stays as in (a), which is accepted.
- **Orchestrator:** adds the field to `assets_dev/worlds/xeen/world.yml` once A1 lands it.
- **A6:** recaptures with the setting off:
  - D6's signature (20,700) and arrival views by night, and by day;
  - D5's Barrier;
  - D4's Blackfang from the jetty (D-36).

  `xaenergy` and `xafield` glow at all hours, so every player will now see them by day. If the strips read too hot by day, A6 recooks them as night glow. Until A1 lands, Alamar's night read is recorded as waiting on A1, as D-36's rim glow was.
- **A7:** rechecks how the `xafield` curtains read by default in DD-16 and XD-19: with D-51's ~0.5 translucency, Corak must still be visible behind his stasis field.

**REVERSIBLE:** Yes, cheaply. Removing the field from `world.yml` gives (a) back with no data change. Extending the field to MM6–MM8 later is a separate decision for the user, once their production and glass review (§8.1) are finished.

**SUMMARY ROW:** D-55 | Night glow with Surface materials off | (b) limited to declaring worlds: a `world.yml` field draws only the glow channel (`_n` of textures with glow, added to the ordinary shading) when the setting is off; only Xeen declares it; MM6–MM9 unchanged with no field; (c) rejected | A1 (cooker list, loader, glow variants, test, MM6 identical), orchestrator (world.yml), A6 (D4/D5/D6 recaptures), A7 (field recheck)

---

I read the docs, code and captures and edited nothing. One thing in my reasoning comes from reading the code rather than from the docs: building and dungeon face vertices already carry their material layer and texture gradients even with the setting off (plan §7), so the glow variant needs no change to the vertex format.
