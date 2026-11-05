# Translucent indoor faces (BLV glass)

Native indoor maps (BLV) may draw chosen faces translucent: alpha-blended over what lies behind them, tinted, lit like
their room. It is opt-in per face through the map's scene file; a map without such data (every MM6–MM8 dungeon,
Hesper's) renders exactly as before. First user: MM9's Lich Lab window and ice glass
(`level_generation/projects/mm9r_lichlab/`), then the Temple of Honk's skylights; MM9's data and why it asks for this:
[MM9 visual properties](mm9_rework/MM9_VISUAL_PROPERTIES.md) (finding 3: opacity = texture alpha × brush `Alpha`).

## Data: the scene's `translucent_faces`

```yaml
translucent_faces:
  - faces: [11025, 11026, 11027]   # BLV face indices
    opacity: 0.7                   # 0..1, times the texture's own alpha (default 1)
    tint: [1.0, 1.0, 1.0]          # multiplies the lit texture colour (default white)
    two_sided: true                # default false: drawn only from the side its plane normal faces
```

Top level of `<map>.scene.yml` (`IndoorSceneYml`: `parseIndoorSceneTranslucentFaces`, `buildIndoorTranslucentFaces`;
a scene overlay's entries add to the base scene's). Faces must exist, be listed once, opacity within 0–1 and the tint
non-negative, or the scene fails to load. The map keeps them as `IndoorMapData::translucentFaces`, sorted by face
(`findIndoorFaceTranslucency`); the editor's scene writer round-trips them.

Why the scene file and not the alternatives:

- **Not a surface-material class.** The surface-material `glass` class ([plan](SURFACE_MATERIALS_PLAN.md)) is a
  per-texel class map that gives opaque faces relief, reflection and night glow. It is per texture (one texture is
  both a translucent pane and an opaque one in the Lich Lab: the panes with nothing behind them stay opaque), is
  desktop-only (Android drops the maps) and follows a video setting. Whether one sees through a window is the map's
  geometry, not a quality option.
- **Not a BLV face attribute.** The native attribute word has no room for an opacity and a colour, and a new bit or
  record would change the format every MM6–MM8 tool reads. The scene file is already the map's per-face sidecar
  (face overrides, doors), parsed at load and written by the converter and the editor.

The converter emits the data (below); by hand, list the face indices from the editor or the compiler's `faces.yml`.

## Rendering (`IndoorRenderer`)

- **Batches.** A translucent face is a batch of its own (`TexturedBatch::translucent`, its translucency and plane
  normal); a portal face may be translucent too (it is drawn, and stays passable). The opaque loop skips these
  batches; everything else about them (animation frames, door movement, lightmap selection) is the ordinary path.
- **Order.** After the opaque world, the 3D models, the actor and decoration billboards (which write depth), and before
  the spell sprites, particles, effects and shield domes, in the sequential world-transparent view (after ambient
  occlusion): `renderTranslucentFaces` collects the visible ones (their room or the room behind visible through the
  portals, as for every face), drops a single-sided face seen from behind (one plane test per face,
  `indoorTranslucentFaceVisibleFrom`), and draws them **back to front per face** by the distance from the eye to the
  face's centre (`sortIndoorTranslucentDrawsBackToFront`, ties by batch so the order is stable). Per face, not per
  room: MM9's engine hall is one room of 2 181 faces with panes on four sides and over the atrium, so a room order
  cannot put its near panes over its far ones. Panes are small and planar, and there are few (78 in the Lich Lab).
  A face at opacity 0 is not drawn at all: it would blend nothing and writes no depth, but each face is its own draw
  (Training Hall's 596 invisible target hit shells raised its archery range from about 90 to 700 draws). It stays a
  face for collision, picking and hits like any other.
- **State.** Depth test on (`LEQUAL` against the opaque scene), depth write off, alpha blend; no culling (two-sided
  is the plane test above). The rooms behind a pane are drawn first because portal visibility ignores faces: a pane
  in a portal (or on one) never hides the rooms behind it from the visibility pass.
- **Shading.** The same shader as every face (`fs_indoor_textured_lit.sc` built with `INDOOR_TRANSLUCENT=1`:
  `fs_indoor_textured_translucent`, and `fs_indoor_textured_baked_translucent` with `INDOOR_BAKED=1`): the lightmap
  where the bake has the face, else the vertex light and room ambient, plus the dynamic lights from the light grid;
  output colour × `tint`, alpha = texture alpha × `opacity`. On a map with [scene fog](INDOOR_FOG.md) glass fades like
  any face (the `INDOOR_FOG` variants of both programs).
  Surface-material maps are not applied to translucent faces.
- **Cost when unused.** The programs and the uniform `u_indoorTranslucency` exist only for a map with translucent
  faces; on any other map the face lookup returns at once (empty list), no batch is split and no pass runs.
- **Not covered.** Water reflections leave translucent faces out. Particles, effects and spell sprites behind a pane
  draw over it (they come later and the pane writes no depth); within one pane's room the order is by face centre, so
  two large panes crossing each other may sort wrongly. Classic outdoor BModel faces have no translucency: their
  renderer (`OutdoorRenderer` draw groups) is a separate path; only the old MM9 `bmodel_world` ODMs blend, by a
  `.render` flag, texture alpha only and unsorted.

## See-through liquids

Liquid faces (`engine/liquids/liquids.yml`) are not translucent faces: the liquid shader draws them, and a face in both
would draw the liquid's flat colour over the shader. A liquid entry's `opacity` below 1 (2026-10-31, MM9's water) makes
its faces see-through instead:

- **Data.** `LiquidDefinition::opacity` (default 1; water and tar faces only, never terrain or lava) rides in the alpha
  byte of the faces' tint (`liquidFaceColorAbgr`, `MapAssetLoader` `liquidFaceTexture`). `buildWaterFaceGeometry` keeps
  see-through faces in surfaces of their own (`WaterSurfaceGeometry::seeThrough`).
- **Draw order.** `WaterRenderer::renderIndoor` takes a `WaterSurfaceSet`: the opaque liquids draw where they always did
  (`Opaque`, after the solid faces); the see-through ones after the creatures and 3D models and before the translucent
  faces (`SeeThrough`), so the bed and whatever stands in the liquid are already drawn under them. They test and write
  depth like the opaque ones (spells and particles under the surface stay hidden). Reflection captures draw both
  (`All`); see-through planar surfaces still take their planar reflection.
- **Shading** (`fs_indoor_water.sc`, only when the tint alpha is below 0.998, so an opaque liquid computes exactly what
  it did): the body covers the bed at about the opacity, rippled like MM9's caustic water sprites (denser and lighter on
  the waves' steep rings, the more so the clearer the liquid; the mean stays the opacity) and lit at least fully (MM9
  draws those sprites unlit); the reflection (Fresnel) and the light highlights lie over it whole, so the surface turns
  mirror-like at grazing angles. Colour is premultiplied by that coverage and divided back for the alpha blend; scene
  fog fades the surface as before.
- **Bake.** The bake export (`IndoorBakeSceneExport.cpp`) gives a see-through liquid face a `translucency` of the
  liquid's opacity (untinted), so the bake lets that share of the light through to the bed. Its bitmap (the bake's
  albedo) must carry an opaque alpha, or the texture alpha counts twice (MM9's `LQ*O*.bmp` do).
- **Outdoors.** Not supported: outdoor BModel faces of such a liquid draw opaque (`fs_water.sc` ignores the alpha of
  faces; a change there moved three pixels of MM6/MM7 sea by one or two levels, so it was left out).
- **Default unchanged.** No MM6–MM8 liquid sets `opacity`; frozen-clock captures (temporary `debug.time_scale 0`) of
  MM6 Free Haven sewer, MM7 d01, MM8 d07, oute3, 7out01 and out01 water were byte-identical before and after outside
  the animated creatures and a flickering lamp, which differ between two runs of the same build too.

## Gameplay

A translucent face is an ordinary solid face: it collides, and it blocks line of sight, missiles and picking as a wall
does (`indoorSegmentBlockedByCombatFace`, `findProjectileIndoorFaceHit`, the inspect ray). MM9's glass surfaces carry
`SURF_SOLID` and its physics raycasts stop on them, so monsters do not see or shoot through windows and the party
cannot click through them. (Before, the Lich Lab panes were invisible collision faces, which line of sight and missiles
pass.)

## Baked lighting

The bake scene (`--headless-export-indoor-bake-scene`) gives each translucent face its `translucency`;
`tools/lighting/bake_indoor.py` lightmaps it like any receiver (the light arriving at its face) and in Cycles gives it
a mix of a transparent BSDF and its diffuse colour: with alpha = opacity × the texture's mean alpha, it lets 1 − alpha
of the light (and of every shadow ray) straight through and scatters alpha with its tinted mean colour. A translucent
face is never a profile emitter (an `outward` window pane is opaque glass with nothing behind it). The report lists
`translucent_faces`; the log prints each glass material's alpha.

## The MM9 dungeon converter

`level_generation/projects/mm9r_common/dungeon` (`rooms.Glass`, `glass_portals`, `glass_backed`,
`build.translucent_faces`, `movers.build_movers`) with each map's `overrides.yml glass` ({texture: {opacity, tint,
two_sided}}): a glass face between two rooms is a portal shaped as the pane plus the pane as a solid glass face; a
glass face inside one room only the glass face; a glass face with air on its front only is glass when the ray out of
its back meets the front of a built face within 1 024 LT (a wall or the sky faces behind it), else stays opaque (the
void outside would draw black); a mover's glass is its own mechanism part `<node>_GLASS<k>`. Glass faces go to
`STATIC_glass<k>_<room>` source nodes, whose face ids the compiler reports in `faces.yml`; the scene gets one
`translucent_faces` entry per kind (texture × brush `Alpha`), opacity = the texture setting × the brush Alpha.

## Tests

- `./build/tests/openyamm_unit_tests --test-case='*translucent*'`: parsing and defaults, validation (range,
  duplicates, opacity, tint), the empty-map fast path, the face lookup, back-to-front order, single- and two-sided.
- The MM9 dungeons' headless scenarios (each project's README) and the MM6–MM8 indoor regressions.
