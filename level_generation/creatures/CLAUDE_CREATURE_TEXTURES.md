# Creature textures and colour tiers (Claude, all 3D models)

User decision, 2026-10-08: every 3D model uses **one shared texture set with region masks and per-variant colour
ramps** for its colour tiers (A/B/C, palettes, future mod recolours). Separate base-colour textures baked per tier are
no longer the default. Both [quadruped](CLAUDE_QUADRUPED_PLAYBOOK.md) and [humanoid](CLAUDE_HUMANOID_NPC_PLAYBOOK.md)
playbooks follow this file. It applies equally to Codex-route models and decorations with colour variants.

## Why

- **It works like the original game.** MM6–MM8 tiers are one sprite drawn with a different palette, and a palette
  swap is a colour ramp per region. A shared skin recoloured per region is the same idea, so every tier keeps the
  same detail.
- **Memory.** Model textures are uploaded as RGBA8 (`engine/render/ModelRenderer.cpp`). One 2K base colour with mips
  is about 22 MB, so baked B/C cost about 45 MB per creature. Region masks add one small mask and a few numbers per
  tier.
- **Flexibility.** A new tier, a recolour or a mod variant is new ramp numbers, with no new art and no Meshy job. A fix
  to the texture is made once.
- **Batching.** Tiers that share every texture can later be instanced together with the tier as per-instance data.

GPU texture compression (BC7/BC5/BC4 desktop, ETC2/EAC Android, as the sprite atlas cook already does) is planned
separately. It is not part of quick dev integrations.

## Texture set per model

| Map | Size | Shared by tiers | Notes |
|---|---|---|---|
| Base colour | 2K body (1K when a separate head set exists, see Head detail) | yes | graded once; masked regions keep Meshy's luminance detail |
| Normal | 1K | yes | glTF convention (+y up); Meshy's are +y down and `tools/prepare_actor_glb.py` converts them |
| Metal/roughness + AO | 1K | yes | glTF ORM packing: R baked AO, G roughness, B metallic (see Specular below) |
| Region mask | 1K, RGBA | yes | one channel per recolourable region, up to 4; soft edges allowed |
| Head set (base, normal, MR, mask) | 1K | yes | for faces seen up close; see Head detail |

Per variant there is only data: for each region, a colour ramp from the tier's native palette.

## Sharp textures: layout, paint resolution and grading (default since 2026-10-30)

Every Meshy-textured model is built for sharpness from the start, not repaired afterwards. The method is the
[texture quality pass](claude_shared/TEXTURE_QUALITY_PASS.md), proved on the MM9 Magreeb (atlas 34 -> 54 %, fine
detail 2.4x, no runtime cost: same 2K/1K maps and triangles). The user saw the earlier 2K paints on Smart UV layouts
as smudged and blotchy; do not ship that again.

- **Our UVs: `claude_shared/uv_atlas.py`**, never Smart UV Project + pack on a reduced Meshy body. Defaults since
  2026-11-12 ([UV study](uv_research_20261111/REPORT.md)): PartUV charts from a skin-weight part tree, small charts
  merged, a seam pass that removes the most visible seams, one density with the head denser, sparrow packing at a
  4-texel gap (about 70 % atlas). The old xatlas route (`charts='xatlas', packer='xatlas', seam_rounds=0`) is the
  switch-back and the automatic fallback.
- **Meshy paints at 4K on those UVs** (`texture_resolution: "4k"`, same 10 credits), and the colour is downsampled
  once to 2K (normal/ORM to 1K). Never re-bake an earlier bake. 8K only for hero models. One paint is one random draw:
  keep the approved colour where faces or designed patterns drift, never repaint chasing the overall look.
- **Gutters last**: `claude_shared/gutter_fill.py` re-fills every map with the nearest island texel as the final step.
- **Grade gently**: `grade_basecolor.py --fine 1.0 --local 0.3 --ao-strength 0.5 --contrast 1.06 --saturation 1.15`
  unless a crop comparison argues otherwise. The old defaults (fine 0.5, local 0.6, AO 0.7) put blotches on the paint.
- **Measure before install** with `claude_shared/texture_quality.py <glb>` and meet the targets: atlas use about 70 %,
  at least 65 % (55 % for layouts made before 2026-11-12), density spread p90/p10 <= 1.3 apart from the deliberately
  denser head, at most 3 % of the surface on islands under 8 triangles (hair cards excepted), stretch p90 <= 1.5, no
  zero-area UV triangles. Record the numbers in the README.
- **Routes that keep Meshy's own UVs** (the humanoid route's `enable_original_uv: false` + `transfer_uv.py`) are
  measured the same way; if they miss the targets, re-lay the UVs with `uv_atlas.py` and repaint at 4K.
- Faces still get their own head set (Head detail below); the runtime cap stays 2K colour
  (`tools/cook/model_textures.yml`), so layout and paint quality are the levers, not bigger runtime textures.

## Region mask and ramps (engine contract, implemented 2026-10-08)

Material extras, read by `engine/models/GltfModelLoader.cpp` (`loadColorRegions`) and applied in
`game/shaders/fs_model.sc`; `openyamm_tint` was removed in the same change, with no fallback:

- **`openyamm_region_mask`: `{"index": <glTF texture>}`.** A linear RGBA image sampled with TEXCOORD_0. Channels R,
  G, B and A are regions 1–4. Every variant material references the same texture, so it is uploaded once.
  Channels without a ramp are ignored, so an RGB mask is fine.
- **`openyamm_region_ramps`: one to four `{"range": [lo, hi], "colors": [[r, g, b] × 16]}`**, list position =
  mask channel. Both are linear: `lo < hi` in 0..1 is the region's luminance range (`dot(rgb, (0.2126, 0.7152,
  0.0722))` of the decoded base colour times its factor), and the 16 colours are linear RGB in 0..1. For each
  region, `t = clamp((lum - lo) / (hi - lo))`, the colour is interpolated between the stops at `t × 15`, and the
  result is `mix(colour, ramp, mask channel)`. The renderer stores the ramps as a 16×4 sRGB texture per material
  (samplers 8 and 9, uniform `u_modelRegion`).
- **Variants:** `KHR_materials_variants` still selects the material per tier (`skin: x_a/x_b/x_c` in `actors.yml`
  is unchanged). Variant materials share every image and differ only in their ramps. Other variant materials,
  such as the walking demon's separate irises, can sit beside them.
- Tier A also goes through its ramp, so all tiers are treated the same. Its ramp must reproduce the accepted A look.
- The loader rejects a mask without ramps, ramps without a mask, a range outside 0..1 or anything but 16 colours.

**Tooling:** `claude_shared/region_variants.py` (library and the runtime GLB step).
- `fit_ramps(base, tiers, weight)` fits each tier's ramp to a target texture by least squares over the region's
  full-weight texels, using the shader's exact interpolation, and reports the error in 8-bit levels.
- `recover_weight(...)` recovers a compose step's blend weight `A·(1−w) + fit(A)·w`, which is how the existing
  baked tiers were migrated.
- `tint_ramp(...)` is the exact equivalent of the removed tint.
- `write_mask(...)` writes the RGBA mask.
- CLI `region_variants.py in.glb out.glb <x>_ramps.json` replaces per-project `add_variants.py` in
  `build_runtime.sh`: one material per tier sharing every image, every primitive mapped, unreferenced old tier
  textures dropped and the buffer compacted.

## Building masks and ramps

If the model reads flat or washed out next to its sprite (shading in different places, not just brighter or darker),
consider [native shading transfer](NATIVE_SHADING_TRANSFER.md) (`claude_shared/native_shading.py`). It bakes the
sprite's brightness by body coordinate into the shared base and builds the ramps from the same native pixels in every
palette. Its doc says when to use it, partially or not at all, and lists the trade-offs.

1. **Compare the tier palettes first** (`.act` files or `native_variants/<frame>_<palette>.png`). List the regions
   whose colours change: often only one (goblin skin, peasant garment) and at most a few (rat fur, skin and eyes).
2. **Mask per texel** in `compose_<x>.py`, using the methods that already work: rest-pose 3D position per texel
   (`dump_uv3d.py`: tail, paws, head), Meshy hue/saturation classes, painted eye spheres. Restored `masks_2x` region
   channels can be used to measure native colours. Feather the edges by 1–2 texels; leave unchanged parts such as
   bone, claws, metal and teeth out of every channel.
3. **Ramp per tier and region** from that tier's own native palette: take the region's palette entries, sort them
   by luminance and resample to 16 stops. Fit the luminance range to the texture: map the region's texel luminance
   percentiles (about 2nd–98th) onto 0..1, with albedo about 1.3–1.45× the native colour because sprites carry
   baked shading. Measure each tier from its own palette; never scale A's colour by palette ratios (that turned
   flying demon B orange instead of olive).
4. **Store the base colour unchanged** where no mask applies. Inside masks the hue no longer matters, because the
   ramp replaces it.
5. **Write** `textures/<x>_region_mask.png` and `textures/<x>_ramps.json` (format in `region_variants.py`; record
   palette ids and the fit report), from a per-project `scripts/tier_ramps.py` (see `mm6_gob_claude/`). The runtime
   step `claude_shared/region_variants.py` makes one material per tier that shares every image.
   **Pad the mask like the colour** (nearest island texel into the gutters and UV cracks) before blurring it. A mask
   that stops at the island edges leaves the gutters unrecoloured, and filtering draws them as tier-A lines along every
   UV seam on the other tiers (gob2, 2026-10-10: olive seams on red/blue skin). Then zero it again on anything painted
   into free texels (prop swatches), or the prop takes the ramp. Texels that carry another part's colour projected
   onto the skin (a buckle sliver behind the buckle) stay out of the mask.
6. **Check** all tiers next to the native palette previews in one in-game capture at the same spawn and camera.
   Look at each recoloured tier close up as well (seams show only on B/C, where the ramp differs from the base).

Bake a separate base colour for a tier only when it differs in **pattern or detail**, not just colour (different
markings, armour, a face). Write the reason in the project README.

## Edge darkening (engine, 2026-10-11)

Every skinned (creature) material darkens toward its silhouette by `DefaultCreatureEdgeDarkening` (0.65) in
`fs_model.sc`: a soft contour like the sprites' dark rim, from the interpolated mesh normal (not the normal map),
over surfaces turned more than ~57° from the view (facing below 0.55) and at least ~1.5 pixels wide at any distance.
The first setting (0.4 below facing 0.35, about 2 px on a close limb) was too faint to see (2026-10-11). Corpse stand-ins keep it; unskinned assets (decorations, held weapons)
have none. Override per material with the glTF extra `openyamm_edge_darkening` (0..1; 0 turns it off), e.g.
`region_variants.py ... --extra <Prefix> openyamm_edge_darkening=0.25`.

Edge darkening alone shades but draws no line. With `[video] creature_outlines=true` (off by default), every material
with it (0 turns both off) also gets the engine's dark contour shell, a 1.5-pixel rim like the sprites' outline (see
`engine/render/MODEL_RENDERING.md`, Creature contour).

## Emission: glowing energy parts (engine, 2026-10-22)

Energy cells, lenses, vents, thrusters, glowing cracks, acid and seams are **emission**, not bright paint: light the
surface gives off, added unlit to its shaded colour and, with bloom on, drawn into the bloom glow view so it halos.
Engine contract: `engine/render/MODEL_RENDERING.md`, "Emission and bloom". Opt-in per material; nothing else changes.

- **glTF emission.** `emissiveFactor` (linear RGB 0..1, optionally times `KHR_materials_emissive_strength` up to 16)
  times `emissiveTexture` (sRGB, UV0). Use a **grey mask** as the texture (where and how strongly it glows) and put
  the **colour in the factor**: tier variants (`KHR_materials_variants`) then share the one mask and differ only in
  their factor, so Kreegan seams go orange on A and white-gold on C, and each crawler tier's acid glows its own green.
  A colour texture works too (several glow colours in one material). glTF multiplies them: with a texture, a factor
  of zero emits nothing. A separate energy material can name **its own base colour map** as the emissive texture (the
  turrets' `scripts/set_emissive.py --texture`): the glow follows the painted energy and costs no extra texture.
- **Bloom.** A creature (skinned) material blooms when it has an emissive texture; a factor-only material (a whole
  separate lens or cell material) needs the extra `openyamm_bloom: true`. Without it, it emits but does not halo,
  as the MM6 robot's eye always has. `openyamm_bloom: false` keeps a textured emitter out of the bloom.
  Held items and corpses are static models: those glow whenever they emit.
- **Pulse.** `openyamm_pulse: [amplitude 0..1, period 0.1..60 s]` scales the emission by `1 + a sin(2 pi t / p)`
  (`openyamm_flicker: [amplitude, changes per second]` for noise). On creatures every one of a material pulses in
  step. Keep it gentle (0.15-0.3) unless it means something (a charging weapon).
- **Tool.** `claude_shared/emission.py in.glb out.glb --material PREFIX [--mask mask.png] --color VARIANT=r,g,b ...
  [--strength S] [--gamma G] [--pulse a,p]`, the last step of `scripts/build_runtime.sh` (after `region_variants.py`,
  `split_attachment.py` and `merge_head_material.py`, which do not carry new emission), on the body and on any
  attachment that glows. Without `--mask` it sets the factor and `openyamm_bloom: true`. `--gamma` > 1 narrows a soft
  mask to its brightest texels. Run it on the review viewer's GLBs too: three.js shows emissive maps as they are.
- **Mask.** Paint or derive it in the body's UV layout at the colour map's size or half (a 1K mask on a 2K body is
  enough for a glow): the region mask channel of the glowing region times brightness is a good start (the crawler's
  `hcr_glow_mask.png`). Keep it black elsewhere. The cook packs it as a colour texture (BC1/BC7 desktop, ETC2 Android).
- **How much.** A glow that covers a large part of the body makes the whole creature a light bulb. Aim for the
  energy parts only: about 1-10 % of the visible surface, factor about 0.4-0.8 of the region's ramp colour, checked in
  game with bloom on and off, by day and in a dark corridor.

Worked examples: `hes_crawler_claude` (acid, per-tier colours, texture mask, gentle pulse; `scripts/build_runtime.sh`)
and `hes_turrets_claude` (blue-white emitters, base colour as the emissive texture; `EMISSIVE_TEXTURE=1`).

## Specular, material classes and AO (kept for a later roughness pass)

**Current setting:** creature skin materials carry `openyamm_specular: 0.0` (material extra, 0..1, read by
`GltfModelLoader.cpp`). Meshy roughness maps (0.5–0.7 on skin and membrane) gave skin a grey, steel-like sheen,
worst at silhouettes (user A/B in The Hive, 2026-10-08: specular off was clearly better). Materials that also cover
metal (goblin armour and sword) keep the default until they are split into their own material.
**With specular off, also set `metallicFactor` 0.** A metallic texel has no diffuse term, so studs, hoops, buckles
and circlets turn black without specular. At metallic 0 they show their base colour, as in the sprites. Runtime
step: `region_variants.py ... --extra <Prefix> openyamm_specular=0 --extra <Prefix> pbr.metallicFactor=0`.

**The proper PBR fix comes later:** per-texel roughness by material class (skin ~0.8, membrane ~0.85, claws and
horns ~0.45, teeth ~0.35, eyes ~0.15), plus specular occlusion from AO in the engine, so eyes, teeth, claws and
metal can glint while skin stays matte. To make that a batch job instead of per-creature archaeology, every
creature's compose step writes these two outputs from now on:

1. **Material class map:** `textures/<x>_material_classes.png`, 1K, single channel (8-bit L), nearest-filtered,
   one label per texel, in the same UV layout as the base colour (a separate head set gets its own
   `<x>_head_material_classes.png`). The compose step already decides most of these classes for its masks; record
   them instead of discarding them. Labels:

   | Value | Class | Value | Class |
   |---|---|---|---|
   | 0 | empty (outside UV islands) | 6 | eye |
   | 1 | skin / hide | 7 | mouth interior (gums, tongue) |
   | 2 | fur / hair | 8 | cloth / leather |
   | 3 | membrane (wings, ears) | 9 | metal |
   | 4 | claw / nail / horn / spike | 10 | wood / plant |
   | 5 | tooth / bone | 11 | other (note it in the README) |

   Not stored in the GLB; it stays in the project, and the README names the script that writes it.
2. **AO in the metal/roughness red channel** (glTF ORM: R occlusion, G roughness, B metallic). Write the baked
   ambient occlusion (`claude_shared/bake_creature_ao.py`, the same bake the grade uses) into R instead of a constant
   255, so a later engine-side specular occlusion needs no asset rebuild. Keep the base colour graded with AO as now;
   the R channel is additional. Do not reference it as `occlusionTexture` until the engine change that uses it.

The later pass is then one shared script (class map → roughness via a lookup table, written into G) plus one engine
change (specular occlusion from R), followed by a batch rebuild and an A/B against specular off.

## Head detail (geometry and texture)

A separate texture set for the head or face is a standard technique: character artists give the face its own
texture set or a much larger share of the UV space, because players look at faces. Separate head meshes joined at
the neck are also common in games with character customisation. For AI-generated models the head is Meshy's
weakest output, since a full-body reference leaves the face under 100 px.

### Geometry: Smart Topology at 15k, then keep the head

Meshy Smart Topology tops out at about 15k triangles (the target counts triangles: goblin 15k → 15,757,
male peasant 12k → 11,643). That is enough. Smart Topology already gives complex shapes more triangles. Measured
on the top 13% of height (head plus hair, hat or ears): goblin 2,316 (15%), female peasant 4,619 (30%),
male peasant 3,574 (31%). About 2–4k triangles per head is normal for game characters at this scale.

- **Generate at the maximum, ship at the minimum.** Request `target_polycount: 15000` (5 credits at any target).
  Meshy's target thins the whole model evenly, face and hands included, while our own region reduction can keep
  them and cut flat areas, so a lower request gives a worse result at the same final count.
- **The LOD0 budget is a ceiling, not a target** (about 10k for townsfolk). Reduce **outside the head** (region
  decimation with a head vertex group kept at full density: flat cloth, limbs, the torso, hidden surfaces) and keep
  going while nothing visible is lost. The head usually ends up at about 20–35% of LOD0.
- **Stop reducing** when one of these shows a loss:
  - same-camera before/after at normal game distance, plus face and hand close-ups;
  - extreme poses (shoulders, elbows, knees collapse first; the rest pose hides it);
  - shading, after baking a normal map from the 15k mesh onto the reduced one (Cycles selected-to-active). Lost
    shape returns as shading, so this allows deeper cuts. Combine it with Meshy's detail normal map, which is
    painted on the reduced mesh.
- Fine detail (wrinkles, brow ridges, teeth edges, scales) belongs in the normal map, not in triangles.

Head quality depends, in order, on: the HD masters (Meshy can only build the shape it sees), the head texture,
and the normal map. Triangle count comes last.

### Texture: route by creature

| Creature | Head geometry | Head texture |
|---|---|---|
| Small (rat, bat, insects) | one mesh, no special treatment | one atlas; head UV island at 2–3× the body's texel density |
| Faces players look at (peasants, goblins, mages, guards) | Smart Topology 15k, head kept during reduction | separate 1K head set from a head-only retexture (below) |
| Head shape wrong after the body generation (jaw, open maw with teeth, horns) | head-only Meshy model, projected and baked onto our head (below) | from the same bake |

Body base colour drops to 1K when a 1K head set exists: two 1K sets (about 11 MB RGBA8 with mips) cost half of
one 2K body (about 22 MB). The head set uses the same region channels and ramps as the body; skin stays one region
across both.

### Head-only retexture (same mesh, no graft) — goblin pilot, then peasants and mage, 2026-10-08

1. **Head turnaround.** Codex generates front, three-quarter, profile and back views of the bust (cut below the
   jaw, 1254²), using the accepted body masters as input (brief as in `mm6_wdm_claude/references_head/`).
2. **Head material and UVs.** In Blender, give the head faces their own material slot and their own UV layout
   filling 0..1. Cut along a natural seam: collar, hairline, fur line or the base of the neck.
3. **Body retexture** as usual (four HD masters, body UVs).
4. **Head retexture** (10 credits). Export the head faces alone as a neutral GLB with the head UVs and retexture
   them with the four head views (`enable_original_uv: true`, `2k`; keep 1K at runtime).
5. **Apply** the head maps to the head material. The vertices are identical, so weights and topology are
   untouched. Match the skin luminance across the seam (`mm6_wdm_claude/scripts/compose_head.py`).

Goblin pilot (`mm6_gob_claude/`, scripts `head_split.py`, `compose_head.py`): it works, with a sharp face and no
visible neck seam. Two lessons:
- **Reuse the body's skin ramps for the head.** Match only the head's skin luminance to the body, so head and neck
  take the same colours in every tier. A per-channel colour match overcorrected (lime ears and skin).
- **Classify skin with true HSV hue.** Meshy's olive skin sits at about 35–45°; brown ears are skin too.
The body base colour is now 1K for every creature with a head set; its old head region is unused atlas space.

Rollout (female peasant, male peasant, mage) with shared tools in `claude_shared/`:
- **`head_texture_split.py`** (Blender, on the master): the face attribute `head` and a head-only upload. Select by
  head-bone weight, optionally limited to `--parts`, plus `--whole-parts` taken entirely: the female peasant's
  braid (part 9); the mage's head skin, eyes and hair (parts 1–4), so the beard is not cut.
- **`compose_head_set.py`**: 1K head maps graded like the body (the peasants and mage are not graded, so neutral
  settings). Their skin does not change between tiers, so the head is one material shared by all tiers, with no
  ramps.
- **`head_seam_gain.py`**: matches brightness across the neck seam, measured on the master's boundary faces (male
  peasant ×1.38, female peasant ×0.96). A head that is a separate shell (the mage's neck under the mantle) shares no
  edge with the body and keeps gain 1.
- The export assigns the head material from `head`. The mage's export leaves head UVs out of its staff-strip remap.
Credits: 10 per head (goblin 87/100, female peasant 95/100, male peasant 25/100, mage 20/100).

### Problem heads: project and bake (instead of a graft)

When the head's shape itself is wrong, generate a head-only Meshy multi-image model from the head turnaround
(about 30 credits). Then keep our own head and transfer the detail onto it:

1. Subdivide our head region once (only the head vertex group; feather into the neck).
2. Shrinkwrap it onto the head-only model's surface (nearest surface point, project along normals for the face).
3. Bake base colour and normal from the head-only model onto our head UVs (Cycles selected-to-active, small cage
   extrusion).
4. Recompute weights for the new head vertices from the original head (data transfer, nearest face interpolated).

This keeps one connected mesh, our weights and our UVs, with no neck seam in the geometry. It is the standard
detailed-to-game-mesh bake. Use the full graft (`mm6_wdm_claude/scripts/graft_head.py`) only when the new head's
silhouette cannot be reached by shrinkwrapping, for example a much larger open maw.

## Migration of existing models (audit and status, 2026-10-08)

| Model | Tiers now | Regions that change | Mesh/texture source | Work needed |
|---|---|---|---|---|
| `mm6_rat` | 3 baked 2K | fur, skin, eyes | x2 sprite frames | **done**: Codex HD masters, `retexture_v2`, head UV ×2.5, 3 regions (17.2 → 9.2 MB) |
| `mm6_bat` | 3 baked 2K | membrane | x2 sprite frames | **done**: Codex HD masters, `retexture_v2`, head UV ×2.5, 1 region (14.5 → 7.6 MB) |
| `mm6_bld` | 3 baked 2K | body, membrane, maw | x2 sprite frames | **done**: Codex HD masters, `retexture_v2` (UVs kept for the maw disc), 4 regions incl. disc (14.9 → 8.3 MB) |
| `mm6_gob` | 3 baked 2K | skin | Codex HD (stage 1) | **done**: `scripts/tier_ramps.py`, head set, 1K body (19.5 → 9.4 MB) |
| `mm6_pfem` | 3 baked 2K | garment | Codex HD (stage 1) | **done**: `scripts/tier_ramps.py`, head set, 1K body (14.5 → 8.4 MB) |
| `mm6_pman` | 3 baked 2K | tunic | Codex HD (stage 1) | **done**: `scripts/tier_ramps.py`, head set, 1K body (13.9 → 7.5 MB) |
| `mm6_pmn2` | single tint | robe | Codex HD (stage 1) | **done**: exact tint equivalent, head set, 1K body (10.6 → 10.3 MB) |
| `mm6_wdm` | single tint, head graft | skin | Codex HD masters | **done** by the flying-demon session (body + head masks) |
| `mm6_demon` | 3 baked 2K + B/C normal/MR (Codex route) | skin, harness; irises are own materials | Codex HD sheet | **done**: `regions_20261008/build_regions.py` (42.9 → 22.9 MB); B/C keep their colours, not their separate Meshy paint |
| `mm6_deco_*` | none | — | — | none |

Engine support and the credit-free migrations are done; each migrated project keeps
`review/region_tiers_20261008.png` (A/B/C in one in-game capture). Fit error against the approved tier
textures: goblin, peasants mean 0.6–4 8-bit levels; demon B/C 11–21, since their old textures were separate Meshy
paints. All listed models are migrated. The goblin also has the head set (see above). For those three a retexture on the existing mesh keeps the rig and clips. A new Smart Topology from
the HD three-quarter master (5 cr more, and the rig and clip scripts rerun) is worth it only when the silhouette
looks poor in game.
