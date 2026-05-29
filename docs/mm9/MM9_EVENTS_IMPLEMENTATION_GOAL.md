# MM9 Events Implementation Goal

Goal: import and execute MM9 map behavior losslessly as source-authored events, with generated per-map event data and
Lua, while preserving existing MM6-MM8 behavior.

## Target Artifacts

For each MM9 map:

- `assets_dev/worlds/mm9/maps/<map>.raw_objects.yml`
  - Existing source/debug truth from DAT objects. This must remain the lossless reference.
- `assets_dev/worlds/mm9/maps/<map>.events.yml`
  - Generated normalized event sidecar.
  - Contains source objects, mechanisms, trigger volumes, general interactions, bindings, scripts, unresolved refs, and
    validation metadata.
- `assets_dev/worlds/mm9/events/<map>.lua`
  - Generated executable map behavior.
- Optional `assets_dev/worlds/mm9/events/<map>.mechanisms.lua`
  - Generated executable mechanism-specific behavior if splitting Lua files proves cleaner.

## Core Requirements

- Preserve every raw object index from `raw_objects.yml`.
- Preserve every decoded raw object property by raw reference and normalized field where known.
- Preserve all script names, script params, trigger slots, message names, movement values, sounds, flags, and unknowns.
- Generate deterministic `<map>.events.yml` files for all MM9 maps.
- Generate Lua from parsed MM9 script IR; generated Lua is executable output, not the only source of truth.
- Bind source event objects to runtime targets: BLV face groups, ODM bmodels, model instances, trigger volumes,
  collision volumes, water volumes, ladder volumes, and script-only objects.
- Keep unresolved targets explicit. Do not guess silently.
- Keep ODM/BLV as geometry/runtime targets, not authoritative MM9 behavior storage.
- Keep MM6-MM8 map loading, events, editor behavior, and saves unchanged unless a map explicitly declares MM9 event data.

## Runtime Goal

At game load, an MM9 map should load:

```text
static scene/ODM/BLV geometry
+ <map>.events.yml
+ generated per-map Lua
= executable MM9 map behavior
```

The runtime should build a source object registry, dispatch named messages, execute built-in mechanisms directly from
`events.yml`, and let generated Lua drive scripted behavior through engine APIs.

## Editor Goal

The editor should load `<map>.events.yml`, show source objects and bindings, highlight bound faces/bmodels/model
instances/volumes, display trigger/message graph edges, surface unresolved diagnostics, and preview implemented
mechanism states. Editor saves must not edit generated raw object data directly.

## Validation Goal

Validation across all MM9 maps must distinguish data loss from unimplemented runtime behavior:

- data loss is a failure;
- unresolved or unimplemented behavior is an explicit diagnostic;
- regenerated event sidecars are deterministic;
- existing MM6-MM8 behavior remains covered by regression tests.
