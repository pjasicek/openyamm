# MM6 Goblin — baseline identity and parts plan

Restarted 2026-09-23 using both documents under `codex/meshy/`. This is a new reference/geometry run;
previous Meshy models and custom animations are retained separately and are not the new starting mesh.

## Resolved source

- World: MM6. Baseline Goblin, merged monster ID **550**, Picture/InternalName **BGoblin A**.
- Siblings: 551 / BGoblin B / Goblin Shaman; 552 / BGoblin C / Goblin King. This run does not select either variant.
- Descriptor: height 145, radius 56, movement speed 140, tint `0x00e7e7e7`. These are game table values, not meters.
- Baseline gameplay: grounded, physical melee attack, no spell in the selected stats row.
- Original art: `assets_dev/engine/sprites/gob*.bmp`, restricted to the 59 filenames in `source/native_manifest.json`.
  Every original BMP hash was rechecked against the prior audit; all 59 matched. `goblet.bmp` is unrelated.
- Descriptor frame groups live in `assets_dev/engine/rendering/sprite_frame_data_common.yml`.
  **Do not use `monsters/m550.yml` merely because the registry ID is 550**: that file describes another sprite family.
- Current checkout's goblin rows point to `atlas:mm6_gob/...`; the corresponding restored presentation is
  `assets_dev/engine/sprites_new/mm6_gob/manifest.json` and its atlas PNGs. Original BMPs remain the native authority.
  `source/frame_groups.json` captures current rows; `source/native_manifest.json` captures the original audit.
- Frame scale is 0.649994, palette ID 745 in current base rows; mirroring and single-image flags are recorded per row.
  Original images use palette index zero as transparency. Palette, descriptor tint and world lighting are separate
  from the neutral reconstruction images; the tint was not painted into these references a second time.
- Table, sprite resolution, mounting and indoor/outdoor billboard paths were inspected. Runtime-model integration
  is a later stage; this reference preparation makes no claim that an importer or performance budget is validated.

## Observed identity

Lean muscular olive-green biped with narrow waist, long forearms, clawed hands and long forward-projecting feet.
Compact angular bald head; heavy brow, small yellow eyes, short broad nose, projecting jaw and irregular teeth.
Tall pointed ears and a backward-tapering rear skull. Small gold ear jewelry is visible in the native art.

Dark riveted V-shaped chest gorget, separate modest spiked shoulder caps, forearm bracers and shin guards.
Abdomen, upper arms, thighs and most of the back remain exposed. Two small upper-back plates; no full back armor.
Brown belt, overlapping leather strips ending on the upper thigh, small pouch at the sword-hand/right hip.

The original weapon is a long curved single-edge sword with a gold guard, carried in the anatomical RIGHT hand.
Its shortened frontal shape is foreshortening. The free LEFT hand counterbalances the slash and shields the face
in the hit reaction. Attack crosses the torso, rises diagonally, cuts across/down and recovers. Death ends prone.

## Reconstruction assumptions and parts

- Body plan: humanoid biped, opaque skin/leather/iron. Relaxed A-pose, head level, straight wrists, open empty hands.
- BODY includes armor and belt/pouch in the reference set. Inspect any reconstruction fusion at shoulder, wrist,
  knee, skirt or straps in the returned master; armor behavior and grip are explicit later finishing tasks.
- SWORD remains a separate rigid asset for right-hand attachment. Existing weapon studies are useful references;
  validate its proportions against the new body before reuse. The unarmed upload does not remove it from the design.
- Reference hands resolve ambiguous native digits as four fingers plus an opposed thumb; toes are reconstructed as
  four prominent forward claws. The initial prompt asked for three, but the output resolves four. This is an explicit
  interpretation of ambiguous small sprites, not an observed exact anatomical count.
- Three right-ear hoops and restrained rivet layout are reconstruction choices. Native jewelry count and microdetail
  are not sufficiently resolved to claim exact recovery. Keep asymmetry consistent across views.
- Skull depth, palm surfaces, armor thickness and hidden strap routes are conservatively inferred. The old restoration's
  long studded spine strap was excluded because the native evidence does not establish it.

## Primary forms to preserve in remesh

1. Compact face, low brow, pointed ears and tapered rear skull.
2. Lean waist/torso and characteristic limb proportions.
3. Separate shoulder/bracer/shin silhouettes with the existing few spikes.
4. Open hand/thumb spaces and long clawed feet.
5. Broad overlapping leather skirt strips and right-hip pouch.
6. Separate curved sword silhouette after attachment.

Skin pores, shallow wear, tiny rivets and leather grain belong mainly in maps. No added ornamental clutter.

## Action mapping for this baseline

| Descriptor slot | Group | Native duration | Intent |
| --- | --- | --- | --- |
| Standing | gobsta | held, raw 2 | restrained armed stance |
| Walking | gobwaa | 0.75 s / 6 frames | alternating contacts and opposing arm motion |
| AttackMelee | gobata0 | 0.75 s / 6 frames | cross-body slash |
| AttackRanged | gobata0 | same alias | existing presentation alias; baseline has no ranged spell |
| GotHit | gobwia0 | 0.75 s / 6 frames | recoil and left forearm shields face |
| Dying | gobdya0 | 0.625 s / 5 frames | bow, knees fold, collapse prone |
| Dead | gobdyf0 | held, raw 2 | final prone corpse |
| Bored | gobfia | 0.75 s / 6 frames | restrained fidget |

Raw frame unit is 62.5 ms. Standing/walking have five source octants and three mirrored octants; original action
families have fewer views. Preserve missing-view uncertainty. Render genuine directions for the finished asymmetric
3D character rather than moving the sword to the left hand through mirroring.
