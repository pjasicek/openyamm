# MM5 Troll Grunt — selected master A production

## Permanent source-to-master mapping

| Role | Exact asset |
| --- | --- |
| Original MM5 creature | **Troll Grunt**, Darkside `DARK.CC/056.mon` and `056.att`; monster-table record 56 |
| Original unpacked idle image | [frame_0000.png](../../../../reference/mm4_5_world_of_xeen/unpacked/sprites/dark/056.mon/frame_0000.png) |
| Original design comparison | [MM5 design](../references/mm5_design.png) |
| User-selected new master | **Option A — faithful rendered design**, [A_faithful_render.png](../style_front_v2/A_faithful_render.png), 1024×1536 |
| Selected master SHA-256 | `8749823bcaf39de66b2650e1f588cccca67043e4c79cf870f33e2dea33563f80` |
| Selection authority | User explicitly replied **A**, then requested end-to-end generation based on it |
| Motion/topology reference | MM8 Troll A: descriptor 58, groups `m477*`, textures `m476*`, palette 477 |

The original MM5 creature and the chosen new master above are the lasting identity mapping. Preserve master A's
face, body proportions, reddish hair, muted teal skin, blue vest, plum trousers, rope belt, leather boots, plain
right-hand wooden club, modeled materials and restrained lighting in all generated views and animation poses.
The earlier 160-frame project used a rejected rendering style and is historical work, not the art authority.

## Authorized production scope

160 unique sprites: standing 5, walking 40, attack 40, hit 25, fidget 25, falling/corpse 25. Five stored directions
plus three mirrored aliases follow the MM8 topology. Attack 2 reuses attack. Native MM8 125 ms timing is adapted;
MM5 provided only twelve frontal source frames, so the additional views/actions are newly authored.

Keep full-resolution generated source cells and raw sheets. Measure real sampling against native MM8 logical
geometry, with at least two generated pixels per native pixel; a larger export canvas alone does not pass.
Generate small, detailed action sheets using master A and the matching-view identity. Export transparent aligned
frames, identical-layout soft vest masks, tightly packed atlas pages, placement/animation JSON and an offline viewer.
One decoded native MM5 appearance is established; no invented native palette variants are required.

Production is in progress. Raw generation, exact prompts, measurements, source hashes and selected versions are
resumable checkpoints. This is staged art production; engine installation and runtime integration are separate scope.

## Identity and generation decisions

The exact original selected A supplies the front idle. A background-extraction trial is retained in
`raw/identity_front.png` but is not selected: alpha compositing demonstrated that the original A already has
transparent surroundings, and preserving the user's exact choice avoids unnecessary redraw differences.
`raw/identity_12.png` and `raw/identity_34.png` establish the four additional views. The back vest is a plain blue
cloth panel; hidden MM5 anatomy is an authored interpretation. The selected master is always the first generation
reference, followed by matching-view identity and correctly paletted native motion guides.

Eight-frame actions use four-pose portrait sheets followed by five-pose landscape sheets with one shared
transition pose. Five-frame actions use compact landscape sheets. First/last overlap art is retained and measured,
but only one copy becomes an exported sprite. Attack continuation follows the generated downward strike into
follow-through and recovery; the MM8 reference supplies the action topology and timing, not an exact recovered
MM5 attack. All raw generated sheets and original-size extracted cells remain available.

The logical working canvas adds 32 native pixels of safety padding on each side of the native 256×256 canvas.
The pivot receives the same padding, preserving local placement. The shared authored scale is calibrated from
the standing MM8 troll's 148-pixel vertical extent. Each action sheet receives one anatomical scale, linked through
its overlap pose. The ochre waist rope fixes the actor root so alternating planted feet cannot cause horizontal
registration drift; native bottom-contact deltas are retained. Masks recolor only the enhanced blue vest.
