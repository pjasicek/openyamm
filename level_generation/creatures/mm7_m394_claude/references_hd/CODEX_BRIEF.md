# Codex brief: HD modelling references for the MM7 Sea Monster / Giant Shark (m394)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm7_m394_claude/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.

## Inputs (attached in this order)

1. `references_hd/native_views.png` — ORIGINAL native MM7 sprite views, enlarged 2x with nearest neighbour, left to
   right: front (head-on), front three-quarter, its right profile (facing image right), rear three-quarter, back
   (tail-on). Magenta is background, not creature. Design, anatomy, proportions and colour authority.
2. `references_hd/native_palettes.png` — the profile in the three tier palettes (teal-blue, lavender, red skin).
   Generate the LEFT, TEAL-BLUE / steel-blue version.
3. `references_hd/native_actions.png` — native attack (it rears up with the jaws wide open), swimming profile frames,
   hit and death (belly up). Anatomy evidence only (jaws, teeth, white belly, fin shapes).
4. `level_generation/creatures/mm7_m394/aligned_2x/m394sa1.png` — restored 2x three-quarter frame, SURFACE MATERIAL
   ONLY. Never sets the design.
5. (second run only) the selected `references_hd/00_three_quarter.png`.

## Deliverables

Five images in `references_hd/`, one shark each, the whole animal from snout to tail tip, unresized returns,
1536x1024 LANDSCAPE, true transparent background, no water, no bubbles, no floor, no shadow, no text:

| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter from its RIGHT side (the head toward image right-front, we see the right flank and some of the face), camera slightly above the body's level |
| `01_front.png` | head-on, from the front (snout toward the camera) |
| `02_back.png` | from behind (tail toward the camera) |
| `03_left.png` | its LEFT side, exact profile: the snout points to image LEFT |
| `04_right.png` | its RIGHT side, exact profile: the snout points to image RIGHT |

Run 1: generate `00_three_quarter.png` only, check it, at most one corrective regeneration, then stop.
Run 2 (a separate invocation): generate 01–04 with the selected 00 as an input so all five show the same shark,
pose and proportions. At most one corrective regeneration per view. Front and back views must still show the whole
animal (foreshortened), not a crop.

## Prompt content (adapt per view)

TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: a faithful high-definition reconstruction of the EXISTING Might and
Magic VII sea monster (a giant great-white-type shark) from the supplied original sprites, as a 3D modelling
reference. Not a new design. Use case: faithful 3D creature modelling reference sheet view. Near-orthographic camera,
even soft neutral studio light (no dramatic lighting, no caustics, no rim light: the light is baked into the
texture), semi-realistic game materials, sharp fine detail, a credible fully three-dimensional animal.

Identity (from the native sprite): a huge, heavy-bodied shark like a great white: a thick torpedo body, a conical
snout, a big mouth slightly open showing rows of sharp white triangular teeth and pink-red gums, small dark eyes,
five gill slits on each side behind the head. The back and flanks are smooth TEAL / steel-blue skin with darker
mottling and faint lighter streaks; a sharp boundary to the clean WHITE belly and underside of the snout. Fins: one
tall triangular first dorsal fin at mid-back, a small second dorsal fin and a small anal fin near the tail, two
long broad pectoral fins angled down and back behind the gills, two small pelvic fins under the belly, and a tall
crescent tail fin whose upper lobe is longer than the lower. Fins share the blue skin colour with paler tips.

Pose (identical in all five views, a neutral modelling pose): swimming straight and level, the body and tail
STRAIGHT (no S-bend), the tail fin vertical, pectoral fins spread out to the sides and slightly down so they are
clearly separated from the body, mouth slightly open with the teeth visible.

Do NOT: add a second dorsal fin pair, extra fins, legs, scars, harpoons, water splashes, bubbles or blood; change the
colours (no grey-brown, no lavender, no red skin: those are other tiers); bend the body; crop the snout or tail.

## Per-image checks (re-run before you select a view)

Whole shark inside the frame with margins; teal/steel-blue back with a crisp white belly; one tall first dorsal fin,
a small second dorsal and anal fin, two pectoral and two pelvic fins, crescent tail with a longer upper lobe; open
mouth with white teeth and pink gums; five gill slits; straight level body; transparent background; for 01–04 the
same shark, pose and proportions as the primary; side views: in `03_left` the snout points to image LEFT, in
`04_right` to image RIGHT. Stop after one corrective regeneration per view and record what remains.

## Records

`references_hd/generation_runs.json`: one entry per generation (id, view, prompt, input paths with sha256, output
path, selected flag, reason, superseded runs). After run 2, a contact sheet `references_hd/selected_views_review.png`
with the five selected views.
