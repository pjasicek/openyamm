# Codex brief: HD halberd references for the MM9 Guard (mm9_guard_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_guard_claude/references_prop/`. No builds, no Meshy.
Use your built-in image generation tool. The authority is the ORIGINAL Might and Magic IX low-poly polearm with its skin.

## Inputs (attached, in order)
1. `mm9_pole_a.png`: render of the whole original pole, in the plane of its blades: spike at IMAGE LEFT, butt at IMAGE RIGHT.
2. `mm9_head_a.png`: enlargement of its head. Silhouette authority.
3. `mm9_pole_skin_a_x12.png`: its 64x64 skin enlarged: surface and colour only.
4. `mm9_pole_c.png`, 5. `mm9_head_c.png`, 6. `mm9_pole_skin_c_x12.png`: the Captain's version: same shapes, darker steel, dark wood shaft with steel studs.

## Deliverables: true transparent background, flat orthographic view straight onto the blade plane, even soft light, no shadow, no text, 1536x1024
| File | Content |
|---|---|
| `head_a.png` | Guard halberd HEAD only, spike pointing IMAGE LEFT, shaft leaving at IMAGE RIGHT edge region (show about 18 cm of shaft and end it with a clean straight cut well inside the frame) |
| `shaft_a.png` | Guard SHAFT only, whole length, horizontal, from the neck to the butt: pale polished steel-sheathed pole, dark leather-wrapped grip with steel collars near the butt end at IMAGE RIGHT, small pointed steel butt cap |
| `head_c.png`, `shaft_c.png` | The Captain's version: darker blued steel blades with bright worn edges, dark red-brown wooden pole with a row of round steel studs, brown leather grip, steel collars |

Run A then C in one run, with the selected `head_a.png` as an extra input for `head_c.png` so the outline is IDENTICAL.

## Shape (head files, exactly the silhouette of input 2)
A long-spiked poleaxe. On the axis a slim conical top spike. At right angles, from a socket on the pole, one big axe blade on the IMAGE-BOTTOM side: a neck widening to a blade with a straight wide cutting edge whose two points sweep out: a long point backward toward the butt (to IMAGE RIGHT), a short barb forward. On the IMAGE-TOP side a smaller fluke: a neck that opens into a T-shaped hooked head with two points. A narrow slit of air separates each neck from the shaft next to the socket as on input 2 is not required: blades simply join the socket. Forged steel, hammer marks, worn bright edges, a fine bevel along the cutting edge; a credible heavy weapon, not ornate.

Keep the outline clean and hard-edged. Single object, centred, margins, no hand, no stand, no glow, no decoration added.

Checks: transparent background, spike toward IMAGE LEFT, big blade on IMAGE BOTTOM, smaller T-fluke on IMAGE TOP, the same outline in A and C, 1536x1024. At most one corrective regeneration per file. Write `generation_runs.json` (id, prompt, inputs with sha256, output, selected, reason). Keep raw returns in `raw/`.
