# Codex brief: HD BODY reference views for the MM9 dwarf townsman PeasantDM3, skin B (mm9_peasantdm3_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_peasantdm3_claude/references_hd/`. Do not
edit any other file, do not run builds, do not call Meshy. Use your built-in image generation tool.

Context: these five views are TEXTURE references that will be projected onto an EXISTING 3D body mesh. That mesh was built
from five approved views of another dwarf (inputs 5-9, the "templates"). MM9's PeasantDM3 wears a DIFFERENT COSTUME on the
SAME body, so each new view must keep its template's figure EXACTLY (silhouette, pose, proportions, arm angle, hand
shape, leg and boot outline, framing, camera, canvas size and light) and change ONLY the costume's design, colours and
materials. Think of it as repainting the clothes on the template images. The HEAD in each view stays exactly as in its
template (it is painted separately later): do not redraw the face, hair or beard.

## Inputs (attached, in order)
1. `references_hd/mm9_views_b.png` — renders of the ORIGINAL Might and Magic IX low-poly model with skin B, five views
   (three-quarter, front, left side, back, right side): COSTUME DESIGN AND COLOUR AUTHORITY. Its faceting, blur, low
   resolution and dark shading are NOT the design.
2. `references_hd/mm9_torso_views_b.png` — closer renders of the same model's torso (front, back, left side).
3. `references_hd/mm9_skin_x4_b.png` — the original 256x256 skin texture enlarged 4x: SURFACE MATERIAL AND COLOUR ONLY.
4. (unused placeholder, same as input 1)
5. `../mm9_peasantdm1_claude/references_hd/00_three_quarter.png` — template for `00_three_quarter.png`
6. `../mm9_peasantdm1_claude/references_hd/01_front.png` — template for `01_front.png`
7. `../mm9_peasantdm1_claude/references_hd/02_back.png` — template for `02_back.png`
8. `../mm9_peasantdm1_claude/references_hd/03_left.png` — template for `03_left.png` (faces IMAGE LEFT)
9. `../mm9_peasantdm1_claude/references_hd/04_right.png` — template for `04_right.png` (faces IMAGE RIGHT)

## Deliverables (true transparent background, 1536x1024 like the templates, unresized returns)
`00_three_quarter.png` (generate FIRST, from template 5), then `01_front.png`, `02_back.png`, `03_left.png`, `04_right.png`
each from its own template plus your selected 00 as an extra input, so all five show the SAME costume. At most ONE
corrective regeneration per view; keep raw returns in `raw/`. Write `generation_runs.json` (id, view, prompt, inputs with
sha256, output path, selected flag, reason, superseded runs, size, alpha extrema) and a `selected_views_review.png`
contact sheet of the five selected views.

## The new costume (skin B, inputs 1-3)
- Tunic: heavy dark CHARCOAL-GREY tweed / knitted wool with fine blue-grey and brown flecks and faint vertical ribbing,
  the SAME cut and outline as the template tunic (short sleeves to the elbow, mid-thigh length, slightly flared below the
  belt). No knotwork bands, no blue.
- Front: the tunic is OPEN at the chest in a long narrow U from the collar down to the belt, showing a plain CREAM /
  pale beige linen shirt underneath (input 2 front). Both edges of the opening carry a narrow OCHRE-GOLD braided
  herringbone (chevron) trim; a dark braided cord with small brown and gold beads runs along the collar round the
  neck; a small round gold brooch at the top of the opening.
- Sleeve ends: a narrow ochre-gold herringbone braid band round each short sleeve end; a similar ochre-gold braid band
  runs round the tunic just above the hem.
- Forearms: the same cream-beige linen undersleeves from the elbow and dark brown leather wrist bands as the template;
  bare hands as the template.
- Belt: wide dark red-brown leather belt with a rectangular silver buckle.
- Legs: rust-brown / brick-brown coarse woven trousers (input 3 lower right).
- Boots: brown suede leather boots with the template's wide folded-down cuff and a small laced X on the cuff front.
- NO medallion, NO pendant, NO necklace cord on the chest (the template's silver medallion and its cord are REMOVED;
  paint the shirt/tunic where they were).

## Common prompt content
Faithful high-definition TEXTURING reference of an EXISTING Might and Magic IX character; semi-realistic game materials
with sharp fine detail (wool fibres and flecks, braid chevrons, linen weave, leather grain, stitching). Even soft neutral
studio light as in the templates: no dramatic light, no strong shadows, nothing baked. Genuine transparent background,
no floor, no shadow, no text.

Per-image checks (re-run before selecting): figure outline, pose, arms, hands, boots and head IDENTICAL to the template
(overlay it mentally: no moved arm, no changed hand, no different head); costume as described; no medallion or cord;
correct side faces the correct image side (03 faces IMAGE LEFT, 04 faces IMAGE RIGHT); true transparent background;
1536x1024.

## Do NOT
- change the head, face, hair or beard from the template; change the pose, arm angle, proportions or framing; add a
  cloak, hood, armour, weapons, jewellery or a medallion; make the tunic purple, blue or brown; stylise as a cartoon;
  crop; add a background, floor, shadow or text.
