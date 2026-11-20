# Codex brief: HD reference views of the MM9 Giant's war mallet (mm9_giant_claude, third pass)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_giant_claude/references_mallet/`. Do not edit any other file, do
not run builds, do not call Meshy. Use your built-in image generation tool. The authority is the ORIGINAL Might and Magic IX 3D mallet with its
skin, shown in renders of that model. This is a fantasy video-game prop (a giant's two-handed war mallet) restored for a game mod; the images
are the master for a 3D model and its texture.

## Inputs (attached, in order)
1. `mm9_mallet_views_a.png`: renders of the ORIGINAL low-poly mallet, standing upright, five views left to right: three-quarter (from the
   front-right, slightly above), front, left side, back, right side. Grey is background. Design, layout and proportion authority. Faceting,
   blur and low resolution are NOT the design.
2. `mm9_mallet_heads.png`: close renders of the head: the oak tier (left), the steel tier (middle), the steel tier's end face (right, the
   engraved round plate).
3. `mm9_mallet_skin_x4_a.png`: the original 128x128 skin of the oak tier enlarged, SURFACE MATERIAL AND COLOUR ONLY.
4. `mm9_mallet_skin_x4_b.png`: the steel tier's skin enlarged, for the engraved end plate only.
5. `proportion_template_front.png`: a flat grey silhouette of the mallet in the FRONT view at the EXACT proportions required (head, top
   spike, shaft, pointed cap). It is a proportion guide only (no material, no shading).
6. `superseded/00_three_quarter_v1.png`: the first run 1, the design to keep (not its proportions or background).
7. (run 2 only) the selected `00_three_quarter.png`.

Note (second run 1, 2026-11-01): a first run 1 (`superseded/00_three_quarter_v1.png`) had a beautiful design but the shaft only 2.9 x the
head's height and a glowing halo in the background. Keep its design and detail, and fix both: the shaft below the head is 4.1 x the
head's height (template input 5), and the background is fully transparent, with no glow, vignette or dark backdrop.

## Deliverables (true transparent background, no floor, no shadow, no text, unresized returns, 1024x1536 PORTRAIT)
| File | View |
|---|---|
| `00_three_quarter.png` | three-quarter from the front-right, slightly above (as input 1 view 1) |
| `01_front.png` | straight front: the head's long side faces the camera, its long axis horizontal across the image |
| `02_back.png` | straight back |
| `03_left.png` | pure 90-degree side from the left: the head seen end-on (its hexagonal end face) |
| `04_right.png` | pure 90-degree side from the right: the other end face |

Run 1: generate `00_three_quarter.png` only, then stop. Run 2 (separate run): generate 01-04 with the selected 00 as an additional input so all
views are the SAME mallet with the SAME proportions and colours. At most ONE corrective regeneration per view; then select the better and note
any residual fault. Keep raw returns in `raw/`. Write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag,
reason, superseded).

## The mallet (detailed, realistic hand-painted game art, sharp, high detail, true to input 1's design)
- Orientation in every view: standing upright, shaft vertical, head at the TOP, the whole mallet in frame with a small margin, centred.
- Proportions (keep exactly, as the template, input 5; MEASURE them in your result before saving): the head is a long HEXAGONAL PRISM lying horizontally across the top of the shaft: its cross-section is an elongated
  hexagon with a broad flat TOP face and a broad flat BOTTOM face and two pairs of slanted faces meeting at a ridge at the front and at the back
  (exactly as input 1's left view). Head length (left to right) = 1.55 x its height (top to bottom); its depth (front to back, ridge to ridge)
  = 1.15 x its height. The shaft below the head is 4.1 x the head's height long; the shaft is ROUND and straight, its diameter 1/6 of the head's
  height (a thick two-handed haft).
- Head material: dark reddish-brown oak in long planks running along the head's length, visible grain and plank seams, slightly worn edges.
- Two broad dark-iron bands wrapped right round the head near each end (each band inset about 1/7 of the head's length from its end, about 1/10
  of the head's length wide), with round iron rivets and small pointed chevron studs on them as in input 1/2.
- Each hexagonal END face: a large round dark-iron plate engraved with a Celtic knot (as input 2 right and input 4), covering most of the face,
  with an iron rim round the hexagon's edge.
- Top of the head: a small square iron pyramid spike at the centre where the shaft comes through.
- Shaft from the head down: a short iron collar under the head; the upper third wrapped in dark leather with three thin bright iron rings
  (input 1); the middle third plain light ash wood with straight grain; the lower third a dark leather grip wrap with visible spiral binding;
  at the bottom an iron ferrule ending in a short pointed iron cap.
- Colours as input 1 and 3: dark red-brown oak, near-black iron with bright worn edges, dark brown leather, light tan ash.

Camera: near-orthographic, even soft studio light, no drama, no cast shadows, no rim light.

Do NOT: make the head square or round in section (it is a hexagon); bend or taper the shaft; add spikes other than the small top pyramid;
add blood, text, decals or a background; crop the mallet; copy faceting or the render's dark sheen.

Per-image checks (redo at most once): whole mallet in frame, head at the top; true alpha; hexagonal head section visible in the three-quarter
and side views; two iron bands near the head's ends; engraved round iron plates on the end faces; round straight shaft with the three-part
wrapping and the pointed iron cap.
