# Codex brief: HD modelling masters for the Hierarch's throne (D12, the enthroned Hierarch 10145)

Scope: image generation only. Write ONLY into `level_generation/creatures/hes_noble_bosses_claude/references_hd/throne/`.
No other files, builds or Meshy. Built-in image generation; PIL only to check sizes/alpha and to make a plain
background transparent.

Design authority: the approved concept `design/kreegan_world/concepts/monsters/boss_hierarch.png` (input 1), its
large right view: the Hierarch enthroned on an alien bone/resin seat. Input 2 is a crop of that view. Draw **the throne
alone, empty** (no figure, no wings, no cables plugged in), as a solid 3D modelling reference.

The throne: a massive alien seat of pale ivory bone and white ceramic grown over black-violet ribbed resin, with
restrained gold grafts and orange-glowing conduit seams/ports; a tall swept backrest of fused curved bone ribs and
spikes (taller than a seated giant's head), two broad armrests ending in curved bone claws, a deep seat, a heavy
flared base of bone buttresses on the floor, a round orange-glowing coupling port in the backrest centre where the
spinal cables plug in, thick resin cable bundles running from the back of the backrest down into the base. Proportions
for a seated giant: seat surface at about one third of the backrest height; seat about as deep as wide.

Deliverables, **1024 × 1536 portrait**, true transparent background, no floor, no shadow, no text, the whole throne
inside the frame, near-orthographic, even soft studio light:

| File | View |
|---|---|
| `00_three_quarter.png` | front three-quarter from the front left, slightly above the seat |
| `01_front.png` | straight front |
| `02_back.png` | straight back |
| `03_left.png` | strict profile of the throne's left side (its front faces image LEFT) |
| `04_right.png` | strict profile of its right side (front faces image RIGHT) |

Generate 00 first, then 01-04 with 00 attached so all five show the same throne. At most one corrective regeneration
per view. Save raw returns as `raw_<view>_<n>.png`; record prompts, input sha256 and selections in
`generation_runs.json`; write `selected_views_review.png`.

Do NOT draw: a figure, wings, people, scenery, a dais, steps, a floor, text.
