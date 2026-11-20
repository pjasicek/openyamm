# Codex brief: loot satchel v2 references (concept E, shared sack, six tiers)

Scope: image generation only. Write ONLY into `level_generation/props/loot_satchel_claude/v2/references_hd/`.
Do not edit any other file, do not run builds, do not call Meshy.

Use your built-in image generation. Attached inputs, in order:
1. `v2/references_hd/concept_E.png` - the USER-APPROVED design sheet ("E: material plus glow"). It is the authority for
   the sack's shape and for the materials of tiers 1-4. The user changed tiers 5 and 6 (see below).
2. `references_hd/native_gold_piles.png` - original Might and Magic VI sprites (magenta background), authority for the
   game's warm, saturated, semi-realistic prerendered look.

These images become ONE 3D mesh (from the master) that is then textured six times from each tier's four views. So the
silhouette must be IDENTICAL in every image of the same view, and only the material may change between tiers.

## The shared sack (all tiers)
A plump drawstring sack like concept E's top row: rounded, slightly pear-shaped body with a flat base resting on the
ground, a gathered ruffled neck opening at the top (closed, nothing visible inside, NO coins anywhere), a twisted cord
tied twice around the neck, a round flat clasp medallion (about one fifth of the body width) on the cord knot at the
FRONT centre, and two short cord ends with round bead/tassel tips hanging down the front, lying against the body (not
dangling free). Simple strong silhouette for a ~900-triangle game prop. No straps, no buckles, no spilled items.

## Tier materials
1. coarse undyed beige burlap, visible weave, natural jute cord, plain wooden clasp disc and wooden beads.
2. patched green wool (moss green, darker patches with coarse stitching), brown cord, plain bone clasp disc.
3. tanned rust-brown leather with stitched seams, brown leather cord, plain brass clasp disc and brass beads.
4. deep blue dyed leather with stitched seams, twisted gold cord, brass clasp disc, round gold bead ends.
5. PURPLE (royal violet) velvet with rich gold embroidery (scrolling vines) over the body, gold cord and tassels,
   gold clasp with a large faceted VIOLET gem that glows softly.
6. CRIMSON velvet (deep, saturated blood red; clearly redder and darker than tier 3's rust leather) with dense gold
   embroidery, gold cord and tassels, gold clasp with a large faceted warm gold-white AMBER gem that glows brighter
   than tier 5's.
Neighbouring tiers must contrast clearly in hue and value; tier 2's green must not resemble any other tier.

## Deliverables (transparent background PNG, 1024 x 1024 square, unresized returns)
- `master/00_three_quarter.png` - tier 3 (rust leather) sack, camera about 35 degrees to the RIGHT of the front and
  about 30 degrees above the ground; the whole silhouette, the ruffled neck, the cord, the clasp and both bead ends
  clearly visible. Generate this FIRST. It alone becomes the 3D mesh.
- For each tier N = 1..6: `tN/01_front.png`, `tN/02_back.png`, `tN/03_left.png` (the sack's own left side toward the
  camera), `tN/04_right.png` (the sack's right side), camera about 20 degrees above the ground. Generate tier 3 first,
  with the master as input; then every other tier with the master and the matching tier-3 view as inputs, so each
  view has the SAME silhouette, framing, size in frame, camera and light as tier 3, and only the material differs.
Every image: the sack centred with about 15 % margin on every side, the same size in frame, near-orthographic camera,
even soft neutral studio light from above (no dramatic light, no coloured light, the gem glow only as a soft local
halo on the gem itself), NO floor, NO ground plane, NO cast shadow, no text.

Also write `generation_runs.json` (id, prompt, inputs with sha256, output path, selected flag, reason, superseded
runs) and `selected_views_review.png` (7 rows: master, then tiers 1-6; columns = views).

## Checks before selecting an image (regenerate on failure)
- same silhouette as the master/tier-3 view of the same angle: body proportions, neck height, cord, clasp position,
  bead ends; nothing cropped; transparent background with clean edges;
- correct tier material; no coins, no items inside the neck, no straps or buckles;
- tiers 2, 5 and 6 clearly separate in colour (green / purple / crimson); tier 6 clearly redder and darker than tier 3.
