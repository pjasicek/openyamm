# Codex brief: HD HEAD reference views and the open MAW for the MM6 Bloodsucker (bld)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm6_bld_head_claude/references_head/`.
Do not edit any other file, do not run builds, do not call Meshy.

Why: the existing 3D bloodsucker shares one texture over the whole body, so its head and the inside of its tube-shaped
mouth are blurry and dark. These views drive a head-only retexture of the EXISTING head mesh (a long tube snout), and
a painted maw disc for the attack. They must show the SAME head as the accepted full-body HD views, much larger.

Use your built-in image generation, same record format as `../../mm6_bld_claude/references_hd/generation_runs.json`.
Attached inputs, in order:
1. `mm6_bld_claude/references_hd/01_front.png`: accepted full-body HD FRONT view. Identity authority for the head:
   the round tube mouth with its ring of small teeth and salmon-red throat, cyan eyes, teal hide with dark bands,
   ivory spikes. Match it.
2. `mm6_bld_claude/references_hd/03_left.png`: accepted full-body HD view of the creature's LEFT side (the head
   points to the IMAGE LEFT). Shows the long tube snout in profile.
3. `mm6_bld_claude/references_hd/00_three_quarter.png`: the same creature, three-quarter.
4. `mm6_bld/references/attack.png`: ORIGINAL native attack frames (magenta is background, never creature colour).
   The top-middle and top-right frames show the maw fully gaping straight at the viewer. Authority for 04_maw only.

## Deliverables (5 images, transparent background, 1024 x 1024 square, unresized returns)
- `00_front.png`: head straight on, looking INTO the round tube mouth (primary; generate first)
- `01_left.png`: the creature's LEFT profile (pure side view; the snout points to the IMAGE LEFT, like input 2)
- `02_right.png`: the creature's RIGHT profile (pure side view; the snout points to the IMAGE RIGHT)
- `03_back.png`: straight from behind (the back of the head and neck, the snout hidden behind)
- `04_maw.png`: the attack maw, fully gaping, seen straight on (see below)
Generate 01 to 04 with 00 as an additional input so all are the SAME head. Allow at most one corrective regeneration
per view, then move on. Also write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag,
reason) and a `selected_views_review.png` contact sheet.

## Prompt content for 00 to 03 (adapt per view)
TASK CONTEXT: MM6 FANTASY-GAME ASSET RESTORATION. High-definition HEAD-AND-NECK reference of the EXISTING Might and
Magic VI Bloodsucker, for texturing an existing 3D head. The head must be the SAME head as in inputs 1 to 3, shown
large. Not a new design.
Framing: the head and the front part of the neck only, like a sculpted bust: the neck is cut cleanly and squarely
about one head-length behind the eyes (no shoulders, no wings, no legs, no body). The head fills about 70 % of the
frame, centred, generous transparent margins, near-orthographic camera, head level. Transparent background, no floor,
no shadow, no scenery, no text. Even soft neutral studio light that still shows form. Credible fully three-dimensional
sculpt with semi-realistic game materials and sharp fine detail.
Head identity: an eyeless-looking eel-like head that ends in a long, straight, round TUBE snout of even width; the
tube's open end is a round mouth with a thick teal lip ringed by many small sharp ivory teeth pointing inward; inside
the tube a salmon-red throat with fine concentric ridges recedes into darkness. Teal-green hide with fine scales and
dark brown-black transverse bands; a salmon-red underside stripe along the throat; small glowing CYAN eyes set on
both sides behind the tube; a row of small ivory spikes along the top of the head and neck. Same colours as input 1.
Front view 00: looking straight into the tube, which is centred and fills about 45 % of the frame width; the throat
interior must be clearly visible and lit (salmon-red ridges, small ivory teeth on the rim), not a black hole.

## Prompt content for 04_maw
The bloodsucker's attack maw fully gaping, seen straight on, as in the native attack frames (input 4, top middle and
top right), redrawn in high definition in the colours of input 1: a large ROUND disc that fills about 92 % of the
square canvas, centred. Outer ring: thick teal hide with dark bands, with about eight short ivory hooked claws evenly
spaced around the rim, pointing outward. Inner ring: salmon-red flesh. Inside it, about sixteen to twenty long thin
ivory teeth arranged radially, converging toward a small dark throat in the centre. Flat, straight-on, perfectly
round, no perspective, no head or body visible behind it. Transparent outside the disc.

## Do NOT
Change colours (teal hide, dark bands, salmon-red throat, ivory teeth and spikes, cyan eyes); add horns, ears, hair,
jewellery, glow effects or blood; crop the snout, the spikes or the maw; draw a checkerboard, backdrop or halo.

## Checks per image
00: round tube mouth straight on with a visible lit interior and a ring of small teeth; both cyan eyes visible.
01/02: the snout points the stated way; same tube length and spike row; neck cut squarely, no shoulders.
03: back of the head and neck with the spike row; no snout tip visible beyond the head outline.
04: one round disc, hooks on the rim, radial teeth, dark centre; transparent corners.
All: transparent background, 1024 x 1024, same head as 00 and input 1.
