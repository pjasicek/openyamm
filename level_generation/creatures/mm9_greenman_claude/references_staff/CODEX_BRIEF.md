# Codex brief: bark texture for The Green Man's staff (mm9_greenman_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_greenman_claude/references_staff/`. No
builds, no Meshy, no other files.

## Inputs (attached, in order)
1. `source/mm9/skins/greenmanstaff.png` — the original 64x64 MM9 staff skin: dark brown wood with wavy vertical grain.
   COLOUR AND MATERIAL authority (dark, warm brown wood; not grey).
2. `references_head/03_back.png` — the approved HD head master: its bark branches show the bark style of this character.

## Deliverable
`staff_bark.png`: 1024x1536 portrait, opaque (no transparency), a FLAT, evenly lit, straight-on texture swatch of
old gnarled walking-staff wood: dark warm brown bark-worn wood with long wavy VERTICAL grain, a few small knots and
shallow cracks, some smoother worn areas where hands grip, faint green moss flecks in a few cracks. It must tile
SEAMLESSLY left-to-right and top-to-bottom (it wraps around a cylinder and repeats along it). No object, no staff
silhouette, no shading toward the edges, no perspective, no shadows, no highlights, no text, no border. Sharp fine
detail at full resolution.

Also write `generation_runs.json` (prompt, inputs with sha256, output, notes). One corrective regeneration at most.
