# MM8 Wasp Warrior m556 — native study and production decisions

Native authority: `work/native_source_receipt.json`, `work/native_timing.json`, original BMPs and
`../mm7_mm8_packed_outline/session_mm8_05/mm8_m556/redo_2x/references/*_sheet_native.png`.
Descriptors 118/119/120 are Wasp Warrior A/B/C; gameplay names Worker/Sentry/Warrior; palettes 557/558/559.
All are flying melee fighters, with no missile or spell. Views 0–4 are drawn; 5–7 mirror. Death/corpse use view 0;
the unused side death supplies depth evidence, not a new played native direction.

## Observed appearance

Long vertical insect head, two curved antennae, lateral green compound eyes, gold-black hard chitin,
slender thorax and narrow petiole, long striped tapering stinging abdomen. Six limbs: upper grasping arms,
short middle pair, long lower legs with green greaves. Green armor cap above abdomen. Two visible long amber-brown
veined wings at independent upper-back roots. Sword in anatomical LEFT hand; round green-rimmed dark shield on
RIGHT arm (viewer left). Neither equipment item is optional despite its absence in body modeling references.
Digit count is obscured by grips; generated claw digits and hidden joint surfaces are reconstruction inferences.

## Timing and motion

| Native action | Time | Authored role / motion |
|---|---:|---|
| Standing and Walk, same W group | .625 s | Fly: two coordinated wing strokes, unequal downstroke holds; torso counter-bob, abdomen and legs lag |
| Attack and Attack2, same A group | .875 s | Attack: sword arm raises sideways/up, then cuts diagonally across front; shield guards; thorax dips, abdomen counters |
| Hit | .625 s | Rearward thorax/head recoil, shield raised, sword down; abdomen curls under body, wing bank |
| Fidget | .875 s | Flight continues, head/thorax alert lean and small arm adjustment |
| Death | .875 s | Backward recoil and limb spread, abdomen curls forward, body rolls onto back/side; wings settle by body |
| Corpse | held | Dead: final grounded death pose, equipment retained |

Source standing frames a,b,c,d,f (e unused), each .125 s. Attack/fidget/death a–g, hit a–e.
Render/export at 48 fps to represent .125-s source holds exactly and supply smooth in-betweens.
Attack impact is authored near the MM8 native end (.875 s), with short follow-through; native gameplay timing is unchanged.
FlyFast is a mild forward-lean version if required by runtime run role, not a native additional action.
No casting clip is invented: runtime cast role maps Attack for this non-caster.

## Rig and review plan

Measure actual returned components and junctions. Use rigid exoskeleton weights on separate chitin segments;
blend only neck/petiole/true joint bridges. Independent root and distal flex for each wing, three arm and leg joints,
measured claw pivots for grips, segmented antennae, short abdomen chain. Keep shoulder swing independent of wingbeat.
Flying Devil supplies coordinated wing/body counter-motion and leg lag, not bat-wing finger anatomy or its old texture defaults.
Sword and buckler are simple locally modeled props, separate supported runtime attachments; fit grip dimensions to this mesh.
Review all actions at normal/slow speed, both hands, wing clearance, joint bridges, final corpse floor contact and all three tiers.
Rig/deformation gates precede complete animation expansion. Retain technical completion separately from user art acceptance.

## Delivery scope

Reach project blend/portable GLB, shared texture maps + native palette ramps, color/shadow LODs, separate equipment,
MM8 source/runtime installs and actors.yml, focused actor regression, existing review viewer, and same-camera indoor/outdoor
native comparisons. No new renderer capability, raw animation-library files, directional sprite export, or commit.
No added hover offset: calibrate flight silhouette area and body height against native frames and verify ceiling clearance.

## User sword/slash correction · m556_slash_v2

Use the current README and `review/slash_path.json` for delivered choreography. The anticipation coils the thorax
and lifts the sword to the anatomical left at 0.65 s. Release cuts across/front/down through native impact at
0.875 s; the body continues into the 1.01 s follow-through and returns by 1.25 s. The head counter-rotates,
abdomen follows with delay, and shield draws aside. A 90° wrist roll keeps the blade edge aligned with the sweep.
The revised sword preserves the existing grip pivot; all other clips retain their original channels.
