# Authored FX showcase

Three original OpenYAMM recipes using CC0 artwork, integrated 2026-09-22:

| Name | Runtime ID | Composition |
| --- | --- | --- |
| Healing Bloom | `openyamm:fx/healing_bloom` | Two ground pulses, rising green/gold sparks, a soft central flash |
| Ember Impact | `openyamm:fx/ember_impact` | Animated fire, outward embers, ground pulse, separately fading alpha smoke |
| Arcane Pulse | `openyamm:fx/arcane_pulse` | Purple energy knot, expanding rings, radial sparks |

`openyamm:fx/creature_fire_hand` is a separate original moving-emitter recipe using the already imported
MM9 fire-bolt sprite. It attaches to a creature socket, emits two world-space sprites at about 30 Hz and
retains them for 180 ms. After native visibility review, sprite dimensions are five times the original hand
recipe's values, with the same count and lifetime. Stopping emission drains that short trail. It is silent and adds no model, light
or ribbon geometry. Its imported artwork retains the MM9 resource provenance; it is outside the CC0
showcase artwork described below.

The common `engine/effects/library.yml` and `resource_bindings.yml` import both this directory and the
generated MM9 library. Both indoor and outdoor runtimes load those common entry points. Imports use full
virtual asset paths; cycles/repeated imports, duplicate effect IDs and duplicate bound resource IDs fail
loading. A failed load preserves the current library. Edit `library.yml` here for authored timing; the MM9
importer does not overwrite this directory.

These effects are available to the runtime by ID. They do not replace existing spell or melee bindings.
The showcase recipes use the `predictable` profile, Z-up coordinates and a foot/ground-level origin. The effects
are silent. Textures are 128×128: four static sprites and sixteen fireball frames, 1.25 MiB RGBA8 before
mipmaps if all are resident. Textures load on use.

## Preview

From the repository root:

```sh
./re_mm8/mm9_vfx/viewer/run.sh --no-browser
```

Open [Healing Bloom](http://127.0.0.1:8099/?effect=openyamm%3Afx%2Fhealing_bloom&target=off),
[Ember Impact](http://127.0.0.1:8099/?effect=openyamm%3Afx%2Fember_impact&target=off), or
[Arcane Pulse](http://127.0.0.1:8099/?effect=openyamm%3Afx%2Farcane_pulse&target=off).
See the [viewer guide](../../../../re_mm8/mm9_vfx/viewer/README.md) for controls and preview limitations.

In the game's debug console, use `effect list` to see loaded effects, then for example:

```text
effect spawn openyamm:fx/healing_bloom X Y Z
effect spawn openyamm:fx/ember_impact X Y Z
effect spawn openyamm:fx/arcane_pulse X Y Z
```

Replace `X Y Z` with a nearby world position. A reproducible isolated New Sorpigal demonstration is:

```sh
./tools/run_game.sh --isolated fx-showcase --world mm6 --map oute3.odm \
  --position -9728 -11319 161 --yaw-radians 0 --pitch-degrees -8 --warmup 0 --seconds 5 \
  --set debug.effect_spawn_id=openyamm:fx/healing_bloom \
  --set debug.effect_spawn_x=-9400 --set debug.effect_spawn_y=-11319 --set debug.effect_spawn_z=161
```

Change the effect ID to view another effect. The effect plays once after loading; the HTML viewer can repeat it.

## Artwork and reproduction

[provenance.yml](provenance.yml) records authors, source URLs, pinned archive SHA-256 hashes and conversion
steps. Kenney provides the ring, spark and smoke masks; Unity Labs supplies FireBall01; Cethiel supplies the
arcane knot. All three selected collections are published under CC0-1.0. Kenney's bundled license is retained
as [KENNEY_LICENSE.txt](KENNEY_LICENSE.txt). License reference:
[CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/).

The Unity TGA has black RGB backing and no source alpha: it is used with additive blending, with alpha
supplied by the recipe's fade. Smoke uses ordinary alpha blending. The arcane sprite is one reviewed static
variant centered on a uniform canvas, not an invented animation sequence.

To reproduce textures/descriptors/bindings from the pinned downloaded archives (Pillow and PyYAML required):

```sh
python3 tools/fx/import_showcase_assets.py \
  --kenney /path/to/kenney_particle-pack.zip \
  --fireball /path/to/FireBall01-flipbooks.zip \
  --arcane /path/to/Arcane_Effect.zip
```

This command deliberately leaves hand-authored `library.yml` untouched. The archives are research downloads;
they are not required to launch the game or viewer after import.

## Validation

- Normal `openyamm` and `openyamm_unit_tests` builds completed.
- Focused effect tests: 14 cases, 284 assertions passed, including composed library/resource loading in
  MM6/MM7/MM8, import failures/collisions, and complete showcase expiry.
- Existing MM9 asset pipeline and native viewer simulation checks passed.
- Authored browser simulation passed at 30/60/120 Hz, including fade/animation timing and complete drain.
- Browser smoke checks passed for all 51 effects, with no JS/WebGL errors; existing Ghost/Blobby missing-source
  warnings are unchanged. Captures are in `output/fx_showcase/viewer/`.
- All three effects were spawned and captured in isolated New Sorpigal desktop runs using the normal OpenGL
  build. Images were visually reviewed; these checks are not GPU performance measurements:
  [healing](../../../../output/fx_showcase/game/healing.png),
  [fire](../../../../output/fx_showcase/game/ember.png),
  [arcane](../../../../output/fx_showcase/game/arcane.png).
