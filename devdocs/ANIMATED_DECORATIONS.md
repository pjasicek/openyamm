# Animated decorations

Decorations drawn as 3D models (`DecorationModelSet`, bound in `engine/models/indoor_decorations.yml`,
`decorations.yml` and a world's own manifests) can move (2026-11-10, for MM9's props that play LithTech clips: chest
and coffin lids, bells, levers, the Lich engine, windmill sails, stat stones; first used by Beethoven's coffins).
They stay ordinary decorations: native collision, events, picking, SetSprite and hiding are unchanged.

## Three kinds

| Binding | What moves | Drawn as |
|---|---|---|
| `parts: [<model>, ...]` | rigid pieces (a lid, a bell and its clapper, a lever) | static placements, lit as decorations |
| a `model` with clips | the whole rigid model (a windmill's sails) | its static placement |
| `animated: <model>` | a skinned copy (a banner, a statue made from a creature model) | a model instance, lit as creatures |

- A **part** is authored in its decoration's asset space, on one rigid mesh node (LODs on it) whose clips move it; the
  static renderer draws the node at rest, so a part's placement is `decoration x node(t) x node(rest)^-1`
  (`DecorationModelSet::poseParts`). The binding's `model` is the rest of the prop and its `height` that rest's own
  (the same scale as before the split).
- A **binding model with clips** must have one rigid mesh node; its placement is posed the same way from its rest
  (aims and swings do not apply to it). Its parts then move from the decoration's rest, not from the posed model.
- An **animated** binding keeps its static `model` for picking only (never drawn); each placement is drawn by an
  instance of the skinned model in the world's `ModelInstanceSystem`, created on first use, hidden with its decoration
  (`poseInstances`). Without a clip it shows its rest (bind) pose, which should match the static model.
- All three need a still ground binding (no `swing`, `turn_in` or `mount: wall`).

## Clips

- **Lua** `evt.PlayDecorationClip(cog, clip[, mode])`: the decorations with this SetSprite key (`cog`, the entity's
  `event_id_primary`, else its entity index) play `clip` on every part, model or instance that has it: mode `"once"`
  (default; holds its last frame), `"loop"`, or `"end"` (its last frame at once). An empty clip returns them to rest.
  Runtime only (`EventRuntimeState::decorationClips`, never saved): a map shows a part left open again from its own
  map variables on load with `"end"`.
- **Uses** `use_clips: [<clip>, ...]`: each click that runs a decoration's event starts the next clip of the list,
  held at its end (MM9's Book.scr: openbook, turnpage, turnback, closebook on `mm9_bookflat`). The clicks are counted
  per decoration key (`EventRuntimeState::decorationUses`, runtime only; `DecorationModelSet::noteUses`). A scripted
  clip wins over a use clip, a use clip over the idle loop.
- **Idle** `idle: <clip>`: loops while no script plays a clip (MM9's PropAnim.scr LoopAnim: the windmill, stat
  stones, banners), each placement out of step with its neighbours.
- **Chest lids**: a chest opened by a decoration's click (the click's key is `EventRuntimeState::activeEventDecorationKey`
  while its event runs, carried by `evt.OpenChest` / `SetChestBit Opened`) plays that decoration's `open` clip as the
  chest view opens and `close` when it closes (`openChestDecoration`, `closeChestDecoration`, both world runtimes).
  No map script is involved: every MM9 chest whose binding has a lid part does it.
- Clip names are lower case (the MM9 conversions rename `Open`, `Closed`, `Down` ... to `open`, `close`, `down` ...).

## Making the models (MM9)

`level_generation/props/mm9_prop_parts/scripts/prop_parts.py` splits an installed MM9 prop into its body and parts
from its LithTech raw import (its props project's `work/raw/<raw>/<raw>.glb`): the raw pieces are fitted onto the
finished model's corners (an axis permutation and scale, a baked tilt, ICP), each triangle goes to its piece, pieces
are grouped by motion, and the clips are carried into asset space at 30 Hz. `--install` installs the GLBs and rewrites
every binding of the model (parts, idle, height). Add a prop to its `PROPS` table (and `POSE` when its props project
built it in an animation pose, `TILT` for a tilted variant, `IDLE` for a loop). `scripts/preview.py <prop> [clip]`
draws the motion. The untouched originals are kept in its `work/originals/`.

Skinned props (banners, the Dark Passageway and Thousand Terrors statues, books) go through `scripts/prop_skins.py`
in the same project: the raw import is skinned into the pose the decoration was built in (its props project's POSES,
else the best of rest and every clip's first frame) and fitted onto the finished model; each finished vertex takes the
weights of the raw vertex it lies on; the skeleton is carried into asset space at rest in that pose, with every clip
sampled at 30 Hz. `--install` adds `animated:` (and `idle:`, `use_clips:`) to the bindings.

Dark Passageway's ice statues use the installed MM9 creature models instead (`scripts/ice_statues.py`): the creature
at rest in `Standing`, fitted onto the old statue (height, base, facing), its tier materials replaced by translucent
ice (the creature texture's shading on MM9's icebolt statue skin colours and alpha, blended; no dedicated shadow LODs,
which the loader allows only under opaque geometry), its clips renamed to the MM9 names the map plays (matched by kind
and length). `scripts/statue_overlay.py <statue>` overlays the fit.

Testing: the debug console's `lua <code>` runs a line of Lua as a map event (`lua evt.PlayDecorationClip(412,
[[taunt]], [[loop]])`; the console strips double quotes, so strings go in `[[...]]`).

## Code

`game/maps/DecorationModelSet.{h,cpp}` (parts, whole models, instances, idle, uses), `game/events/EventRuntime.{h,cpp}`
(`evt.PlayDecorationClip`, `decorationClips`, `advanceDecorationClips`, chest lids), the renderers'
`updateDecorationModels` (indoor and outdoor), `GameApplication` (the clock), the world runtimes (chest lids).
