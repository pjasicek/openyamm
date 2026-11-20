# Codex brief: two small part textures for the Imp (mm9_imp_claude)

Scope: image generation only. Write ONLY into `level_generation/creatures/mm9_imp_claude/references_hd/`. No builds, no Meshy.
Use your built-in image generation tool. Stop after these two images; at most one correction each.

## 06_wrap.png (input 1: `mm9_wrap_x10.png`, the original low-res skin of this part, colour and design authority)
A flat, straight-on, seamless-left-to-right texture swatch filling the WHOLE 1536x1024 canvas edge to edge, opaque, no
background: black-brown worn leather wrapping as used on a small goblinoid's shin: a smooth dark base crossed by three
narrow horizontal steel-grey metal bands with a soft highlight, each band with a thin dark outline. No studs, no folds
that would read as a separate object, no perspective, no lighting gradient, no shadow, no text. It will be wrapped round
a cylinder, so left and right edges must match.

## 07_tongue.png (input 2: `mm9_tongue_x12.png`, the original low-res face with the tongue on the chin)
A demon's long pointed tongue seen straight from the front, hanging straight down, filling a 1024x1536 portrait canvas with
a true transparent background: glossy wet dark red to crimson, a central groove, a pointed tip, darker at the root at the
top. No mouth, no teeth, no face. Even soft light, no shadow, no text.

Write `generation_runs_parts.json` (id, prompt, inputs with sha256, output path).
