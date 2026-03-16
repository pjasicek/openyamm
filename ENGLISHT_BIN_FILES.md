# EnglishT BIN Files

This document describes the `assets_dev/Data/EnglishT/*.bin` files currently known in OpenYAMM.

The purpose is:

- identify what each file is for
- note the binary format shape at a practical level
- show which systems reference the file
- show which other tables or assets it links to

This is a clean-room working reference derived from local assets and reference behavior, not copied runtime code.

## Load Order

A useful mental model is:

1. map files place instances or refer to ids
2. `EnglishT/*.bin` tables resolve those ids into definitions
3. definitions resolve into frame sets, texture names, sounds, or gameplay metadata
4. those names resolve to actual assets under `Data/bitmaps`, `Data/sprites`, audio containers, and so on

## Relationship Summary

- World decorations:
  `ODM/BLV placed decoration -> ddeclist.bin -> dsft.bin -> Data/sprites/*.bmp`
- Dynamic sprite objects, projectiles, dropped items:
  `Sprite object / object desc id -> dobjlist.bin -> dsft.bin -> Data/sprites/*.bmp`
- Monsters:
  `monster id -> dmonlist.bin -> sprite names / animation families -> Data/sprites/*.bmp`
- Overlays:
  `overlay id -> doverlay.bin -> dsft.bin -> Data/sprites/*.bmp`
- Animated world textures:
  `face texture name -> dtft.bin -> Data/bitmaps/*.bmp`
- Outdoor terrain:
  `outdoor tile id / tileset lookup -> dtile.bin / dtile2.bin / dtile3.bin -> Data/bitmaps/*.bmp`
- UI icons:
  `icon animation name/id -> dift.bin -> icons asset set`
- Portrait animation:
  `portrait id -> dpft.bin -> portrait face textures`
- Sounds:
  `sound id -> dsounds.bin -> sound asset name`
- Chests:
  `chest type id -> dchest.bin -> chest UI size / texture selection`

## File List

### `dchest.bin`

Purpose:

- chest type table
- describes chest archetypes used by chest inventory UI and chest appearance selection

Practical binary shape:

- fixed-size records
- reference shape is equivalent to a `ChestData_MM7`-style record
- fields are effectively:
  - name
  - width
  - height
  - texture id

Important notes:

- some stored size fields are historically odd or unreliable
- chest presentation logic may still treat part of this as constrained by game rules rather than trusting the file blindly

Referenced by:

- chest/inventory systems
- chest UI texture selection

Referenced from:

- chest instances in map/gameplay state

Links to:

- chest texture ids, typically resolving into chest icon/bitmap assets

### `ddeclist.bin`

Purpose:

- decoration definition table for static map decorations
- used for plants, trees, torches, signs, decorative interactives, markers, and many map-placed billboard objects

Practical binary shape:

- `uint32` record count
- followed by fixed-size records, `84` bytes per entry in MM7/MM8-era data
- practical fields:
  - `internalName[32]`
  - `hint[32]`
  - `type`
  - `height`
  - `radius`
  - `lightRadius`
  - `spriteId`
  - `flags`
  - `soundId`
  - colored light bytes

Referenced by:

- `ODM` and `BLV` placed decoration/entity records via decoration id
- collision and interaction systems
- decoration sound/light setup
- billboard rendering for static world decorations

Referenced from:

- outdoor and indoor placed decoration records
- event logic that mutates decorations by id/name

Links to:

- `dsft.bin` through `spriteId`
- `dsounds.bin` through `soundId`
- `Data/sprites/*.bmp` indirectly through `dsft.bin`

### `dift.bin`

Purpose:

- icon frame table for UI/icon animations

Practical binary shape:

- sequence of fixed-size frame records
- practical fields:
  - texture name
  - frame flags
  - animation name
  - animation length
  - frame length

Referenced by:

- UI systems
- spellbook/inventory/turn-order/interface icon animations

Referenced from:

- UI animation lookups by animation name or icon id

Links to:

- icon texture assets, not world billboard sprite textures

### `dmonlist.bin`

Purpose:

- monster descriptor table
- defines how monster families map to sprite names, sounds, and gameplay-side physical properties

Practical binary shape:

- fixed-size typed monster records
- practical fields include:
  - monster height/radius
  - movement speed
  - hit radius
  - tint
  - sound ids
  - internal monster name
  - sprite-name set for animation families

Referenced by:

- actor creation and monster runtime setup
- monster rendering
- monster sound selection
- projectile/spell behavior tied to monster descriptors

Referenced from:

- actor/monster ids in maps and spawn systems

Links to:

- `Data/sprites/*.bmp` through monster sprite-name families
- `dsounds.bin` through sound ids

Important note:

- unlike `ddeclist.bin` and `dobjlist.bin`, this is not mainly an id-to-single-`spriteId` table
- it is more of a monster-family render/gameplay descriptor table

### `dobjlist.bin`

Purpose:

- object descriptor table for dynamic sprite objects
- covers projectiles, dropped items, spell sprites, and similar dynamic billboarded objects

Practical binary shape:

- `uint32` record count
- followed by fixed-size records, `56` bytes per entry in MM7/MM8-era data
- practical fields:
  - unused/name field
  - object id
  - radius
  - height
  - flags
  - `spriteId`
  - lifetime
  - trail color
  - speed

Referenced by:

- dynamic sprite object runtime
- projectile and dropped-item rendering
- collision and pickability logic

Referenced from:

- sprite object instances via object descriptor id
- item/projectile creation logic

Links to:

- `dsft.bin` through `spriteId`
- `Data/sprites/*.bmp` indirectly through `dsft.bin`

### `doverlay.bin`

Purpose:

- overlay descriptor table
- used for temporary overlays/effects associated with game objects or UI-like effect rendering

Practical binary shape:

- fixed-size records, effectively:
  - overlay id
  - overlay type
  - sprite frameset id
  - frameset group

Referenced by:

- active overlay runtime
- spell/effect overlay playback

Referenced from:

- overlay trigger/effect systems

Links to:

- `dsft.bin` through sprite frameset id
- `Data/sprites/*.bmp` indirectly through `dsft.bin`

### `dpft.bin`

Purpose:

- portrait frame table
- drives animated character portrait faces in UI

Practical binary shape:

- fixed-size records
- practical fields:
  - portrait id
  - texture index
  - frame length
  - animation length
  - frame flags

Referenced by:

- character portrait UI
- talking/idle portrait animation logic

Referenced from:

- character portrait selection and portrait animation systems

Links to:

- portrait face textures, not world sprites

### `dsft.bin`

Purpose:

- sprite frame table
- central world-sprite animation/direction table

Practical binary shape:

- header:
  - `uint32 frameCount`
  - `uint32 eframeCount`
- `frameCount` sprite-frame records
- `eframeCount` extra index records used for sprite-name lookup

Frame record shape:

- `60` bytes per entry in MM7/MM8-era data
- practical fields:
  - `spriteName[12]`
  - `textureName[12]`
  - hardware sprite ids array in original engine layout
  - fixed-point `scale`
  - `flags`
  - `glowRadius`
  - `paletteId`
  - `paletteIndex`
  - `frameLength`
  - `animationLength`

Referenced by:

- decoration billboards
- dynamic sprite objects
- overlays
- monster/projectile/spell sprite rendering

Referenced from:

- `ddeclist.bin` through decoration `spriteId`
- `dobjlist.bin` through object `spriteId`
- overlay tables through sprite frameset id
- spell/monster systems through sprite ids or sprite-family lookups

Links to:

- `Data/sprites/*.bmp`
- one sprite id can resolve to:
  - one image for all octants
  - 3-image directional layout
  - mirrored directional variants
  - chained animation frames

Important note:

- this is the key table for billboard rendering semantics
- if sprite billboards look wrong, `dsft.bin` parsing and its flag interpretation are the first things to verify

### `dsounds.bin`

Purpose:

- sound metadata table
- maps sound ids to sound names/types/flags

Practical binary shape:

- fixed-size sound info records
- practical fields:
  - sound file name
  - sound id
  - type
  - flags
  - extra sound data fields

Referenced by:

- audio lookup and playback
- monsters, decorations, and gameplay systems that carry sound ids

Referenced from:

- `ddeclist.bin`
- `dmonlist.bin`
- gameplay code using sound ids directly

Links to:

- audio assets in the game sound container set

### `dtft.bin`

Purpose:

- texture frame table for animated world textures
- separate from `dsft.bin`, which is for sprites

Practical binary shape:

- sequence of texture-frame records
- practical fields:
  - texture name
  - frame length
  - animation length
  - frame flags

Referenced by:

- animated face textures on `BLV` / `ODM` geometry
- animated bitmap-based world materials

Referenced from:

- geometry faces by texture name or derived animation id

Links to:

- `Data/bitmaps/*.bmp`

### `dtile.bin`

Purpose:

- base outdoor terrain tile descriptor table

Practical binary shape:

- sequence of tile descriptor records
- practical fields:
  - texture name
  - tileset
  - variant
  - tile flags

Referenced by:

- outdoor terrain tile lookup
- outdoor terrain generation and rendering
- terrain water/shore/transition classification

Referenced from:

- outdoor map tile ids and tileset/variant logic

Links to:

- `Data/bitmaps/*.bmp`

### `dtile2.bin`

Purpose:

- second outdoor terrain tile descriptor bank

Practical binary shape:

- same kind of tile descriptor records as `dtile.bin`

Referenced by:

- outdoor terrain lookup when the outdoor map’s master-tile setting selects bank 2

Referenced from:

- `ODM` master-tile selection and tileset lookup indices

Links to:

- `Data/bitmaps/*.bmp`

### `dtile3.bin`

Purpose:

- third outdoor terrain tile descriptor bank

Practical binary shape:

- same kind of tile descriptor records as `dtile.bin`

Referenced by:

- outdoor terrain lookup when the outdoor map’s master-tile setting selects bank 3

Referenced from:

- `ODM` master-tile selection and tileset lookup indices

Links to:

- `Data/bitmaps/*.bmp`

## Practical Notes For OpenYAMM

Recommended implementation order for sprite/billboard work:

1. `ddeclist.bin`
2. `dsft.bin`
3. outdoor/indoor decoration billboards
4. `dmonlist.bin`
5. monster billboards
6. `dobjlist.bin`
7. dynamic object/projectile sprites

Recommended implementation order for texture/material work:

1. `dtile.bin` / `dtile2.bin` / `dtile3.bin`
2. outdoor terrain
3. `dtft.bin`
4. animated world textures

Keep these as original authoritative source files for now.

Do not convert them into JSON/CSV as the primary source yet.
Parse them into typed runtime structures and only add export/debug dumps later if needed.
